# -*- coding: utf-8 -*-
"""
团购套餐配置管理API路由模块
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import sys

# 创建蓝图
admin_groupon_package_api_bp = Blueprint('admin_groupon_package_api', __name__, url_prefix='/api/admin/groupon-package')

def get_models():
    """延迟导入数据库模型，避免循环导入"""
    try:
        test_server = sys.modules.get('test_server')
        if test_server:
            return {
                'GrouponPackage': test_server.GrouponPackage,
                'db': test_server.db
            }
        return None
    except Exception as e:
        print(f"⚠️ 获取数据库模型失败: {e}")
        return None

@admin_groupon_package_api_bp.route('/list', methods=['GET'])
@login_required
def get_package_list():
    """获取团购套餐列表"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({
                'status': 'error',
                'message': '权限不足'
            }), 403
        
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        GrouponPackage = models['GrouponPackage']
        
        # 查询所有套餐
        packages = GrouponPackage.query.order_by(
            GrouponPackage.platform.asc(),
            GrouponPackage.sort_order.asc(),
            GrouponPackage.id.asc()
        ).all()
        
        result = []
        for pkg in packages:
            result.append({
                'id': pkg.id,
                'platform': pkg.platform,
                'package_name': pkg.package_name,
                'package_amount': float(pkg.package_amount),
                'description': pkg.description or '',
                'status': pkg.status,
                'sort_order': pkg.sort_order,
                'created_at': pkg.created_at.strftime('%Y-%m-%d %H:%M:%S') if pkg.created_at else '',
                'updated_at': pkg.updated_at.strftime('%Y-%m-%d %H:%M:%S') if pkg.updated_at else ''
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取团购套餐列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取团购套餐列表失败: {str(e)}'
        }), 500

@admin_groupon_package_api_bp.route('/create', methods=['POST'])
@login_required
def create_package():
    """创建团购套餐"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({
                'status': 'error',
                'message': '权限不足'
            }), 403
        
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        GrouponPackage = models['GrouponPackage']
        db = models['db']
        
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['platform', 'package_name', 'package_amount']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必要字段: {field}'
                }), 400
        
        platform = data['platform'].strip()
        package_name = data['package_name'].strip()
        package_amount = float(data['package_amount'])
        description = data.get('description', '').strip()
        status = data.get('status', 'active')
        sort_order = int(data.get('sort_order', 0))
        
        if package_amount <= 0:
            return jsonify({
                'status': 'error',
                'message': '套餐金额必须大于0'
            }), 400
        
        # 检查是否已存在相同平台和套餐名称
        existing = GrouponPackage.query.filter_by(
            platform=platform,
            package_name=package_name
        ).first()
        
        if existing:
            return jsonify({
                'status': 'error',
                'message': f'该平台下已存在名为"{package_name}"的套餐'
            }), 400
        
        # 创建套餐
        package = GrouponPackage(
            platform=platform,
            package_name=package_name,
            package_amount=package_amount,
            description=description,
            status=status,
            sort_order=sort_order
        )
        
        db.session.add(package)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '团购套餐创建成功',
            'data': {
                'id': package.id,
                'platform': package.platform,
                'package_name': package.package_name,
                'package_amount': float(package.package_amount)
            }
        })
        
    except Exception as e:
        print(f"创建团购套餐失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'创建团购套餐失败: {str(e)}'
        }), 500

@admin_groupon_package_api_bp.route('/update/<int:package_id>', methods=['POST'])
@login_required
def update_package(package_id):
    """更新团购套餐"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({
                'status': 'error',
                'message': '权限不足'
            }), 403
        
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        GrouponPackage = models['GrouponPackage']
        db = models['db']
        
        package = GrouponPackage.query.get_or_404(package_id)
        data = request.get_json()
        
        # 更新字段
        if 'platform' in data:
            package.platform = data['platform'].strip()
        if 'package_name' in data:
            package.package_name = data['package_name'].strip()
        if 'package_amount' in data:
            amount = float(data['package_amount'])
            if amount <= 0:
                return jsonify({
                    'status': 'error',
                    'message': '套餐金额必须大于0'
                }), 400
            package.package_amount = amount
        if 'description' in data:
            package.description = data['description'].strip()
        if 'status' in data:
            package.status = data['status']
        if 'sort_order' in data:
            package.sort_order = int(data['sort_order'])
        
        package.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '团购套餐更新成功'
        })
        
    except Exception as e:
        print(f"更新团购套餐失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'更新团购套餐失败: {str(e)}'
        }), 500

@admin_groupon_package_api_bp.route('/delete/<int:package_id>', methods=['POST'])
@login_required
def delete_package(package_id):
    """删除团购套餐"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({
                'status': 'error',
                'message': '权限不足'
            }), 403
        
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        GrouponPackage = models['GrouponPackage']
        db = models['db']
        
        package = GrouponPackage.query.get_or_404(package_id)
        db.session.delete(package)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '团购套餐删除成功'
        })
        
    except Exception as e:
        print(f"删除团购套餐失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'删除团购套餐失败: {str(e)}'
        }), 500

@admin_groupon_package_api_bp.route('/platforms', methods=['GET'])
@login_required
def get_platforms():
    """获取所有平台列表（用于下拉选择）"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        GrouponPackage = models['GrouponPackage']
        db = models['db']
        
        # 获取所有不重复的平台
        platforms = db.session.query(GrouponPackage.platform).distinct().all()
        platform_list = [p[0] for p in platforms if p[0]]
        
        # 如果没有平台，返回默认平台列表
        if not platform_list:
            platform_list = ['美团', '抖音', '大众点评', '其他']
        
        return jsonify({
            'status': 'success',
            'data': sorted(set(platform_list))
        })
        
    except Exception as e:
        print(f"获取平台列表失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取平台列表失败: {str(e)}'
        }), 500
