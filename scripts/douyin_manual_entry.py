#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音小店手动录入功能（最简单的方式）
"""

from flask import request, jsonify, render_template
from test_server import db, Order
import json
from datetime import datetime

def create_douyin_manual_entry_routes(app):
    """创建抖音手动录入路由"""
    
    @app.route('/admin/douyin/manual', methods=['GET'])
    def douyin_manual_page():
        """抖音手动录入页面"""
        return render_template('admin/douyin_manual_entry.html')
    
    @app.route('/api/douyin/manual/add', methods=['POST'])
    def add_douyin_order_manual():
        """手动添加抖音订单"""
        try:
            data = request.get_json()
            
            # 验证必填字段
            required_fields = ['order_id', 'customer_name', 'customer_phone', 'product_name', 'total_amount']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({
                        'success': False,
                        'message': f'缺少必填字段: {field}'
                    }), 400
            
            # 检查订单是否已存在
            existing_order = Order.query.filter_by(
                external_order_number=data['order_id']
            ).first()
            
            if existing_order:
                return jsonify({
                    'success': False,
                    'message': '订单已存在'
                }), 400
            
            # 创建新订单
            order = Order(
                order_number=f"DY{data['order_id']}",
                customer_name=data['customer_name'],
                customer_phone=data['customer_phone'],
                size=data.get('size', ''),
                style_name=data.get('style_name', ''),
                product_name=data['product_name'],
                original_image=data.get('image_url', ''),
                status=data.get('status', 'pending'),
                shipping_info=json.dumps({
                    'receiver': data.get('receiver_name', ''),
                    'address': data.get('shipping_address', ''),
                    'remark': data.get('remark', '')
                }),
                price=float(data['total_amount']),
                external_platform='douyin',
                external_order_number=data['order_id'],
                source_type='douyin',
                created_at=datetime.now()
            )
            
            db.session.add(order)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '抖音订单添加成功',
                'order_id': order.id
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'添加失败: {str(e)}'
            }), 500

# 创建手动录入页面模板
def create_douyin_manual_template():
    """创建抖音手动录入页面模板"""
    template_content = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>抖音订单手动录入</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h4>抖音订单手动录入</h4>
                    </div>
                    <div class="card-body">
                        <form id="douyinOrderForm">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">订单号 *</label>
                                        <input type="text" class="form-control" name="order_id" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">订单金额 *</label>
                                        <input type="number" class="form-control" name="total_amount" step="0.01" required>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">买家姓名 *</label>
                                        <input type="text" class="form-control" name="customer_name" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">买家电话 *</label>
                                        <input type="tel" class="form-control" name="customer_phone" required>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">商品名称 *</label>
                                        <input type="text" class="form-control" name="product_name" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">商品尺寸</label>
                                        <input type="text" class="form-control" name="size">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">收货人</label>
                                        <input type="text" class="form-control" name="receiver_name">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">订单状态</label>
                                        <select class="form-select" name="status">
                                            <option value="pending">待处理</option>
                                            <option value="processing">处理中</option>
                                            <option value="shipped">已发货</option>
                                            <option value="completed">已完成</option>
                                            <option value="cancelled">已取消</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">收货地址</label>
                                <textarea class="form-control" name="shipping_address" rows="2"></textarea>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">备注</label>
                                <textarea class="form-control" name="remark" rows="2"></textarea>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">图片URL</label>
                                <input type="url" class="form-control" name="image_url">
                            </div>
                            
                            <button type="submit" class="btn btn-primary">添加订单</button>
                            <button type="reset" class="btn btn-secondary">重置</button>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>录入说明</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li><strong>订单号：</strong>抖音小店后台的订单编号</li>
                            <li><strong>订单金额：</strong>订单总金额（元）</li>
                            <li><strong>买家信息：</strong>从抖音订单详情获取</li>
                            <li><strong>商品信息：</strong>商品名称和尺寸</li>
                            <li><strong>收货信息：</strong>收货人和地址</li>
                            <li><strong>图片URL：</strong>商品图片链接（可选）</li>
                        </ul>
                        
                        <div class="alert alert-info">
                            <strong>提示：</strong>
                            <br>• 标有 * 的字段为必填项
                            <br>• 订单号不能重复
                            <br>• 图片URL需要是可访问的链接
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('douyinOrderForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            fetch('/api/douyin/manual/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    alert('订单添加成功！');
                    this.reset();
                } else {
                    alert('添加失败：' + result.message);
                }
            })
            .catch(error => {
                alert('网络错误：' + error.message);
            });
        });
    </script>
</body>
</html>
    '''
    
    # 确保模板目录存在
    import os
    template_dir = 'templates/admin'
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    # 写入模板文件
    with open(os.path.join(template_dir, 'douyin_manual_entry.html'), 'w', encoding='utf-8') as f:
        f.write(template_content)

if __name__ == "__main__":
    print("抖音手动录入功能已准备就绪")
    print("使用方法：")
    print("1. 访问 /admin/douyin/manual")
    print("2. 填写订单信息")
    print("3. 点击添加订单")




