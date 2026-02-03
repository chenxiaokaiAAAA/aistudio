#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
加盟商二维码生成工具
为加盟商生成专属的二维码，用户扫码后自动关联到对应加盟商
"""

import qrcode
from io import BytesIO
import base64
from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required, current_user
import os

# 导入数据库模型
try:
    from test_server import db, FranchiseeAccount
except ImportError:
    # 如果直接导入失败，尝试从当前模块导入
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from test_server import db, FranchiseeAccount

qrcode_bp = Blueprint('franchisee_qrcode', __name__, url_prefix='/franchisee')

@qrcode_bp.route('/api/generate-qrcode/<int:franchisee_id>')
@login_required
def generate_franchisee_qrcode(franchisee_id):
    """为加盟商生成二维码"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    try:
        # 查找加盟商账户
        franchisee = FranchiseeAccount.query.get(franchisee_id)
        if not franchisee:
            return jsonify({'success': False, 'message': '加盟商账户不存在'}), 404
        
        # 生成二维码内容（指向扫码处理路由）
        qr_content = f"https://photogooo/franchisee/scan/{franchisee.qr_code}"
        
        # 创建二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        # 生成二维码图片
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 保存到内存
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # 生成文件名
        filename = f"franchisee_{franchisee.id}_{franchisee.qr_code}.png"
        
        return send_file(
            img_buffer,
            mimetype='image/png',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成二维码失败: {str(e)}'}), 500

@qrcode_bp.route('/api/qrcode-info/<qr_code>')
def get_qrcode_info(qr_code):
    """获取二维码对应的加盟商信息"""
    try:
        # 查找加盟商账户
        franchisee = FranchiseeAccount.query.filter_by(qr_code=qr_code, status='active').first()
        
        if not franchisee:
            return jsonify({'success': False, 'message': '加盟商账户不存在或已禁用'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': franchisee.id,
                'company_name': franchisee.company_name,
                'contact_person': franchisee.contact_person,
                'contact_phone': franchisee.contact_phone,
                'remaining_quota': franchisee.remaining_quota,
                'qr_code': franchisee.qr_code
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取信息失败: {str(e)}'}), 500

@qrcode_bp.route('/api/validate-qrcode', methods=['POST'])
def validate_qrcode():
    """验证加盟商二维码"""
    try:
        data = request.get_json()
        qr_code = data.get('qr_code')
        
        if not qr_code:
            return jsonify({'success': False, 'message': '二维码不能为空'}), 400
        
        # 查找加盟商账户
        franchisee = FranchiseeAccount.query.filter_by(qr_code=qr_code, status='active').first()
        
        if not franchisee:
            return jsonify({'success': False, 'message': '加盟商账户不存在或已禁用'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'franchisee_id': franchisee.id,
                'company_name': franchisee.company_name,
                'remaining_quota': franchisee.remaining_quota,
                'qr_code': franchisee.qr_code
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'验证失败: {str(e)}'}), 500
