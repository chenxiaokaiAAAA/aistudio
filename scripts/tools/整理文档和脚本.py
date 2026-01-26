#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档和脚本整理工具
自动将散落的 .md 和 .py 文件整理到对应目录
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# 项目根目录（脚本在 AI-studio 目录下，所以 PROJECT_ROOT 就是 AI-studio）
PROJECT_ROOT = Path(__file__).parent
AI_STUDIO = PROJECT_ROOT  # 脚本已经在 AI-studio 目录下了

# 目标目录
DOCS_DIR = AI_STUDIO / "docs"
SCRIPTS_DIR = AI_STUDIO / "scripts"
BATCH_DIR = AI_STUDIO / "batch"

# 文档分类规则
DOC_CATEGORIES = {
    "api": ["API", "接口", "api"],
    "deployment": ["部署", "配置", "环境", "nginx", "https", "ssl"],
    "features": ["功能", "实现", "完成", "说明", "总结"],
    "troubleshooting": ["问题", "修复", "错误", "调试", "测试"],
    "database": ["数据库", "迁移", "字段", "表"],
}

# 脚本分类规则
SCRIPT_CATEGORIES = {
    "database": ["add_", "create_", "migrate_", "fix_", "check_", "verify_"],
    "setup": ["install", "setup", "start", "run"],
    "tools": ["analyze", "compare", "export", "import", "sync"],
    "tests": ["test_", "debug_", "simulate_"],
}

def create_directories():
    """创建目标目录结构"""
    directories = [
        DOCS_DIR / "api",
        DOCS_DIR / "deployment",
        DOCS_DIR / "features",
        DOCS_DIR / "troubleshooting",
        DOCS_DIR / "database",
        SCRIPTS_DIR / "database",
        SCRIPTS_DIR / "setup",
        SCRIPTS_DIR / "tools",
        SCRIPTS_DIR / "tests",
        BATCH_DIR / "setup",
        BATCH_DIR / "maintenance",
        BATCH_DIR / "deployment",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {directory}")

def categorize_file(filename, categories):
    """根据文件名和分类规则确定文件应该放在哪个目录"""
    filename_lower = filename.lower()
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword.lower() in filename_lower:
                return category
    
    return "other"

def move_md_files():
    """移动 .md 文件到 docs 目录"""
    moved_count = 0
    skipped_files = [
        "README.md",  # 保留在根目录
        "项目结构梳理和优化方案.md",  # 保留在项目根目录
        "API接口文档-厂家版.md",  # 保留在项目根目录
        "代码拆分方案.md",  # 保留在根目录
        "代码重构执行计划.md",  # 保留在根目录
    ]
    
    # 调试信息
    print(f"🔍 查找目录: {AI_STUDIO}")
    md_files = list(AI_STUDIO.glob("*.md"))
    print(f"🔍 找到 {len(md_files)} 个 .md 文件")
    
    for md_file in md_files:
        if md_file.name in skipped_files:
            print(f"⏭️  跳过文件: {md_file.name}")
            continue
        
        category = categorize_file(md_file.name, DOC_CATEGORIES)
        
        if category == "other":
            target_dir = DOCS_DIR
        else:
            target_dir = DOCS_DIR / category
        
        target_path = target_dir / md_file.name
        
        # 如果目标文件已存在，添加时间戳
        if target_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = md_file.stem, timestamp, md_file.suffix
            target_path = target_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
        
        try:
            shutil.move(str(md_file), str(target_path))
            print(f"✅ 移动文档: {md_file.name} -> {target_dir.name}/")
            moved_count += 1
        except Exception as e:
            print(f"❌ 移动失败: {md_file.name} - {e}")
    
    return moved_count

def move_py_scripts():
    """移动 .py 脚本到 scripts 目录"""
    moved_count = 0
    skipped_files = [
        "test_server.py",  # 主服务文件，保留
        "start.py",  # 启动脚本，保留
        "server_config.py",  # 配置文件，保留
        "printer_config.py",  # 配置文件，保留
        "size_config.py",  # 配置文件，保留
        "order_notification.py",  # 通知模块，保留
        "wechat_notification.py",  # 通知模块，保留
        "franchisee_routes.py",  # 路由模块，保留
        "printer_client.py",  # 客户端模块，保留
        "sync_config_routes.py",  # 同步模块，保留
        "整理文档和脚本.py",  # 当前脚本，保留
        "创建代码模块结构.py",  # 当前脚本，保留
    ]
    
    # 调试信息
    py_files = list(AI_STUDIO.glob("*.py"))
    print(f"🔍 找到 {len(py_files)} 个 .py 文件")
    
    for py_file in py_files:
        if py_file.name in skipped_files:
            print(f"⏭️  跳过文件: {py_file.name}")
            continue
        
        category = categorize_file(py_file.name, SCRIPT_CATEGORIES)
        
        if category == "other":
            target_dir = SCRIPTS_DIR
        else:
            target_dir = SCRIPTS_DIR / category
        
        target_path = target_dir / py_file.name
        
        # 如果目标文件已存在，添加时间戳
        if target_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = py_file.stem, timestamp, py_file.suffix
            target_path = target_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
        
        try:
            shutil.move(str(py_file), str(target_path))
            print(f"✅ 移动脚本: {py_file.name} -> {target_dir.name}/")
            moved_count += 1
        except Exception as e:
            print(f"❌ 移动失败: {py_file.name} - {e}")
    
    return moved_count

def move_bat_files():
    """移动 .bat 文件到 batch 目录"""
    moved_count = 0
    skipped_files = [
        "start.py",  # 如果有的话
    ]
    
    # 调试信息
    bat_files = list(AI_STUDIO.glob("*.bat"))
    print(f"🔍 找到 {len(bat_files)} 个 .bat 文件")
    
    for bat_file in bat_files:
        if bat_file.name in skipped_files:
            print(f"⏭️  跳过文件: {bat_file.name}")
            continue
        
        # 根据文件名判断分类
        filename_lower = bat_file.name.lower()
        if "install" in filename_lower or "setup" in filename_lower or "start" in filename_lower:
            target_dir = BATCH_DIR / "setup"
        elif "backup" in filename_lower or "clean" in filename_lower or "fix" in filename_lower:
            target_dir = BATCH_DIR / "maintenance"
        elif "deploy" in filename_lower or "nginx" in filename_lower:
            target_dir = BATCH_DIR / "deployment"
        else:
            target_dir = BATCH_DIR
        
        target_path = target_dir / bat_file.name
        
        # 如果目标文件已存在，添加时间戳
        if target_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = bat_file.stem, timestamp, bat_file.suffix
            target_path = target_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
        
        try:
            shutil.move(str(bat_file), str(target_path))
            print(f"✅ 移动批处理: {bat_file.name} -> {target_dir.name}/")
            moved_count += 1
        except Exception as e:
            print(f"❌ 移动失败: {bat_file.name} - {e}")
    
    return moved_count

def create_docs_index():
    """创建文档索引文件"""
    index_content = """# 文档索引

本文档目录包含所有项目文档，按类别组织。

## 📁 目录结构

### API文档 (`api/`)
API接口相关文档，包括：
- API接口文档-厂家版.md
- API使用示例
- 接口测试文档

### 部署文档 (`deployment/`)
部署和配置相关文档，包括：
- 服务器配置说明
- Nginx配置
- HTTPS配置
- 环境切换说明

### 功能文档 (`features/`)
功能实现和说明文档，包括：
- 功能实现总结
- 功能使用说明
- 功能完成报告

### 问题排查 (`troubleshooting/`)
问题修复和调试文档，包括：
- 问题修复说明
- 错误排查指南
- 调试方法

### 数据库文档 (`database/`)
数据库相关文档，包括：
- 数据库迁移说明
- 字段添加说明
- 表结构说明

## 🔍 快速查找

### 按关键词查找

- **API接口**：查看 `api/` 目录
- **部署配置**：查看 `deployment/` 目录
- **功能说明**：查看 `features/` 目录
- **问题修复**：查看 `troubleshooting/` 目录
- **数据库**：查看 `database/` 目录

## 📝 文档维护

- 新增文档请放在对应的分类目录
- 文档命名使用中文，清晰描述内容
- 重要文档请在本文档中添加链接

---

**最后更新**：{update_time}
""".format(update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    index_path = DOCS_DIR / "README.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)
    print(f"✅ 创建文档索引: {index_path}")

def main():
    """主函数"""
    print("=" * 60)
    print("文档和脚本整理工具")
    print("=" * 60)
    print()
    
    # 创建目录结构
    print("📁 创建目录结构...")
    create_directories()
    print()
    
    # 移动文档
    print("📄 整理文档文件...")
    md_count = move_md_files()
    print(f"✅ 共移动 {md_count} 个文档文件")
    print()
    
    # 移动脚本
    print("🐍 整理Python脚本...")
    py_count = move_py_scripts()
    print(f"✅ 共移动 {py_count} 个Python脚本")
    print()
    
    # 移动批处理
    print("📦 整理批处理脚本...")
    bat_count = move_bat_files()
    print(f"✅ 共移动 {bat_count} 个批处理脚本")
    print()
    
    # 创建文档索引
    print("📝 创建文档索引...")
    create_docs_index()
    print()
    
    print("=" * 60)
    print("✅ 整理完成！")
    print("=" * 60)
    print()
    print("📊 统计：")
    print(f"  - 文档文件: {md_count} 个")
    print(f"  - Python脚本: {py_count} 个")
    print(f"  - 批处理脚本: {bat_count} 个")
    print()
    print("📁 新目录结构：")
    print(f"  - 文档目录: {DOCS_DIR}")
    print(f"  - 脚本目录: {SCRIPTS_DIR}")
    print(f"  - 批处理目录: {BATCH_DIR}")
    print()

if __name__ == "__main__":
    main()
