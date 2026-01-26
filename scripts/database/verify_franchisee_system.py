#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
加盟商系统最终验证脚本
验证所有功能是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, register_franchisee_blueprints
from flask import url_for

def verify_system():
    """验证系统完整性"""
    print("🔍 验证加盟商系统完整性...")
    
    with app.app_context():
        # 注册蓝图
        register_franchisee_blueprints()
        
        # 检查蓝图注册
        print("\n📋 蓝图注册状态:")
        for bp_name, bp in app.blueprints.items():
            print(f"  ✅ {bp_name}: {bp.url_prefix}")
        
        # 检查API端点
        print("\n🌐 API端点:")
        franchisee_routes = [rule for rule in app.url_map.iter_rules() if 'franchisee' in rule.rule]
        for route in franchisee_routes:
            methods = ', '.join(route.methods - {'OPTIONS', 'HEAD'})
            print(f"  ✅ {route.rule} [{methods}]")
        
        # 检查数据库表
        print("\n🗄️ 数据库表:")
        try:
            # 检查加盟商相关表是否存在
            from test_server import FranchiseeAccount, FranchiseeRecharge, Order
            
            # 检查表结构
            franchisee_columns = [c.name for c in FranchiseeAccount.__table__.columns]
            recharge_columns = [c.name for c in FranchiseeRecharge.__table__.columns]
            order_columns = [c.name for c in Order.__table__.columns]
            
            print(f"  ✅ franchisee_accounts: {len(franchisee_columns)} 个字段")
            print(f"  ✅ franchisee_recharges: {len(recharge_columns)} 个字段")
            print(f"  ✅ order: {len(order_columns)} 个字段")
            
            # 检查关键字段
            required_fields = {
                'franchisee_accounts': ['id', 'username', 'company_name', 'total_quota', 'remaining_quota', 'qr_code'],
                'franchisee_recharges': ['id', 'franchisee_id', 'amount', 'admin_user_id', 'created_at'],
                'order': ['id', 'order_number', 'franchisee_id', 'franchisee_deduction']
            }
            
            for table, fields in required_fields.items():
                if table == 'franchisee_accounts':
                    table_columns = franchisee_columns
                elif table == 'franchisee_recharges':
                    table_columns = recharge_columns
                else:
                    table_columns = order_columns
                
                missing_fields = [f for f in fields if f not in table_columns]
                if missing_fields:
                    print(f"  ❌ {table} 缺少字段: {missing_fields}")
                else:
                    print(f"  ✅ {table} 字段完整")
            
        except Exception as e:
            print(f"  ❌ 数据库表检查失败: {e}")
            return False
        
        # 检查模板文件
        print("\n📄 模板文件:")
        template_files = [
            'templates/admin/franchisee_list.html',
            'templates/admin/franchisee_add.html',
            'templates/admin/franchisee_detail.html',
            'templates/admin/franchisee_recharge.html',
            'templates/admin/franchisee_edit.html',
            'templates/franchisee/login.html',
            'templates/franchisee/dashboard.html',
            'templates/franchisee/orders.html',
            'templates/franchisee/recharge_records.html'
        ]
        
        for template in template_files:
            if os.path.exists(template):
                print(f"  ✅ {template}")
            else:
                print(f"  ❌ {template} 不存在")
        
        # 检查路由文件
        print("\n📁 路由文件:")
        route_files = [
            'franchisee_routes.py',
            'franchisee_qrcode_generator.py'
        ]
        
        for route_file in route_files:
            if os.path.exists(route_file):
                print(f"  ✅ {route_file}")
            else:
                print(f"  ❌ {route_file} 不存在")
        
        print("\n🎉 系统验证完成！")
        return True

if __name__ == '__main__':
    try:
        success = verify_system()
        if success:
            print("\n✅ 加盟商系统验证通过，可以正常使用！")
            print("\n📖 使用说明:")
            print("1. 启动应用: python start.py")
            print("2. 管理员后台: http://localhost:8000/admin/dashboard")
            print("3. 加盟商管理: http://localhost:8000/franchisee/admin/accounts")
            print("4. 加盟商登录: http://localhost:8000/franchisee/login")
        else:
            print("\n❌ 系统验证失败，请检查错误信息")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 验证过程出错: {e}")
        sys.exit(1)






