#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
重新创建数据库表
"""

from test_server import app, db, User, Order, OrderImage, PromotionUser, Commission, PromotionTrack

def recreate_database():
    """重新创建数据库表"""
    with app.app_context():
        try:
            # 删除现有表
            db.drop_all()
            print('✅ 删除现有表')
            
            # 创建所有表
            db.create_all()
            print('✅ 创建所有表')
            
            # 创建默认管理员账号
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print('✅ 创建默认管理员账号')
            
            print('🎉 数据库重新创建完成！')
            
        except Exception as e:
            print(f'❌ 创建失败: {e}')
            db.session.rollback()

if __name__ == '__main__':
    recreate_database()
