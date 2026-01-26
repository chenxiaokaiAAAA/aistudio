#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建新的测试优惠券
"""

import sys
sys.path.insert(0, '.')

from test_server import app, db, Coupon, UserCoupon
from datetime import datetime, timedelta

def create_test_coupon():
    """创建新的测试优惠券"""
    print('🎫 创建新的测试优惠券')
    print('=' * 50)
    
    with app.app_context():
        # 创建新的测试优惠券
        new_coupon = Coupon(
            name='动态测试券',
            code='DYNAMIC001',
            type='cash',
            value=20.0,
            min_amount=50.0,
            total_count=100,
            used_count=0,
            per_user_limit=2,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=30),
            status='active',
            description='动态测试优惠券，满50元减20元'
        )
        
        db.session.add(new_coupon)
        db.session.commit()
        
        print(f'✅ 创建成功: {new_coupon.name} ({new_coupon.code})')
        print(f'  面值: ¥{new_coupon.value}')
        print(f'  最低消费: ¥{new_coupon.min_amount}')
        print(f'  总数量: {new_coupon.total_count}')
        print(f'  每用户限领: {new_coupon.per_user_limit}')
        print(f'  有效期: {new_coupon.start_time} - {new_coupon.end_time}')
        
        # 测试新优惠券
        print(f'\n🧪 测试新优惠券')
        print('-' * 30)
        
        test_user = 'USER9999999999'
        available_coupons = Coupon.query.filter(
            Coupon.status == 'active',
            Coupon.start_time <= datetime.now(),
            Coupon.end_time > datetime.now(),
            Coupon.total_count > Coupon.used_count
        ).all()
        
        print(f'可领取优惠券数量: {len(available_coupons)}')
        for coupon in available_coupons:
            user_count = UserCoupon.query.filter_by(user_id=test_user, coupon_id=coupon.id).count()
            can_claim = user_count < coupon.per_user_limit
            can_claim_text = "是" if can_claim else "否"
            print(f'  {coupon.name}: 可领取={can_claim_text}')

if __name__ == "__main__":
    create_test_coupon()


