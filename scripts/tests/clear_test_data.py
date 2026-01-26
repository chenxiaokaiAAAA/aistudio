# 清空测试数据脚本 - clear_test_data.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# 创建Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pet_painting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 导入模型
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    commission_rate = db.Column(db.Float, default=0.1)
    qr_code = db.Column(db.String(100), unique=True)
    contact_person = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    wechat_id = db.Column(db.String(50))

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    size = db.Column(db.String(20))
    original_image = db.Column(db.String(200), nullable=False)
    final_image = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    shipping_info = db.Column(db.String(500))
    merchant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default='2025-01-01 00:00:00')
    completed_at = db.Column(db.DateTime)
    commission = db.Column(db.Float, default=0.0)
    price = db.Column(db.Float, default=0.0)
    external_platform = db.Column(db.String(50))
    external_order_number = db.Column(db.String(100))

class OrderImage(db.Model):
    __tablename__ = 'order_image'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    path = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default='2025-01-01 00:00:00')

class SizeOption(db.Model):
    __tablename__ = 'size_option'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False, default=50.0)

def clear_test_data():
    """清空测试数据"""
    with app.app_context():
        try:
            # 删除所有订单图片
            OrderImage.query.delete()
            print("已删除所有订单图片记录")
            
            # 删除所有订单
            Order.query.delete()
            print("已删除所有订单记录")
            
            # 删除所有商家（保留管理员）
            User.query.filter(User.role != 'admin').delete()
            print("已删除所有商家记录（保留管理员）")
            
            # 提交更改
            db.session.commit()
            print("✅ 测试数据清空完成！")
            
            # 显示剩余数据统计
            admin_count = User.query.filter_by(role='admin').count()
            order_count = Order.query.count()
            image_count = OrderImage.query.count()
            
            print(f"\n📊 当前数据统计：")
            print(f"管理员账号: {admin_count}")
            print(f"订单数量: {order_count}")
            print(f"图片记录: {image_count}")
            
        except Exception as e:
            print(f"❌ 清空数据失败: {e}")
            db.session.rollback()

if __name__ == '__main__':
    print("🧹 开始清空测试数据...")
    clear_test_data()
