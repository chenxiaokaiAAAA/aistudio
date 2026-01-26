#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音小店文件导入同步功能（最适合新店铺）
"""

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️ pandas模块未安装，文件导入功能不可用")
import json
import os
from datetime import datetime
from test_server import db, Order
import requests

class DouyinFileSync:
    """抖音小店文件同步类"""
    
    def __init__(self):
        self.upload_dir = "douyin_imports"
        self.ensure_upload_dir()
    
    def ensure_upload_dir(self):
        """确保上传目录存在"""
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
    
    def sync_from_excel(self, file_path):
        """从Excel文件同步订单"""
        if not PANDAS_AVAILABLE:
            print("❌ pandas模块未安装，无法处理Excel文件")
            return 0, 1
        
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            synced_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    if self.sync_single_order_from_excel(row):
                        synced_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    print(f"同步第{index+1}行失败: {e}")
                    error_count += 1
            
            print(f"Excel同步完成: 成功{synced_count}个, 失败{error_count}个")
            return synced_count, error_count
            
        except Exception as e:
            print(f"读取Excel文件失败: {e}")
            return 0, 0
    
    def sync_from_csv(self, file_path):
        """从CSV文件同步订单"""
        if not PANDAS_AVAILABLE:
            print("❌ pandas模块未安装，无法处理CSV文件")
            return 0, 1
        
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path, encoding='utf-8')
            
            synced_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    if self.sync_single_order_from_csv(row):
                        synced_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    print(f"同步第{index+1}行失败: {e}")
                    error_count += 1
            
            print(f"CSV同步完成: 成功{synced_count}个, 失败{error_count}个")
            return synced_count, error_count
            
        except Exception as e:
            print(f"读取CSV文件失败: {e}")
            return 0, 0
    
    def sync_single_order_from_excel(self, row):
        """从Excel行数据同步单个订单"""
        try:
            # 提取订单信息（根据抖音小店Excel格式调整字段名）
            order_id = str(row.get('订单号', row.get('order_id', '')))
            customer_name = str(row.get('买家姓名', row.get('buyer_name', '')))
            customer_phone = str(row.get('买家电话', row.get('buyer_phone', '')))
            product_name = str(row.get('商品名称', row.get('product_name', '')))
            total_amount = float(row.get('订单金额', row.get('total_amount', 0)))
            status = str(row.get('订单状态', row.get('status', 'pending')))
            receiver_name = str(row.get('收货人', row.get('receiver_name', '')))
            shipping_address = str(row.get('收货地址', row.get('shipping_address', '')))
            remark = str(row.get('备注', row.get('remark', '')))
            create_time = row.get('下单时间', row.get('create_time', datetime.now()))
            
            # 检查订单是否已存在
            existing_order = Order.query.filter_by(
                external_order_number=order_id
            ).first()
            
            if existing_order:
                print(f"订单已存在: {order_id}")
                return True
            
            # 创建新订单
            order = Order(
                order_number=f"DY{order_id}",
                customer_name=customer_name,
                customer_phone=customer_phone,
                size='',  # 抖音订单可能没有尺寸信息
                style_name='',  # 抖音订单可能没有风格信息
                product_name=product_name,
                original_image='',  # 需要单独处理图片
                status=self.map_douyin_status(status),
                shipping_info=json.dumps({
                    'receiver': receiver_name,
                    'address': shipping_address,
                    'remark': remark
                }),
                price=total_amount,
                external_platform='douyin',
                external_order_number=order_id,
                source_type='douyin',
                created_at=create_time if isinstance(create_time, datetime) else datetime.now()
            )
            
            db.session.add(order)
            db.session.commit()
            
            print(f"抖音订单同步成功: {order_id}")
            return True
            
        except Exception as e:
            print(f"同步单个订单失败: {e}")
            db.session.rollback()
            return False
    
    def sync_single_order_from_csv(self, row):
        """从CSV行数据同步单个订单"""
        # CSV和Excel处理逻辑相同
        return self.sync_single_order_from_excel(row)
    
    def map_douyin_status(self, douyin_status):
        """映射抖音订单状态"""
        status_mapping = {
            '待付款': 'pending',
            '已付款': 'processing',
            '已发货': 'shipped',
            '已完成': 'completed',
            '已取消': 'cancelled',
            '待发货': 'processing',
            '退款中': 'cancelled',
            '已退款': 'cancelled'
        }
        return status_mapping.get(douyin_status, 'pending')

# Flask路由
def create_douyin_file_sync_routes(app):
    """创建抖音文件同步路由"""
    
    @app.route('/admin/douyin/import', methods=['GET'])
    def douyin_import_page():
        """抖音导入页面"""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>抖音订单导入</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h2>抖音订单导入</h2>
                <div class="card">
                    <div class="card-body">
                        <form action="/api/douyin/import/file" method="post" enctype="multipart/form-data">
                            <div class="mb-3">
                                <label class="form-label">选择文件</label>
                                <input type="file" class="form-control" name="file" accept=".xlsx,.xls,.csv" required>
                                <div class="form-text">支持Excel(.xlsx, .xls)和CSV文件</div>
                            </div>
                            <button type="submit" class="btn btn-primary">开始导入</button>
                        </form>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h4>导入说明</h4>
                    <ul>
                        <li>从抖音小店后台导出订单数据</li>
                        <li>确保文件包含：订单号、买家姓名、买家电话、商品名称、订单金额、订单状态、收货人、收货地址</li>
                        <li>支持Excel和CSV格式</li>
                        <li>重复订单会自动跳过</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        '''
    
    @app.route('/api/douyin/import/file', methods=['POST'])
    def import_douyin_file():
        """导入抖音文件"""
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'message': '没有选择文件'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'message': '没有选择文件'}), 400
            
            # 保存文件
            filename = file.filename
            file_path = os.path.join('douyin_imports', filename)
            file.save(file_path)
            
            # 根据文件类型同步
            sync_client = DouyinFileSync()
            
            if filename.endswith(('.xlsx', '.xls')):
                synced_count, error_count = sync_client.sync_from_excel(file_path)
            elif filename.endswith('.csv'):
                synced_count, error_count = sync_client.sync_from_csv(file_path)
            else:
                return jsonify({'success': False, 'message': '不支持的文件格式'}), 400
            
            # 删除临时文件
            os.remove(file_path)
            
            return jsonify({
                'success': True,
                'message': f'导入完成！成功{synced_count}个，失败{error_count}个',
                'synced_count': synced_count,
                'error_count': error_count
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'导入失败: {str(e)}'
            }), 500

if __name__ == "__main__":
    print("抖音文件导入同步功能已准备就绪")
    print("使用方法：")
    print("1. 从抖音小店后台导出订单数据")
    print("2. 访问 /admin/douyin/import 上传文件")
    print("3. 系统自动同步订单到后台")
