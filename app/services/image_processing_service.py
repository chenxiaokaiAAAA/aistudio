# -*- coding: utf-8 -*-
"""
图片处理服务 - 串联美图API和AI工作流
"""
import os
import sys
import threading
import time
from datetime import datetime

def process_order_images(order_id, order_number=None, style_category_id=None, style_image_id=None):
    """
    处理订单图片：先经过美图API（如果启用），然后调用AI工作流
    
    Args:
        order_id: 订单ID
        order_number: 订单号（可选）
        style_category_id: 风格分类ID（可选）
        style_image_id: 风格图片ID（可选）
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # 获取数据库模型
        if 'test_server' not in sys.modules:
            return False, "数据库未初始化"
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        Order = test_server_module.Order
        OrderImage = test_server_module.OrderImage
        MeituAPIConfig = test_server_module.MeituAPIConfig
        MeituAPIPreset = test_server_module.MeituAPIPreset
        MeituAPICallLog = test_server_module.MeituAPICallLog
        
        # 获取订单
        order = Order.query.get(order_id)
        if not order:
            return False, "订单不存在"
        
        # 获取订单的所有原图（支持多图处理）
        app = test_server_module.app
        all_images = OrderImage.query.filter_by(order_id=order.id).all()
        
        if not all_images:
            return False, "订单没有上传的图片"
        
        # 获取所有图片路径
        image_paths = []
        for img in all_images:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], img.path)
            if os.path.exists(img_path):
                image_paths.append({
                    'path': img_path,
                    'order_image': img,
                    'is_main': img.is_main
                })
        
        if not image_paths:
            return False, "订单没有可用的图片文件"
        
        # 优先使用主图，如果没有主图则使用第一张
        main_image_info = next((img for img in image_paths if img['is_main']), image_paths[0])
        original_image_path = main_image_info['path']
        
        # 检查美图API是否在流程中启用
        meitu_config = MeituAPIConfig.query.filter_by(is_active=True).first()
        use_meitu = False
        retouched_image_path = None
        
        if meitu_config and meitu_config.enable_in_workflow:
            print(f"✅ 美图API已在流程中启用，开始处理订单 {order_number or order.order_number} 的图片")
            use_meitu = True
            
            # 获取预设ID（根据风格分类或风格图片）
            preset_id = None
            if style_category_id:
                preset = MeituAPIPreset.query.filter_by(
                    style_category_id=style_category_id,
                    is_active=True
                ).first()
                if preset:
                    preset_id = preset.preset_id
            elif style_image_id:
                preset = MeituAPIPreset.query.filter_by(
                    style_image_id=style_image_id,
                    is_active=True
                ).first()
                if preset:
                    preset_id = preset.preset_id
            
            if preset_id:
                # 调用美图API（带超时和轮询处理）
                try:
                    from app.services.meitu_api_service import call_meitu_api, download_result_image
                    import json
                    import requests
                    
                    print(f"📞 调用美图API，预设ID: {preset_id}")
                    start_time = time.time()
                    
                    # 设置总超时时间（120秒 = 2分钟）
                    total_timeout = 120
                    poll_interval = 3  # 每3秒轮询一次
                    max_poll_attempts = total_timeout // poll_interval  # 最多轮询次数
                    
                    # 调用美图API（异步接口，返回msg_id）
                    success, result_path, error_msg, call_log = call_meitu_api(
                        image_path=original_image_path,
                        preset_id=preset_id,
                        api_key=meitu_config.api_key,
                        api_secret=meitu_config.api_secret,
                        api_base_url=meitu_config.api_base_url,
                        api_endpoint=meitu_config.api_endpoint,
                        repost_url=meitu_config.repost_url,
                        db=db,
                        MeituAPICallLog=MeituAPICallLog,
                        order_id=order.id,
                        order_number=order.order_number
                    )
                    
                    if not success or not call_log:
                        print(f"❌ 美图API调用失败: {error_msg}，跳过美图处理，直接进行AI工作流")
                        use_meitu = False
                    else:
                        # 解析msg_id（从call_log的response_data中获取）
                        msg_id = None
                        if call_log.response_data:
                            try:
                                response_data = json.loads(call_log.response_data)
                                msg_id = response_data.get('msg_id')
                            except:
                                pass
                        
                        if not msg_id:
                            print(f"⚠️  未获取到msg_id，跳过美图处理，直接进行AI工作流")
                            use_meitu = False
                        else:
                            # 轮询查询结果（最多等待2分钟）
                            print(f"🔄 开始轮询美图API结果，msg_id: {msg_id}")
                            result_found = False
                            
                            for attempt in range(max_poll_attempts):
                                elapsed_time = time.time() - start_time
                                if elapsed_time >= total_timeout:
                                    print(f"⏱️  美图API轮询超时（{elapsed_time:.2f}秒），跳过美图处理，直接进行AI工作流")
                                    use_meitu = False
                                    break
                                
                                # 查询结果（通过查询call_log的状态）
                                db.session.refresh(call_log)
                                
                                if call_log.status == 'success' and call_log.result_image_url:
                                    # 成功获取结果
                                    result_image_url = call_log.result_image_url
                                    print(f"✅ 美图API处理完成，结果图片URL: {result_image_url}")
                                    
                                    # 下载结果图片
                                    result_image_path = download_result_image(result_image_url, order.order_number)
                                    if result_image_path and os.path.exists(result_image_path):
                                        retouched_image_path = result_image_path
                                        result_found = True
                                        
                                        # 保存美颜后的图片到订单
                                        retouched_image = OrderImage(
                                            order_id=order.id,
                                            path=os.path.basename(retouched_image_path),
                                            image_type='retouched',
                                            is_main=False
                                        )
                                        db.session.add(retouched_image)
                                        
                                        # 更新订单的美颜完成时间
                                        if hasattr(order, 'retouch_completed_at'):
                                            order.retouch_completed_at = datetime.now()
                                        
                                        # 更新订单状态为"美颜处理中"（如果当前状态是shooting）
                                        if hasattr(order, 'status') and order.status in ['shooting', 'paid']:
                                            order.status = 'retouching'  # 美颜处理中
                                        
                                        db.session.commit()
                                        print(f"✅ 美颜后的图片已保存到订单: {retouched_image_path}")
                                        break
                                    else:
                                        print(f"⚠️  下载美图结果图片失败，跳过美图处理")
                                        use_meitu = False
                                        break
                                
                                elif call_log.status == 'failed':
                                    # 处理失败
                                    error_msg = call_log.error_message or '未知错误'
                                    print(f"❌ 美图API处理失败: {error_msg}，跳过美图处理，直接进行AI工作流")
                                    use_meitu = False
                                    break
                                
                                # 等待后继续轮询
                                time.sleep(poll_interval)
                                print(f"⏳ 等待美图API结果... ({attempt + 1}/{max_poll_attempts})")
                            
                            if not result_found and use_meitu:
                                # 轮询结束但未找到结果
                                elapsed_time = time.time() - start_time
                                print(f"⏱️  美图API轮询超时（{elapsed_time:.2f}秒），跳过美图处理，直接进行AI工作流")
                                use_meitu = False
                
                except Exception as e:
                    print(f"❌ 调用美图API异常: {str(e)}，跳过美图处理，直接进行AI工作流")
                    import traceback
                    traceback.print_exc()
                    use_meitu = False
            else:
                print(f"⚠️  未找到对应的美图API预设配置，跳过美图处理")
                use_meitu = False
        
        # 调用AI工作流处理
        print(f"🤖 开始调用AI工作流处理订单 {order_number or order.order_number}")
        
        # 确定使用的图片路径（优先使用美颜后的图片）
        input_image_path = retouched_image_path if (use_meitu and retouched_image_path) else original_image_path
        
        # 获取风格分类ID（如果未提供）
        if not style_category_id and order.style_category_id:
            style_category_id = order.style_category_id
        
        if not style_category_id:
            return False, "订单没有关联的风格分类"
        
        # 调用AI工作流服务（使用任务队列）
        try:
            from app.services.task_queue_service import submit_task
            
            # 提交任务到队列
            task_data = {
                'order_id': order.id,
                'style_category_id': style_category_id,
                'style_image_id': style_image_id,
                'kwargs': {
                    'db': db,
                    'Order': Order,
                    'AITask': test_server_module.AITask if hasattr(test_server_module, 'AITask') else None,
                    'StyleCategory': test_server_module.StyleCategory if hasattr(test_server_module, 'StyleCategory') else None,
                    'StyleImage': test_server_module.StyleImage if hasattr(test_server_module, 'StyleImage') else None,
                    'OrderImage': OrderImage
                }
            }
            
            # 提交到队列（如果队列未启动，回退到直接调用）
            queue_submitted = submit_task('comfyui', task_data)
            
            if queue_submitted:
                print(f"✅ AI工作流任务已提交到队列，订单ID: {order.id}")
                return True, "图片处理流程已提交到队列"
            else:
                # 队列提交失败，回退到直接调用（兼容模式）
                print(f"⚠️ 队列提交失败，使用直接调用模式")
                from app.services.workflow_service import create_ai_task
                
                success, ai_task, error_message = create_ai_task(
                    order_id=order.id,
                    style_category_id=style_category_id,
                    style_image_id=style_image_id,
                    db=db,
                    Order=Order,
                    AITask=test_server_module.AITask if hasattr(test_server_module, 'AITask') else None,
                    StyleCategory=test_server_module.StyleCategory if hasattr(test_server_module, 'StyleCategory') else None,
                    StyleImage=test_server_module.StyleImage if hasattr(test_server_module, 'StyleImage') else None,
                    OrderImage=OrderImage
                )
                
                if success:
                    print(f"✅ AI工作流任务创建成功，任务ID: {ai_task.id if ai_task else 'N/A'}")
                    return True, "图片处理流程启动成功"
                else:
                    print(f"❌ AI工作流任务创建失败: {error_message}")
                    return False, f"AI工作流任务创建失败: {error_message}"
        except ImportError:
            # 如果任务队列服务不可用，回退到直接调用
            print(f"⚠️ 任务队列服务不可用，使用直接调用模式")
            from app.services.workflow_service import create_ai_task
            
            success, ai_task, error_message = create_ai_task(
                order_id=order.id,
                style_category_id=style_category_id,
                style_image_id=style_image_id,
                db=db,
                Order=Order,
                AITask=test_server_module.AITask if hasattr(test_server_module, 'AITask') else None,
                StyleCategory=test_server_module.StyleCategory if hasattr(test_server_module, 'StyleCategory') else None,
                StyleImage=test_server_module.StyleImage if hasattr(test_server_module, 'StyleImage') else None,
                OrderImage=OrderImage
            )
            
            if success:
                print(f"✅ AI工作流任务创建成功，任务ID: {ai_task.id if ai_task else 'N/A'}")
                return True, "图片处理流程启动成功"
            else:
                print(f"❌ AI工作流任务创建失败: {error_message}")
                return False, f"AI工作流任务创建失败: {error_message}"
    
    except Exception as e:
        print(f"❌ 处理订单图片失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"处理失败: {str(e)}"

