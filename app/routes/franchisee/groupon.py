# -*- coding: utf-8 -*-
"""
加盟商团购核销路由模块
"""
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from datetime import datetime, timedelta
import random
import string
import qrcode
import base64
from io import BytesIO
import sys
from sqlalchemy import func, desc, or_

from app.routes.franchisee.common import get_models

# 创建蓝图
bp = Blueprint('franchisee_groupon', __name__)

def generate_random_code(length=8):
    """生成随机码"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_qr_code(data):
    """生成二维码图片（base64编码）"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@bp.route('/groupon/verify')
def franchisee_groupon_verify():
    """加盟商团购核销页面"""
    franchisee_id = session.get('franchisee_id')
    if not franchisee_id:
        flash('请先登录', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    FranchiseeAccount = models['FranchiseeAccount']
    account = FranchiseeAccount.query.get(franchisee_id)
    if not account or account.status != 'active':
        flash('账户不存在或已被禁用', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    # 获取团购套餐列表（从管理后台配置的）
    GrouponPackage = models.get('GrouponPackage')
    packages = []
    if GrouponPackage:
        try:
            packages = GrouponPackage.query.filter_by(status='active').order_by(
                GrouponPackage.platform.asc(),
                GrouponPackage.sort_order.asc()
            ).all()
            print(f"[DEBUG] 获取到 {len(packages)} 个套餐")
        except Exception as e:
            print(f"[ERROR] 获取套餐列表失败: {e}")
            import traceback
            traceback.print_exc()
            packages = []
    else:
        print("[WARNING] GrouponPackage 模型未找到，请检查模型导入")
    
    # 按平台分组
    platforms = {}
    for pkg in packages:
        platform = pkg.platform
        if platform not in platforms:
            platforms[platform] = []
        platforms[platform].append(pkg)
    
    print(f"[DEBUG] 平台分组结果: {list(platforms.keys())}, 共 {len(platforms)} 个平台")
    
    return render_template('franchisee/groupon_verify.html', 
                         account=account,
                         platforms=platforms)

@bp.route('/groupon/records')
def franchisee_groupon_records():
    """加盟商团购核销记录查看页面"""
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
    StaffUser = models.get('StaffUser')
    GrouponPackage = models.get('GrouponPackage')
    db = models['db']
    
    if not Coupon:
        flash('优惠券模型未初始化', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    account = FranchiseeAccount.query.get(franchisee_id)
    if not account or account.status != 'active':
        flash('账户不存在或已被禁用', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    # 获取筛选参数
    platform = request.args.get('platform', '')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 构建查询 - 只查询该加盟商及其店员创建的团购核销券
    # 获取该加盟商的所有店员ID
    staff_ids = []
    if StaffUser:
        staff_list = StaffUser.query.filter_by(franchisee_id=franchisee_id, status='active').all()
        staff_ids = [staff.id for staff in staff_list]
    
    # 查询条件：该加盟商直接创建的，或者该加盟商的店员创建的
    # 注意：or_已经在文件顶部导入
    if staff_ids:
        query = Coupon.query.filter(
            Coupon.source_type == 'groupon',
            or_(
                Coupon.franchisee_id == franchisee_id,  # 加盟商直接创建的
                Coupon.staff_user_id.in_(staff_ids)  # 该加盟商的店员创建的
            )
        )
    else:
        # 如果没有店员，只查询加盟商直接创建的
        query = Coupon.query.filter(
            Coupon.source_type == 'groupon',
            Coupon.franchisee_id == franchisee_id
        )
    
    # 平台筛选
    if platform:
        query = query.filter(Coupon.groupon_platform == platform)
    
    # 搜索
    if search:
        query = query.filter(
            or_(
                Coupon.groupon_order_id.like(f'%{search}%'),
                Coupon.code.like(f'%{search}%')
            )
        )
    
    # 分页
    pagination = query.order_by(desc(Coupon.create_time)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    coupons = pagination.items
    
    # 获取每个核销记录的详细信息
    verify_records = []
    for coupon in coupons:
        # 获取创建人信息
        creator_info = account.company_name or account.username
        
        # 如果是店员创建的，显示店员信息
        if coupon.creator_type == 'staff' and coupon.staff_user_id and StaffUser:
            staff = StaffUser.query.get(coupon.staff_user_id)
            if staff and staff.franchisee_id == franchisee_id:
                creator_info = f"{staff.name}（店员）"
        
        # 获取平台和套餐信息
        platform_name = coupon.groupon_platform or ''
        package_name = ''
        if GrouponPackage and coupon.groupon_package_id:
            try:
                package_id_int = int(coupon.groupon_package_id)
                package = GrouponPackage.query.get(package_id_int)
                if package:
                    platform_name = package.platform
                    package_name = package.package_name
            except (ValueError, TypeError):
                pass
        
        verify_records.append({
            'coupon': coupon,
            'creator_info': creator_info,
            'platform': platform_name,
            'package_name': package_name
        })
    
    # 获取所有平台（用于筛选）- 使用相同的查询条件
    platform_list = []
    if GrouponPackage:
        # 使用与主查询相同的条件
        if staff_ids:
            platforms_query = Coupon.query.filter(
                Coupon.source_type == 'groupon',
                or_(
                    Coupon.franchisee_id == franchisee_id,  # 加盟商直接创建的
                    Coupon.staff_user_id.in_(staff_ids)  # 该加盟商的店员创建的
                ),
                Coupon.groupon_platform.isnot(None)
            ).with_entities(Coupon.groupon_platform).distinct().all()
        else:
            platforms_query = Coupon.query.filter(
                Coupon.source_type == 'groupon',
                Coupon.franchisee_id == franchisee_id,
                Coupon.groupon_platform.isnot(None)
            ).with_entities(Coupon.groupon_platform).distinct().all()
        platform_list = [p[0] for p in platforms_query if p[0]]
    
    # 统计数据（使用相同的查询条件）
    if staff_ids:
        stats_query = Coupon.query.filter(
            Coupon.source_type == 'groupon',
            or_(
                Coupon.franchisee_id == franchisee_id,  # 加盟商直接创建的
                Coupon.staff_user_id.in_(staff_ids)  # 该加盟商的店员创建的
            )
        )
    else:
        stats_query = Coupon.query.filter(
            Coupon.source_type == 'groupon',
            Coupon.franchisee_id == franchisee_id
        )
    
    total_verifies = stats_query.count()
    
    today_verifies = stats_query.filter(
        func.date(Coupon.create_time) == datetime.now().date()
    ).count()
    
    return render_template('franchisee/groupon_records.html',
                         account=account,
                         verify_records=verify_records,
                         pagination=pagination,
                         platforms=platform_list,
                         platform=platform,
                         search=search,
                         total_verifies=total_verifies,
                         today_verifies=today_verifies)

@bp.route('/groupon/verify', methods=['POST'])
def franchisee_groupon_verify_api():
    """加盟商团购核销API"""
    franchisee_id = session.get('franchisee_id')
    if not franchisee_id:
        return jsonify({
            'status': 'error',
            'message': '请先登录'
        }), 401
    
    try:
        data = request.get_json()
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        Coupon = models.get('Coupon')
        UserCoupon = models.get('UserCoupon')
        GrouponPackage = models.get('GrouponPackage')
        User = models.get('User')
        db = models['db']
        
        if not Coupon:
            return jsonify({
                'status': 'error',
                'message': '优惠券模型未初始化'
            }), 500
        
        # 验证必填字段
        required_fields = ['groupon_order_id', 'customer_phone']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必要字段: {field}'
                }), 400
        
        groupon_order_id = data['groupon_order_id']
        customer_phone = data['customer_phone']
        customer_name = data.get('customer_name', '')
        expire_days = int(data.get('expire_days', 30))
        
        # 获取核销金额（从套餐配置获取）
        verify_amount = None
        platform = data.get('platform', '')
        package_id = data.get('package_id')
        
        package = None
        if package_id and GrouponPackage:
            try:
                package_id_int = int(package_id)
                package = GrouponPackage.query.get(package_id_int)
                if package:
                    verify_amount = float(package.package_amount)
                    platform = package.platform
                else:
                    return jsonify({
                        'status': 'error',
                        'message': '套餐不存在'
                    }), 400
            except (ValueError, TypeError) as e:
                return jsonify({
                    'status': 'error',
                    'message': f'套餐ID格式错误: {str(e)}'
                }), 400
        else:
            return jsonify({
                'status': 'error',
                'message': '请选择团购套餐'
            }), 400
        
        if verify_amount <= 0:
            return jsonify({
                'status': 'error',
                'message': '核销金额必须大于0'
            }), 400
        
        # 检查是否已存在该团购订单的优惠券
        existing_coupon = Coupon.query.filter_by(
            groupon_order_id=groupon_order_id,
            source_type='groupon'
        ).first()
        
        if existing_coupon:
            return jsonify({
                'status': 'error',
                'message': '该团购订单已核销，优惠券已生成'
            }), 400
        
        # 生成随机码
        random_code = generate_random_code(8)
        while Coupon.query.filter_by(code=random_code).first():
            random_code = generate_random_code(8)
        
        # 获取加盟商信息
        FranchiseeAccount = models.get('FranchiseeAccount')
        franchisee = None
        creator_name = ''
        if FranchiseeAccount:
            franchisee = FranchiseeAccount.query.get(franchisee_id)
            if franchisee:
                creator_name = franchisee.company_name or franchisee.username
        
        # 创建优惠券
        now = datetime.now()
        coupon = Coupon(
            name=f'团购核销券-{verify_amount}元',
            code=random_code,
            type='free',
            value=verify_amount,
            min_amount=0.0,
            total_count=1,
            used_count=0,
            per_user_limit=1,
            start_time=now,
            end_time=now + timedelta(days=expire_days),
            status='active',
            description=f'团购订单{groupon_order_id}核销券，金额{verify_amount}元',
            source_type='groupon',
            groupon_order_id=groupon_order_id,
            verify_amount=verify_amount,
            is_random_code=True
        )
        
        # 保存创建人信息
        if hasattr(coupon, 'franchisee_id'):
            coupon.franchisee_id = franchisee_id
        if hasattr(coupon, 'creator_type'):
            coupon.creator_type = 'franchisee'  # 加盟商创建
        if hasattr(coupon, 'creator_name'):
            coupon.creator_name = creator_name
        
        # 保存平台和套餐信息
        if hasattr(coupon, 'groupon_platform'):
            coupon.groupon_platform = platform
        if hasattr(coupon, 'groupon_package_id') and package:
            try:
                coupon.groupon_package_id = int(package.id)
            except (ValueError, TypeError):
                pass
        
        # 如果Coupon模型有customer_phone字段，保存客户手机号用于匹配
        if hasattr(coupon, 'customer_phone'):
            coupon.customer_phone = customer_phone
        if hasattr(coupon, 'customer_name'):
            coupon.customer_name = customer_name
        
        db.session.add(coupon)
        db.session.flush()
        
        # 生成领取二维码
        qr_data = f"coupon_code:{random_code}"
        qr_code_url = generate_qr_code(qr_data)
        
        # 保存二维码URL
        if hasattr(coupon, 'qr_code_url'):
            coupon.qr_code_url = qr_code_url
        
        # 尝试自动保存到用户账户（如果手机号匹配）
        auto_saved = False
        if User and customer_phone:
            user = User.query.filter_by(phone=customer_phone).first()
            if user:
                user_coupon = UserCoupon(
                    user_id=str(user.id),
                    coupon_id=coupon.id,
                    coupon_code=random_code,
                    status='unused',
                    expire_time=coupon.end_time
                )
                db.session.add(user_coupon)
                auto_saved = True
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '团购核销成功',
            'data': {
                'coupon_code': random_code,
                'coupon_name': coupon.name,
                'verify_amount': verify_amount,
                'expire_time': coupon.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'qr_code_url': qr_code_url,
                'auto_saved': auto_saved
            }
        })
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"团购核销失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'团购核销失败: {str(e)}'
        }), 500
