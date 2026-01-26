# -*- coding: utf-8 -*-
"""
物流回调API路由模块
从 test_server.py 迁移物流相关路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import sys
import json

# 创建蓝图
logistics_api_bp = Blueprint('logistics_api', __name__, url_prefix='/api')


def get_models():
    """获取数据库模型（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'Order': test_server_module.Order,
    }


@logistics_api_bp.route('/printer/logistics-callback', methods=['POST'])
def printer_logistics_callback():
    """
    冲印系统物流信息回传接口
    厂家完成制作后，通过此接口回传物流信息
    """
    try:
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        Order = models['Order']
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '缺少请求数据'}), 400
        
        # 验证必要字段
        required_fields = ['order_id', 'logistics_company', 'tracking_number']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        
        order_id = data['order_id']
        logistics_company = data['logistics_company']
        tracking_number = data['tracking_number']
        status = data.get('status', 'shipped')
        remark = data.get('remark', '')
        
        # 查找对应的订单
        # order_id格式: YT_123，需要提取数字部分
        if order_id.startswith('YT_'):
            order_number = order_id[3:]  # 移除YT_前缀
            try:
                order_id_int = int(order_number)
                order = Order.query.get(order_id_int)
            except ValueError:
                return jsonify({'success': False, 'message': '订单ID格式错误'}), 400
        else:
            return jsonify({'success': False, 'message': '订单ID格式错误'}), 400
        
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'}), 404
        
        # 更新订单物流信息
        logistics_data = {
            'company': logistics_company,
            'tracking_number': tracking_number,
            'status': status,
            'remark': remark,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 更新订单状态和物流信息
        order.logistics_info = json.dumps(logistics_data, ensure_ascii=False)
        # 更新订单状态：如果当前是printing，改为pending_shipment；如果已经是pending_shipment，改为shipped
        if order.status == 'printing':
            order.status = 'pending_shipment'  # 待发货
        elif order.status == 'pending_shipment':
            order.status = 'shipped'  # 已发货
        else:
            order.status = 'shipped'  # 已发货（兼容旧逻辑）
        order.printer_send_status = 'logistics_updated'  # 新增状态：物流已更新
        
        # 添加发货时间字段（如果不存在则使用当前时间）
        if hasattr(order, 'shipped_at'):
            order.shipped_at = datetime.now()
        
        db.session.commit()
        
        print(f"✅ 订单 {order.order_number} 物流信息已更新:")
        print(f"   快递公司: {logistics_company}")
        print(f"   快递单号: {tracking_number}")
        print(f"   状态: {status}")
        
        return jsonify({
            'success': True,
            'message': '物流信息更新成功',
            'order_number': order.order_number
        })
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"物流信息回传失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'处理失败: {str(e)}'}), 500


@logistics_api_bp.route('/logistics/callback', methods=['POST'])
def logistics_callback():
    """
    物流信息回调接口（通用）
    支持多种物流系统的回调
    """
    try:
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        Order = models['Order']
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '缺少请求数据'}), 400
        
        # 验证必要字段
        order_number = data.get('order_number') or data.get('orderNumber')
        logistics_company = data.get('logistics_company') or data.get('logisticsCompany')
        tracking_number = data.get('tracking_number') or data.get('trackingNumber')
        
        if not all([order_number, logistics_company, tracking_number]):
            return jsonify({'success': False, 'message': '缺少必要字段'}), 400
        
        # 查找订单
        order = Order.query.filter_by(order_number=order_number).first()
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'}), 404
        
        # 构建物流信息
        logistics_data = {
            'company': logistics_company,
            'tracking_number': tracking_number,
            'status': data.get('status', 'shipped'),
            'remark': data.get('remark', ''),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'callback'  # 标记为回调来源
        }
        
        # 更新订单物流信息
        order.logistics_info = json.dumps(logistics_data, ensure_ascii=False)
        
        # 如果订单状态不是已发货相关状态，更新为已发货
        if order.status not in ['shipped', 'delivered']:
            order.status = 'shipped'
        
        # 添加发货时间字段
        if hasattr(order, 'shipped_at'):
            order.shipped_at = datetime.now()
        
        db.session.commit()
        
        print(f"✅ 订单 {order.order_number} 物流信息已更新（回调）:")
        print(f"   快递公司: {logistics_company}")
        print(f"   快递单号: {tracking_number}")
        
        return jsonify({
            'success': True,
            'message': '物流信息更新成功',
            'order_number': order.order_number
        })
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"物流回调处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'处理失败: {str(e)}'}), 500


@logistics_api_bp.route('/logistics/test', methods=['GET'])
def logistics_test():
    """
    物流回调测试接口
    用于测试物流回调功能
    """
    try:
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        Order = models['Order']
        
        # 获取测试参数
        order_number = request.args.get('order_number')
        if not order_number:
            return jsonify({
                'success': False,
                'message': '缺少订单号参数',
                'usage': '/api/logistics/test?order_number=ORDER123'
            }), 400
        
        # 查找订单
        order = Order.query.filter_by(order_number=order_number).first()
        if not order:
            return jsonify({
                'success': False,
                'message': '订单不存在'
            }), 404
        
        # 返回订单物流信息
        logistics_info = {}
        if order.logistics_info:
            try:
                logistics_info = json.loads(order.logistics_info)
            except:
                logistics_info = {'raw': order.logistics_info}
        
        return jsonify({
            'success': True,
            'order_number': order.order_number,
            'order_status': order.status,
            'logistics_info': logistics_info,
            'test_message': '物流回调测试接口正常'
        })
        
    except Exception as e:
        print(f"物流测试接口失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}'
        }), 500
