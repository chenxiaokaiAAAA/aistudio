# -*- coding: utf-8 -*-
"""
AI任务管理路由
"""
from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import login_required, current_user
import os
import json
import requests
import time
from datetime import datetime
from urllib.parse import urlparse
from werkzeug.utils import secure_filename

ai_bp = Blueprint('ai', __name__, url_prefix='/admin/ai')

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@ai_bp.route('/tasks')
@login_required
def ai_tasks():
    """AI任务管理页面"""
    if current_user.role not in ['admin', 'operator']:
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    return render_template('admin/ai_tasks.html')


@ai_bp.route('/config')
@login_required
def ai_config():
    """AI配置管理页面"""
    if current_user.role not in ['admin', 'operator']:
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    return render_template('admin/ai_config.html')


# ============================================================================
# API接口
# ============================================================================

@ai_bp.route('/api/tasks', methods=['GET'])
@login_required
def get_ai_tasks():
    """获取AI任务列表"""
    try:
        # 获取数据库模型
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        AITask = test_server_module.AITask
        Order = test_server_module.Order
        StyleCategory = test_server_module.StyleCategory
        StyleImage = test_server_module.StyleImage
        APIProviderConfig = test_server_module.APIProviderConfig
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        order_number = request.args.get('order_number')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        image_type = request.args.get('image_type')
        
        # 构建查询
        query = AITask.query
        
        if status:
            query = query.filter_by(status=status)
        if order_number:
            query = query.filter(AITask.order_number.like(f'%{order_number}%'))
        if start_date:
            query = query.filter(AITask.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(AITask.created_at <= datetime.fromisoformat(end_date))
        if image_type:
            query = query.filter_by(input_image_type=image_type)
        
        # 分页
        pagination = query.order_by(AITask.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        tasks = []
        for task in pagination.items:
            # 获取关联信息
            style_category_name = None
            style_image_name = None
            if task.style_category_id:
                category = StyleCategory.query.get(task.style_category_id)
                if category:
                    style_category_name = category.name
            if task.style_image_id:
                image = StyleImage.query.get(task.style_image_id)
                if image:
                    style_image_name = image.name
            
            # 状态文本映射
            status_map = {
                'pending': '待处理',
                'processing': '处理中',
                'completed': '已完成',
                'failed': '失败',
                'cancelled': '已取消'
            }
            
            # 获取任务ID（comfyui_prompt_id或processing_log中的task_id）
            task_id = task.comfyui_prompt_id
            api_task_id = None  # API返回的任务ID（用于异步任务）
            api_info = {}
            if task.processing_log:
                try:
                    parsed_log = json.loads(task.processing_log)
                    # 检查是否是字典类型，如果是list则跳过
                    if isinstance(parsed_log, dict):
                        api_info = parsed_log
                        if not task_id:
                            task_id = api_info.get('task_id') or api_info.get('id')
                        # 提取API任务ID（异步API返回的taskId，如RunningHub）
                        api_task_id = api_info.get('api_task_id') or api_info.get('taskId') or api_info.get('task_id')
                    elif isinstance(parsed_log, list):
                        # 如果是list，记录警告但继续处理
                        print(f"⚠️ 任务 {task.id} 的 processing_log 是 list 类型，跳过解析")
                except:
                    pass
            # 如果没有从processing_log中提取到，尝试从comfyui_prompt_id获取
            if not api_task_id and task.comfyui_prompt_id:
                api_task_id = task.comfyui_prompt_id
            # 如果还没有，尝试从notes中提取（T8Star格式：T8_API_TASK_ID:xxx）
            if not api_task_id and task.notes:
                try:
                    if 'T8_API_TASK_ID:' in task.notes:
                        api_task_id = task.notes.split('T8_API_TASK_ID:')[1].split('|')[0].strip()
                except:
                    pass
            if not task_id:
                task_id = f"TASK_{task.id}"
            
            # 获取API服务商信息
            api_provider_name = None
            if isinstance(api_info, dict) and api_info.get('api_config_id'):
                api_config = APIProviderConfig.query.get(api_info['api_config_id'])
                if api_config:
                    api_provider_name = api_config.name
            elif api_info.get('api_config_name'):
                api_provider_name = api_info['api_config_name']
            
            # 计算完成耗时（秒）
            duration_seconds = None
            if task.completed_at and task.created_at:
                duration = task.completed_at - task.created_at
                duration_seconds = int(duration.total_seconds())
            
            # 获取请求参数和结果数据
            request_params = api_info.get('request_params')
            response_data = api_info.get('response_data')
            
            task_data = {
                'id': task.id,
                'task_id': task_id,  # 添加任务ID
                'api_task_id': api_task_id,  # API返回的任务ID（用于异步任务，如RunningHub的taskId）
                'order_id': task.order_id,
                'order_number': task.order_number,
                'input_image_path': task.input_image_path,
                'input_image_type': task.input_image_type,
                'output_image_path': task.output_image_path,
                'status': task.status,
                'status_text': status_map.get(task.status, task.status),
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'estimated_completion_time': task.estimated_completion_time.isoformat() if task.estimated_completion_time else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'error_message': task.error_message,
                'retry_count': task.retry_count,
                'notes': task.notes,  # 关键修复：添加notes字段，用于显示重试信息
                'workflow_name': task.workflow_name,
                'style_category_name': style_category_name,
                'style_image_name': style_image_name,
                # 新增字段
                'api_provider_name': api_provider_name,
                'duration_seconds': duration_seconds,
                'request_params': request_params,
                'response_data': response_data
            }
            tasks.append(task_data)
        
        return jsonify({
            'status': 'success',
            'data': {
                'tasks': tasks,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
    
    except Exception as e:
        print(f"获取AI任务列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取任务列表失败: {str(e)}'}), 500


@ai_bp.route('/api/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_ai_task_detail(task_id):
    """获取AI任务详情"""
    try:
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        AITask = test_server_module.AITask
        StyleCategory = test_server_module.StyleCategory
        StyleImage = test_server_module.StyleImage
        
        task = AITask.query.get_or_404(task_id)
        
        # 获取关联信息
        style_category_name = None
        style_image_name = None
        if task.style_category_id:
            category = StyleCategory.query.get(task.style_category_id)
            if category:
                style_category_name = category.name
        if task.style_image_id:
            image = StyleImage.query.get(task.style_image_id)
            if image:
                style_image_name = image.name
        
        # 解析处理日志
        processing_log = []
        if task.processing_log:
            try:
                processing_log = json.loads(task.processing_log)
            except:
                pass
        
        task_data = {
            'id': task.id,
            'order_id': task.order_id,
            'order_number': task.order_number,
            'workflow_name': task.workflow_name,
            'workflow_file': task.workflow_file,
            'style_category_id': task.style_category_id,
            'style_category_name': style_category_name,
            'style_image_id': task.style_image_id,
            'style_image_name': style_image_name,
            'input_image_path': task.input_image_path,
            'input_image_type': task.input_image_type,
            'output_image_path': task.output_image_path,
            'status': task.status,
            'comfyui_prompt_id': task.comfyui_prompt_id,
            'comfyui_node_id': task.comfyui_node_id,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'estimated_completion_time': task.estimated_completion_time.isoformat() if task.estimated_completion_time else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'error_message': task.error_message,
            'error_code': task.error_code,
            'retry_count': task.retry_count,
            'processing_log': processing_log,
            'comfyui_response': json.loads(task.comfyui_response) if task.comfyui_response else None,
            'notes': task.notes
        }
        
        return jsonify({
            'status': 'success',
            'data': task_data
        })
    
    except Exception as e:
        print(f"获取AI任务详情失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取任务详情失败: {str(e)}'}), 500


@ai_bp.route('/api/tasks/<int:task_id>/upload-image', methods=['POST'])
@login_required
def upload_task_image(task_id):
    """上传任务输入图片"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': '文件名为空'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'status': 'error', 'message': '不支持的文件格式'}), 400
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        AITask = test_server_module.AITask
        app = test_server_module.app
        
        task = AITask.query.get_or_404(task_id)
        
        # 保存文件
        filename = secure_filename(f"ai_task_{task_id}_{int(time.time())}_{file.filename}")
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # 更新任务
        task.input_image_path = file_path
        task.input_image_type = 'original'
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '图片上传成功',
            'data': {
                'input_image_path': file_path,
                'input_image_type': 'original'
            }
        })
    
    except Exception as e:
        print(f"上传任务图片失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'上传失败: {str(e)}'}), 500


@ai_bp.route('/api/tasks/<int:task_id>/retry', methods=['POST'])
@login_required
def retry_ai_task(task_id):
    """重新处理AI任务"""
    try:
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        AITask = test_server_module.AITask
        Order = test_server_module.Order
        StyleCategory = test_server_module.StyleCategory
        StyleImage = test_server_module.StyleImage
        OrderImage = test_server_module.OrderImage
        
        from app.services.workflow_service import retry_ai_task as retry_task_service
        
        success, task, error_message = retry_task_service(
            task_id,
            db=db,
            AITask=AITask,
            Order=Order,
            StyleCategory=StyleCategory,
            StyleImage=StyleImage,
            OrderImage=OrderImage
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '任务已重新提交处理',
                'data': {
                    'task_id': task.id,
                    'status': task.status,
                    'retry_count': task.retry_count
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': error_message or '重新处理失败'
            }), 400
    
    except Exception as e:
        print(f"重新处理任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'重新处理失败: {str(e)}'}), 500


@ai_bp.route('/api/config', methods=['GET'])
@login_required
def get_ai_config():
    """获取AI配置"""
    try:
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        AIConfig = test_server_module.AIConfig
        
        configs = AIConfig.query.all()
        config_data = {}
        for config in configs:
            config_data[config.config_key] = {
                'value': config.config_value,
                'description': config.description
            }
        
        return jsonify({
            'status': 'success',
            'data': config_data
        })
    
    except Exception as e:
        print(f"获取AI配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取配置失败: {str(e)}'}), 500


@ai_bp.route('/api/config', methods=['PUT'])
@login_required
def update_ai_config():
    """更新AI配置"""
    try:
        if current_user.role != 'admin':
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': '请求数据为空'}), 400
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        AIConfig = test_server_module.AIConfig
        
        updated_configs = []
        for config_key, config_value in data.items():
            config = AIConfig.query.filter_by(config_key=config_key).first()
            if config:
                config.config_value = str(config_value)
                config.updated_at = datetime.now()
                updated_configs.append(config_key)
            else:
                # 创建新配置
                new_config = AIConfig(
                    config_key=config_key,
                    config_value=str(config_value),
                    description=''
                )
                db.session.add(new_config)
                updated_configs.append(config_key)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '配置更新成功',
            'data': {
                'updated_keys': updated_configs
            }
        })
    
    except Exception as e:
        print(f"更新AI配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': f'更新配置失败: {str(e)}'}), 500


@ai_bp.route('/api/tasks/debug-query/<path:task_id>', methods=['GET', 'POST'])
@login_required
def debug_query_task(task_id):
    """调试查询任务（输出详细信息）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        AITask = test_server_module.AITask
        APIProviderConfig = test_server_module.APIProviderConfig
        
        # 查找任务
        task = AITask.query.filter_by(comfyui_prompt_id=task_id).first()
        if not task:
            return jsonify({'status': 'error', 'message': '任务不存在'}), 404
        
        # 获取API配置
        api_config = APIProviderConfig.query.filter_by(is_active=True, is_default=True).first()
        if not api_config:
            api_config = APIProviderConfig.query.filter_by(is_active=True).first()
        
        if not api_config:
            return jsonify({'status': 'error', 'message': '未找到API配置'}), 500
        
        # 解析processing_log
        processing_log_info = {}
        original_response = None
        if task.processing_log:
            try:
                api_info = json.loads(task.processing_log)
                processing_log_info = api_info
                original_response = api_info.get('original_response', {})
            except:
                pass
        
        # 构建查询信息
        host = api_config.host_domestic or api_config.host_overseas
        result_endpoint = api_config.result_endpoint or '/v1/draw/result'
        result_url = host.rstrip('/') + result_endpoint
        
        # 尝试查询
        headers = {
            "Authorization": f"Bearer {api_config.api_key}"
        }
        proxies = {'http': None, 'https': None}
        
        request_payload = {"task_id": task_id}
        response = requests.post(result_url, json=request_payload, headers=headers, timeout=30, proxies=proxies)
        
        result_data = None
        if response.status_code == 200:
            result_data = response.json()
        
        return jsonify({
            'status': 'success',
            'data': {
                'task_info': {
                    'id': task.id,
                    'comfyui_prompt_id': task.comfyui_prompt_id,
                    'status': task.status,
                    'order_id': task.order_id,
                    'order_number': task.order_number,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'error_message': task.error_message
                },
                'api_config': {
                    'name': api_config.name,
                    'host': host,
                    'draw_endpoint': api_config.draw_endpoint,
                    'result_endpoint': result_endpoint,
                    'result_url': result_url
                },
                'processing_log': processing_log_info,
                'original_response': original_response,
                'query_request': {
                    'url': result_url,
                    'method': 'POST',
                    'payload': request_payload
                },
                'query_response': {
                    'status_code': response.status_code,
                    'data': result_data,
                    'text': response.text[:1000] if response.text else None
                }
            }
        })
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


@ai_bp.route('/api/tasks/<int:task_id>/update-api-task-id', methods=['POST'])
@login_required
def update_task_api_task_id(task_id):
    """手动更新任务的 API taskId（用于 RunningHub 等场景）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        AITask = test_server_module.AITask
        
        # 获取任务
        task = AITask.query.get(task_id)
        if not task:
            return jsonify({'status': 'error', 'message': '任务不存在'}), 404
        
        # 获取请求数据
        data = request.get_json()
        if not data or 'api_task_id' not in data:
            return jsonify({'status': 'error', 'message': '请提供 api_task_id'}), 400
        
        api_task_id = str(data['api_task_id']).strip()
        if not api_task_id:
            return jsonify({'status': 'error', 'message': 'api_task_id 不能为空'}), 400
        
        # 更新任务的 api_task_id
        task.comfyui_prompt_id = api_task_id
        
        # 更新 processing_log
        api_info = json.loads(task.processing_log) if task.processing_log else {}
        api_info['api_task_id'] = api_task_id
        api_info['manual_update'] = True
        api_info['manual_update_time'] = datetime.now().isoformat()
        task.processing_log = json.dumps(api_info, ensure_ascii=False)
        
        # 更新 notes
        if task.notes:
            if 'T8_API_TASK_ID:' not in task.notes:
                task.notes = f"T8_API_TASK_ID:{api_task_id} | {task.notes}"
            else:
                # 替换现有的 T8_API_TASK_ID
                import re
                task.notes = re.sub(r'T8_API_TASK_ID:[^\s|]+', f'T8_API_TASK_ID:{api_task_id}', task.notes)
        else:
            task.notes = f"T8_API_TASK_ID:{api_task_id}"
        
        # 如果任务状态是失败，改为处理中（因为现在有了 taskId，可以继续查询）
        if task.status == 'failed':
            task.status = 'processing'
            task.error_message = None
        
        db.session.commit()
        
        print(f"✅ 手动更新任务 {task_id} 的 api_task_id: {api_task_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'API任务ID已更新',
            'data': {
                'task_id': task_id,
                'api_task_id': api_task_id,
                'status': task.status
            }
        })
        
    except Exception as e:
        print(f"更新任务API任务ID失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'更新失败: {str(e)}'}), 500


@ai_bp.route('/api/tasks/recheck/<task_id>', methods=['POST'])
@login_required
def recheck_api_task_result(task_id):
    """重新查询API任务结果（用于手动重新获取结果）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        AITask = test_server_module.AITask
        APIProviderConfig = test_server_module.APIProviderConfig
        app = test_server_module.app
        
        # 获取任务（task_id可能是comfyui_prompt_id或任务ID）
        task = None
        print(f"🔍 开始查找任务，task_id: {task_id}")
        
        # 先尝试通过comfyui_prompt_id查找（API任务ID，完整匹配）
        if task_id:
            task = AITask.query.filter_by(comfyui_prompt_id=task_id).first()
            if task:
                print(f"✅ 通过comfyui_prompt_id找到任务: {task.id}, 状态: {task.status}")
            else:
                print(f"⚠️ 通过comfyui_prompt_id未找到任务，尝试其他方式")
        
        # 如果没找到，尝试通过ID查找（整数ID）
        if not task:
            try:
                task_id_int = int(task_id)
                task = AITask.query.get(task_id_int)
                if task:
                    print(f"✅ 通过ID找到任务: {task.id}, 状态: {task.status}")
            except:
                print(f"⚠️ task_id不是整数，跳过ID查找")
        
        # 如果还没找到，尝试在processing_log中搜索（完整匹配）
        if not task:
            print(f"⚠️ 尝试在processing_log中搜索task_id")
            all_tasks = AITask.query.filter(AITask.processing_log.isnot(None)).all()
            for t in all_tasks:
                try:
                    api_info = json.loads(t.processing_log)
                    # 尝试多种字段名
                    stored_task_id = api_info.get('task_id') or api_info.get('api_task_id') or api_info.get('id')
                    # 完整匹配（任务ID是随机的，不是前缀）
                    if stored_task_id and str(stored_task_id) == str(task_id):
                        task = t
                        print(f"✅ 在processing_log中找到任务: {task.id}, 状态: {task.status}")
                        break
                except:
                    continue
        
        if not task:
            print(f"❌ 未找到任务，task_id: {task_id}")
            # 列出所有任务的comfyui_prompt_id，帮助调试
            all_task_ids = AITask.query.with_entities(AITask.id, AITask.comfyui_prompt_id, AITask.status).limit(10).all()
            print(f"📋 最近10个任务的ID和comfyui_prompt_id:")
            for tid, cpid, stat in all_task_ids:
                print(f"   - 任务ID: {tid}, comfyui_prompt_id: {cpid}, 状态: {stat}")
            return jsonify({'status': 'error', 'message': f'任务不存在 (task_id: {task_id})'}), 404
        
        print(f"📋 找到任务: ID={task.id}, comfyui_prompt_id={task.comfyui_prompt_id}, status={task.status}, order_id={task.order_id}, workflow_file={task.workflow_file}")
        
        # 检查是否是本地ComfyUI任务
        is_local_comfyui_task = False
        if task.comfyui_prompt_id and task.workflow_file:
            # 检查是否有api_config_id（如果有，说明是API服务商的ComfyUI任务）
            has_api_config = False
            if task.processing_log:
                try:
                    api_info = json.loads(task.processing_log)
                    if isinstance(api_info, dict) and api_info.get('api_config_id'):
                        has_api_config = True
                except:
                    pass
            
            # 如果没有api_config_id，说明是本地ComfyUI任务
            if not has_api_config:
                is_local_comfyui_task = True
                print(f"🔍 [重新获取] 任务 {task.id} 是本地ComfyUI任务，将查询ComfyUI history API")
        
        # 如果是本地ComfyUI任务，直接处理
        if is_local_comfyui_task:
            try:
                from app.services.workflow_service import get_comfyui_config
                comfyui_config = get_comfyui_config(db=db, AIConfig=None)
                prompt_id = task.comfyui_prompt_id
                output_id = task.comfyui_node_id
                
                if not prompt_id or not output_id:
                    return jsonify({'status': 'error', 'message': f'任务缺少 prompt_id 或 output_id (prompt_id={prompt_id}, output_id={output_id})'}), 400
                
                # 查询ComfyUI history API
                history_url = f"{comfyui_config['base_url']}/history/{prompt_id}"
                print(f"🔄 [重新获取] 查询ComfyUI任务状态: {history_url}")
                
                import requests
                response = requests.get(history_url, timeout=10, proxies={'http': None, 'https': None})
                
                if response.status_code == 200:
                    history_data = response.json()
                    print(f"   - history响应: {json.dumps(history_data, ensure_ascii=False)[:200]}...")
                    
                    # 查找对应的输出节点
                    if prompt_id in history_data:
                        outputs = history_data[prompt_id].get('outputs', {})
                        if output_id in outputs:
                            output_node = outputs[output_id]
                            images = output_node.get('images', [])
                            
                            if images and len(images) > 0:
                                # 任务已完成，获取结果图片
                                image_info = images[0]
                                image_filename = image_info.get('filename')
                                image_subfolder = image_info.get('subfolder', '')
                                image_type = image_info.get('type', 'output')
                                
                                # 构建图片URL
                                if image_subfolder:
                                    image_url = f"{comfyui_config['base_url']}/view?filename={image_filename}&subfolder={image_subfolder}&type={image_type}"
                                else:
                                    image_url = f"{comfyui_config['base_url']}/view?filename={image_filename}&type={image_type}"
                                
                                # 更新任务状态
                                task.status = 'completed'
                                task.output_image_path = image_url
                                task.completed_at = datetime.now()
                                
                                # 下载图片到本地
                                try:
                                    from app.routes.ai import download_api_result_image
                                    local_path = download_api_result_image(image_url, prompt_id, app)
                                    if local_path:
                                        task.output_image_path = local_path
                                        print(f"✅ [重新获取] ComfyUI任务 {task.id} 结果图已下载到本地: {local_path}")
                                        
                                        # 生成缩略图
                                        try:
                                            from app.utils.image_thumbnail import generate_thumbnail
                                            thumbnail_path = generate_thumbnail(local_path, max_size=1920, quality=85)
                                            if thumbnail_path:
                                                print(f"✅ [重新获取] ComfyUI任务 {task.id} 缩略图生成成功: {thumbnail_path}")
                                        except Exception as thumb_error:
                                            print(f"⚠️ [重新获取] ComfyUI任务 {task.id} 生成缩略图失败: {str(thumb_error)}")
                                except Exception as download_error:
                                    print(f"⚠️ [重新获取] 下载ComfyUI结果图失败: {str(download_error)}")
                                
                                # 检查该订单的所有AI任务是否都已完成
                                if task.order_id and task.order_id > 0:
                                    try:
                                        Order = test_server_module.Order if hasattr(test_server_module, 'Order') else None
                                        if Order:
                                            # 查询该订单的所有AI任务
                                            all_tasks = AITask.query.filter_by(order_id=task.order_id).all()
                                            # 过滤掉失败和取消的任务，只统计有效任务
                                            valid_tasks = [t for t in all_tasks if t.status not in ['failed', 'cancelled']]
                                            completed_tasks = [t for t in valid_tasks if t.status == 'completed' and t.output_image_path]
                                            
                                            # 如果所有有效任务都已完成，更新订单状态为"待选片"
                                            if len(valid_tasks) > 0 and len(completed_tasks) == len(valid_tasks):
                                                order = Order.query.get(task.order_id)
                                                if order and order.status in ['ai_processing', 'retouching', 'shooting', 'processing']:
                                                    old_status = order.status
                                                    order.status = 'pending_selection'  # 待选片
                                                    print(f"✅ [重新获取] 订单 {order.order_number} 所有AI任务已完成 ({len(completed_tasks)}/{len(valid_tasks)})，状态已更新为: pending_selection (从 {old_status} 更新)")
                                                elif order:
                                                    print(f"ℹ️ [重新获取] 订单 {order.order_number} 所有AI任务已完成，但当前状态是 {order.status}，不更新")
                                    except Exception as e:
                                        print(f"⚠️ [重新获取] 检查订单状态失败: {str(e)}")
                                        import traceback
                                        traceback.print_exc()
                                
                                db.session.commit()
                                print(f"✅ [重新获取] ComfyUI任务 {task.id} 已完成，图片URL: {image_url}")
                                
                                return jsonify({
                                    'status': 'success',
                                    'message': '任务已完成',
                                    'data': {
                                        'task_id': task.id,
                                        'status': 'completed',
                                        'image_url': image_url,
                                        'local_path': task.output_image_path
                                    }
                                })
                            else:
                                return jsonify({
                                    'status': 'processing',
                                    'message': '任务仍在处理中（输出节点还没有图片）',
                                    'data': {
                                        'task_id': task.id,
                                        'status': 'processing'
                                    }
                                })
                        else:
                            return jsonify({
                                'status': 'processing',
                                'message': f'任务仍在处理中（输出节点 {output_id} 不存在）',
                                'data': {
                                    'task_id': task.id,
                                    'status': 'processing'
                                }
                            })
                    else:
                        return jsonify({
                            'status': 'processing',
                            'message': '任务仍在队列中（history中未找到）',
                            'data': {
                                'task_id': task.id,
                                'status': 'processing'
                            }
                        })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': f'查询ComfyUI history失败: HTTP {response.status_code}'
                    }), 500
            except Exception as e:
                print(f"⚠️ [重新获取] 处理ComfyUI任务 {task.id} 时出错: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'status': 'error',
                    'message': f'处理ComfyUI任务失败: {str(e)}'
                }), 500
        
        # 获取API配置（用于API服务商任务）
        api_config = None
        if task.processing_log:
            try:
                api_info = json.loads(task.processing_log)
                api_config_id = api_info.get('api_config_id')
                if api_config_id:
                    api_config = APIProviderConfig.query.get(api_config_id)
            except:
                pass
        
        if not api_config:
            api_config = APIProviderConfig.query.filter_by(is_active=True, is_default=True).first()
        if not api_config:
            api_config = APIProviderConfig.query.filter_by(is_active=True).first()
        
        if not api_config:
            return jsonify({'status': 'error', 'message': '未找到API配置'}), 500
        
        # 获取API任务ID（关键修复：优先使用comfyui_prompt_id，因为它可能包含重试后的新ID）
        api_task_id = None
        original_response = None
        api_info = {}
        
        # 关键修复：优先从comfyui_prompt_id获取（重试后应该更新为新的task_id）
        if task.comfyui_prompt_id:
            api_task_id = task.comfyui_prompt_id
            print(f"✅ [重新获取] 从comfyui_prompt_id提取到API任务ID: {api_task_id}（优先使用，可能是重试后的新ID）")
        
        # 如果comfyui_prompt_id中没有，从notes中提取T8_API_TASK_ID（作为备选）
        if not api_task_id and task.notes and 'T8_API_TASK_ID:' in task.notes:
            try:
                notes_task_id = task.notes.split('T8_API_TASK_ID:')[1].split('|')[0].split()[0].strip()
                if notes_task_id:
                    api_task_id = notes_task_id
                    print(f"✅ [重新获取] 从notes中提取到T8_API_TASK_ID: {api_task_id}")
            except Exception as e:
                print(f"⚠️ 解析任务 {task_id} 的notes中的T8_API_TASK_ID失败: {str(e)}")
        
        # 关键修复：如果comfyui_prompt_id和notes中的ID不一致，且comfyui_prompt_id看起来更新，使用comfyui_prompt_id
        if task.comfyui_prompt_id and task.notes and 'T8_API_TASK_ID:' in task.notes:
            try:
                notes_task_id = task.notes.split('T8_API_TASK_ID:')[1].split('|')[0].split()[0].strip()
                if notes_task_id and task.comfyui_prompt_id != notes_task_id:
                    # 检查comfyui_prompt_id是否看起来是新的（更长或包含特定前缀如b1f3b4f8）
                    if len(task.comfyui_prompt_id) > len(notes_task_id) or task.comfyui_prompt_id.startswith('b1f3b4f8'):
                        print(f"⚠️ [重新获取] notes中的ID({notes_task_id})与comfyui_prompt_id({task.comfyui_prompt_id})不一致，使用comfyui_prompt_id（可能重试后未更新notes）")
                        api_task_id = task.comfyui_prompt_id
            except:
                pass
        
        # 从processing_log中提取原始响应和task_id（作为备选）
        if task.processing_log:
            try:
                api_info = json.loads(task.processing_log)
                # 如果还没有api_task_id，从processing_log中提取
                if not api_task_id:
                    api_task_id = api_info.get('api_task_id') or api_info.get('task_id') or api_info.get('id')
                # 获取原始响应，用于提取task_id的多种格式
                original_response = api_info.get('original_response', {})
                # 如果result_data是字符串，尝试解析
                if not original_response and api_info.get('result_data'):
                    try:
                        result_data_str = api_info.get('result_data')
                        if isinstance(result_data_str, str):
                            original_response = json.loads(result_data_str)
                        else:
                            original_response = result_data_str
                    except:
                        pass
                print(f"📋 processing_log中的api_task_id: {api_info.get('api_task_id')}")
                print(f"📋 processing_log中的task_id: {api_info.get('task_id')}")
                print(f"📋 processing_log中的original_response: {json.dumps(original_response, ensure_ascii=False)[:500] if original_response else 'None'}")
            except Exception as e:
                print(f"⚠️ 解析processing_log失败: {str(e)}")
        
        if not api_task_id:
            return jsonify({'status': 'error', 'message': '任务没有API任务ID，无法重新查询'}), 400
        
        # 尝试多种task_id格式（grsai可能接受不同的格式）
        task_id_variants = []
        
        # 1. 使用保存的api_task_id（完整格式，包括"14-"前缀）
        task_id_variants.append(api_task_id)
        
        # 2. 从original_response中提取（如果不同）
        if original_response:
            try:
                if isinstance(original_response, dict):
                    if original_response.get('code') == 0 and 'data' in original_response:
                        data = original_response.get('data')
                        if isinstance(data, dict):
                            original_task_id = data.get('id') or data.get('task_id')
                            if original_task_id and original_task_id != api_task_id:
                                task_id_variants.append(original_task_id)
                                print(f"📋 从original_response提取到task_id: {original_task_id}")
            except:
                pass
        
        # 3. 尝试去掉"14-"前缀（grsai查询时可能需要纯UUID）
        if api_task_id and '-' in api_task_id:
            parts = api_task_id.split('-', 1)
            if len(parts) > 1:
                # 检查第一部分是否是数字（如"14"）
                if parts[0].isdigit():
                    uuid_part = parts[1]  # 去掉数字前缀，只保留UUID部分
                    if uuid_part not in task_id_variants:
                        task_id_variants.append(uuid_part)
                        print(f"📋 去掉前缀后的task_id: {uuid_part}")
        
        # 4. 从processing_log中提取task_id（系统生成的UUID，虽然可能不是API task_id，但也尝试一下）
        if api_info.get('task_id') and api_info.get('task_id') != api_task_id:
            log_task_id = api_info.get('task_id')
            if log_task_id not in task_id_variants:
                task_id_variants.append(log_task_id)
                print(f"📋 从processing_log提取到task_id: {log_task_id}")
        
        # 去重
        task_id_variants = list(dict.fromkeys(task_id_variants))
        
        print(f"📋 将尝试以下task_id变体（共{len(task_id_variants)}个）: {task_id_variants}")
        
        # 构建查询URL
        host = api_config.host_domestic or api_config.host_overseas
        if not host:
            return jsonify({'status': 'error', 'message': 'API Host未配置'}), 500
        
        # 关键修复：检查是否是T8Star服务商（通过host判断）
        is_t8star = host and 't8star.cn' in host.lower()
        
        # 根据draw_endpoint推断查询端点
        result_endpoint = api_config.result_endpoint
        
        # 关键修复：如果result_endpoint中包含{task_id}占位符，需要替换为实际的task_id
        if result_endpoint and '{task_id}' in result_endpoint:
            result_endpoint = result_endpoint.replace('{task_id}', api_task_id)
            print(f"📝 [重新获取] 替换result_endpoint中的{{task_id}}占位符: {result_endpoint}")
        
        # 关键修复：如果result_endpoint已配置但格式不正确（T8Star应该使用/v1/images/tasks/{task_id}），自动修正
        if result_endpoint and is_t8star and api_config.api_type == 'nano-banana-edits':
            # T8Star的nano-banana-edits应该使用GET /v1/images/tasks/{task_id}格式
            if '/v1/images/edits/result' in result_endpoint or result_endpoint.endswith('/edits/result'):
                # 错误的格式，自动修正为正确的格式
                result_endpoint = f'/v1/images/tasks/{api_task_id}'
                print(f"📝 [重新获取] T8Star result_endpoint格式不正确，自动修正为: {result_endpoint}")
            elif '/v1/images/tasks/' not in result_endpoint:
                # 如果result_endpoint不是/v1/images/tasks/格式，也修正
                result_endpoint = f'/v1/images/tasks/{api_task_id}'
                print(f"📝 [重新获取] T8Star result_endpoint不是OpenAPI格式，自动修正为: {result_endpoint}")
        
        if not result_endpoint:
            draw_endpoint = api_config.draw_endpoint or '/v1/draw/nano-banana'
            if '/v1/images/generations' in draw_endpoint or '/v1/images/tasks/' in draw_endpoint:
                result_endpoint = f'/v1/images/tasks/{api_task_id}'
            elif draw_endpoint.endswith('/edits') and is_t8star:
                # T8Star的/v1/images/edits异步模式使用OpenAPI格式：GET /v1/images/tasks/{task_id}
                result_endpoint = f'/v1/images/tasks/{api_task_id}'  # GET请求，task_id在URL中
                print(f"📝 [重新获取] T8Star nano-banana-edits异步模式：使用OpenAPI格式查询端点 GET /v1/images/tasks/{api_task_id}")
            elif draw_endpoint.endswith('/edits'):
                result_endpoint = draw_endpoint + '/result'
            else:
                # grsai等使用 /v1/draw/result
                result_endpoint = '/v1/draw/result'
        
        # 判断是GET还是POST请求
        # OpenAPI格式：GET /v1/images/tasks/{task_id}（T8Star使用此格式）
        # 其他格式：POST /v1/images/edits/result 或 POST /v1/draw/result
        use_get_method = '/v1/images/tasks/' in result_endpoint
        
        if use_get_method:
            # GET请求：task_id已经在URL中
            result_url = host.rstrip('/') + result_endpoint
        else:
            # POST请求：task_id在请求体中
            result_url = host.rstrip('/') + result_endpoint
        
        headers = {
            "Authorization": f"Bearer {api_config.api_key}"
        }
        
        # 禁用代理（国内服务商）
        proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        has_proxy = any(os.environ.get(var) for var in proxy_env_vars)
        is_known_domestic_domain = host and any(domain in host.lower() for domain in [
            'grsai.dakka.com.cn', 'grsai-file.dakka.com.cn', 't8star.cn', 'ai.t8star.cn'
        ])
        
        if is_known_domestic_domain or api_config.host_domestic:
            proxies = {'http': None, 'https': None}
        else:
            proxies = None
        
        print(f"🔄 重新查询任务 {task_id} 的状态")
        print(f"   - 数据库任务ID: {task.id}")
        print(f"   - API任务ID: {api_task_id}")
        print(f"   - 当前任务状态: {task.status}")
        print(f"   - 查询URL: {result_url}")
        print(f"   - 请求方法: {'GET' if use_get_method else 'POST'}")
        
        # 尝试多个task_id变体（如果第一个失败）
        response = None
        result_data = None
        found_result = False
        
        for current_task_id in task_id_variants:
            try:
                print(f"🔄 尝试使用task_id: {current_task_id}")
                if use_get_method:
                    # GET请求：task_id在URL中
                    current_result_url = result_url.replace(api_task_id, current_task_id) if api_task_id in result_url else result_url
                    print(f"📤 GET请求:")
                    print(f"   - URL: {current_result_url}")
                    print(f"   - Headers: Authorization=Bearer {api_config.api_key[:20]}...")
                    response = requests.get(current_result_url, headers=headers, timeout=30, proxies=proxies)
                    
                    print(f"📥 响应状态码: {response.status_code}")
                    if response.status_code == 200:
                        result_data = response.json()
                        print(f"📥 响应内容（完整）:")
                        print(json.dumps(result_data, ensure_ascii=False, indent=2))
                        
                        # 检查是否成功
                        if isinstance(result_data, dict):
                            # 关键修复：T8Star格式检查（code可能是字符串"success"或数字0）
                            if is_t8star:
                                # T8Star可能返回 code: "success" 或 code: 0
                                code_value = result_data.get('code')
                                if code_value == "success" or code_value == "SUCCESS" or code_value == 0:
                                    # 进一步检查data.status是否为SUCCESS
                                    data = result_data.get('data')
                                    if isinstance(data, dict) and data.get('status') == 'SUCCESS':
                                        found_result = True
                                        print(f"✅ 使用task_id {current_task_id} 查询成功（T8Star格式：code={code_value}, status=SUCCESS）")
                                        break
                                    elif isinstance(data, dict) and data.get('status') in ['PROCESSING', 'PENDING', 'QUEUED', 'RUNNING']:
                                        # 任务还在处理中，也算成功获取到状态
                                        found_result = True
                                        print(f"✅ 使用task_id {current_task_id} 查询成功（T8Star格式：任务处理中）")
                                        break
                                elif code_value == -22 or (isinstance(code_value, str) and 'not found' in str(code_value).lower()):
                                    print(f"⚠️ task_id {current_task_id} 不存在 (code={code_value})，尝试下一个变体")
                                    continue
                            # 其他服务商格式
                            elif 'status' in result_data and 'code' not in result_data:
                                found_result = True
                                print(f"✅ 使用task_id {current_task_id} 查询成功（grsai根级别格式）")
                                break
                            elif result_data.get('code') == 0:
                                found_result = True
                                print(f"✅ 使用task_id {current_task_id} 查询成功（code=0）")
                                break
                            elif result_data.get('code') == -22:
                                print(f"⚠️ task_id {current_task_id} 不存在 (code=-22)，尝试下一个变体")
                                continue
                    else:
                        print(f"⚠️ HTTP错误: {response.status_code}，尝试下一个task_id变体")
                        continue
                else:
                    # POST请求：需要传递task_id
                    # 参考bk-photo-v4文档：通用异步API使用{"Id": "api_task_id"}格式（大写Id）
                    # 虽然文档提到nano-banana-edits用{"task_id": "..."}，但用户说不用nano-banana-edits了
                    # 所以优先使用{"Id": "..."}格式
                    request_payloads = [
                        {"Id": current_task_id},  # 参考bk-photo-v4：通用异步API格式（大写Id，优先）
                        {"task_id": current_task_id},  # nano-banana-edits格式（备选，虽然不用了）
                        {"id": current_task_id},  # 小写id格式（备选）
                    ]
                    
                    response = None
                    result_data = None
                    payload_used = None
                    
                    for payload in request_payloads:
                        try:
                            print(f"📤 POST请求:")
                            print(f"   - URL: {result_url}")
                            print(f"   - 参数: {json.dumps(payload, ensure_ascii=False)}")
                            print(f"   - Headers: Authorization=Bearer {api_config.api_key[:20]}...")
                            
                            response = requests.post(result_url, json=payload, headers=headers, timeout=30, proxies=proxies)
                            
                            print(f"📥 响应状态码: {response.status_code}")
                            if response.status_code == 200:
                                result_data = response.json()
                                print(f"📥 响应内容（完整）:")
                                print(json.dumps(result_data, ensure_ascii=False, indent=2))
                                
                                # 检查是否成功
                                if isinstance(result_data, dict):
                                    # grsai格式1：直接在根级别有status（没有code字段）
                                    if 'status' in result_data and 'code' not in result_data:
                                        found_result = True
                                        payload_used = payload
                                        print(f"✅ 使用task_id {current_task_id} 和参数 {payload} 查询成功（grsai根级别格式）")
                                        break
                                    # grsai格式2：有code字段
                                    elif 'code' in result_data:
                                        if result_data.get('code') == 0:
                                            found_result = True
                                            payload_used = payload
                                            print(f"✅ 使用task_id {current_task_id} 和参数 {payload} 查询成功（code=0）")
                                            break
                                        elif result_data.get('code') == -22:
                                            # 任务不存在，尝试下一个payload格式
                                            print(f"⚠️ 使用参数 {payload} 返回code=-22，尝试下一个参数格式")
                                            continue
                                        else:
                                            # 其他错误，停止尝试
                                            print(f"⚠️ API返回错误: code={result_data.get('code')}, msg={result_data.get('msg')}")
                                            found_result = True  # 视为已处理
                                            payload_used = payload
                                            break
                                    else:
                                        # 其他格式，视为成功
                                        found_result = True
                                        payload_used = payload
                                        print(f"✅ 使用task_id {current_task_id} 和参数 {payload} 查询成功（其他格式）")
                                        break
                                else:
                                    # 非标准格式，视为成功
                                    found_result = True
                                    payload_used = payload
                                    print(f"✅ 使用task_id {current_task_id} 和参数 {payload} 查询成功（非字典格式）")
                                    break
                            else:
                                print(f"⚠️ HTTP错误: {response.status_code}，尝试下一个参数格式")
                                continue
                        except Exception as e:
                            print(f"⚠️ 请求异常: {str(e)}，尝试下一个参数格式")
                            continue
                    
                    if found_result:
                        break  # 跳出task_id变体循环
            except Exception as e:
                print(f"⚠️ 查询异常 (task_id={current_task_id}): {str(e)}")
                continue
        
        if not found_result or not result_data:
            # 所有变体都失败
            return jsonify({
                'status': 'error',
                'message': f'无法查询到任务结果，已尝试的task_id: {task_id_variants}'
            }), 400
        
        try:
            # 解析响应（grsai格式：{"code": 0, "data": {"status": "succeeded", "url": "..."}}）
            status = None
            image_url = None
            progress = None
            
            # 关键修复：T8Star格式（实际是三层嵌套）：{"code": "success", "data": {"status": "SUCCESS", "data": {"data": [{"url": "..."}]}}}
            # 根据实际响应：data.data 是对象，data.data.data 才是数组
            if isinstance(result_data, dict) and is_t8star and use_get_method and 'data' in result_data:
                data = result_data.get('data')
                if isinstance(data, dict):
                    status = data.get('status')  # "SUCCESS", "FAILED", "PROCESSING"等
                    # 关键修复：优先检查 data.data.data 是否是数组（三层嵌套格式，这是实际格式）
                    if 'data' in data:
                        inner_data = data.get('data')
                        # 优先：data.data 是对象，继续检查 data.data.data（三层嵌套格式，实际格式）
                        if isinstance(inner_data, dict) and 'data' in inner_data:
                            if isinstance(inner_data.get('data'), list) and len(inner_data.get('data')) > 0:
                                data_list = inner_data.get('data')
                                first_item = data_list[0]
                                if isinstance(first_item, dict):
                                    image_url = first_item.get('url')
                                    print(f"✅ [重新获取] T8Star从三层嵌套格式（data.data.data数组）提取图片URL: {image_url}")
                        # 备选：data.data 是数组（两层嵌套格式，可能某些情况下存在）
                        elif isinstance(inner_data, list) and len(inner_data) > 0:
                            first_item = inner_data[0]
                            if isinstance(first_item, dict):
                                image_url = first_item.get('url')
                                print(f"✅ [重新获取] T8Star从两层嵌套格式（data.data数组）提取图片URL: {image_url}")
                    # 如果还是没有，尝试从data直接获取
                    if not image_url:
                        image_url = data.get('url') or data.get('image_url')
                        if image_url:
                            print(f"✅ [重新获取] T8Star从data字段提取图片URL: {image_url}")
                    # 状态映射：T8Star返回"SUCCESS"，需要映射为"completed"
                    if status == 'SUCCESS':
                        status = 'completed'
                        print(f"✅ [重新获取] T8Star任务状态为SUCCESS，映射为completed")
                    elif status == 'FAILED':
                        status = 'failed'
                        print(f"❌ [重新获取] T8Star任务状态为FAILED，映射为failed")
                    elif status in ['PROCESSING', 'PENDING', 'QUEUED', 'RUNNING']:
                        status = 'processing'
                        print(f"🔄 [重新获取] T8Star任务状态为{status}，映射为processing")
                    # 关键修复：T8Star解析完成后，打印解析结果，确保后续更新逻辑能执行
                    if status and image_url:
                        print(f"📊 [重新获取] T8Star解析完成: status={status}, image_url={image_url}")
            
            # 关键修复：修改条件判断，让T8Star的情况也能执行后续的更新逻辑
            # 如果T8Star已经解析完成（status和image_url都已设置），直接跳过GRSAI格式解析，进入更新逻辑
            if isinstance(result_data, dict) and not (is_t8star and use_get_method and status and image_url):
                # grsai格式1：直接在根级别有status和results（从图片中看到的格式）
                # {"id": "...", "results": [{"url": "..."}], "status": "succeeded", ...}
                if 'status' in result_data and 'results' in result_data:
                    status = result_data.get('status')
                    results = result_data.get('results', [])
                    if isinstance(results, list) and len(results) > 0:
                        image_url = results[0].get('url') or results[0].get('image_url')
                    progress = result_data.get('progress')
                    print(f"✅ 检测到grsai格式1（根级别status和results）")
                # grsai格式2：{"code": 0, "data": {"status": "...", "results": [...]}}
                elif 'code' in result_data:
                    if result_data.get('code') == 0 and 'data' in result_data:
                        data = result_data.get('data')
                        if isinstance(data, dict):
                            status = data.get('status')
                            # 关键修复：即使code=0，如果status是failed，也要提取错误信息
                            if status == 'failed':
                                # 提取错误信息
                                error_msg = data.get('error') or data.get('error_message') or data.get('failure_reason') or '任务失败'
                                print(f"⚠️ GRSAI任务失败，错误信息: {error_msg}")
                                # 不设置image_url，让后续逻辑处理失败状态
                                image_url = None
                            else:
                                # 优先从results数组获取URL（参考bk-photo-v4）
                                results = data.get('results', [])
                                if isinstance(results, list) and len(results) > 0:
                                    image_url = results[0].get('url') or results[0].get('image_url')
                                else:
                                    # 如果没有results数组，从data直接获取
                                    image_url = data.get('url') or data.get('image_url') or data.get('result_url')
                            progress = data.get('progress')
                        elif isinstance(data, list) and len(data) > 0:
                            # 如果data是数组，取第一个元素
                            first_item = data[0]
                            if isinstance(first_item, dict):
                                status = first_item.get('status')
                                image_url = first_item.get('url') or first_item.get('image_url')
                    elif result_data.get('code') != 0:
                        # API返回错误（可能是任务不存在、已过期等）
                        error_code = result_data.get('code')
                        error_msg = result_data.get('msg') or result_data.get('message') or 'API返回错误'
                        print(f"API返回错误: code={error_code}, msg={error_msg}")
                        
                        # 直接标记为失败（参考bk-photo-v4，保留完整的task_id，不尝试去掉前缀）
                        task.status = 'failed'
                        task.error_message = f"API错误 (code={error_code}): {error_msg}"
                        db.session.commit()
                        return jsonify({
                            'status': 'error',
                            'message': f'API返回错误 (code={error_code}): {error_msg}'
                        })
                # 标准格式：直接有status字段（但没有results）
                elif 'status' in result_data:
                    status = result_data.get('status')
                    image_url = result_data.get('url') or result_data.get('image_url')
                    progress = result_data.get('progress')
                # 嵌套data格式
                elif 'data' in result_data and isinstance(result_data.get('data'), dict):
                    data = result_data.get('data')
                    status = data.get('status')
                    image_url = data.get('url') or data.get('image_url')
                    progress = data.get('progress')
                
                # 如果还没找到图片URL，继续尝试提取（参考bk-photo-v4）
                if not image_url:
                    # 再次检查根级别的results
                    if 'results' in result_data:
                        results = result_data.get('results', [])
                        if isinstance(results, list) and len(results) > 0:
                            image_url = results[0].get('url') or results[0].get('image_url')
                    
                    if not image_url and 'data' in result_data:
                        data = result_data.get('data')
                        if isinstance(data, dict):
                            # 优先从results数组获取
                            results = data.get('results', [])
                            if isinstance(results, list) and len(results) > 0:
                                image_url = results[0].get('url') or results[0].get('image_url')
                            else:
                                image_url = data.get('url') or data.get('image_url') or data.get('result_url')
                        elif isinstance(data, list) and len(data) > 0:
                            image_url = data[0].get('url') or data[0].get('image_url')
                    
                    if not image_url:
                        if 'url' in result_data:
                            image_url = result_data.get('url')
                        elif 'image_url' in result_data:
                            image_url = result_data.get('image_url')
                
                print(f"📊 解析结果: status={status}, image_url={image_url}")
                print(f"   - 原始响应: {json.dumps(result_data, ensure_ascii=False)[:500]}")
            
            # 关键修复：检查 RunningHub API 的 errorCode/errorMessage 字段
            # 如果 status 为空但 errorCode 或 errorMessage 存在，应该识别为失败状态
            if not status or status == '':
                if isinstance(result_data, dict):
                    error_code = result_data.get('errorCode')
                    error_message = result_data.get('errorMessage')
                    if error_code or error_message:
                        # RunningHub API 返回了错误码或错误信息，但 status 为空，应该识别为失败
                        status = 'failed'
                        error_msg = error_message or f"API错误 (errorCode={error_code})" if error_code else '任务失败'
                        print(f"⚠️ [重新获取] RunningHub API 返回错误但 status 为空，识别为失败: errorCode={error_code}, errorMessage={error_message}")
            
            # 关键修复：将更新任务状态的代码移到条件判断块外面，确保T8Star和GRSAI都能执行
            # 更新任务状态（关键修复：即使是失败状态的任务，如果查询到成功结果，也要更新为completed）
            # 关键修复：T8Star解析完成后，status和image_url都已经设置，需要执行更新逻辑
            print(f"🔍 [重新获取] 准备更新任务状态: status={status}, image_url={image_url if image_url else 'None'}")
            if status in ['succeeded', 'completed', 'success'] and image_url:
                print(f"✅ 任务已完成，准备更新状态和下载图片")
                # 无论当前状态是什么（包括failed），都更新为completed（允许修复失败状态的任务）
                task.status = 'completed'
                task.output_image_path = image_url
                task.error_message = None
                task.completed_at = datetime.now()
                
                # 更新processing_log
                if task.processing_log:
                    try:
                        api_info = json.loads(task.processing_log)
                        api_info['result_image'] = image_url
                        api_info['result_data'] = result_data
                        task.processing_log = json.dumps(api_info, ensure_ascii=False)
                    except:
                        pass
                
                db.session.commit()
                print(f"任务 {task_id} 重新查询成功，图片URL: {image_url}")
                
                # 自动下载图片到final_works目录
                try:
                    local_path = download_api_result_image(image_url, task.comfyui_prompt_id or str(task.id), app)
                    if local_path:
                        # 更新output_image_path为本地路径
                        task.output_image_path = local_path
                        db.session.commit()
                        print(f"✅ 任务 {task_id} 结果图已下载到本地: {local_path}")
                except Exception as download_error:
                    print(f"⚠️ 下载图片失败: {str(download_error)}")
                
                return jsonify({
                    'status': 'success',
                    'message': '任务已完成，结果已更新',
                    'data': {
                        'status': 'completed',
                        'result_image_url': image_url,
                        'local_path': task.output_image_path if task.output_image_path and not task.output_image_path.startswith('http') else None
                    }
                })
            elif status in ['failed', 'error']:
                # GRSAI格式：从data.error中提取错误信息（如"google gemini timeout..."）
                error_msg = None
                if isinstance(result_data, dict):
                    # 检查data字段中的error（优先，因为GRSAI的错误信息在这里）
                    if 'data' in result_data and isinstance(result_data.get('data'), dict):
                        data = result_data.get('data')
                        error_msg = data.get('error') or data.get('error_message') or data.get('failure_reason')
                        print(f"🔍 从data字段提取错误信息: {error_msg}")
                    # 检查根级别的error
                    if not error_msg:
                        error_obj = result_data.get('error')
                        if isinstance(error_obj, dict):
                            error_msg = error_obj.get('message') or error_obj.get('error')
                        elif isinstance(error_obj, str):
                            error_msg = error_obj
                    # 如果还没有，使用msg字段（但注意：GRSAI的msg可能是"success"即使任务失败）
                    if not error_msg:
                        # 只有当msg不是"success"时才使用
                        msg = result_data.get('msg') or result_data.get('message')
                        if msg and msg.lower() != 'success':
                            error_msg = msg
                
                if not error_msg:
                    error_msg = '任务失败（未提供具体错误信息）'
                
                print(f"❌ 提取到的错误信息: {error_msg}")
                
                task.status = 'failed'
                task.error_message = str(error_msg)[:500]
                if task.processing_log:
                    try:
                        api_info = json.loads(task.processing_log)
                        api_info['result_data'] = result_data
                        task.processing_log = json.dumps(api_info, ensure_ascii=False)
                    except:
                        pass
                db.session.commit()
                print(f"✅ 任务已更新为失败状态，错误信息: {error_msg}")
                return jsonify({
                    'status': 'error',
                    'message': f'任务状态为失败: {error_msg}',
                    'error': error_msg,  # 单独返回错误信息字段，方便前端显示
                    'data': {
                        'status': 'failed',
                        'error_message': error_msg
                    }
                })
            elif status in ['running', 'processing', 'pending']:
                # 任务仍在处理中，只更新状态为processing，不重置为pending
                if task.status != 'processing':
                    task.status = 'processing'
                    db.session.commit()
                    print(f"⏳ 任务仍在处理中，状态已更新为processing")
                return jsonify({
                    'status': 'success',
                    'message': f'任务仍在处理中，状态: {status}',
                    'data': {
                        'status': 'processing',
                        'progress': progress
                    }
                })
            else:
                # 未知状态，不更新任务状态，只返回错误
                print(f"⚠️ 未知的任务状态: {status}，不更新数据库状态")
                return jsonify({
                    'status': 'error',
                    'message': f'未知的任务状态: {status}'
                })
                
        except requests.exceptions.RequestException as e:
            return jsonify({
                'status': 'error',
                'message': f'查询API失败: {str(e)}'
            }), 500
        except Exception as e:
            import traceback
            print(f"重新查询任务失败: {traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'message': f'重新查询失败: {str(e)}'
            }), 500
            
    except Exception as e:
        import traceback
        print(f"重新查询任务失败: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'重新查询失败: {str(e)}'}), 500


@ai_bp.route('/api/tasks/parse-base64/<path:task_id>', methods=['POST'])
@login_required
def parse_base64_image(task_id):
    """解析已完成任务的base64图片并保存到本地"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        AITask = test_server_module.AITask
        app = test_server_module.app
        
        with app.app_context():
            # 查找任务
            task = AITask.query.filter_by(id=task_id).first()
            if not task:
                # 尝试通过comfyui_prompt_id查找
                task = AITask.query.filter_by(comfyui_prompt_id=task_id).first()
            
            if not task:
                return jsonify({'status': 'error', 'message': f'未找到任务: {task_id}'}), 404
            
            print(f"✅ 找到任务: {task.id}")
            print(f"   订单号: {task.order_number}")
            print(f"   状态: {task.status}")
            
            # 从processing_log中获取响应数据
            if not task.processing_log:
                return jsonify({'status': 'error', 'message': '任务没有processing_log数据'}), 400
            
            try:
                api_info = json.loads(task.processing_log) if isinstance(task.processing_log, str) else task.processing_log
            except:
                return jsonify({'status': 'error', 'message': '解析processing_log失败'}), 400
            
            # 获取响应数据（优先从original_response获取完整数据，如果没有则使用response_data）
            response_data = None
            
            # 优先使用original_response（完整响应）
            if 'original_response' in api_info:
                response_data = api_info.get('original_response')
                print(f"✅ 使用original_response作为响应数据")
            elif 'result_data' in api_info:
                response_data = api_info.get('result_data')
                print(f"✅ 使用result_data作为响应数据")
            else:
                response_data = api_info.get('response_data')
                print(f"✅ 使用response_data作为响应数据")
            
            if not response_data:
                # 如果response_data为空，尝试从response_data字段获取（可能是None）
                print(f"⚠️ 响应数据为空，检查processing_log结构...")
                print(f"   api_info键: {list(api_info.keys())}")
                print(f"   response_data值: {api_info.get('response_data')}")
                print(f"   response_data类型: {type(api_info.get('response_data'))}")
                
                # 尝试直接使用response_data（即使它是None或空字符串）
                raw_response_data = api_info.get('response_data')
                if raw_response_data is None or (isinstance(raw_response_data, str) and len(raw_response_data.strip()) == 0):
                    return jsonify({
                        'status': 'error', 
                        'message': '响应数据为空，任务可能没有保存完整的响应数据',
                        'debug': {
                            'api_info_keys': list(api_info.keys()),
                            'has_original_response': 'original_response' in api_info,
                            'has_result_data': 'result_data' in api_info,
                            'has_response_data': 'response_data' in api_info,
                            'response_data_type': str(type(raw_response_data)),
                            'response_data_length': len(str(raw_response_data)) if raw_response_data else 0
                        }
                    }), 400
                else:
                    response_data = raw_response_data
            
            print(f"📦 响应数据类型: {type(response_data).__name__}")
            if isinstance(response_data, str):
                print(f"📦 响应数据长度: {len(response_data)} 字符")
                print(f"📦 响应数据前200字符: {response_data[:200]}")
            
            # 处理响应数据：可能是字符串、字典或其他格式
            if isinstance(response_data, str):
                # 如果是字符串，尝试解析为JSON
                try:
                    response_data = json.loads(response_data)
                    print(f"✅ JSON解析成功，响应数据类型: {type(response_data).__name__}")
                except json.JSONDecodeError as e:
                    # 如果解析失败，提供详细错误信息
                    print(f"⚠️ JSON解析失败: {str(e)}")
                    print(f"   响应数据前500字符: {response_data[:500]}")
                    print(f"   响应数据长度: {len(response_data)}")
                    
                    # 检查是否是截断的JSON
                    if response_data.strip().startswith('{') or response_data.strip().startswith('['):
                        # 尝试找到可能的JSON部分
                        if len(response_data) > 5000:
                            # 可能是截断的，尝试提取前5000字符并尝试解析
                            try:
                                truncated = response_data[:5000]
                                # 尝试找到最后一个完整的JSON对象
                                if truncated.rstrip().endswith('}') or truncated.rstrip().endswith(']'):
                                    response_data = json.loads(truncated)
                                    print(f"✅ 使用截断后的JSON数据（前5000字符）")
                                else:
                                    return jsonify({
                                        'status': 'error', 
                                        'message': '响应数据是截断的JSON字符串，无法完整解析',
                                        'debug': {
                                            'error': str(e),
                                            'response_preview': response_data[:500],
                                            'response_length': len(response_data),
                                            'suggestion': '响应数据可能被截断，请检查processing_log中的original_response字段'
                                        }
                                    }), 400
                            except:
                                return jsonify({
                                    'status': 'error', 
                                    'message': f'响应数据不是有效的JSON: {str(e)}',
                                    'debug': {
                                        'error': str(e),
                                        'response_preview': response_data[:500],
                                        'response_length': len(response_data)
                                    }
                                }), 400
                        else:
                            return jsonify({
                                'status': 'error', 
                                'message': f'响应数据不是有效的JSON: {str(e)}',
                                'debug': {
                                    'error': str(e),
                                    'response_preview': response_data[:500],
                                    'response_length': len(response_data)
                                }
                            }), 400
                    else:
                        return jsonify({
                            'status': 'error', 
                            'message': f'响应数据不是有效的JSON格式: {str(e)}',
                            'debug': {
                                'error': str(e),
                                'response_preview': response_data[:500],
                                'response_type': 'string (not JSON)'
                            }
                        }), 400
            elif isinstance(response_data, dict) or isinstance(response_data, list):
                # 已经是字典或列表，直接使用
                print(f"✅ 响应数据已经是 {type(response_data).__name__} 格式，无需解析")
            else:
                # 其他类型，尝试转换为字符串再解析
                print(f"⚠️ 响应数据是 {type(response_data).__name__} 类型，尝试转换")
                try:
                    response_data_str = str(response_data)
                    response_data = json.loads(response_data_str)
                    print(f"✅ 转换并解析成功")
                except Exception as e:
                    return jsonify({
                        'status': 'error', 
                        'message': f'响应数据格式不支持: {type(response_data).__name__}',
                        'debug': {
                            'response_type': str(type(response_data)),
                            'response_preview': str(response_data)[:500],
                            'error': str(e)
                        }
                    }), 400
            
            print(f"📦 开始解析响应数据...")
            
            # 查找base64图片数据
            image_data_base64 = None
            mime_type = 'image/png'
            
            # 方式1: 标准Gemini格式 (candidates -> content -> parts)
            if isinstance(response_data, dict) and 'candidates' in response_data:
                candidates = response_data.get('candidates', [])
                if candidates:
                    candidate = candidates[0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        for idx, part in enumerate(parts):
                            if isinstance(part, dict):
                                if 'inlineData' in part:
                                    inline_data = part['inlineData']
                                    if isinstance(inline_data, dict) and 'data' in inline_data:
                                        image_data_base64 = inline_data['data']
                                        mime_type = inline_data.get('mimeType', 'image/png')
                                        print(f"✅ 在candidates[0].content.parts[{idx}]中找到图片数据（inlineData）")
                                        break
                                elif 'inline_data' in part:
                                    inline_data = part['inline_data']
                                    if isinstance(inline_data, dict) and 'data' in inline_data:
                                        image_data_base64 = inline_data['data']
                                        mime_type = inline_data.get('mime_type', 'image/png')
                                        print(f"✅ 在candidates[0].content.parts[{idx}]中找到图片数据（inline_data）")
                                        break
            
            # 方式2: T8Star格式 (直接是parts数组)
            if not image_data_base64 and isinstance(response_data, list):
                print(f"📦 检测到响应为数组格式，尝试解析parts...")
                for idx, part in enumerate(response_data):
                    if isinstance(part, dict):
                        if 'inlineData' in part:
                            inline_data = part['inlineData']
                            if isinstance(inline_data, dict) and 'data' in inline_data:
                                image_data_base64 = inline_data['data']
                                mime_type = inline_data.get('mimeType', 'image/png')
                                print(f"✅ 在parts[{idx}]中找到图片数据（inlineData）")
                                break
                        elif 'inline_data' in part:
                            inline_data = part['inline_data']
                            if isinstance(inline_data, dict) and 'data' in inline_data:
                                image_data_base64 = inline_data['data']
                                mime_type = inline_data.get('mime_type', 'image/png')
                                print(f"✅ 在parts[{idx}]中找到图片数据（inline_data）")
                                break
            
            # 方式3: 响应中有parts字段
            if not image_data_base64 and isinstance(response_data, dict) and 'parts' in response_data:
                parts = response_data['parts']
                for idx, part in enumerate(parts):
                    if isinstance(part, dict):
                        if 'inlineData' in part:
                            inline_data = part['inlineData']
                            if isinstance(inline_data, dict) and 'data' in inline_data:
                                image_data_base64 = inline_data['data']
                                mime_type = inline_data.get('mimeType', 'image/png')
                                print(f"✅ 在response.parts[{idx}]中找到图片数据（inlineData）")
                                break
            
            if not image_data_base64:
                return jsonify({
                    'status': 'error', 
                    'message': '未找到base64图片数据',
                    'debug': {
                        'response_type': str(type(response_data)),
                        'response_keys': list(response_data.keys()) if isinstance(response_data, dict) else 'N/A',
                        'response_preview': json.dumps(response_data, ensure_ascii=False)[:500]
                    }
                }), 400
            
            print(f"✅ 找到base64图片数据，MIME类型: {mime_type}, 数据长度: {len(image_data_base64)} 字符")
            
            # 解码base64图片
            try:
                import base64
                image_data = base64.b64decode(image_data_base64)
                print(f"✅ base64解码成功，图片大小: {len(image_data)} bytes")
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'base64解码失败: {str(e)}'}), 400
            
            # 保存到final_works目录
            final_folder = 'final_works'
            os.makedirs(final_folder, exist_ok=True)
            
            # 确定文件扩展名
            if 'jpeg' in mime_type.lower() or 'jpg' in mime_type.lower():
                suffix = '.jpg'
            elif 'png' in mime_type.lower():
                suffix = '.png'
            elif 'gif' in mime_type.lower():
                suffix = '.gif'
            elif 'webp' in mime_type.lower():
                suffix = '.webp'
            else:
                suffix = '.png'  # 默认PNG
            
            # 生成文件名
            import time
            timestamp = int(time.time())
            task_id_short = str(task.id)[:8] if task.id else 'unknown'
            filename = f"final_{task_id_short}_{timestamp}{suffix}"
            local_path = os.path.join(final_folder, filename)
            
            # 保存文件
            try:
                with open(local_path, 'wb') as f:
                    f.write(image_data)
                print(f"✅ 图片已保存到: {local_path}")
                
                # 生成缩略图（长边1920px的JPG）
                try:
                    from app.utils.image_thumbnail import generate_thumbnail
                    thumbnail_path = generate_thumbnail(local_path, max_size=1920, quality=85)
                    if thumbnail_path:
                        print(f"✅ 缩略图生成成功: {thumbnail_path}")
                except Exception as thumb_error:
                    print(f"⚠️ 生成缩略图失败: {str(thumb_error)}")
                    import traceback
                    traceback.print_exc()
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'保存文件失败: {str(e)}'}), 500
            
            # 更新任务记录
            try:
                # 使用相对路径（用于存储到数据库）
                result_image_path = os.path.join(final_folder, filename).replace('\\', '/')
                task.output_image_path = result_image_path
                task.completed_at = datetime.now()
                
                # 更新processing_log中的result_image
                if task.processing_log:
                    try:
                        api_info = json.loads(task.processing_log) if isinstance(task.processing_log, str) else task.processing_log
                        api_info['result_image'] = result_image_path
                        api_info['result_image_local_path'] = local_path
                        task.processing_log = json.dumps(api_info, ensure_ascii=False)
                    except:
                        pass
                
                db.session.commit()
                print(f"✅ 任务记录已更新，output_image_path: {result_image_path}")
                
                return jsonify({
                    'status': 'success',
                    'message': '图片解析成功',
                    'data': {
                        'task_id': task.id,
                        'image_path': result_image_path,
                        'local_path': local_path,
                        'file_size': len(image_data)
                    }
                })
            except Exception as e:
                db.session.rollback()
                return jsonify({'status': 'error', 'message': f'更新任务记录失败: {str(e)}'}), 500
    
    except Exception as e:
        print(f"解析base64图片失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'解析失败: {str(e)}'}), 500


def download_api_result_image(image_url, task_id, app):
    """
    下载API返回的结果图片到final_works目录
    
    Args:
        image_url: 图片URL
        task_id: 任务ID（用于生成文件名）
        app: Flask应用实例
    
    Returns:
        str: 本地保存的图片路径（相对于项目根目录）
    """
    try:
        # 获取final_works目录
        final_folder = app.config.get('FINAL_FOLDER', 'final_works')
        os.makedirs(final_folder, exist_ok=True)
        
        # 从URL中提取文件扩展名
        parsed_url = urlparse(image_url)
        path = parsed_url.path
        ext = os.path.splitext(path)[1] or '.png'
        
        # 生成文件名：final_任务ID_时间戳.扩展名
        timestamp = int(time.time())
        filename = f"final_{task_id}_{timestamp}{ext}"
        local_path = os.path.join(final_folder, filename)
        
        # 下载图片
        print(f"开始下载API结果图: {image_url} -> {local_path}")
        
        # 禁用代理（结果图URL通常是公开的CDN）
        proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        has_proxy = any(os.environ.get(var) for var in proxy_env_vars)
        
        # 判断是否需要代理：如果URL是Google域名，可能需要代理；否则禁用代理
        is_google_domain = 'google' in parsed_url.netloc.lower() or 'googleapis.com' in parsed_url.netloc.lower()
        
        if has_proxy and not is_google_domain:
            download_proxies = {'http': None, 'https': None}
        else:
            download_proxies = None
        
        response = requests.get(image_url, timeout=60, stream=True, proxies=download_proxies)
        
        if response.status_code == 200:
            # 保存到本地，使用临时文件确保原子性
            temp_path = local_path + '.tmp'
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 原子性重命名（确保文件完整）
            if os.path.exists(local_path):
                os.remove(local_path)
            os.rename(temp_path, local_path)
            
            file_size = os.path.getsize(local_path)
            print(f"✅ API结果图下载成功: {local_path} ({file_size} bytes)")
            
            # 生成缩略图（长边1920px的JPG）
            try:
                from app.utils.image_thumbnail import generate_thumbnail
                thumbnail_path = generate_thumbnail(local_path, max_size=1920, quality=85)
                if thumbnail_path:
                    print(f"✅ 缩略图生成成功: {thumbnail_path}")
            except Exception as thumb_error:
                print(f"⚠️ 生成缩略图失败: {str(thumb_error)}")
                import traceback
                traceback.print_exc()
            
            # 返回相对路径（用于存储到数据库）
            return os.path.join(final_folder, filename).replace('\\', '/')
        else:
            print(f"❌ 下载失败: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        import traceback
        print(f"❌ 下载API结果图异常: {str(e)}")
        print(traceback.format_exc())
        return None
