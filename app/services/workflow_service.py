# -*- coding: utf-8 -*-
"""
AI工作流服务
处理ComfyUI工作流调用相关业务逻辑
"""
import json
import os
import time
import requests
from datetime import datetime, timedelta
from flask import current_app
from threading import Semaphore
from app.utils.config_loader import get_int_config

# 限流机制：限制ComfyUI并发调用数（从数据库读取配置）
def get_comfyui_semaphore():
    """获取ComfyUI信号量（动态从数据库读取配置）"""
    max_concurrency = get_int_config('comfyui_max_concurrency', 10)
    return Semaphore(max_concurrency)

# 全局信号量（会在首次使用时初始化）
COMFYUI_SEMAPHORE = None

def _get_comfyui_semaphore():
    """获取或创建ComfyUI信号量"""
    global COMFYUI_SEMAPHORE
    if COMFYUI_SEMAPHORE is None:
        max_concurrency = get_int_config('comfyui_max_concurrency', 10)
        COMFYUI_SEMAPHORE = Semaphore(max_concurrency)
        print(f"✅ ComfyUI并发信号量已初始化: {max_concurrency}")
    return COMFYUI_SEMAPHORE


def get_workflow_config(style_category_id, style_image_id=None, db=None, StyleCategory=None, StyleImage=None):
    """
    获取工作流配置（支持混合方案：图片级别 > 分类级别）
    
    Args:
        style_category_id: 风格分类ID
        style_image_id: 风格图片ID（可选）
        db: 数据库实例
        StyleCategory: StyleCategory模型类
        StyleImage: StyleImage模型类
    
    Returns:
        dict: 工作流配置，如果未启用则返回None
    """
    if not all([db, StyleCategory, StyleImage]):
        # 尝试从test_server获取
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                db = test_server_module.db
            if hasattr(test_server_module, 'StyleCategory'):
                StyleCategory = test_server_module.StyleCategory
            if hasattr(test_server_module, 'StyleImage'):
                StyleImage = test_server_module.StyleImage
    
    if not all([db, StyleCategory, StyleImage]):
        print("❌ 无法获取数据库模型，请确保db、StyleCategory、StyleImage已初始化")
        return None
    
    config = {}
    
    # 1. 获取分类级别配置
    category = StyleCategory.query.get(style_category_id)
    if not category or not category.is_ai_enabled:
        return None
    
    config = {
        'workflow_name': category.workflow_name,
        'workflow_file': category.workflow_file,
        'workflow_input_ids': json.loads(category.workflow_input_ids) if category.workflow_input_ids else [],
        'workflow_output_id': category.workflow_output_id,
        'workflow_ref_id': category.workflow_ref_id,
        'workflow_ref_image': category.workflow_ref_image,
        'workflow_user_prompt_id': category.workflow_user_prompt_id,
        'workflow_custom_prompt_id': category.workflow_custom_prompt_id,
        'workflow_custom_prompt_content': category.workflow_custom_prompt_content,
    }
    
    # 2. 如果指定了风格图片，检查是否有图片级别配置（覆盖分类配置）
    if style_image_id:
        style_image = StyleImage.query.get(style_image_id)
        if style_image:
            # 如果图片级别启用了AI，使用图片级别配置
            if style_image.is_ai_enabled is True:
                if style_image.workflow_name:
                    config['workflow_name'] = style_image.workflow_name
                if style_image.workflow_file:
                    config['workflow_file'] = style_image.workflow_file
                if style_image.workflow_input_ids:
                    config['workflow_input_ids'] = json.loads(style_image.workflow_input_ids)
                if style_image.workflow_output_id:
                    config['workflow_output_id'] = style_image.workflow_output_id
                if style_image.workflow_ref_id:
                    config['workflow_ref_id'] = style_image.workflow_ref_id
                if style_image.workflow_ref_image:
                    config['workflow_ref_image'] = style_image.workflow_ref_image
                if style_image.workflow_custom_prompt_id:
                    config['workflow_custom_prompt_id'] = style_image.workflow_custom_prompt_id
                if style_image.workflow_custom_prompt_content:
                    config['workflow_custom_prompt_content'] = style_image.workflow_custom_prompt_content
            # 如果图片级别明确禁用AI，返回None
            elif style_image.is_ai_enabled is False:
                return None
    
    return config


def get_input_image(order, db=None, OrderImage=None):
    """
    获取输入图片（优先使用美颜后的图片，否则使用原图）
    
    Args:
        order: Order对象
        db: 数据库实例
        OrderImage: OrderImage模型类
    
    Returns:
        tuple: (image_path: str, image_type: str)  # image_type: 'original' or 'retouched'
    """
    if not db or not OrderImage:
        # 尝试从test_server获取
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                db = test_server_module.db
            if hasattr(test_server_module, 'OrderImage'):
                OrderImage = test_server_module.OrderImage
    
    # 1. 检查是否优先使用美颜后的图片
    prefer_retouched = get_ai_config('prefer_retouched_image', db=db)
    if prefer_retouched and prefer_retouched.lower() == 'true':
        # 2. 检查是否有美颜后的图片（retouch_completed_at不为空）
        if order.retouch_completed_at:
            # 查找美颜后的图片（假设美颜后的图片有特定标识，或存储在特定字段）
            # 这里需要根据实际业务逻辑实现
            # 暂时假设美颜后的图片路径可以通过某种方式获取
            # 例如：如果Order有retouched_image字段，或通过OrderImage的某个标识
            retouched_image = get_retouched_image_path(order, db=db, OrderImage=OrderImage)
            if retouched_image and os.path.exists(retouched_image):
                return retouched_image, 'retouched'
    
    # 3. 使用原图（从OrderImage或original_image字段获取）
    original_image = get_original_image_path(order, db=db, OrderImage=OrderImage)
    if original_image and os.path.exists(original_image):
        return original_image, 'original'
    
    return None, None


def get_retouched_image_path(order, db=None, OrderImage=None):
    """
    获取美颜后的图片路径
    注意：这里需要根据实际业务逻辑实现
    """
    # 如果Order有retouched_image字段，直接返回
    if hasattr(order, 'retouched_image') and order.retouched_image:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads') if current_app else 'uploads'
        image_path = os.path.join(upload_folder, order.retouched_image)
        if os.path.exists(image_path):
            return image_path
    
    # 或者通过OrderImage查找（需要根据实际业务逻辑）
    # 这里暂时返回None，需要根据实际实现
    return None


def get_original_image_path(order, db=None, OrderImage=None):
    """
    获取原图路径
    """
    if not db or not OrderImage:
        # 尝试从test_server获取
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                db = test_server_module.db
            if hasattr(test_server_module, 'OrderImage'):
                OrderImage = test_server_module.OrderImage
    
    # 1. 优先从OrderImage获取
    if db and OrderImage:
        order_images = OrderImage.query.filter_by(order_id=order.id).all()
        if order_images:
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads') if current_app else 'uploads'
            # 取第一张图片
            image_path = os.path.join(upload_folder, order_images[0].path)
            if os.path.exists(image_path):
                return image_path
    
    # 2. 从Order.original_image字段获取
    if order.original_image:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads') if current_app else 'uploads'
        image_path = os.path.join(upload_folder, order.original_image)
        if os.path.exists(image_path):
            return image_path
    
    return None


def get_comfyui_config(db=None, AIConfig=None):
    """
    从数据库获取ComfyUI配置
    
    Returns:
        dict: ComfyUI配置
    """
    if not db or not AIConfig:
        # 尝试从test_server获取
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                db = test_server_module.db
            if hasattr(test_server_module, 'AIConfig'):
                AIConfig = test_server_module.AIConfig
    
    result = {
        'base_url': 'http://127.0.0.1:8187',  # 默认值
        'api_endpoint': '/api/prompt',
        'timeout': '300'
    }
    
    if db and AIConfig:
        configs = AIConfig.query.all()
        for config in configs:
            if config.config_key == 'comfyui_base_url':
                result['base_url'] = config.config_value
                print(f"📝 从数据库读取ComfyUI地址: {config.config_value}")
            elif config.config_key == 'comfyui_api_endpoint':
                result['api_endpoint'] = config.config_value
            elif config.config_key == 'comfyui_timeout':
                result['timeout'] = config.config_value
    else:
        print(f"⚠️ 无法获取数据库配置，使用默认值: {result['base_url']}")
    
    return result


def get_ai_config(config_key, default_value=None, db=None, AIConfig=None):
    """
    获取AI配置项
    
    Args:
        config_key: 配置键
        default_value: 默认值
        db: 数据库实例
        AIConfig: AIConfig模型类
    
    Returns:
        str: 配置值
    """
    if not db or not AIConfig:
        # 尝试从test_server获取
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                db = test_server_module.db
            if hasattr(test_server_module, 'AIConfig'):
                AIConfig = test_server_module.AIConfig
    
    if db and AIConfig:
        config = AIConfig.query.filter_by(config_key=config_key).first()
        if config:
            return config.config_value
    
    return default_value


def load_workflow_file(workflow_file):
    """
    加载工作流JSON文件
    
    Args:
        workflow_file: 工作流文件名
    
    Returns:
        dict: 工作流数据（节点字典格式，节点ID为键）
    
    注意：只支持ComfyUI API格式：{"prompt": {...}}
    此函数会提取prompt字段的内容并返回
    """
    # 查找工作流文件
    workflow_paths = [
        os.path.join('workflows', workflow_file),
        os.path.join('AI-studio', 'workflows', workflow_file),
        os.path.join(os.path.dirname(__file__), '..', '..', 'workflows', workflow_file)
    ]
    
    workflow_path = None
    for path in workflow_paths:
        if os.path.exists(path):
            workflow_path = path
            break
    
    if not workflow_path:
        raise FileNotFoundError(f"工作流文件不存在: {workflow_file}")
    
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow_data = json.load(f)
    
    # 处理不同的ComfyUI导出格式
    # 1. API格式：{"prompt": {...}} - 包含prompt字段
    if isinstance(workflow_data, dict) and 'prompt' in workflow_data:
        return workflow_data['prompt']
    
    # 2. 工作流格式：直接是节点字典（节点ID为键）
    # 3. 其他格式：直接返回，让调用方处理
    return workflow_data


def create_ai_task(order_id, style_category_id, style_image_id=None, order_image_id=None, db=None, Order=None, AITask=None, StyleCategory=None, StyleImage=None, OrderImage=None, workflow_config=None):
    """
    创建AI任务并提交到ComfyUI
    
    Args:
        order_id: 订单ID
        style_category_id: 风格分类ID
        style_image_id: 风格图片ID（可选）
        order_image_id: OrderImage的ID（可选，如果提供则处理指定的图片，否则处理主图或第一张）
        db: 数据库实例
        Order: Order模型类
        AITask: AITask模型类
        StyleCategory: StyleCategory模型类
        StyleImage: StyleImage模型类
        OrderImage: OrderImage模型类
        workflow_config: 工作流配置字典（可选，如果提供则直接使用，否则从数据库读取）
    
    Returns:
        tuple: (success: bool, task: AITask, error_message: str)
    """
    try:
        # 获取数据库模型（如果未传入）
        if not all([db, Order, AITask, StyleCategory, StyleImage, OrderImage]):
            import sys
            if 'test_server' in sys.modules:
                test_server_module = sys.modules['test_server']
                if hasattr(test_server_module, 'db'):
                    db = test_server_module.db
                if hasattr(test_server_module, 'Order'):
                    Order = test_server_module.Order
                if hasattr(test_server_module, 'AITask'):
                    AITask = test_server_module.AITask
                if hasattr(test_server_module, 'StyleCategory'):
                    StyleCategory = test_server_module.StyleCategory
                if hasattr(test_server_module, 'StyleImage'):
                    StyleImage = test_server_module.StyleImage
                if hasattr(test_server_module, 'OrderImage'):
                    OrderImage = test_server_module.OrderImage
        
        if not all([db, Order, AITask, StyleCategory, StyleImage, OrderImage]):
            return False, None, "数据库模型未初始化"
        
        # 1. 获取订单（使用悲观锁防止并发）
        from sqlalchemy import select
        try:
            order = db.session.execute(
                select(Order).where(Order.id == order_id).with_for_update()
            ).scalar_one_or_none()
        except:
            # 如果with_for_update不支持，回退到普通查询
            order = Order.query.get(order_id)
        
        if not order:
            return False, None, "订单不存在"
        
        # 1.1 检查是否已有相同订单和图片的待处理/处理中任务（防重复提交）
        # 如果指定了order_image_id，则检查该图片是否已有任务；否则检查订单是否已有任务
        try:
            if order_image_id:
                # 获取该order_image对应的图片路径
                target_image = OrderImage.query.get(order_image_id)
                if target_image:
                    # 获取app实例以获取upload_folder配置
                    app = None
                    import sys
                    if 'test_server' in sys.modules:
                        test_server_module = sys.modules['test_server']
                        if hasattr(test_server_module, 'app'):
                            app = test_server_module.app
                    if not app:
                        from flask import current_app
                        try:
                            app = current_app
                        except:
                            pass
                    
                    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads') if app else 'uploads'
                    expected_path = os.path.join(upload_folder, target_image.path)
                    
                    # 检查该订单的该图片是否已有任务（通过input_image_path匹配）
                    existing_tasks = db.session.execute(
                        select(AITask).where(
                            AITask.order_id == order_id,
                            AITask.status.in_(['pending', 'processing'])
                        ).with_for_update()
                    ).scalars().all()
                    
                    # 检查是否有任务处理的是同一张图片
                    for existing_task in existing_tasks:
                        if existing_task.input_image_path == expected_path or existing_task.input_image_path == target_image.path:
                            print(f"⚠️ 订单 {order_id} 的图片 {order_image_id} 已有待处理/处理中的任务（ID: {existing_task.id}），跳过重复创建")
                            return True, existing_task, None
                    # 如果没有找到同一张图片的任务，允许创建新任务（不同图片可以有不同的任务）
            else:
                # 没有指定order_image_id，检查订单是否已有任务（保持向后兼容）
                existing_task = db.session.execute(
                    select(AITask).where(
                        AITask.order_id == order_id,
                        AITask.status.in_(['pending', 'processing'])
                    ).with_for_update()
                ).scalar_one_or_none()
                if existing_task:
                    print(f"⚠️ 订单 {order_id} 已有待处理/处理中的任务（ID: {existing_task.id}），跳过重复创建")
                    return True, existing_task, None
        except:
            # 如果with_for_update不支持，使用普通查询
            if order_image_id:
                existing_task = AITask.query.filter_by(
                    order_id=order_id
                ).filter(
                    AITask.status.in_(['pending', 'processing'])
                ).first()
                # 进一步检查是否是同一张图片的任务
                if existing_task:
                    target_image = OrderImage.query.get(order_image_id)
                    if target_image:
                        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads') if app else 'uploads'
                        expected_path = os.path.join(upload_folder, target_image.path)
                        if existing_task.input_image_path == expected_path or existing_task.input_image_path == target_image.path:
                            print(f"⚠️ 订单 {order_id} 的图片 {order_image_id} 已有待处理/处理中的任务（ID: {existing_task.id}），跳过重复创建")
                            return True, existing_task, None
            else:
                existing_task = AITask.query.filter_by(
                    order_id=order_id
                ).filter(
                    AITask.status.in_(['pending', 'processing'])
                ).first()
                if existing_task:
                    print(f"⚠️ 订单 {order_id} 已有待处理/处理中的任务（ID: {existing_task.id}），跳过重复创建")
                    return True, existing_task, None
        
        # 2. 获取工作流配置
        # 如果传入了workflow_config，直接使用；否则从数据库读取
        if workflow_config is None:
            workflow_config = get_workflow_config(style_category_id, style_image_id, db=db, StyleCategory=StyleCategory, StyleImage=StyleImage)
            if not workflow_config:
                return False, None, "工作流未启用或配置不存在"
        else:
            # 验证传入的workflow_config是否完整
            required_keys = ['workflow_file', 'workflow_input_ids', 'workflow_output_id']
            missing_keys = [key for key in required_keys if not workflow_config.get(key)]
            if missing_keys:
                return False, None, f"工作流配置不完整，缺少: {', '.join(missing_keys)}"
            
            # 确保workflow_name存在（如果没有则使用默认值）
            if 'workflow_name' not in workflow_config:
                workflow_config['workflow_name'] = '测试工作流'
        
        # 3. 获取输入图片（如果指定了order_image_id，则处理指定的图片；否则处理主图或第一张）
        if order_image_id:
            # 处理指定的图片
            target_image = OrderImage.query.get(order_image_id)
            if not target_image or target_image.order_id != order_id:
                return False, None, f"指定的图片不存在或不属于该订单: order_image_id={order_image_id}"
            
            # 获取图片路径
            app = None
            import sys
            if 'test_server' in sys.modules:
                test_server_module = sys.modules['test_server']
                if hasattr(test_server_module, 'app'):
                    app = test_server_module.app
            
            if not app:
                from flask import current_app
                app = current_app
            
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads') if app else 'uploads'
            input_image_path = os.path.join(upload_folder, target_image.path)
            
            if not os.path.exists(input_image_path):
                return False, None, f"图片文件不存在: {input_image_path}"
            
            # 检查是否优先使用美颜后的图片（只有主图才有美颜后的图片）
            prefer_retouched = get_ai_config('prefer_retouched_image', db=db)
            if prefer_retouched and prefer_retouched.lower() == 'true' and order.retouch_completed_at and target_image.is_main:
                retouched_image = get_retouched_image_path(order, db=db, OrderImage=OrderImage)
                if retouched_image and os.path.exists(retouched_image):
                    input_image_path = retouched_image
                    input_image_type = 'retouched'
                else:
                    input_image_type = 'original'
            else:
                input_image_type = 'original'
            
            print(f"📸 处理指定的图片: {target_image.path} (order_image_id={order_image_id})")
        else:
            # 处理主图或第一张（保持向后兼容）
            input_image_path, input_image_type = get_input_image(order, db=db, OrderImage=OrderImage)
            if not input_image_path:
                return False, None, "订单没有可用的输入图片"
        
        # 4. 创建AI任务记录
        ai_task = AITask(
            order_id=order_id,
            order_number=order.order_number,
            workflow_name=workflow_config['workflow_name'],
            workflow_file=workflow_config['workflow_file'],
            style_category_id=style_category_id,
            style_image_id=style_image_id,
            input_image_path=input_image_path,
            input_image_type=input_image_type,
            status='pending'
        )
        db.session.add(ai_task)
        
        # 更新订单状态为"AI任务处理中"（如果当前状态是retouching或shooting）
        if order.status in ['retouching', 'shooting', 'paid']:
            order.status = 'ai_processing'  # AI任务处理中
            print(f"✅ 订单 {order.order_number} 状态已更新为: ai_processing")
        
        db.session.commit()
        
        # 5. 加载工作流JSON文件
        try:
            workflow_data = load_workflow_file(workflow_config['workflow_file'])
        except FileNotFoundError as e:
            ai_task.status = 'failed'
            ai_task.error_message = str(e)
            db.session.commit()
            return False, ai_task, str(e)
        
        # 6. 获取ComfyUI配置
        # 尝试获取AIConfig模型
        AIConfig_model = None
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'AIConfig'):
                AIConfig_model = test_server_module.AIConfig
        
        comfyui_config = get_comfyui_config(db=db, AIConfig=AIConfig_model)
        
        # 7. 上传图片到ComfyUI服务器，并替换工作流参数
        input_ids = workflow_config['workflow_input_ids']
        if input_ids and len(input_ids) > 0:
            # ComfyUI需要图片在输入目录中，需要通过API上传
            comfyui_base_url = comfyui_config.get('base_url', 'http://127.0.0.1:8188')
            comfyui_upload_url = f"{comfyui_base_url.rstrip('/')}/upload/image"
            
            # 上传图片到ComfyUI
            comfyui_image_filename = None
            try:
                print(f"📤 开始上传图片到ComfyUI: {comfyui_upload_url}")
                print(f"   本地图片路径: {input_image_path}")
                
                # 优化：先检查文件大小，如果文件很大，可以考虑压缩或跳过上传（使用已有文件）
                file_size = os.path.getsize(input_image_path)
                file_size_mb = file_size / (1024 * 1024)
                print(f"   文件大小: {file_size_mb:.2f} MB")
                
                # 读取图片文件
                with open(input_image_path, 'rb') as f:
                    # 生成唯一的文件名（避免冲突）
                    original_filename = os.path.basename(input_image_path)
                    name, ext = os.path.splitext(original_filename)
                    upload_filename = f"{name}_{ai_task.id}_{int(time.time())}{ext}"
                    
                    # 上传文件（ComfyUI的/upload/image API）
                    # 优化：减少超时时间到5秒（本地ComfyUI应该很快），加快响应速度
                    files = {
                        'image': (upload_filename, f, 'image/jpeg' if ext.lower() in ['.jpg', '.jpeg'] else 'image/png')
                    }
                    
                    import time as time_module
                    upload_start_time = time_module.time()
                    upload_response = requests.post(
                        comfyui_upload_url,
                        files=files,
                        timeout=5,  # 进一步减少超时时间到5秒（本地ComfyUI应该很快）
                        proxies={'http': None, 'https': None}  # 禁用代理
                    )
                    upload_duration = time_module.time() - upload_start_time
                    print(f"   上传耗时: {upload_duration:.2f} 秒")
                    
                    if upload_response.status_code == 200:
                        upload_result = upload_response.json()
                        # ComfyUI返回格式通常是: {"name": "filename.jpg", "subfolder": "", "type": "input"}
                        comfyui_image_filename = upload_result.get('name', upload_filename)
                        print(f"✅ 图片已上传到ComfyUI: {comfyui_image_filename}")
                    else:
                        error_msg = f"上传图片到ComfyUI失败: HTTP {upload_response.status_code}, {upload_response.text}"
                        print(f"❌ {error_msg}")
                        # 如果上传失败，尝试使用原始文件名（可能文件已存在）
                        comfyui_image_filename = upload_filename
                        print(f"⚠️ 使用文件名作为后备方案: {comfyui_image_filename}")
                        
            except requests.exceptions.Timeout:
                # 超时：直接使用文件名，ComfyUI可能已经有这个文件
                original_filename = os.path.basename(input_image_path)
                comfyui_image_filename = original_filename
                print(f"⚠️ 上传图片超时，使用原始文件名: {comfyui_image_filename}")
            except Exception as e:
                error_msg = f"上传图片到ComfyUI异常: {str(e)}"
                print(f"❌ {error_msg}")
                # 如果上传失败，使用原始文件名作为后备
                comfyui_image_filename = os.path.basename(input_image_path)
                print(f"⚠️ 使用原始文件名作为后备方案: {comfyui_image_filename}")
            
            # 替换工作流中的图片路径（使用上传后的文件名）
            if isinstance(workflow_data, dict) and input_ids[0] in workflow_data:
                # ComfyUI的LoadImage节点使用文件名（相对于input目录）
                workflow_data[input_ids[0]]['inputs']['image'] = comfyui_image_filename
                print(f"📸 工作流节点 {input_ids[0]} 的图片路径已设置为: {comfyui_image_filename}")
        
        if workflow_config.get('workflow_ref_id') and workflow_config.get('workflow_ref_image'):
            ref_id = workflow_config['workflow_ref_id']
            if isinstance(workflow_data, dict) and ref_id in workflow_data:
                workflow_data[ref_id]['inputs']['image'] = workflow_config['workflow_ref_image']
        
        if workflow_config.get('workflow_custom_prompt_id') and workflow_config.get('workflow_custom_prompt_content'):
            prompt_id = workflow_config['workflow_custom_prompt_id']
            if isinstance(workflow_data, dict) and prompt_id in workflow_data:
                workflow_data[prompt_id]['inputs']['text'] = workflow_config['workflow_custom_prompt_content']
        
        # 8. 提交到ComfyUI（comfyui_config已在第6步获取）
        comfyui_url = f"{comfyui_config['base_url']}{comfyui_config['api_endpoint']}"
        
        print(f"🔗 使用ComfyUI地址: {comfyui_url}")
        
        # 8. 提交到ComfyUI
        request_body = {
            "prompt": workflow_data,
            "client_id": f"order_{order_id}_task_{ai_task.id}_{int(time.time())}"
        }
        
        try:
            # 使用信号量限制并发数（防止ComfyUI过载）
            # 优化：减少超时时间，加快响应速度（本地ComfyUI应该很快响应）
            semaphore = _get_comfyui_semaphore()
            semaphore.acquire()
            try:
                # 禁用代理，直接连接ComfyUI
                # 优化：本地ComfyUI应该很快响应，减少超时时间到30秒
                response = requests.post(
                    comfyui_url,
                    json=request_body,
                    timeout=30,  # 减少超时时间到30秒（本地ComfyUI应该很快）
                    proxies={'http': None, 'https': None}
                )
            finally:
                semaphore.release()
            
            if response.status_code == 200:
                result = response.json()
                prompt_id = result.get('prompt_id')
                
                # 9. 更新AI任务
                ai_task.comfyui_prompt_id = prompt_id
                ai_task.comfyui_node_id = workflow_config['workflow_output_id']
                ai_task.status = 'processing'
                ai_task.started_at = datetime.now()
                ai_task.comfyui_response = json.dumps(result, ensure_ascii=False)
                
                # 添加处理日志
                log_entry = {
                    "time": datetime.now().isoformat(),
                    "status": "submitted",
                    "message": f"已提交到ComfyUI，Prompt ID: {prompt_id}",
                    "level": "info"
                }
                ai_task.processing_log = json.dumps([log_entry], ensure_ascii=False)
                
                # 预计完成时间（可以根据历史数据估算，这里暂时不设置）
                db.session.commit()
                
                return True, ai_task, None
            else:
                ai_task.status = 'failed'
                ai_task.error_message = f"ComfyUI提交失败: {response.text}"
                ai_task.error_code = f"HTTP_{response.status_code}"
                db.session.commit()
                return False, ai_task, ai_task.error_message
        
        except requests.exceptions.RequestException as e:
            ai_task.status = 'failed'
            ai_task.error_message = f"ComfyUI请求异常: {str(e)}"
            ai_task.error_code = "REQUEST_EXCEPTION"
            db.session.commit()
            return False, ai_task, ai_task.error_message
    
    except Exception as e:
        if 'ai_task' in locals() and db:
            try:
                ai_task.status = 'failed'
                ai_task.error_message = str(e)
                db.session.commit()
            except:
                pass
        import traceback
        traceback.print_exc()
        return False, None, str(e)


def retry_ai_task(task_id, db=None, AITask=None, Order=None, StyleCategory=None, StyleImage=None, OrderImage=None):
    """
    重新处理AI任务
    
    Args:
        task_id: 任务ID
        db: 数据库实例
        AITask: AITask模型类
        Order: Order模型类
        StyleCategory: StyleCategory模型类
        StyleImage: StyleImage模型类
        OrderImage: OrderImage模型类
    
    Returns:
        tuple: (success: bool, task: AITask, error_message: str)
    """
    # 获取任务
    if not db or not AITask:
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                db = test_server_module.db
            if hasattr(test_server_module, 'AITask'):
                AITask = test_server_module.AITask
    
    if not db or not AITask:
        return False, None, "数据库模型未初始化"
    
    task = AITask.query.get(task_id)
    if not task:
        return False, None, "任务不存在"
    
    # 更新重试次数
    task.retry_count += 1
    task.status = 'pending'
    task.error_message = None
    task.error_code = None
    
    # 重新创建任务（使用原有的配置）
    return create_ai_task(
        task.order_id,
        task.style_category_id,
        task.style_image_id,
        db=db,
        Order=Order,
        AITask=AITask,
        StyleCategory=StyleCategory,
        StyleImage=StyleImage,
        OrderImage=OrderImage
    )
