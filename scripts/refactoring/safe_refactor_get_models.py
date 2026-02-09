#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全重构工具：统一 get_models() 函数
逐步替换，每次只处理一个文件，并创建备份
"""

import os
import re
import shutil
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKUP_DIR = PROJECT_ROOT / 'backups' / 'refactor_backups'

def backup_file(file_path):
    """备份单个文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file_path = BACKUP_DIR / f'file_backup_{timestamp}' / file_path.relative_to(PROJECT_ROOT)
    backup_file_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_path, backup_file_path)
    return backup_file_path

def get_local_get_models_code(file_path):
    """提取本地 get_models() 函数代码"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # 查找 get_models 函数定义
    start_line = None
    end_line = None
    indent_level = None
    
    for i, line in enumerate(lines):
        if re.match(r'^\s*def get_models\(', line):
            start_line = i
            # 获取缩进级别
            indent_level = len(line) - len(line.lstrip())
            break
    
    if start_line is None:
        return None, None
    
    # 查找函数结束（下一个同级别或更高级别的定义）
    for i in range(start_line + 1, len(lines)):
        line = lines[i]
        # 空行或注释继续
        if not line.strip() or line.strip().startswith('#'):
            continue
        # 如果缩进级别相同或更少，说明函数结束
        current_indent = len(line) - len(line.lstrip())
        if line.strip() and current_indent <= indent_level:
            end_line = i
            break
    
    if end_line is None:
        end_line = len(lines)
    
    function_code = '\n'.join(lines[start_line:end_line])
    return function_code, (start_line, end_line)

def determine_import_source(file_path):
    """确定应该从哪个模块导入"""
    # 如果是小程序相关路由，使用 miniprogram/common
    if 'miniprogram' in str(file_path):
        return 'from app.routes.miniprogram.common import get_models, get_helper_functions'
    # 其他使用 admin_helpers
    else:
        return 'from app.utils.admin_helpers import get_models'

def refactor_file(file_path, dry_run=True):
    """重构单个文件"""
    print(f"\n处理文件: {file_path.relative_to(PROJECT_ROOT)}")
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        original_content = content
    
    # 检查是否已有导入
    if 'from app.utils.admin_helpers import' in content or 'from app.routes.miniprogram.common import' in content:
        print("  已从公共模块导入，跳过")
        return False, "已导入"
    
    # 提取本地 get_models 函数
    function_code, (start_line, end_line) = get_local_get_models_code(file_path)
    if not function_code:
        print("  未找到本地 get_models 定义，跳过")
        return False, "未找到"
    
    # 确定导入源
    import_statement = determine_import_source(file_path)
    
    # 检查文件开头是否已有导入
    lines = content.split('\n')
    import_insert_pos = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            import_insert_pos = i + 1
        elif line.strip() and not line.strip().startswith('#'):
            break
    
    if dry_run:
        print(f"  [DRY RUN] 将:")
        print(f"    1. 在第 {import_insert_pos + 1} 行插入: {import_statement}")
        print(f"    2. 删除第 {start_line + 1}-{end_line} 行的 get_models() 函数定义")
        return True, "dry_run"
    
    # 实际重构
    # 1. 插入导入语句
    lines.insert(import_insert_pos, import_statement)
    
    # 2. 删除本地函数定义
    # 注意：行号已经因为插入而改变
    adjusted_start = start_line + 1  # 因为插入了导入
    adjusted_end = end_line + 1
    del lines[adjusted_start:adjusted_end]
    
    # 写回文件
    new_content = '\n'.join(lines)
    
    # 备份原文件
    backup_path = backup_file(file_path)
    print(f"  原文件已备份到: {backup_path}")
    
    # 写入新内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  [OK] 重构完成")
    return True, "refactored"

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='安全重构工具：统一 get_models() 函数')
    parser.add_argument('--file', help='指定要重构的文件路径')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不实际修改')
    parser.add_argument('--all', action='store_true', help='重构所有需要重构的文件')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("安全重构工具：统一 get_models() 函数")
    print("=" * 60)
    
    if args.dry_run:
        print("[DRY RUN 模式] 仅预览，不会实际修改文件")
    
    # 先运行分析脚本
    print("\n正在分析文件...")
    import subprocess
    result = subprocess.run(
        ['python', str(PROJECT_ROOT / 'scripts' / 'refactoring' / 'analyze_get_models_usage.py')],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    # 读取分析结果
    analysis_file = PROJECT_ROOT / 'docs' / 'refactoring' / 'get_models_analysis.json'
    if not analysis_file.exists():
        print("错误: 分析结果文件不存在")
        return
    
    with open(analysis_file, 'r', encoding='utf-8') as f:
        analysis = json.load(f)
    
    files_to_refactor = analysis['files_needing_refactor']
    
    if args.file:
        # 重构指定文件
        file_path = PROJECT_ROOT / args.file
        if file_path.exists():
            refactor_file(file_path, dry_run=args.dry_run)
        else:
            print(f"错误: 文件不存在: {args.file}")
    elif args.all:
        # 重构所有文件
        print(f"\n找到 {len(files_to_refactor)} 个需要重构的文件")
        confirm = input("是否继续? (yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消")
            return
        
        refactored_count = 0
        for file_rel_path in files_to_refactor:
            file_path = PROJECT_ROOT / file_rel_path
            if file_path.exists():
                success, status = refactor_file(file_path, dry_run=args.dry_run)
                if success and status == 'refactored':
                    refactored_count += 1
            else:
                print(f"  文件不存在: {file_rel_path}")
        
        print("\n" + "=" * 60)
        print(f"重构完成: {refactored_count} 个文件")
        print("=" * 60)
    else:
        # 显示需要重构的文件列表
        print(f"\n找到 {len(files_to_refactor)} 个需要重构的文件:")
        for i, file_path in enumerate(files_to_refactor[:20], 1):  # 只显示前20个
            print(f"  {i}. {file_path}")
        if len(files_to_refactor) > 20:
            print(f"  ... 还有 {len(files_to_refactor) - 20} 个文件")
        print("\n使用方法:")
        print("  --file <文件路径>  : 重构指定文件")
        print("  --all              : 重构所有文件")
        print("  --dry-run          : 仅预览，不实际修改")

if __name__ == '__main__':
    main()
