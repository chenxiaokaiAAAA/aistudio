#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建受限管理员账户脚本
该管理员可以管理订单、产品等，但不能管理加盟商和充值
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, User
from werkzeug.security import generate_password_hash

def create_limited_admin():
    """创建受限管理员账户"""
    with app.app_context():
        # 检查是否已存在
        username = 'operator'  # 营运管理员
        password = 'operator123'  # 密码
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"用户 {username} 已存在")
            return
        
        # 创建受限管理员
        limited_admin = User(
            username=username,
            password=generate_password_hash(password),
            role='operator'  # 新角色：营运管理员
        )
        
        db.session.add(limited_admin)
        db.session.commit()
        
        print("=" * 50)
        print("受限管理员账户创建成功！")
        print("=" * 50)
        print(f"用户名: {username}")
        print(f"密码: {password}")
        print(f"角色: operator (营运管理员)")
        print("权限: 可以管理订单、产品、风格等，但不能管理加盟商和充值")
        print("=" * 50)

if __name__ == '__main__':
    create_limited_admin()


