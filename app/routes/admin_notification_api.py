# -*- coding: utf-8 -*-
"""
管理后台消息通知API路由模块
从 test_server.py 迁移消息通知相关路由
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import sys

# 创建蓝图
admin_notification_api_bp = Blueprint('admin_notification_api', __name__, url_prefix='/api/admin')


def get_models():
    """获取数据库模型（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'Order': test_server_module.Order,
        'Commission': test_server_module.Commission,
        'PromotionUser': test_server_module.PromotionUser,
        'send_subscribe_message': getattr(test_server_module, 'send_subscribe_message', None),
    }


@admin_notification_api_bp.route('/send-order-completion-notification', methods=['POST'])
@login_required
def send_order_completion_notification():
    """发送订单完成通知"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        Order = models['Order']
        send_subscribe_message = models.get('send_subscribe_message')
        
        if not send_subscribe_message:
            return jsonify({'success': False, 'message': '消息发送功能不可用'}), 500
        
        data = request.get_json()
        order_id = data.get('orderId')
        
        if not order_id:
            return jsonify({
                'success': False,
                'message': '缺少订单ID'
            }), 400
        
        # 获取订单信息
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': '订单不存在'
            }), 404
        
        # 获取用户openid
        openid = getattr(order, 'openid', None)
        if not openid:
            return jsonify({
                'success': False,
                'message': '用户信息不完整'
            }), 400
        
        # 发送订阅消息 - 制作完成通知模板
        template_data = {
            'character_string13': {'value': order.order_number},  # 订单编号
            'thing1': {'value': order.size or '定制产品'},  # 作品名称
            'time17': {'value': order.completed_at.strftime('%Y年%m月%d日 %H:%M') if order.completed_at else '待定'}  # 制作完成时间
        }
        
        success = send_subscribe_message(
            openid=openid,
            template_id='BOy7pDiq-pM1qiJHJfP9jUjAbi9o0bZG5-mEKZbnYT8',  # 制作完成通知模板ID
            data=template_data,
            page=f'/pages/order-detail/order-detail?orderId={order.order_number}'  # 跳转到订单详情页
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': '通知发送成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '通知发送失败'
            }), 500
            
    except Exception as e:
        print(f"发送订单完成通知失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'发送通知失败: {str(e)}'
        }), 500


@admin_notification_api_bp.route('/send-commission-notification', methods=['POST'])
@login_required
def send_commission_notification():
    """发送推广收益通知"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        Commission = models['Commission']
        Order = models['Order']
        PromotionUser = models['PromotionUser']
        send_subscribe_message = models.get('send_subscribe_message')
        
        if not send_subscribe_message:
            return jsonify({'success': False, 'message': '消息发送功能不可用'}), 500
        
        data = request.get_json()
        commission_id = data.get('commissionId')
        
        if not commission_id:
            return jsonify({
                'success': False,
                'message': '缺少分佣记录ID'
            }), 400
        
        # 获取分佣记录信息
        commission = Commission.query.get(commission_id)
        if not commission:
            return jsonify({
                'success': False,
                'message': '分佣记录不存在'
            }), 404
        
        # 获取用户信息
        promotion_user = PromotionUser.query.filter_by(user_id=commission.referrer_user_id).first()
        if not promotion_user or not promotion_user.open_id:
            return jsonify({
                'success': False,
                'message': '用户信息不完整'
            }), 400
        
        # 获取订单信息
        order = Order.query.filter_by(order_number=commission.order_id).first()
        if not order:
            return jsonify({
                'success': False,
                'message': '订单信息不存在'
            }), 404
        
        # 发送订阅消息 - 收益提成提醒模板
        template_data = {
            'thing1': {'value': f'¥{order.price}'},  # 下单金额
            'thing2': {'value': f'¥{commission.amount}'},  # 提成金额
            'thing3': {'value': '已结算' if commission.status == 'completed' else '待结算'}  # 金额状态
        }
        
        success = send_subscribe_message(
            openid=promotion_user.open_id,
            template_id='bcY_uUJMP1IGFIuUyiFeBSFIPbCb4areeTXs78HUe9Y',  # 收益提成提醒模板ID
            data=template_data,
            page='/pages/promotion/promotion'
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': '通知发送成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '通知发送失败'
            }), 500
            
    except Exception as e:
        print(f"发送推广收益通知失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'发送通知失败: {str(e)}'
        }), 500


@admin_notification_api_bp.route('/send-message', methods=['POST'])
@login_required
def send_message_to_user():
    """发送消息给用户（后台管理）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        
        data = request.get_json()
        
        # 验证必要参数
        if not data.get('title') or not data.get('content'):
            return jsonify({"success": False, "message": "消息标题和内容不能为空"}), 400
        
        if not data.get('userId') and not data.get('sessionId'):
            return jsonify({"success": False, "message": "用户ID或会话ID不能为空"}), 400
        
        # 插入消息
        result = db.session.execute(
            db.text("""
                INSERT INTO user_messages 
                (user_id, session_id, title, content, message_type, action, url)
                VALUES (:user_id, :session_id, :title, :content, :message_type, :action, :url)
            """),
            {
                'user_id': data.get('userId'),
                'session_id': data.get('sessionId'),
                'title': data.get('title'),
                'content': data.get('content'),
                'message_type': data.get('type', 'info'),
                'action': data.get('action'),
                'url': data.get('url')
            }
        )
        
        db.session.commit()
        
        # 获取插入的记录ID
        message_id = db.session.execute(
            db.text("SELECT last_insert_rowid()")
        ).fetchone()[0]
        
        print(f"✅ 消息发送成功: messageId={message_id}, userId={data.get('userId')}")
        
        return jsonify({
            "success": True,
            "messageId": message_id,
            "message": "消息发送成功"
        })
        
    except Exception as e:
        print(f"❌ 发送消息失败: {e}")
        if 'db' in locals():
            db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@admin_notification_api_bp.route('/batch-send-message', methods=['POST'])
@login_required
def batch_send_message():
    """批量发送消息（后台管理）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        
        data = request.get_json()
        
        # 验证参数
        if not data.get('title') or not data.get('content'):
            return jsonify({"success": False, "message": "消息标题和内容不能为空"}), 400
        
        target_type = data.get('targetType', 'all')  # all, promotion_users, unread_users
        message_type = data.get('type', 'info')
        action = data.get('action')
        url = data.get('url')
        
        # 根据目标类型获取用户列表
        if target_type == 'all':
            result = db.session.execute(
                db.text("SELECT DISTINCT user_id, session_id FROM user_access_logs WHERE user_id IS NOT NULL AND user_id != ''")
            )
        elif target_type == 'promotion_users':
            result = db.session.execute(
                db.text("SELECT DISTINCT user_id, session_id FROM user_access_logs WHERE final_promotion_code IS NOT NULL")
            )
        elif target_type == 'unread_users':
            result = db.session.execute(
                db.text("""
                    SELECT DISTINCT v.user_id, v.session_id 
                    FROM user_access_logs v 
                    LEFT JOIN user_messages m ON (v.user_id = m.user_id OR v.session_id = m.session_id)
                    WHERE (m.is_read = 0 OR m.id IS NULL)
                    AND v.user_id IS NOT NULL AND v.user_id != ''
                """)
            )
        else:
            return jsonify({"success": False, "message": "无效的目标类型"}), 400
        
        users = result.fetchall()
        
        # 批量插入消息
        sent_count = 0
        for user_id, session_id in users:
            try:
                db.session.execute(
                    db.text("""
                        INSERT INTO user_messages 
                        (user_id, session_id, title, content, message_type, action, url)
                        VALUES (:user_id, :session_id, :title, :content, :message_type, :action, :url)
                    """),
                    {
                        'user_id': user_id,
                        'session_id': session_id,
                        'title': data['title'],
                        'content': data['content'],
                        'message_type': message_type,
                        'action': action,
                        'url': url
                    }
                )
                sent_count += 1
            except Exception as e:
                print(f"⚠️ 发送消息给用户失败: {e}")
                continue
        
        db.session.commit()
        
        print(f"✅ 批量发送消息成功: 发送给 {sent_count} 个用户")
        
        return jsonify({
            "success": True,
            "sentCount": sent_count,
            "message": f"消息已发送给 {sent_count} 个用户"
        })
        
    except Exception as e:
        print(f"❌ 批量发送消息失败: {e}")
        if 'db' in locals():
            db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
