# -*- coding: utf-8 -*-
"""
加盟商优惠券管理路由模块
"""
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from datetime import datetime
from sqlalchemy import func, or_

from app.routes.franchisee.common import get_models

# 创建蓝图
bp = Blueprint('franchisee_coupons', __name__)

@bp.route('/coupons')
def franchisee_coupons():
    """加盟商优惠券管理页面"""
    franchisee_id = session.get('franchisee_id')
    if not franchisee_id:
        flash('请先登录', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    FranchiseeAccount = models['FranchiseeAccount']
    Coupon = models.get('Coupon')
    UserCoupon = models.get('UserCoupon')
    StaffUser = models.get('StaffUser')
    db = models['db']
    
    if not Coupon:
        flash('优惠券模型未初始化', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    account = FranchiseeAccount.query.get(franchisee_id)
    if not account or account.status != 'active':
        flash('账户不存在或已被禁用', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    # 获取筛选参数
    status = request.args.get('status', '')
    source_type = request.args.get('source_type', '')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 构建查询 - 只查询该加盟商创建的优惠券
    query = Coupon.query.filter(
        or_(
            Coupon.franchisee_id == franchisee_id,
            Coupon.creator_type == 'franchisee',
            Coupon.source_type == 'groupon'
        )
    )
    
    # 如果指定了来源类型，进一步过滤
    if source_type:
        query = query.filter(Coupon.source_type == source_type)
    
    # 状态筛选
    if status:
        query = query.filter(Coupon.status == status)
    
    # 搜索
    if search:
        query = query.filter(
            or_(
                Coupon.name.like(f'%{search}%'),
                Coupon.code.like(f'%{search}%'),
                Coupon.groupon_order_id.like(f'%{search}%')
            )
        )
    
    # 分页
    pagination = query.order_by(Coupon.create_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    coupons = pagination.items
    
    # 获取每个优惠券的使用情况
    coupons_data = []
    for coupon in coupons:
        # 获取领取数量
        claimed_count = UserCoupon.query.filter_by(coupon_id=coupon.id).count()
        
        # 获取使用数量
        used_count = UserCoupon.query.filter_by(
            coupon_id=coupon.id,
            status='used'
        ).count()
        
        # 获取创建人信息
        creator_info = '系统'
        if coupon.creator_type == 'franchisee':
            if coupon.creator_name:
                creator_info = coupon.creator_name
            elif coupon.franchisee_id:
                franchisee = FranchiseeAccount.query.get(coupon.franchisee_id)
                if franchisee:
                    creator_info = franchisee.company_name or franchisee.username
        elif coupon.creator_type == 'staff' and coupon.staff_user_id and StaffUser:
            staff = StaffUser.query.get(coupon.staff_user_id)
            if staff:
                creator_info = f"{staff.name}（店员）"
        
        coupons_data.append({
            'coupon': coupon,
            'claimed_count': claimed_count,
            'used_count': used_count,
            'creator_info': creator_info
        })
    
    # 统计数据
    total_coupons = query.count()
    active_coupons = query.filter(Coupon.status == 'active').count()
    expired_coupons = query.filter(Coupon.status == 'expired').count()
    groupon_coupons = query.filter(Coupon.source_type == 'groupon').count()
    
    return render_template('franchisee/coupons.html',
                         account=account,
                         coupons_data=coupons_data,
                         pagination=pagination,
                         status=status,
                         source_type=source_type,
                         search=search,
                         total_coupons=total_coupons,
                         active_coupons=active_coupons,
                         expired_coupons=expired_coupons,
                         groupon_coupons=groupon_coupons)
