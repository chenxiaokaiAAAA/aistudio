# -*- coding: utf-8 -*-
"""
安全地替换print语句为logging
逐文件处理，避免误替换
"""
import os
import re
import sys
import ast
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_DIR = os.path.join(PROJECT_ROOT, 'app')

# 排除的文件
EXCLUDE_FILES = ['test_server.py', '__init__.py']  # __init__.py需要手动处理

# 保护的关键字（不会被替换）
PROTECTED_KEYWORDS = ['Blueprint', 'register_blueprint', 'blueprint']

def determine_log_level(print_content):
    """根据print内容判断日志级别"""
    content_lower = print_content.lower()
    
    # 错误相关
    if any(keyword in content_lower for keyword in ['错误', 'error', '失败', 'fail', '异常', 'exception', '❌']):
        return 'error'
    
    # 警告相关
    if any(keyword in content_lower for keyword in ['警告', 'warning', '⚠️', '注意', '注意']):
        return 'warning'
    
    # 调试相关
    if any(keyword in content_lower for keyword in ['调试', 'debug', '测试', 'test']):
        return 'debug'
    
    # 默认info
    return 'info'

def replace_print_in_file(filepath):
    """替换单个文件中的print语句"""
    try:
        # 读取文件
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        modified = False
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 检查是否是print语句（排除注释和字符串中的print）
            # 匹配: print(...) 或 print (...
            print_match = re.match(r'^(\s*)print\s*\((.*)$', line.rstrip())
            
            if print_match and not line.strip().startswith('#'):
                indent = print_match.group(1)
                content = print_match.group(2)
                
                # 检查是否包含保护关键字
                if any(keyword in line for keyword in PROTECTED_KEYWORDS):
                    new_lines.append(line)
                    i += 1
                    continue
                
                # 收集完整的print语句（可能跨多行）
                full_content = content
                paren_count = content.count('(') - content.count(')')
                j = i + 1
                
                while paren_count > 0 and j < len(lines):
                    full_content += lines[j]
                    paren_count += lines[j].count('(') - lines[j].count(')')
                    j += 1
                
                # 提取print的内容（去掉括号）
                # 尝试解析print的参数
                try:
                    # 移除末尾的换行和可能的注释
                    full_line = ''.join(lines[i:j]).rstrip()
                    if '#' in full_line:
                        # 如果有注释，分离出来
                        comment_match = re.search(r'(\s*#.*)$', full_line)
                        comment = comment_match.group(1) if comment_match else ''
                        full_line = full_line[:full_line.index('#')] if '#' in full_line else full_line
                    else:
                        comment = ''
                    
                    # 提取括号内的内容
                    match = re.search(r'print\s*\((.*)\)', full_line, re.DOTALL)
                    if match:
                        print_args = match.group(1).strip()
                        
                        # 判断日志级别
                        log_level = determine_log_level(print_args)
                        
                        # 构建新的logger语句
                        # 处理f-string
                        if print_args.startswith('f"') or print_args.startswith("f'"):
                            new_statement = f"{indent}logger.{log_level}({print_args}){comment}\n"
                        else:
                            new_statement = f"{indent}logger.{log_level}({print_args}){comment}\n"
                        
                        new_lines.append(new_statement)
                        modified = True
                        i = j
                        continue
                except Exception as e:
                    # 如果解析失败，保持原样
                    print(f"Warning: Failed to parse print statement in {filepath}:{i+1}: {e}")
                    new_lines.append(line)
                    i += 1
                    continue
            else:
                new_lines.append(line)
                i += 1
        
        if modified:
            # 备份原文件
            backup_path = filepath + '.print.bak'
            shutil.copy2(filepath, backup_path)
            
            # 写入新内容
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            # 验证语法
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    ast.parse(f.read(), filename=filepath)
                return True, None
            except SyntaxError as e:
                # 恢复备份
                shutil.copy2(backup_path, filepath)
                return False, f"Syntax error: {e}"
        
        return modified, None
    
    except Exception as e:
        return False, str(e)

def main():
    """主函数"""
    print("开始安全替换print语句...\n")
    
    # 获取所有需要处理的文件
    files_to_process = []
    for root, dirs, files in os.walk(APP_DIR):
        if '__pycache__' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                filename = os.path.basename(filepath)
                
                if filename not in EXCLUDE_FILES:
                    # 检查是否包含print
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            if 'print(' in f.read():
                                files_to_process.append(filepath)
                    except:
                        pass
    
    print(f"找到 {len(files_to_process)} 个文件需要处理\n")
    
    success_count = 0
    error_count = 0
    modified_count = 0
    
    for filepath in files_to_process:
        relative_path = filepath.replace(PROJECT_ROOT + os.sep, '')
        modified, error = replace_print_in_file(filepath)
        
        if error:
            print(f"[ERROR] {relative_path}: {error}")
            error_count += 1
        elif modified:
            print(f"[OK] {relative_path}")
            modified_count += 1
            success_count += 1
        else:
            # 文件已处理但没有修改（可能已经被替换过）
            pass
    
    print(f"\n处理完成!")
    print(f"  成功: {success_count} 个文件")
    print(f"  修改: {modified_count} 个文件")
    print(f"  错误: {error_count} 个文件")
    print(f"\n所有原文件已备份为 .print.bak")

if __name__ == '__main__':
    main()
