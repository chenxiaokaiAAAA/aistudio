# -*- coding: utf-8 -*-
"""
修复Bluelogger错误 - 将Bluelogger替换回Blueprint
"""
import os
import re
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_DIR = os.path.join(PROJECT_ROOT, 'app')

def fix_file(filepath):
    """修复单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 替换 Bluelogger.info 为 Blueprint
        content = re.sub(r'Bluelogger\.info\(', 'Blueprint(', content)
        
        # 替换 register_bluelogger.info 为 register_blueprint
        content = re.sub(r'\.register_bluelogger\.info\(', '.register_blueprint(', content)
        
        if content != original_content:
            # 备份
            backup_path = filepath + '.bluelogger.bak'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # 写入修复后的内容
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        
        return False
    
    except Exception as e:
        print(f"修复文件 {filepath} 失败: {e}")
        return False

def main():
    """主函数"""
    print("开始修复Bluelogger错误...")
    
    fixed_count = 0
    
    # 遍历app/routes目录
    for root, dirs, files in os.walk(APP_DIR):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    fixed_count += 1
                    print(f"[OK] Fixed: {filepath}")
    
    # 修复app/__init__.py
    init_file = os.path.join(PROJECT_ROOT, 'app', '__init__.py')
    if os.path.exists(init_file):
        if fix_file(init_file):
            fixed_count += 1
            print(f"✅ 已修复: {init_file}")
    
    print(f"\nFixed {fixed_count} files")
    print("All original files backed up as .bluelogger.bak")

if __name__ == '__main__':
    main()
