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
        # 微信小程序AppID和AppSecret
        appid = 'wx8e9715aac932a79b'  # 您的AppID
        secret = '3cdb890ade31e5673c88fbf1aa8a46df'  # 您的AppSecret
        
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
