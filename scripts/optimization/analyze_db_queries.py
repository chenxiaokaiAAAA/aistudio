# -*- coding: utf-8 -*-
"""
分析数据库查询优化点
1. 查找N+1查询问题
2. 查找缺少索引的字段
3. 查找可以优化的查询
"""
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_DIR = os.path.join(PROJECT_ROOT, 'app')

def find_n_plus_one_queries():
    """查找N+1查询问题"""
    n_plus_one_patterns = [
        # 在循环中使用query.get或query.filter
        (r'for\s+.*\s+in\s+.*\.(?:all|items|paginate)\(\):.*?query\.(?:get|filter)', re.DOTALL),
        # 在循环中访问关联对象（可能触发懒加载）
        (r'for\s+.*\s+in\s+.*:.*?\.(?:query\.get|\.filter_by)', re.DOTALL),
    ]
    
    issues = []
    
    for root, dirs, files in os.walk(APP_DIR):
        if '__pycache__' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')
                    
                    # 查找循环中的查询
                    in_loop = False
                    loop_start = 0
                    for i, line in enumerate(lines):
                        # 检测循环开始
                        if re.match(r'^\s*for\s+.*\s+in\s+.*:', line):
                            in_loop = True
                            loop_start = i
                        
                        # 在循环中查找查询
                        if in_loop:
                            if re.search(r'\.query\.(?:get|filter|filter_by)', line):
                                # 检查缩进，确保在循环内
                                if line.strip() and len(line) - len(line.lstrip()) > len(lines[loop_start]) - len(lines[loop_start].lstrip()):
                                    relative_path = filepath.replace(PROJECT_ROOT + os.sep, '')
                                    issues.append({
                                        'file': relative_path,
                                        'line': i + 1,
                                        'code': line.strip(),
                                        'type': 'N+1查询'
                                    })
                        
                        # 检测循环结束（通过缩进）
                        if in_loop and line.strip():
                            current_indent = len(line) - len(line.lstrip())
                            loop_indent = len(lines[loop_start]) - len(lines[loop_start].lstrip())
                            if current_indent <= loop_indent and not re.match(r'^\s*for\s+.*\s+in\s+.*:', line):
                                in_loop = False
                
                except Exception as e:
                    pass
    
    return issues

def find_missing_indexes():
    """查找可能缺少索引的字段"""
    # 常见需要索引的字段模式
    index_patterns = [
        r'order_id\s*=\s*db\.Column',  # 外键
        r'status\s*=\s*db\.Column',    # 状态字段
        r'created_at\s*=\s*db\.Column', # 时间字段
        r'order_number\s*=\s*db\.Column', # 订单号
        r'user_id\s*=\s*db\.Column',   # 用户ID
    ]
    
    # 读取models.py
    models_file = os.path.join(PROJECT_ROOT, 'app', 'models.py')
    if not os.path.exists(models_file):
        return []
    
    issues = []
    try:
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        for i, line in enumerate(lines):
            for pattern in index_patterns:
                if re.search(pattern, line):
                    # 检查是否已有索引
                    # 查看后续几行是否有Index定义
                    has_index = False
                    for j in range(i, min(i + 10, len(lines))):
                        if 'Index' in lines[j] or '__table_args__' in lines[j]:
                            has_index = True
                            break
                    
                    if not has_index:
                        issues.append({
                            'file': 'app/models.py',
                            'line': i + 1,
                            'field': re.search(r'(\w+)\s*=\s*db\.Column', line).group(1) if re.search(r'(\w+)\s*=\s*db\.Column', line) else 'unknown',
                            'type': '缺少索引'
                        })
    except:
        pass
    
    return issues

def main():
    """主函数"""
    print("分析数据库查询优化点...\n")
    
    # 查找N+1查询
    print("1. 查找N+1查询问题...")
    n_plus_one_issues = find_n_plus_one_queries()
    print(f"   找到 {len(n_plus_one_issues)} 个潜在N+1查询问题")
    for issue in n_plus_one_issues[:10]:
        print(f"   - {issue['file']}:{issue['line']} - {issue['code'][:50]}")
    if len(n_plus_one_issues) > 10:
        print(f"   ... 还有 {len(n_plus_one_issues) - 10} 个问题")
    
    # 查找缺少索引的字段
    print("\n2. 查找缺少索引的字段...")
    index_issues = find_missing_indexes()
    print(f"   找到 {len(index_issues)} 个可能缺少索引的字段")
    for issue in index_issues[:10]:
        print(f"   - {issue['file']}:{issue['line']} - {issue['field']}")
    if len(index_issues) > 10:
        print(f"   ... 还有 {len(index_issues) - 10} 个字段")
    
    print("\n分析完成!")

if __name__ == '__main__':
    main()
