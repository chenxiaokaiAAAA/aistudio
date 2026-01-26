#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能存储管理方案
根据图片使用频率和存储时间自动选择最优存储策略
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

class SmartStorageManager:
    """智能存储管理器"""
    
    def __init__(self):
        self.storage_config = {
            # 存储策略配置
            'local_retention_days': 10,      # 本地保留天数（发货后）
            'oss_frequent_days': 30,          # OSS标准存储天数
            'oss_infrequent_days': 365,      # OSS低频存储天数
            'oss_archive_days': 3650,        # OSS归档存储天数（10年）
            
            # 成本配置（元/GB/月）
            'costs': {
                'local': 0,                  # 本地存储成本
                'oss_standard': 0.12,        # OSS标准存储
                'oss_infrequent': 0.08,      # OSS低频存储
                'oss_archive': 0.033,        # OSS归档存储
                'oss_cold_archive': 0.015    # OSS冷归档存储
            },
            
            # 文件大小估算（MB）
            'avg_hd_image_size': 50,         # 平均高清图片大小
            'orders_per_month': 100,         # 每月订单数量
        }
        
        self.storage_log_file = 'storage_management_log.json'
    
    def calculate_storage_costs(self, total_gb):
        """计算不同存储方案的成本"""
        costs = {}
        
        # 本地存储（10天）
        local_gb = total_gb * (self.storage_config['local_retention_days'] / 30)
        costs['local'] = local_gb * self.storage_config['costs']['local']
        
        # OSS标准存储（30天）
        oss_standard_gb = total_gb * (self.storage_config['oss_frequent_days'] / 30)
        costs['oss_standard'] = oss_standard_gb * self.storage_config['costs']['oss_standard']
        
        # OSS低频存储（1年）
        oss_infrequent_gb = total_gb * (self.storage_config['oss_infrequent_days'] / 30)
        costs['oss_infrequent'] = oss_infrequent_gb * self.storage_config['costs']['oss_infrequent']
        
        # OSS归档存储（10年）
        oss_archive_gb = total_gb * (self.storage_config['oss_archive_days'] / 30)
        costs['oss_archive'] = oss_archive_gb * self.storage_config['costs']['oss_archive']
        
        return costs
    
    def get_storage_strategy(self, file_age_days, access_frequency='low'):
        """根据文件年龄和访问频率确定存储策略"""
        
        if file_age_days <= self.storage_config['local_retention_days']:
            return {
                'storage_type': 'local',
                'action': 'keep_local',
                'cost_per_gb': self.storage_config['costs']['local'],
                'description': '本地存储（发货后10天内）'
            }
        
        elif file_age_days <= self.storage_config['oss_frequent_days']:
            return {
                'storage_type': 'oss_standard',
                'action': 'upload_to_oss_standard',
                'cost_per_gb': self.storage_config['costs']['oss_standard'],
                'description': 'OSS标准存储（30天内）'
            }
        
        elif file_age_days <= self.storage_config['oss_infrequent_days']:
            return {
                'storage_type': 'oss_infrequent',
                'action': 'move_to_oss_infrequent',
                'cost_per_gb': self.storage_config['costs']['oss_infrequent'],
                'description': 'OSS低频存储（1年内）'
            }
        
        else:
            return {
                'storage_type': 'oss_archive',
                'action': 'move_to_oss_archive',
                'cost_per_gb': self.storage_config['costs']['oss_archive'],
                'description': 'OSS归档存储（长期）'
            }
    
    def estimate_monthly_costs(self):
        """估算月度存储成本"""
        monthly_orders = self.storage_config['orders_per_month']
        avg_file_size_gb = self.storage_config['avg_hd_image_size'] / 1024
        
        # 计算不同阶段的存储量
        total_monthly_gb = monthly_orders * avg_file_size_gb
        
        costs = self.calculate_storage_costs(total_monthly_gb)
        
        return {
            'monthly_orders': monthly_orders,
            'avg_file_size_mb': self.storage_config['avg_hd_image_size'],
            'total_monthly_gb': total_monthly_gb,
            'costs': costs,
            'total_monthly_cost': sum(costs.values())
        }
    
    def generate_cost_report(self):
        """生成成本分析报告"""
        report = self.estimate_monthly_costs()
        
        print("📊 存储成本分析报告")
        print("=" * 50)
        print(f"每月订单数量: {report['monthly_orders']}")
        print(f"平均文件大小: {report['avg_file_size_mb']} MB")
        print(f"每月存储总量: {report['total_monthly_gb']:.2f} GB")
        print()
        
        print("💰 存储成本明细:")
        for storage_type, cost in report['costs'].items():
            print(f"  {storage_type}: ¥{cost:.2f}/月")
        
        print(f"\n💵 总月度成本: ¥{report['total_monthly_cost']:.2f}")
        print(f"💵 年度成本: ¥{report['total_monthly_cost'] * 12:.2f}")
        
        return report
    
    def recommend_strategy(self):
        """推荐最优存储策略"""
        report = self.estimate_monthly_costs()
        
        print("\n🎯 存储策略推荐")
        print("=" * 50)
        
        # 方案1：纯本地存储
        local_cost = 0
        print(f"方案1 - 纯本地存储: ¥{local_cost}/月")
        print("  优点: 无额外费用，访问速度快")
        print("  缺点: 存储空间有限，数据安全风险")
        
        # 方案2：本地+OSS混合
        hybrid_cost = report['costs']['oss_infrequent'] + report['costs']['oss_archive']
        print(f"\n方案2 - 混合存储: ¥{hybrid_cost:.2f}/月")
        print("  优点: 成本低，数据安全，自动管理")
        print("  缺点: 需要配置OSS")
        
        # 方案3：纯OSS存储
        oss_cost = report['total_monthly_cost']
        print(f"\n方案3 - 纯OSS存储: ¥{oss_cost:.2f}/月")
        print("  优点: 完全托管，高可用性")
        print("  缺点: 成本较高")
        
        # 推荐
        if hybrid_cost < oss_cost * 0.5:
            print(f"\n🏆 推荐方案: 混合存储策略")
            print(f"   月度成本: ¥{hybrid_cost:.2f}")
            print(f"   年度节省: ¥{(oss_cost - hybrid_cost) * 12:.2f}")
        else:
            print(f"\n🏆 推荐方案: 纯本地存储")
            print("   成本最低，适合初期使用")
    
    def create_implementation_plan(self):
        """创建实施计划"""
        print("\n📋 实施计划")
        print("=" * 50)
        
        print("阶段1: 立即实施（0成本）")
        print("  ✅ 启用智能图片清理系统")
        print("  ✅ 发货后10天自动清理本地高清图片")
        print("  ✅ 保留数据库记录")
        
        print("\n阶段2: 中期优化（1-3个月后）")
        print("  🔄 配置阿里云OSS")
        print("  🔄 实现自动备份到OSS")
        print("  🔄 设置存储生命周期策略")
        
        print("\n阶段3: 长期优化（6个月后）")
        print("  🔄 根据实际使用情况调整策略")
        print("  🔄 优化存储成本")
        print("  🔄 实现智能存储迁移")

def main():
    """主函数"""
    print("🧠 智能存储管理方案")
    print("=" * 50)
    
    manager = SmartStorageManager()
    
    # 生成成本报告
    manager.generate_cost_report()
    
    # 推荐策略
    manager.recommend_strategy()
    
    # 实施计划
    manager.create_implementation_plan()
    
    print("\n💡 建议:")
    print("1. 先使用智能清理系统（0成本）")
    print("2. 观察1-3个月的实际使用情况")
    print("3. 根据数据量决定是否使用OSS")
    print("4. 逐步优化存储策略")

if __name__ == '__main__':
    main()




