# -*- coding: utf-8 -*-
"""
最终版本：安全替换print语句为logging
只替换真正的print语句，排除Blueprint等关键字
"""
import os
import re
import shutil
import ast

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_DIR = os.path.join(PROJECT_ROOT, 'app')

EXCLUDE_FILES = ['test_server.py']

def determine_log_level(content):
    """根据内容判断日志级别"""
    content_lower = content.lower()
    if any(kw in content_lower for kw in ['错误', 'error', '失败', 'fail', '异常', 'exception', '❌']):
        return 'error'
    if any(kw in content_lower for kw in ['警告', 'warning', '⚠️', '注意']):
        return 'warning'
    if any(kw in content_lower for kw in ['调试', 'debug']):
        return 'debug'
    return 'info'

def replace_print_statements(filepath):
    """替换文件中的print语句"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        modified = False
        
        # 匹配真正的print语句（排除Blueprint等）
        # 模式：行首空白 + print + 空白 + (
        # 但排除：Blueprint, register_blueprint等
        pattern = r'^(\s+)print\s*\((.*?)\)'
        
        def replace_match(match):
            nonlocal modified
            indent = match.group(1)
            args = match.group(2)
            
            # 检查是否是保护的关键字（如Blueprint）
            full_line = match.group(0)
            if 'Blueprint' in full_line or 'register_blueprint' in full_line:
                return full_line
            
            # 判断日志级别
            log_level = determine_log_level(args)
            
            # 构建新的logger语句
            new_line = f"{indent}logger.{log_level}({args})"
            modified = True
            return new_line
        
        # 逐行处理（更安全）
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            # 检查是否是print语句
            # 排除注释行
            stripped = line.lstrip()
            if stripped.startswith('#'):
                new_lines.append(line)
                continue
            
            # 匹配 print(...) 但排除 Blueprint 等
            match = re.match(r'^(\s+)print\s*\((.*?)\)\s*(#.*)?$', line)
            if match and 'Blueprint' not in line and 'register_blueprint' not in line:
                indent = match.group(1)
                args = match.group(2)
                comment = match.group(3) or ''
                
                log_level = determine_log_level(args)
                new_line = f"{indent}logger.{log_level}({args}){comment}"
                new_lines.append(new_line)
                modified = True
            else:
                new_lines.append(line)
        
        if modified:
            new_content = '\n'.join(new_lines)
            
            # 备份
            backup = filepath + '.print.bak'
            shutil.copy2(filepath, backup)
            
            # 验证语法
            try:
                ast.parse(new_content, filename=filepath)
            except SyntaxError as e:
                # 恢复备份
                shutil.copy2(backup, filepath)
                return False, f"Syntax error: {e}"
            
            # 写入新内容
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True, None
        
        return False, None
    
    except Exception as e:
        return False, str(e)

def main():
    """主函数"""
    print("开始替换print语句...\n")
    
    # 查找所有包含print的文件
    files_to_process = []
    for root, dirs, files in os.walk(APP_DIR):
        if '__pycache__' in root:
            continue
        
        for file in files:
            if file.endswith('.py') and file not in EXCLUDE_FILES:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # 检查是否有真正的print语句（排除Blueprint）
                        if re.search(r'^\s+print\s*\(', content, re.MULTILINE) and 'Blueprint' not in content[:500]:
                            files_to_process.append(filepath)
                except:
                    pass
    
    print(f"找到 {len(files_to_process)} 个文件需要处理\n")
    
    success = 0
    errors = 0
    modified = 0
    
    for filepath in files_to_process:
        rel_path = filepath.replace(PROJECT_ROOT + os.sep, '')
        result, error = replace_print_statements(filepath)
        
        if error:
            print(f"[ERROR] {rel_path}: {error}")
            errors += 1
        elif result:
            print(f"[OK] {rel_path}")
            modified += 1
            success += 1
    
    print(f"\n完成!")
    print(f"  成功: {success} 个文件")
    print(f"  修改: {modified} 个文件")
    print(f"  错误: {errors} 个文件")
    print(f"\n备份文件: .print.bak")

if __name__ == '__main__':
    main()
