#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断宠物摄影报名错误
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 创建Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pet_painting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 定义模型
class PhotoSignup(db.Model):
    """宠物摄影报名表"""
    __tablename__ = 'photo_signup'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    pet_breed = db.Column(db.String(50), nullable=False)
    pet_weight = db.Column(db.String(50), nullable=True)
    pet_age = db.Column(db.String(50), nullable=True)
    pet_character = db.Column(db.String(500))
    available_date = db.Column(db.String(50))
    additional_notes = db.Column(db.String(500))
    pet_images = db.Column(db.Text)
    user_id = db.Column(db.String(100))
    referrer_user_id = db.Column(db.String(100))
    referrer_promotion_code = db.Column(db.String(50))
    source = db.Column(db.String(50), default='miniprogram_carousel')
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.String(1000))
    submit_time = db.Column(db.DateTime, default=datetime.utcnow)
    contact_time = db.Column(db.DateTime)
    schedule_time = db.Column(db.DateTime)
    complete_time = db.Column(db.DateTime)

def test_model_creation():
    """测试模型创建"""
    try:
        print("🧪 测试模型创建...")
        
        with app.app_context():
            # 创建表
            db.create_all()
            print("✅ 表创建成功")
            
            # 检查表是否存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'photo_signup' in tables:
                print("✅ photo_signup表存在")
                
                # 检查列
                columns = inspector.get_columns('photo_signup')
                print(f"📋 表列数：{len(columns)}")
                
                column_names = []
                for column in columns:
                    column_names.append(column['name'])
                    print(f"   - {column['name']} ({column['type']})")
                
                # 检查关键字段
                required_fields = ['pet_breed', 'pet_weight', 'pet_images']
                missing_fields = []
                for field in required_fields:
                    if field not in column_names:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"❌ 缺少字段: {missing_fields}")
                    return False
                else:
                    print("✅ 所有关键字段都存在")
                
                # 尝试插入测试数据
                test_signup = PhotoSignup(
                    name='测试用户',
                    phone='13800138000',
                    pet_breed='金毛',
                    pet_weight='1-5kg (小型)',
                    pet_age='幼体 (0-6个月)',
                    pet_character='温顺活泼',
                    available_date='2025-09-30',
                    additional_notes='测试备注',
                    pet_images='[{"url": "https://example.com/test.jpg"}]',
                    user_id='TEST_USER',
                    source='test',
                    status='pending'
                )
                
                db.session.add(test_signup)
                db.session.commit()
                print("✅ 测试数据插入成功")
                
                # 查询验证
                result = PhotoSignup.query.first()
                print(f"✅ 查询成功: {result.name} - {result.phone}")
                
                return True
                
            else:
                print("❌ photo_signup表不存在")
                return False
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 诊断宠物摄影报名错误...")
    
    if test_model_creation():
        print("🎉 模型测试通过！")
    else:
        print("💥 模型测试失败")
