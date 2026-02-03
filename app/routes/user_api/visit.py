# -*- coding: utf-8 -*-
"""
访问统计相关API路由
包含：记录用户访问、获取用户访问统计
"""
from flask import Blueprint, request, jsonify
import sys
import json
import threading

# 导入主蓝图
from . import user_api_bp


def get_models():
    """获取数据库模型和配置（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'UserVisit': test_server_module.UserVisit,
    }


@user_api_bp.route('/visit', methods=['POST', 'OPTIONS'])
def record_user_visit():
    """记录用户访问（支持完整访问追踪）- 优化版本：快速响应，避免超时"""
    # 处理 OPTIONS 预检请求
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        # CORS头由after_request统一处理，这里不需要重复设置
        return response
    
    # 先快速返回响应，避免小程序超时
    response_data = {
        'success': True,
        'message': '用户访问记录成功',
        'visitId': None,
        'promotionCode': None,
        'isNewUser': False
    }
    
    try:
        # 添加调试日志
        print(f"📥 [用户访问记录] 收到请求: {request.method} {request.path}")
        print(f"📥 [用户访问记录] Content-Type: {request.content_type}")
        print(f"📥 [用户访问记录] Content-Length: {request.content_length}")
        
        # 安全地获取JSON数据，避免JSONDecodeError
        try:
            data = request.get_json(force=True, silent=True) or {}
        except Exception as json_error:
            print(f"⚠️ [用户访问记录] JSON解析失败: {json_error}")
            # 尝试从原始数据获取
            try:
                raw_data = request.get_data(as_text=True)
                print(f"📥 [用户访问记录] 原始数据: {raw_data[:200]}")
                if raw_data:
                    data = json.loads(raw_data)
                else:
                    data = {}
            except:
                data = {}
        
        session_id = data.get('sessionId') or data.get('session_id')
        openid = data.get('openId') or data.get('openid')
        user_id = data.get('userId') or data.get('user_id')
        visit_type = data.get('visitType') or data.get('type', 'launch')
        promotion_code = data.get('promotionCode') or data.get('promotion_code')
        referrer_user_id = data.get('referrerUserId') or data.get('referrer_user_id')
        scene = data.get('scene')
        user_info = data.get('userInfo') or data.get('user_info') or {}
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        print(f"📥 [用户访问记录] 数据: sessionId={session_id}, type={visit_type}, userId={user_id}")
        
        if not session_id:
            print("⚠️ [用户访问记录] 缺少sessionId")
            return jsonify({
                'success': False,
                'message': '会话ID不能为空'
            }), 400
        
        models = get_models()
        if not models:
            print("⚠️ [用户访问记录] 系统未初始化，返回默认响应")
            # 即使系统未初始化，也返回成功，避免阻塞小程序
            return jsonify(response_data)
        
        # ⚡ 优化：先快速返回响应，避免超时
        # 数据库操作在后台异步处理，不阻塞响应
        print(f"✅ [用户访问记录] 准备快速返回响应")
        
        # 使用线程异步处理数据库操作
        from flask import current_app
        
        def save_visit_async():
            # 在异步线程中需要创建应用上下文
            try:
                # 获取应用实例
                if 'test_server' in sys.modules:
                    test_server_module = sys.modules['test_server']
                    app_instance = test_server_module.app
                else:
                    print("⚠️ [用户访问记录] 异步保存：无法获取应用实例")
                    return
                
                # 在应用上下文中执行数据库操作
                with app_instance.app_context():
                    # 重新获取models，确保线程安全
                    async_models = get_models()
                    if not async_models:
                        print("⚠️ [用户访问记录] 异步保存：系统未初始化")
                        return
                        
                    db = async_models['db']
                    UserVisit = async_models.get('UserVisit')
                    
                    if UserVisit:
                        # 使用 ORM 快速插入
                        new_visit = UserVisit(
                            session_id=session_id,
                            openid=openid if openid and openid != 'anonymous' else None,
                            user_id=user_id if user_id and user_id != 'anonymous' else None,
                            visit_type=visit_type,
                            source='miniprogram',
                            scene=scene,
                            user_info=json.dumps(user_info) if user_info else None,
                            is_authorized=bool(openid and openid != 'anonymous'),
                            is_registered=bool(user_id and user_id != 'anonymous'),
                            has_ordered=(visit_type == 'order'),
                            ip_address=ip_address,
                            user_agent=user_agent,
                            promotion_code=promotion_code,
                            referrer_user_id=referrer_user_id
                        )
                        db.session.add(new_visit)
                        db.session.commit()
                        print(f"✅ [用户访问记录] 异步保存成功: visitId={new_visit.id}")
                    else:
                        # 使用原始 SQL（如果模型不存在）
                        result = db.session.execute(
                            db.text("""
                                INSERT INTO user_visits 
                                (session_id, openid, user_id, promotion_code, referrer_user_id,
                                 visit_time, visit_type, source, scene, user_info, is_authorized, 
                                 is_registered, has_ordered, ip_address, user_agent)
                                VALUES (:session_id, :openid, :user_id, :promotion_code, :referrer_user_id,
                                        CURRENT_TIMESTAMP, :visit_type, :source, :scene, :user_info, :is_authorized, 
                                        :is_registered, :has_ordered, :ip_address, :user_agent)
                            """),
                            {
                                'session_id': session_id, 
                                'openid': openid if openid and openid != 'anonymous' else None, 
                                'user_id': user_id if user_id and user_id != 'anonymous' else None,
                                'promotion_code': promotion_code,
                                'referrer_user_id': referrer_user_id,
                                'visit_type': visit_type, 
                                'source': 'miniprogram', 
                                'scene': scene,
                                'user_info': json.dumps(user_info) if user_info else None,
                                'is_authorized': bool(openid and openid != 'anonymous'), 
                                'is_registered': bool(user_id and user_id != 'anonymous'),
                                'has_ordered': (visit_type == 'order'), 
                                'ip_address': ip_address,
                                'user_agent': user_agent
                            }
                        )
                        db.session.commit()
                        print(f"✅ [用户访问记录] 异步保存成功（SQL方式）")
            except Exception as e:
                # 如果是重复记录错误，忽略
                if 'UNIQUE' not in str(e) and 'duplicate' not in str(e).lower():
                    print(f"⚠️ [用户访问记录] 异步保存失败: {e}")
                    import traceback
                    traceback.print_exc()
        
        # 启动异步保存线程
        thread = threading.Thread(target=save_visit_async, daemon=True)
        thread.start()
        
        # 立即返回响应，不等待数据库操作完成
        print(f"✅ [用户访问记录] 快速返回响应")
        response = jsonify(response_data)
        # 确保响应头正确设置（使用set避免重复，让after_request处理CORS）
        # Content-Type由jsonify自动设置，这里只确保CORS头
        # 注意：不要在这里设置CORS头，让after_request统一处理，避免重复
        print(f"✅ [用户访问记录] 响应已准备: {response_data}")
        return response
        
    except Exception as e:
        print(f"❌ [用户访问记录] 异常: {e}")
        import traceback
        traceback.print_exc()
        # 即使异常也返回成功，避免阻塞小程序
        print(f"⚠️ [用户访问记录] 返回默认成功响应")
        response = jsonify(response_data)
        # CORS头由after_request统一处理，这里不需要重复设置
        return response


@user_api_bp.route('/visit/stats', methods=['GET'])
def get_user_visit_stats():
    """获取用户访问统计"""
    try:
        from sqlalchemy import func
        
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        UserVisit = models['UserVisit']
        db = models['db']
        
        query = UserVisit.query
        
        if start_date:
            query = query.filter(UserVisit.visit_time >= start_date)
        if end_date:
            query = query.filter(UserVisit.visit_time <= end_date)
        
        total_visits = query.count()
        unique_users = query.with_entities(func.count(func.distinct(UserVisit.user_id))).scalar() or 0
        unique_sessions = query.with_entities(func.count(func.distinct(UserVisit.session_id))).scalar() or 0
        
        return jsonify({
            'success': True,
            'stats': {
                'totalVisits': total_visits,
                'uniqueUsers': unique_users,
                'uniqueSessions': unique_sessions
            }
        })
        
    except Exception as e:
        print(f"获取访问统计失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取统计失败: {str(e)}'
        }), 500
