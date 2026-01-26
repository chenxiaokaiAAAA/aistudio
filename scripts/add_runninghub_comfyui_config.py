#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 RunningHub ComfyUI 工作流 API 配置
用于在 aistudio 项目中添加 RunningHub ComfyUI 工作流 API 配置
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

def add_runninghub_comfyui_config():
    """添加 RunningHub ComfyUI 工作流 API 配置"""
    with app.app_context():
        try:
            # 检查是否已存在同名配置
            existing = APIProviderConfig.query.filter_by(name='RunningHub-ComfyUI工作流').first()
            if existing:
                print(f"\n[INFO] 配置 'RunningHub-ComfyUI工作流' 已存在 (ID: {existing.id})")
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
                config.name = 'RunningHub-ComfyUI工作流'
            
            # 配置基本信息
            config.api_type = 'runninghub-comfyui-workflow'
            config.host_domestic = 'https://www.runninghub.cn'
            config.host_overseas = 'https://www.runninghub.cn'
            # draw_endpoint 留空，因为 workflow_id 在模板的 request_body_template 中配置
            config.draw_endpoint = '/run/workflow/{workflow_id}'  # 占位符，实际 workflow_id 在模板中
            config.result_endpoint = '/openapi/v2/task/outputs'  # RunningHub 查询任务结果接口
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
            config.is_sync_api = False  # False=异步API（RunningHub ComfyUI 工作流返回 taskId，需要轮询）
            config.priority = 0  # 优先级
            
            # 模型名称（ComfyUI 工作流不需要模型名称，但可以留空）
            config.model_name = None
            
            # 配置描述（可选）
            description = input("\n请输入配置描述 (留空跳过): ").strip()
            config.description = description if description else 'RunningHub ComfyUI 工作流 API 配置，支持自定义工作流节点参数映射'
            
            # 保存配置
            if not existing:
                db.session.add(config)
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("[OK] RunningHub ComfyUI 工作流 API 配置已保存")
            print("=" * 60)
            print(f"配置ID: {config.id}")
            print(f"配置名称: {config.name}")
            print(f"API类型: {config.api_type}")
            print(f"国内Host: {config.host_domestic}")
            print(f"海外Host: {config.host_overseas}")
            print(f"绘画接口: {config.draw_endpoint} (workflow_id 在模板中配置)")
            print(f"结果接口: {config.result_endpoint}")
            print(f"API Key: {'已设置' if config.api_key else '未设置'}")
            print(f"状态: {'启用' if config.is_active else '禁用'}")
            print(f"同步API: {'是' if config.is_sync_api else '否'} (False=异步API)")
            print(f"启用重试: {'是' if config.enable_retry else '否'}")
            print(f"描述: {config.description}")
            print("\n[提示] 可以通过管理后台查看和编辑配置")
            print("[提示] 配置已保存，可以立即使用")
            print("\n[重要] RunningHub ComfyUI 工作流 API 特点:")
            print("  - 请求格式: application/json")
            print("  - 工作流ID: 在风格图片的API模板中配置（request_body_template）")
            print("  - 节点参数: 通过 nodeInfoList 动态映射到工作流节点")
            print("  - 响应格式: 返回 taskId，需要异步轮询查询结果")
            print("  - 没有标准的 prompt, size, aspect_ratio 参数")
            print("\n[下一步] 在风格分类/图片的API模板配置中:")
            print("  1. 选择此 API 配置")
            print("  2. 填写工作流ID")
            print("  3. 配置 nodeInfoList（节点参数映射）")
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] 添加配置失败: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("添加 RunningHub ComfyUI 工作流 API 配置")
    print("=" * 60)
    print("\n此脚本将添加 RunningHub 的 ComfyUI 工作流 API 配置")
    print("配置信息:")
    print("  - API类型: runninghub-comfyui-workflow")
    print("  - Host: https://www.runninghub.cn")
    print("  - 绘画接口: /run/workflow/{workflow_id} (workflow_id 在模板中配置)")
    print("  - 结果接口: /openapi/v2/task/outputs")
    print("  - 异步API: 是 (is_sync_api = False)")
    print("  - 请求格式: application/json")
    print("  - 请求参数: nodeInfoList（节点参数映射列表）")
    print("\n参考文档: https://www.runninghub.cn/call-api/api-detail/2004375142916210689?apiType=3")
    print("=" * 60)
    
    if add_runninghub_comfyui_config():
        print("\n✅ 完成！")
    else:
        print("\n❌ 失败！")
        sys.exit(1)
