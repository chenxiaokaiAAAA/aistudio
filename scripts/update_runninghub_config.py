#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新 RunningHub ComfyUI 工作流 API 配置
使用提供的 API Key 和工作流 ID
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

def update_runninghub_config():
    """更新 RunningHub ComfyUI 工作流 API 配置"""
    with app.app_context():
        try:
            # 配置信息
            API_KEY = "14014c51362d40f3b7794b50f0a67551"
            WORKFLOW_ID = "2014169267842850817"
            
            # 检查是否已存在配置
            existing = APIProviderConfig.query.filter_by(name='RunningHub-ComfyUI工作流').first()
            if existing:
                print(f"\n[INFO] 找到现有配置 'RunningHub-ComfyUI工作流' (ID: {existing.id})")
                config = existing
            else:
                print(f"\n[INFO] 创建新配置 'RunningHub-ComfyUI工作流'")
                config = APIProviderConfig()
                config.name = 'RunningHub-ComfyUI工作流'
            
            # 配置基本信息
            config.api_type = 'runninghub-comfyui-workflow'
            config.host_domestic = 'https://www.runninghub.cn'
            config.host_overseas = 'https://www.runninghub.cn'
            config.draw_endpoint = '/run/workflow/{workflow_id}'  # 占位符，实际 workflow_id 在模板中
            config.result_endpoint = '/openapi/v2/task/outputs'
            config.file_upload_endpoint = '/v1/file/upload'
            config.api_key = API_KEY
            
            # 配置选项
            config.is_active = True
            config.is_default = False
            config.enable_retry = True
            config.is_sync_api = False  # 异步API
            config.priority = 0
            config.model_name = None
            config.description = 'RunningHub ComfyUI 工作流 API 配置，支持自定义工作流节点参数映射'
            
            # 保存配置
            if not existing:
                db.session.add(config)
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("[OK] RunningHub ComfyUI 工作流 API 配置已更新")
            print("=" * 60)
            print(f"配置ID: {config.id}")
            print(f"配置名称: {config.name}")
            print(f"API类型: {config.api_type}")
            print(f"Host: {config.host_domestic}")
            print(f"绘画接口: {config.draw_endpoint}")
            print(f"结果接口: {config.result_endpoint}")
            print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]} (已设置)")
            print(f"工作流ID: {WORKFLOW_ID}")
            print(f"状态: {'启用' if config.is_active else '禁用'}")
            print("\n[提示] 配置已保存，可以在风格图片的API模板中使用")
            print(f"[提示] 工作流地址: https://www.runninghub.cn/workflow/{WORKFLOW_ID}")
            print("\n[下一步] 在风格图片的API-ComfyUI工作流配置中:")
            print(f"  1. 选择此 API 配置 (ID: {config.id})")
            print(f"  2. 填写工作流ID: {WORKFLOW_ID}")
            print("  3. 配置节点参数映射（输入图片节点ID、提示词节点ID等）")
            
            return True, config.id, WORKFLOW_ID
            
        except Exception as e:
            print(f"\n[ERROR] 更新配置失败: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False, None, None

if __name__ == "__main__":
    print("=" * 60)
    print("更新 RunningHub ComfyUI 工作流 API 配置")
    print("=" * 60)
    print("\n配置信息:")
    print("  - API Key: 14014c51362d40f3b7794b50f0a67551")
    print("  - 工作流ID: 2014169267842850817")
    print("  - 工作流地址: https://www.runninghub.cn/workflow/2014169267842850817")
    print("=" * 60)
    
    success, config_id, workflow_id = update_runninghub_config()
    
    if success:
        print("\n✅ 配置更新成功！")
        print(f"\n📝 配置摘要:")
        print(f"   - API配置ID: {config_id}")
        print(f"   - 工作流ID: {workflow_id}")
        print(f"   - 可以在管理后台的'风格管理'中配置此工作流")
    else:
        print("\n❌ 配置更新失败！")
        sys.exit(1)
