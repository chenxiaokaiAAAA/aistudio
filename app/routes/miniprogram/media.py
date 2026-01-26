# -*- coding: utf-8 -*-
"""
小程序媒体文件路由
"""
from flask import Blueprint, request, jsonify, send_from_directory, current_app
import sys
import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
from server_config import get_media_url

# 创建媒体文件相关的子蓝图
bp = Blueprint('media', __name__)


@bp.route('/media/original/<filename>')
def miniprogram_media_original(filename):
    """小程序访问原图（无需登录）"""
    try:
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            app = test_server_module.app
        else:
            app = current_app
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)
    except Exception as e:
        print(f"访问原图失败: {e}")
        return jsonify({'error': '图片不存在'}), 404


@bp.route('/media/final/<filename>')
def miniprogram_media_final(filename):
    """小程序访问效果图（无需登录）"""
    try:
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            app = test_server_module.app
        else:
            app = current_app
        return send_from_directory(app.config['FINAL_FOLDER'], filename, as_attachment=False)
    except Exception as e:
        print(f"访问效果图失败: {e}")
        return jsonify({'error': '图片不存在'}), 404


@bp.route('/static/images/<path:filename>')
def miniprogram_static_images(filename):
    """小程序访问静态图片（无需登录）"""
    try:
        return send_from_directory('static/images', filename, as_attachment=False)
    except Exception as e:
        print(f"访问静态图片失败: {e}")
        return jsonify({'error': '图片不存在'}), 404


@bp.route('/upload', methods=['POST'])
def miniprogram_upload_image():
    """小程序上传图片"""
    try:
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            app = test_server_module.app
        else:
            app = current_app
        
        if 'image' not in request.files:
            return jsonify({'status': 'error', 'message': '没有上传图片'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': '没有选择文件'}), 400
        
        # 生成文件名
        filename = secure_filename(f"mp_{uuid.uuid4().hex[:8]}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 保存文件
        file.save(file_path)
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        print(f"图片上传成功: {filename}, 大小: {file_size} bytes")
        
        # 如果文件太大，尝试压缩
        if file_size > 5 * 1024 * 1024:  # 5MB
            try:
                with Image.open(file_path) as img:
                    # 压缩图片
                    img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                    img.save(file_path, 'JPEG', quality=85, optimize=True)
                    new_size = os.path.getsize(file_path)
                    print(f"图片已压缩: {file_size} -> {new_size} bytes")
            except Exception as compress_error:
                print(f"图片压缩失败: {compress_error}")
        
        return jsonify({
            'status': 'success',
            'message': '图片上传成功',
            'filename': filename,
            'url': f'{get_media_url()}/original/{filename}'
        })
        
    except Exception as e:
        print(f"图片上传失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'图片上传失败: {str(e)}'}), 500
