#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能图片清理机制
基于订单状态的图片清理系统
- 已发货订单的高清图片在发货后10天自动清理
- 保留数据库记录，支持从百度云恢复
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, OrderImage

class SmartImageCleanup:
    """智能图片清理器"""
    
    def __init__(self):
        self.hd_folder = app.config.get('HD_FOLDER', 'hd_images')
        self.uploads_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        self.final_folder = app.config.get('FINAL_FOLDER', 'final_works')
        
        # 清理配置
        self.hd_cleanup_days = 10  # 高清图片发货后10天清理
        self.backup_log_file = 'image_cleanup_log.json'
        
        # 确保目录存在
        os.makedirs(self.hd_folder, exist_ok=True)
        os.makedirs(self.uploads_folder, exist_ok=True)
        os.makedirs(self.final_folder, exist_ok=True)
    
    def load_cleanup_log(self):
        """加载清理日志"""
        if os.path.exists(self.backup_log_file):
            try:
                with open(self.backup_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载清理日志失败: {e}")
        return {}
    
    def save_cleanup_log(self, log_data):
        """保存清理日志"""
        try:
            with open(self.backup_log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存清理日志失败: {e}")
    
    def add_order_shipped_time_field(self):
        """为订单表添加发货时间字段"""
        try:
            with app.app_context():
                # 检查字段是否已存在
                from sqlalchemy import text
                result = db.session.execute(text("PRAGMA table_info(orders)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'shipped_at' not in columns:
                    print("添加shipped_at字段到订单表...")
                    db.session.execute(text("ALTER TABLE orders ADD COLUMN shipped_at DATETIME"))
                    db.session.commit()
                    print("✅ shipped_at字段添加成功")
                else:
                    print("✅ shipped_at字段已存在")
                    
        except Exception as e:
            print(f"添加shipped_at字段失败: {e}")
    
    def update_shipped_orders(self):
        """更新已发货订单的发货时间"""
        try:
            with app.app_context():
                # 查找状态为shipped但shipped_at为空的订单
                shipped_orders = Order.query.filter(
                    Order.status == 'shipped',
                    Order.shipped_at.is_(None)
                ).all()
                
                if shipped_orders:
                    print(f"更新 {len(shipped_orders)} 个已发货订单的发货时间...")
                    
                    for order in shipped_orders:
                        # 使用completed_at作为发货时间，如果没有则使用当前时间
                        shipped_time = order.completed_at or datetime.now()
                        order.shipped_at = shipped_time
                    
                    db.session.commit()
                    print(f"✅ 已更新 {len(shipped_orders)} 个订单的发货时间")
                else:
                    print("✅ 没有需要更新发货时间的订单")
                    
        except Exception as e:
            print(f"更新发货时间失败: {e}")
    
    def cleanup_hd_images_by_order_status(self):
        """基于订单状态清理高清图片"""
        try:
            with app.app_context():
                cleanup_log = self.load_cleanup_log()
                current_time = datetime.now()
                cleanup_threshold = current_time - timedelta(days=self.hd_cleanup_days)
                
                print(f"🔍 查找发货时间早于 {cleanup_threshold.strftime('%Y-%m-%d %H:%M:%S')} 的订单...")
                
                # 查找需要清理的订单
                orders_to_cleanup = Order.query.filter(
                    Order.status == 'shipped',
                    Order.shipped_at.isnot(None),
                    Order.shipped_at <= cleanup_threshold,
                    Order.hd_image.isnot(None)
                ).all()
                
                if not orders_to_cleanup:
                    print("✅ 没有需要清理的高清图片")
                    return 0
                
                print(f"📋 找到 {len(orders_to_cleanup)} 个订单需要清理高清图片")
                
                cleaned_count = 0
                for order in orders_to_cleanup:
                    if self._cleanup_order_hd_image(order, cleanup_log):
                        cleaned_count += 1
                
                # 保存清理日志
                self.save_cleanup_log(cleanup_log)
                
                print(f"✅ 高清图片清理完成，共清理 {cleaned_count} 个订单")
                return cleaned_count
                
        except Exception as e:
            print(f"清理高清图片失败: {e}")
            return 0
    
    def _cleanup_order_hd_image(self, order, cleanup_log):
        """清理单个订单的高清图片"""
        try:
            hd_image_filename = order.hd_image
            if not hd_image_filename:
                return False
            
            hd_image_path = os.path.join(self.hd_folder, hd_image_filename)
            
            # 检查文件是否存在
            if not os.path.exists(hd_image_path):
                print(f"⚠️  高清图片文件不存在: {hd_image_filename}")
                return False
            
            # 记录清理信息
            cleanup_info = {
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'hd_image_filename': hd_image_filename,
                'shipped_at': order.shipped_at.isoformat() if order.shipped_at else None,
                'cleanup_time': datetime.now().isoformat(),
                'file_size': os.path.getsize(hd_image_path),
                'backup_status': 'pending'  # 等待备份到百度云
            }
            
            # 删除文件
            os.remove(hd_image_path)
            
            # 更新清理日志
            cleanup_log[order.order_number] = cleanup_info
            
            # 清空数据库中的高清图片字段（保留记录）
            order.hd_image = None
            db.session.commit()
            
            print(f"🗑️  已清理订单 {order.order_number} 的高清图片: {hd_image_filename}")
            return True
            
        except Exception as e:
            print(f"清理订单 {order.order_number} 高清图片失败: {e}")
            return False
    
    def restore_hd_image_from_backup(self, order_number, backup_file_path):
        """从备份恢复高清图片"""
        try:
            with app.app_context():
                order = Order.query.filter_by(order_number=order_number).first()
                if not order:
                    print(f"❌ 订单 {order_number} 不存在")
                    return False
                
                if not os.path.exists(backup_file_path):
                    print(f"❌ 备份文件不存在: {backup_file_path}")
                    return False
                
                # 生成新的文件名
                backup_filename = os.path.basename(backup_file_path)
                new_filename = f"restored_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{backup_filename}"
                new_path = os.path.join(self.hd_folder, new_filename)
                
                # 复制文件
                import shutil
                shutil.copy2(backup_file_path, new_path)
                
                # 更新数据库
                order.hd_image = new_filename
                db.session.commit()
                
                print(f"✅ 已恢复订单 {order_number} 的高清图片: {new_filename}")
                return True
                
        except Exception as e:
            print(f"恢复订单 {order_number} 高清图片失败: {e}")
            return False
    
    def get_cleanup_statistics(self):
        """获取清理统计信息"""
        try:
            cleanup_log = self.load_cleanup_log()
            
            stats = {
                'total_cleaned': len(cleanup_log),
                'total_size_saved': 0,
                'pending_backup': 0,
                'completed_backup': 0,
                'recent_cleanup': []
            }
            
            for order_number, info in cleanup_log.items():
                stats['total_size_saved'] += info.get('file_size', 0)
                
                if info.get('backup_status') == 'pending':
                    stats['pending_backup'] += 1
                elif info.get('backup_status') == 'completed':
                    stats['completed_backup'] += 1
                
                # 最近清理的记录
                cleanup_time = datetime.fromisoformat(info['cleanup_time'])
                if (datetime.now() - cleanup_time).days <= 7:
                    stats['recent_cleanup'].append({
                        'order_number': order_number,
                        'customer_name': info['customer_name'],
                        'cleanup_time': cleanup_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'file_size': info['file_size']
                    })
            
            return stats
            
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {}
    
    def list_cleanup_log(self):
        """列出清理日志"""
        try:
            cleanup_log = self.load_cleanup_log()
            
            if not cleanup_log:
                print("📋 清理日志为空")
                return
            
            print(f"📋 清理日志 (共 {len(cleanup_log)} 条记录):")
            print("-" * 80)
            
            for order_number, info in cleanup_log.items():
                print(f"订单号: {order_number}")
                print(f"客户: {info['customer_name']}")
                print(f"高清图片: {info['hd_image_filename']}")
                print(f"发货时间: {info['shipped_at']}")
                print(f"清理时间: {info['cleanup_time']}")
                print(f"文件大小: {info['file_size']} bytes")
                print(f"备份状态: {info['backup_status']}")
                print("-" * 80)
                
        except Exception as e:
            print(f"列出清理日志失败: {e}")

def main():
    """主函数"""
    print("🧹 智能图片清理系统")
    print("=" * 50)
    
    cleanup = SmartImageCleanup()
    
    # 添加发货时间字段
    cleanup.add_order_shipped_time_field()
    
    # 更新已发货订单的发货时间
    cleanup.update_shipped_orders()
    
    # 执行清理
    cleaned_count = cleanup.cleanup_hd_images_by_order_status()
    
    # 显示统计信息
    stats = cleanup.get_cleanup_statistics()
    if stats:
        print(f"\n📊 清理统计:")
        print(f"  总清理数量: {stats['total_cleaned']}")
        print(f"  节省空间: {stats['total_size_saved'] / 1024 / 1024:.2f} MB")
        print(f"  待备份: {stats['pending_backup']}")
        print(f"  已备份: {stats['completed_backup']}")
    
    print("\n✅ 智能图片清理完成")

if __name__ == '__main__':
    main()




