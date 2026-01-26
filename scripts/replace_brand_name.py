#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量替换项目中的"萌宠绘"为"AI自拍机-"
"""
import os
import re
from pathlib import Path

# 需要排除的文件和目录
EXCLUDE_DIRS = {
    '__pycache__',
    '.git',
    'node_modules',
    'instance',
    'uploads',
    'static',
    'templates',
    'logs',
    'back',
    'unused_databases',
    'final_works',
    'hd_images',
    '小程序前端修改代码',
    'media'
}

EXCLUDE_FILES = {
    '.db',
    '.pyc',
    '.pyo',
    '.log',
    '.jpg',
    '.png',
    '.gif',
    '.ico',
    '.lnk',
    '.bak',
    'test_server.py.bak'
}

# 需要处理的文件扩展名
INCLUDE_EXTENSIONS = {
    '.py',
    '.html',
    '.md',
    '.txt',
    '.bat',
    '.ps1',
    '.conf',
    '.js',
    '.json',
    '.wxml',
    '.wxss',
    '.js'
}

def should_process_file(file_path):
    """判断是否应该处理该文件"""
    # 检查扩展名
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in INCLUDE_EXTENSIONS and ext:
        return False
    
    # 检查文件名
    filename = os.path.basename(file_path)
    for exclude in EXCLUDE_FILES:
        if exclude in filename:
            return False
    
    return True

def should_process_dir(dir_path):
    """判断是否应该处理该目录"""
    dir_name = os.path.basename(dir_path)
    return dir_name not in EXCLUDE_DIRS

def replace_in_file(file_path):
    """替换文件中的内容"""
    try:
        # 尝试以UTF-8读取
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含"萌宠绘"
        if '萌宠绘' not in content:
            return False
        
        # 替换
        new_content = content.replace('萌宠绘', 'AI自拍机-')
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    except UnicodeDecodeError:
        # 如果UTF-8失败，尝试其他编码
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
            if '萌宠绘' not in content:
                return False
            new_content = content.replace('萌宠绘', 'AI自拍机-')
            with open(file_path, 'w', encoding='gbk') as f:
                f.write(new_content)
            return True
        except:
            return False
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return False

def main():
    """主函数"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 60)
    print("开始批量替换'萌宠绘'为'AI自拍机-'")
    print("=" * 60)
    print()
    
    replaced_files = []
    
    # 遍历所有文件
    for root, dirs, files in os.walk(base_dir):
        # 过滤目录
        dirs[:] = [d for d in dirs if should_process_dir(os.path.join(root, d))]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, base_dir)
            
            if should_process_file(file_path):
                if replace_in_file(file_path):
                    replaced_files.append(rel_path)
                    print(f"✅ 已替换: {rel_path}")
    
    print()
    print("=" * 60)
    print(f"替换完成！共处理 {len(replaced_files)} 个文件")
    print("=" * 60)
    
    if replaced_files:
        print("\n已替换的文件列表:")
        for f in replaced_files:
            print(f"  - {f}")

if __name__ == "__main__":
    main()
