#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 RunningHub rhart-image-n-pro/edit API 配置
用于在 aistudio 项目中添加 RunningHub 全能图片PRO-图生图 API 配置
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入 Flask app 和数据库
try:
    from test_server import app, db
    from app.models import APIProviderConfig
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)

def add_runninghub_config():
    """添加 RunningHub API 配置"""
    with app.app_context():
        try:
            # 检查是否已存在同名配置
            existing = APIProviderConfig.query.filter_by(name='RunningHub-全能图片PRO').first()
            if existing:
                print(f"\n[INFO] 配置 'RunningHub-全能图片PRO' 已存在 (ID: {existing.id})")
                print(f"       Host: {existing.host_domestic or existing.host_overseas}")
                print(f"       API类型: {existing.api_type}")
                print(f"       状态: {'启用' if existing.is_active else '禁用'}")
                response = input("\n是否要更新现有配置? (y/n): ").strip().lower()
                if response != 'y':
                    print("[INFO] 已取消操作")
                    return False
                # 更新现有配置
                config = existing
            else:
                # 创建新配置
                config = APIProviderConfig()
                config.name = 'RunningHub-全能图片PRO'
            
            # 配置基本信息
            config.api_type = 'runninghub-rhart-edit'
            config.host_domestic = 'https://www.runninghub.cn'
            config.host_overseas = 'https://www.runninghub.cn'
            config.draw_endpoint = '/openapi/v2/rhart-image-n-pro/edit'
            config.result_endpoint = '/openapi/v2/query'  # RunningHub 查询任务结果接口（新格式，请求体只需要 taskId）
            config.file_upload_endpoint = '/v1/file/upload'  # 如果有文件上传接口
            
            # 需要用户输入 API Key
            if not existing or not existing.api_key:
                api_key = input("\n请输入 RunningHub 的 API Key (留空跳过): ").strip()
                if api_key:
                    config.api_key = api_key
                elif not existing:
                    print("[WARNING] 未输入 API Key，配置将保存但无法使用，请稍后通过管理后台编辑")
            else:
                print(f"\n[INFO] 使用现有 API Key (已隐藏)")
                response = input("是否要更新 API Key? (y/n): ").strip().lower()
                if response == 'y':
                    api_key = input("请输入新的 API Key: ").strip()
                    if api_key:
                        config.api_key = api_key
            
            # 配置选项
            config.is_active = True
            config.is_default = False
            config.enable_retry = True  # 启用重试机制
            config.is_sync_api = False  # False=异步API（RunningHub 返回 taskId，需要轮询）
            config.priority = 0  # 优先级
            
            # 模型名称（可选）
            model_name = input("\n请输入模型名称 (留空使用默认，如: rhart-image-n-pro): ").strip()
            config.model_name = model_name if model_name else None
            
            # 配置描述（可选）
            description = input("\n请输入配置描述 (留空跳过): ").strip()
            config.description = description if description else 'RunningHub 全能图片PRO-图生图 API 配置，支持4K超清画质输出，专业级图像编辑'
            
            # 保存配置
            if not existing:
                db.session.add(config)
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("[OK] RunningHub API 配置已保存")
            print("=" * 60)
            print(f"配置ID: {config.id}")
            print(f"配置名称: {config.name}")
            print(f"API类型: {config.api_type}")
            print(f"国内Host: {config.host_domestic}")
            print(f"海外Host: {config.host_overseas}")
            print(f"绘画接口: {config.draw_endpoint}")
            print(f"结果接口: {config.result_endpoint}")
            print(f"文件上传接口: {config.file_upload_endpoint}")
            print(f"模型名称: {config.model_name or '(未设置)'}")
            print(f"API Key: {'已设置' if config.api_key else '未设置'}")
            print(f"状态: {'启用' if config.is_active else '禁用'}")
            print(f"同步API: {'是' if config.is_sync_api else '否'} (False=异步API)")
            print(f"启用重试: {'是' if config.enable_retry else '否'}")
            print(f"优先级: {config.priority}")
            print(f"描述: {config.description}")
            print("\n[提示] 可以通过管理后台查看和编辑配置")
            print("[提示] 配置已保存，可以立即使用")
            print("\n[重要] RunningHub API 特点:")
            print("  - 请求格式: application/json")
            print("  - 图片参数: imageUrls 数组（最多10张）")
            print("  - 响应格式: 返回 taskId，需要异步轮询查询结果")
            print("  - 支持分辨率: 1K, 2K, 4K")
            print("  - 支持比例: 3:4, 16:9, auto 等")
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] 添加配置失败: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("添加 RunningHub 全能图片PRO-图生图 API 配置")
    print("=" * 60)
    print("\n此脚本将添加 RunningHub 的 rhart-image-n-pro/edit 类型 API 配置")
    print("配置信息:")
    print("  - API类型: runninghub-rhart-edit")
    print("  - Host: https://www.runninghub.cn")
    print("  - 绘画接口: /openapi/v2/rhart-image-n-pro/edit")
    print("  - 结果接口: /openapi/v2/query (新格式，请求体只需要 taskId)")
    print("  - 异步API: 是 (is_sync_api = False)")
    print("  - 请求格式: application/json")
    print("  - 图片参数: imageUrls 数组（最多10张）")
    print("\n参考文档: https://www.runninghub.cn/call-api/api-detail/2004543527918551041?apiType=1")
    print("=" * 60)
    
    if add_runninghub_config():
        print("\n✅ 完成！")
    else:
        print("\n❌ 失败！")
        sys.exit(1)
