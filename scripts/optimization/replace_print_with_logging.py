# -*- coding: utf-8 -*-
"""
批量替换print语句为logging
使用方法: python scripts/optimization/replace_print_with_logging.py
"""
import os
import re
import sys

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_DIR = os.path.join(PROJECT_ROOT, 'app')

# 需要处理的文件扩展名
PYTHON_EXTENSIONS = ['.py']

# 排除的目录和文件
EXCLUDE_DIRS = ['__pycache__', '.git', 'venv', 'env', 'node_modules']
EXCLUDE_FILES = ['test_server.py']  # test_server.py需要手动处理

# 保护的关键字（不会被替换）
PROTECTED_KEYWORDS = [
    'Blueprint',  # Flask Blueprint
    'register_blueprint',  # Flask register_blueprint
    'blueprint',  # 变量名可能包含blueprint
]

# print语句模式
PRINT_PATTERNS = [
    # print("...")
    (r'print\s*\(\s*"([^"]*)"\s*\)', r'logger.info("\1")'),
    (r"print\s*\(\s*'([^']*)'\s*\)", r"logger.info('\1')"),
    # print(f"...")
    (r'print\s*\(\s*f"([^"]*)"\s*\)', r'logger.info(f"\1")'),
    (r"print\s*\(\s*f'([^']*)'\s*\)", r"logger.info(f'\1')"),
    # print(...)
    (r'print\s*\(\s*([^)]+)\s*\)', r'logger.info(\1)'),
]

# 错误和警告模式
ERROR_PATTERNS = [
    (r'print\s*\(\s*[f]?"❌\s*([^"]*)"\s*\)', r'logger.error("\1")'),
    (r"print\s*\(\s*[f]?'❌\s*([^']*)'\s*\)", r"logger.error('\1')"),
    (r'print\s*\(\s*[f]?"⚠️\s*([^"]*)"\s*\)', r'logger.warning("\1")'),
    (r"print\s*\(\s*[f]?'⚠️\s*([^']*)'\s*\)", r"logger.warning('\1')"),
]


def should_process_file(filepath):
    """判断是否应该处理该文件"""
    # 检查扩展名
    if not any(filepath.endswith(ext) for ext in PYTHON_EXTENSIONS):
        return False
    
    # 检查排除的文件
    filename = os.path.basename(filepath)
    if filename in EXCLUDE_FILES:
        return False
    
    # 检查排除的目录
    for exclude_dir in EXCLUDE_DIRS:
        if exclude_dir in filepath:
            return False
    
    return True


def add_logger_import(content):
    """在文件开头添加logger导入"""
    # 检查是否已有logger导入
    if 'logger = logging.getLogger' in content or 'from app.utils.logger_config import' in content:
        return content
    
    # 查找import语句的位置
    import_pattern = r'(^import\s+logging|^from\s+logging\s+import)'
    if re.search(import_pattern, content, re.MULTILINE):
        # 如果已有logging导入，添加logger定义
        if 'logger = logging.getLogger(__name__)' not in content:
            # 在第一个import后添加logger定义
            content = re.sub(
                r'(^import\s+logging)',
                r'\1\nlogger = logging.getLogger(__name__)',
                content,
                count=1,
                flags=re.MULTILINE
            )
    else:
        # 如果没有logging导入，添加import和logger定义
        # 查找第一个import语句
        first_import = re.search(r'^(import|from)', content, re.MULTILINE)
        if first_import:
            insert_pos = first_import.start()
            # 在第一个import前插入
            content = content[:insert_pos] + 'import logging\nlogger = logging.getLogger(__name__)\n' + content[insert_pos:]
        else:
            # 如果没有import，在文件开头添加
            content = 'import logging\nlogger = logging.getLogger(__name__)\n\n' + content
    
    return content


def replace_print_statements(content):
    """替换print语句为logging"""
    modified = False
    
    # 检查是否包含保护的关键字，如果包含则跳过替换
    for keyword in PROTECTED_KEYWORDS:
        if keyword in content:
            # 只替换不包含保护关键字的print语句
            pass
    
    # 先处理错误和警告
    for pattern, replacement in ERROR_PATTERNS:
        # 检查替换后是否会影响保护的关键字
        matches = re.finditer(pattern, content)
        for match in matches:
            # 检查匹配的上下文是否包含保护关键字
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end]
            
            # 如果上下文包含保护关键字，跳过
            if any(keyword in context for keyword in PROTECTED_KEYWORDS):
                continue
            
            # 执行替换
            new_content = content[:match.start()] + replacement + content[match.end():]
            if new_content != content:
                content = new_content
                modified = True
    
    # 再处理普通print（更保守的替换）
    # 只替换简单的print语句，避免误替换
    simple_print_pattern = r'^(\s*)print\s*\(\s*(["\'])(.*?)\2\s*\)\s*$'
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        match = re.match(simple_print_pattern, line)
        if match:
            indent = match.group(1)
            quote = match.group(2)
            message = match.group(3)
            # 检查是否包含保护关键字
            if not any(keyword in line for keyword in PROTECTED_KEYWORDS):
                new_line = f"{indent}logger.info({quote}{message}{quote})"
                new_lines.append(new_line)
                modified = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    if modified:
        content = '\n'.join(new_lines)
    
    return content, modified


def process_file(filepath):
    """处理单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 添加logger导入
        content = add_logger_import(content)
        
        # 替换print语句
        content, modified = replace_print_statements(content)
        
        if content != original_content:
            # 备份原文件
            backup_path = filepath + '.bak'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # 写入新内容
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, modified
        
        return False, False
    
    except Exception as e:
        print(f"处理文件 {filepath} 失败: {e}")
        return False, False


def main():
    """主函数"""
    print("开始批量替换print语句为logging...")
    print(f"项目目录: {PROJECT_ROOT}")
    print(f"应用目录: {APP_DIR}")
    
    processed_count = 0
    modified_count = 0
    
    # 遍历app目录
    for root, dirs, files in os.walk(APP_DIR):
        # 过滤排除的目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            filepath = os.path.join(root, file)
            
            if should_process_file(filepath):
                processed, modified = process_file(filepath)
                processed_count += 1
                if modified:
                    modified_count += 1
                    print(f"✅ 已修改: {filepath}")
    
    print(f"\n处理完成!")
    print(f"处理文件数: {processed_count}")
    print(f"修改文件数: {modified_count}")
    print(f"\n注意: 所有原文件已备份为 .bak 文件")


if __name__ == '__main__':
    main()
