#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音订单同步服务
"""

import json
import time
from datetime import datetime, timedelta
from test_server import db, Order
from douyin_open_api import DouyinOpenAPI
from douyin_config import map_order_status

class DouyinOrderSyncService:
    """抖音订单同步服务"""
    
    def __init__(self):
        self.api_client = DouyinOpenAPI()
        self.last_sync_time = None
        
    def sync_orders(self, start_time=None, end_time=None):
        """同步订单"""
        try:
            print("开始同步抖音订单...")
            
            # 获取订单数据
            orders = self.api_client.get_orders(start_time, end_time)
            
            if not orders:
                print("没有获取到订单数据")
                return 0
            
            synced_count = 0
            error_count = 0
            
            for order_data in orders:
                try:
                    if self.sync_single_order(order_data):
                        synced_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    print(f"同步订单失败: {e}")
                    error_count += 1
            
            self.last_sync_time = datetime.now()
            
            print(f"订单同步完成: 成功 {synced_count} 个, 失败 {error_count} 个")
            return synced_count
            
        except Exception as e:
            print(f"同步订单异常: {e}")
            return 0
    
    def sync_single_order(self, order_data):
        """同步单个订单"""
        try:
            order_id = order_data.get('order_id')
            if not order_id:
                print("订单ID为空，跳过")
                return False
            
            # 检查订单是否已存在
            existing_order = Order.query.filter_by(
                external_order_number=str(order_id)
            ).first()
            
            if existing_order:
                print(f"订单已存在: {order_id}")
                # 更新订单状态
                self.update_order_status(existing_order, order_data)
                return True
            
            # 创建新订单
            order = Order(
                order_number=f"DY{order_id}",
                customer_name=order_data.get('buyer_name', ''),
                customer_phone=order_data.get('buyer_phone', ''),
                size=order_data.get('product_size', ''),
                style_name=order_data.get('style_name', ''),
                product_name=order_data.get('product_name', ''),
                original_image=order_data.get('image_url', ''),
                status=map_order_status(order_data.get('status', '')),
                shipping_info=json.dumps({
                    'receiver': order_data.get('receiver_name', ''),
                    'address': order_data.get('shipping_address', ''),
                    'remark': order_data.get('remark', '')
                }),
                price=float(order_data.get('total_amount', 0)),
                external_platform='douyin',
                external_order_number=str(order_id),
                source_type='douyin',
                created_at=datetime.fromtimestamp(order_data.get('create_time', 0)) if order_data.get('create_time') else datetime.now()
            )
            
            db.session.add(order)
            db.session.commit()
            
            print(f"订单同步成功: {order_id}")
            return True
            
        except Exception as e:
            print(f"同步单个订单失败: {e}")
            db.session.rollback()
            return False
    
    def update_order_status(self, order, order_data):
        """更新订单状态"""
        try:
            new_status = map_order_status(order_data.get('status', ''))
            if order.status != new_status:
                old_status = order.status
                order.status = new_status
                
                # 如果订单完成，更新完成时间
                if new_status == 'completed' and not order.completed_at:
                    order.completed_at = datetime.now()
                
                db.session.commit()
                print(f"订单状态更新: {order.external_order_number} {old_status} -> {new_status}")
            
        except Exception as e:
            print(f"更新订单状态失败: {e}")
            db.session.rollback()
    
    def sync_recent_orders(self, hours=24):
        """同步最近N小时的订单"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        return self.sync_orders(start_time, end_time)
    
    def get_sync_status(self):
        """获取同步状态"""
        try:
            # 统计抖音订单数量
            total_orders = Order.query.filter_by(source_type='douyin').count()
            
            # 统计最近同步的订单
            recent_orders = Order.query.filter(
                Order.source_type == 'douyin',
                Order.created_at >= datetime.now() - timedelta(hours=24)
            ).count()
            
            return {
                'total_douyin_orders': total_orders,
                'recent_synced_orders': recent_orders,
                'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
                'api_status': 'connected' if self.api_client.is_token_valid() else 'disconnected'
            }
            
        except Exception as e:
            print(f"获取同步状态失败: {e}")
            return None

# 定时同步任务
class DouyinSyncScheduler:
    """抖音同步定时任务"""
    
    def __init__(self):
        self.sync_service = DouyinOrderSyncService()
        self.is_running = False
    
    def start_scheduler(self, interval_minutes=5):
        """启动定时同步"""
        import threading
        import schedule
        
        def sync_job():
            print(f"[{datetime.now()}] 开始执行抖音订单同步...")
            self.sync_service.sync_recent_orders(hours=1)  # 同步最近1小时的订单
        
        def run_scheduler():
            schedule.every(interval_minutes).minutes.do(sync_job)
            self.is_running = True
            
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)
        
        # 在后台线程中运行
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        print(f"抖音订单同步定时任务已启动，每{interval_minutes}分钟同步一次")
    
    def stop_scheduler(self):
        """停止定时同步"""
        self.is_running = False
        print("抖音订单同步定时任务已停止")

# 全局同步服务实例
douyin_sync_service = DouyinOrderSyncService()
douyin_scheduler = DouyinSyncScheduler()

# 使用示例
def test_douyin_sync():
    """测试抖音同步功能"""
    print("测试抖音订单同步...")
    
    # 测试同步最近24小时的订单
    count = douyin_sync_service.sync_recent_orders(hours=24)
    print(f"同步了 {count} 个订单")
    
    # 获取同步状态
    status = douyin_sync_service.get_sync_status()
    if status:
        print(f"同步状态: {status}")

if __name__ == "__main__":
    print("抖音订单同步服务已准备就绪")
    print("使用方法:")
    print("1. 配置 douyin_config.py 中的API信息")
    print("2. 调用 test_douyin_sync() 测试同步功能")
    print("3. 调用 douyin_scheduler.start_scheduler() 启动定时同步")




