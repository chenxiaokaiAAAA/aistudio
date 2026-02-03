# -*- coding: utf-8 -*-
"""
消息管理相关API路由
包含：获取未读消息数量、获取消息列表、检查新消息、标记消息为已读
"""
from flask import Blueprint, request, jsonify
import sys

# 导入主蓝图
from . import user_api_bp


def get_models():
    """获取数据库模型和配置（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
    }


@user_api_bp.route('/messages/unread-count', methods=['GET'])
def get_unread_message_count():
    """获取用户未读消息数量"""
    try:
        user_id = request.args.get('userId')
        session_id = request.args.get('sessionId')
        
        if not user_id and not session_id:
            return jsonify({"success": False, "message": "用户ID或会话ID不能为空"}), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        
        result = db.session.execute(
            db.text("""
                SELECT COUNT(*) FROM user_messages 
                WHERE (user_id = :user_id OR session_id = :session_id) 
                AND is_read = 0
            """),
            {'user_id': user_id, 'session_id': session_id}
        )
        
        count = result.fetchone()[0]
        
        return jsonify({
            "success": True,
            "unreadCount": count
        })
        
    except Exception as e:
        print(f"❌ 获取未读消息数量失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@user_api_bp.route('/messages', methods=['GET'])
def get_user_messages():
    """获取用户消息列表"""
    try:
        user_id = request.args.get('userId')
        session_id = request.args.get('sessionId')
        
        if not user_id and not session_id:
            return jsonify({"success": False, "message": "用户ID或会话ID不能为空"}), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        
        result = db.session.execute(
            db.text("""
                SELECT 
                    id,
                    title,
                    content,
                    message_type,
                    action,
                    url,
                    is_read,
                    created_at
                FROM user_messages 
                WHERE user_id = :user_id OR session_id = :session_id
                ORDER BY created_at DESC
                LIMIT 50
            """),
            {'user_id': user_id, 'session_id': session_id}
        )
        
        messages = []
        for row in result.fetchall():
            messages.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "type": row[3],
                "action": row[4],
                "url": row[5],
                "isRead": bool(row[6]),
                "time": row[7]
            })
        
        return jsonify({
            "success": True,
            "messages": messages
        })
        
    except Exception as e:
        print(f"❌ 获取消息列表失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@user_api_bp.route('/messages/check', methods=['GET'])
def check_user_messages():
    """检查用户是否有新消息"""
    try:
        user_id = request.args.get('userId')
        session_id = request.args.get('sessionId')
        
        if not user_id and not session_id:
            return jsonify({
                "success": False,
                "hasNewMessage": False,
                "message": "用户ID或会话ID不能为空"
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({
                'success': False,
                'hasNewMessage': False,
                'message': '系统未初始化'
            }), 500
        
        db = models['db']
        
        # 查询是否有未读消息
        result = db.session.execute(
            db.text("""
                SELECT 
                    id,
                    title,
                    content,
                    message_type,
                    action,
                    url
                FROM user_messages 
                WHERE (user_id = :user_id OR session_id = :session_id) 
                AND is_read = 0
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {'user_id': user_id, 'session_id': session_id}
        )
        
        row = result.fetchone()
        
        if row:
            return jsonify({
                "success": True,
                "hasNewMessage": True,
                "message": {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "type": row[3],
                    "action": row[4],
                    "url": row[5]
                }
            })
        else:
            return jsonify({
                "success": True,
                "hasNewMessage": False
            })
        
    except Exception as e:
        print(f"❌ 检查消息失败: {e}")
        return jsonify({
            "success": False,
            "hasNewMessage": False,
            "message": str(e)
        }), 500


@user_api_bp.route('/messages/read', methods=['POST'])
def mark_messages_as_read():
    """标记消息为已读"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        session_id = data.get('sessionId')
        
        if not user_id and not session_id:
            return jsonify({"success": False, "message": "用户ID或会话ID不能为空"}), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        
        result = db.session.execute(
            db.text("""
                UPDATE user_messages 
                SET is_read = 1, read_at = CURRENT_TIMESTAMP
                WHERE (user_id = :user_id OR session_id = :session_id) 
                AND is_read = 0
            """),
            {'user_id': user_id, 'session_id': session_id}
        )
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "消息已标记为已读",
            "updatedCount": result.rowcount
        })
        
    except Exception as e:
        print(f"❌ 标记消息为已读失败: {e}")
        models = get_models()
        if models:
            models['db'].session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
