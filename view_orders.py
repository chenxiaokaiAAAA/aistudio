# -*- coding: utf-8 -*-
"""查看PostgreSQL中的订单数据"""
import os
import sys
import io

# 设置输出编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 设置环境变量（如果未设置）
if not os.environ.get('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'postgresql://aistudio_user:a3183683@localhost:5432/pet_painting'

from app import create_app, db
from app.models import Order, OrderImage
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    print("=" * 80)
    print("订单数据查看工具")
    print("=" * 80)
    
    # 检查数据库连接
    database_url = os.environ.get('DATABASE_URL', '')
    if 'postgresql' in database_url:
        print(f"✅ 使用PostgreSQL数据库")
        db_name = database_url.split('/')[-1]
        print(f"   数据库: {db_name}")
    else:
        print(f"⚠️  使用SQLite数据库")
        print(f"   如需切换到PostgreSQL，请设置DATABASE_URL环境变量")
    
    print("\n" + "=" * 80)
    print("订单统计")
    print("=" * 80)
    
    total_orders = Order.query.count()
    print(f"总订单数: {total_orders}")
    
    # 按状态统计
    from sqlalchemy import func
    status_stats = db.session.query(
        Order.status,
        func.count(Order.id).label('count'),
        func.sum(Order.price).label('total_amount')
    ).group_by(Order.status).all()
    
    print("\n按状态统计:")
    for status, count, total in status_stats:
        total = total or 0
        print(f"  {status:20s}: {count:4d} 单, 总金额: ¥{total:,.2f}")
    
    # 今日订单
    today = datetime.now().date()
    today_orders = Order.query.filter(
        db.func.date(Order.created_at) == today
    ).count()
    print(f"\n今日订单: {today_orders} 单")
    
    # 最近7天订单
    week_ago = datetime.now() - timedelta(days=7)
    week_orders = Order.query.filter(
        Order.created_at >= week_ago
    ).count()
    print(f"最近7天: {week_orders} 单")
    
    print("\n" + "=" * 80)
    print("最新订单列表（最近10单）")
    print("=" * 80)
    
    orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    if not orders:
        print("暂无订单数据")
    else:
        for i, order in enumerate(orders, 1):
            print(f"\n【订单 {i}】")
            print(f"  订单号: {order.order_number}")
            print(f"  订单ID: {order.id}")
            print(f"  客户: {order.customer_name} ({order.customer_phone})")
            print(f"  产品: {order.product_name}")
            print(f"  尺寸: {order.size}")
            print(f"  风格: {order.style_name}")
            print(f"  状态: {order.status}")
            print(f"  金额: ¥{order.price}")
            print(f"  创建时间: {order.created_at}")
            
            # 查看订单图片
            images = OrderImage.query.filter_by(order_id=order.id).all()
            if images:
                print(f"  图片数量: {len(images)}")
                for img in images:
                    is_main = "主图" if img.is_main else "副图"
                    print(f"    - {img.path} ({is_main})")
            else:
                print(f"  图片: 无")
            
            # 加盟商信息
            if hasattr(order, 'franchisee_id') and order.franchisee_id:
                print(f"  加盟商ID: {order.franchisee_id}")
    
    print("\n" + "=" * 80)
    print("查询完成")
    print("=" * 80)
    print("\n提示:")
    print("  - 新创建的订单会保存在PostgreSQL数据库中")
    print("  - 可以通过Web管理界面查看: http://localhost:5000/admin/orders")
    print("  - 或使用pgAdmin查看数据库")
