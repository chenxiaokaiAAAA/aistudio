# -*- coding: utf-8 -*-
"""
二维码生成API路由模块
从 test_server.py 迁移二维码生成相关路由
"""
from flask import Blueprint, request, jsonify
import sys
import os
import requests
import time

# 创建蓝图
qrcode_api_bp = Blueprint('qrcode_api', __name__, url_prefix='/api/qrcode')


def get_access_token():
    """获取微信小程序access_token"""
    try:
        # 优先从数据库读取小程序配置，如果没有则使用默认值
        from app.services.payment_service import get_wechat_pay_config
        config = get_wechat_pay_config()
        
        if config:
            appid = config.get('appid', 'wx01e841dfc50052a9')
            secret = config.get('app_secret', '3cdb890ade31e5673c88fbf1aa8a46df')
        else:
            # 如果配置未初始化，使用默认值
            appid = 'wx01e841dfc50052a9'  # 您的AppID（与前端project.config.json保持一致）
            secret = '3cdb890ade31e5673c88fbf1aa8a46df'  # 您的AppSecret（需要与AppID匹配）
        
        url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}'
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'access_token' in data:
            print(f"获取access_token成功: {data['access_token'][:20]}...")
            return data['access_token']
        else:
            print(f"获取access_token失败: {data}")
            return None
            
    except Exception as e:
        print(f"获取access_token异常: {e}")
        return None


@qrcode_api_bp.route('/generate', methods=['POST'])
def generate_qrcode():
    """生成小程序码"""
    try:
        data = request.get_json()
        promotion_code = data.get('promotionCode')
        user_id = data.get('userId')
        
        if not promotion_code or not user_id:
            return jsonify({
                'success': False,
                'message': '推广码和用户ID不能为空'
            }), 400
        
        print(f"生成小程序码请求: promotionCode={promotion_code}, userId={user_id}")
        
        # 获取access_token
        access_token = get_access_token()
        if not access_token:
            return jsonify({
                'success': False,
                'message': '获取access_token失败'
            }), 500
        
        # 微信小程序码API
        url = f'https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={access_token}'
        
        # 构建参数
        scene = f"p={promotion_code}&u={user_id}"
        
        print(f"=== 小程序码生成调试 ===")
        print(f"原始promotionCode: {promotion_code}")
        print(f"原始userId: {user_id}")
        print(f"最终scene参数: {scene}")
        print(f"scene参数长度: {len(scene)}")
        
        params = {
            'scene': scene,
            'page': 'pages/index/index',
            'env_version': 'release',
            'width': 300,
            'auto_color': False,
            'line_color': {"r": 0, "g": 0, "b": 0}
        }
        
        print(f"调用微信API生成小程序码...")
        response = requests.post(url, json=params, timeout=(10, 30))
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容类型: {content_type}")
            print(f"响应内容长度: {len(response.content)}")
            
            if 'application/json' in content_type:
                # 如果返回JSON，说明有错误
                error_data = response.json()
                print(f"微信API返回错误: {error_data}")
                return jsonify({
                    'success': False,
                    'message': f'生成小程序码失败: {error_data.get("errmsg", "未知错误")}'
                }), 500
            
            # 保存图片到服务器
            timestamp = int(time.time())
            filename = f'qrcode_{promotion_code}_{user_id}_{timestamp}.jpg'
            qrcode_dir = os.path.join('static', 'qrcodes')
            filepath = os.path.join(qrcode_dir, filename)
            
            # 确保目录存在
            os.makedirs(qrcode_dir, exist_ok=True)
            
            # 保存图片
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ 小程序码保存成功: {filepath}")
            
            # 返回图片URL
            return jsonify({
                'success': True,
                'qrcode_url': f'/static/qrcodes/{filename}',
                'filename': filename
            })
        else:
            return jsonify({
                'success': False,
                'message': f'生成小程序码失败: HTTP {response.status_code}'
            }), 500
            
    except Exception as e:
        print(f"生成小程序码失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'生成小程序码失败: {str(e)}'
        }), 500


@qrcode_api_bp.route('/generate-franchisee', methods=['POST'])
def generate_franchisee_qrcode():
    """生成门店专属小程序码"""
    from flask_login import login_required, current_user
    from app.utils.decorators import admin_required
    from app.utils.admin_helpers import get_models
    
    try:
        # 权限检查
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': '请先登录'
            }), 401
        
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'message': '权限不足'
            }), 403
        
        data = request.get_json()
        franchisee_id = data.get('franchiseeId') or data.get('franchisee_id')
        
        if not franchisee_id:
            return jsonify({
                'success': False,
                'message': '门店ID不能为空'
            }), 400
        
        # 获取门店信息
        models = get_models(['FranchiseeAccount'])
        if not models:
            return jsonify({
                'success': False,
                'message': '系统未初始化'
            }), 500
        
        FranchiseeAccount = models['FranchiseeAccount']
        franchisee = FranchiseeAccount.query.get(franchisee_id)
        
        if not franchisee:
            return jsonify({
                'success': False,
                'message': '门店不存在'
            }), 404
        
        if not franchisee.qr_code:
            return jsonify({
                'success': False,
                'message': '门店二维码标识未设置，请先在门店管理中设置二维码标识'
            }), 400
        
        print(f"生成门店小程序码请求: franchiseeId={franchisee_id}, qrCode={franchisee.qr_code}")
        
        # 获取access_token
        access_token = get_access_token()
        if not access_token:
            return jsonify({
                'success': False,
                'message': '获取access_token失败'
            }), 500
        
        # 微信小程序码API
        url = f'https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={access_token}'
        
        # 构建参数：s=门店二维码标识
        scene = f"s={franchisee.qr_code}"
        
        print(f"=== 门店小程序码生成调试 ===")
        print(f"门店ID: {franchisee_id}")
        print(f"门店二维码标识: {franchisee.qr_code}")
        print(f"最终scene参数: {scene}")
        print(f"scene参数长度: {len(scene)}")
        
        # 尝试不同的小程序版本和页面配置
        # 先尝试带页面路径的，如果失败则尝试不指定页面（使用默认首页）
        attempts = [
            {'env_version': 'release', 'page': 'pages/index/index'},
            {'env_version': 'trial', 'page': 'pages/index/index'},
            {'env_version': 'release', 'page': None},  # 不指定页面，使用默认首页
            {'env_version': 'trial', 'page': None},
        ]
        
        last_error = None
        response = None
        success = False
        
        for attempt in attempts:
            env_version = attempt['env_version']
            page = attempt['page']
            
            params = {
                'scene': scene,
                'env_version': env_version,
                'width': 300,
                'auto_color': False,
                'line_color': {"r": 0, "g": 0, "b": 0}
            }
            
            # 如果指定了页面，添加到参数中
            if page:
                params['page'] = page
            
            page_desc = page if page else '默认首页'
            print(f"调用微信API生成门店小程序码 (版本: {env_version}, 页面: {page_desc})...")
            response = requests.post(url, json=params, timeout=(10, 30))
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                print(f"响应状态码: {response.status_code}")
                print(f"响应内容类型: {content_type}")
                print(f"响应内容长度: {len(response.content)}")
                
                if 'application/json' in content_type:
                    # 如果返回JSON，说明有错误
                    error_data = response.json()
                    print(f"微信API返回错误 (版本 {env_version}, 页面 {page_desc}): {error_data}")
                    last_error = error_data.get("errmsg", "未知错误")
                    # 如果是页面路径错误，继续尝试下一个配置
                    if 'invalid page' in str(error_data).lower() or 'page' in str(error_data).lower():
                        print(f"页面路径错误，尝试下一个配置...")
                        continue
                    else:
                        # 其他错误，继续尝试
                        continue
                else:
                    # 成功返回图片，跳出循环
                    success = True
                    print(f"✅ 成功生成小程序码 (版本: {env_version}, 页面: {page_desc})")
                    break
            else:
                last_error = f'HTTP {response.status_code}'
                continue
        
        # 检查是否成功
        if not success or not response or response.status_code != 200:
            error_msg = last_error or "所有配置都失败"
            if 'invalid page' in str(error_msg).lower():
                error_msg = "小程序尚未发布或体验版未设置。请先在小程序后台：\n1. 上传代码并设置为体验版，或\n2. 提交审核并发布到正式版"
            return jsonify({
                'success': False,
                'message': f'生成小程序码失败: {error_msg}'
            }), 500
        
        # 保存图片到服务器
        timestamp = int(time.time())
        filename = f'franchisee_{franchisee_id}_{franchisee.qr_code}_{timestamp}.jpg'
        qrcode_dir = os.path.join('static', 'qrcodes')
        filepath = os.path.join(qrcode_dir, filename)
        
        # 确保目录存在
        os.makedirs(qrcode_dir, exist_ok=True)
        
        # 保存图片
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ 门店小程序码保存成功: {filepath}")
        
        # 返回图片URL
        return jsonify({
            'success': True,
            'qrcode_url': f'/static/qrcodes/{filename}',
            'filename': filename,
            'franchisee_id': franchisee_id,
            'franchisee_name': franchisee.company_name,
            'qr_code': franchisee.qr_code
        })
            
    except Exception as e:
        print(f"生成门店小程序码失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'生成门店小程序码失败: {str(e)}'
        }), 500