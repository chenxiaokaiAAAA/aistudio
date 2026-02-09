#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复小程序中因清理console.log导致的孤立代码片段
"""
import os
import re
import sys

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def fix_orphaned_code(file_path):
    """修复文件中的孤立代码片段"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修复模式1: 孤立的 ); 行（前后都是空行或注释）
        # 匹配: 行首空白 + ); + 可选分号 + 行尾
        pattern1 = r'^\s+\)\s*;?\s*$'
        content = re.sub(pattern1, '', content, flags=re.MULTILINE)
        
        # 修复模式2: 以 : 开头的行（不完整的console.log）
        # 匹配: 行首空白 + : + 引号开头的字符串 + );
        pattern2 = r'^\s+:\s*[\'"][^\'"]*[\'"]\s*\);?\s*$'
        content = re.sub(pattern2, '', content, flags=re.MULTILINE)
        
        # 修复模式3: 不完整的表达式，如 || []).length);
        pattern3 = r'^\s+\|\|\s*\[\]\)\.length\)\s*;?\s*$'
        content = re.sub(pattern3, '', content, flags=re.MULTILINE)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"❌ 处理文件失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    miniprogram_dir = 'aistudio-小程序'
    
    if not os.path.exists(miniprogram_dir):
        print(f"❌ 目录不存在: {miniprogram_dir}")
        return
    
    fixed_count = 0
    total_count = 0
    
    # 遍历所有.js文件（排除备份文件）
    for root, dirs, files in os.walk(miniprogram_dir):
        # 跳过node_modules等目录
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git']]
        
        for file in files:
            if file.endswith('.js') and not file.endswith('.bak'):
                file_path = os.path.join(root, file)
                total_count += 1
                
                if fix_orphaned_code(file_path):
                    fixed_count += 1
                    print(f"✅ 已修复: {file_path}")
    
    print(f"\n📊 修复完成:")
    print(f"   总文件数: {total_count}")
    print(f"   修复文件数: {fixed_count}")

if __name__ == '__main__':
    main()
