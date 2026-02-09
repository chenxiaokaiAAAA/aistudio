# -*- coding: utf-8 -*-
"""
清理小程序中的console语句
策略：
- console.log: 删除（可配置保留关键文件）
- console.error: 保留（或替换为统一错误处理）
- console.warn: 保留
"""
import os
import re
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MINIPROGRAM_DIR = os.path.join(PROJECT_ROOT, 'aistudio-小程序')

# 需要保留console.log的文件（关键业务逻辑）
KEEP_CONSOLE_LOG_FILES = [
    'app.js',  # 主入口，可能需要保留一些关键日志
    'utils/api.js',  # API工具，错误处理可能需要
]

# 清理模式
CLEAN_MODE = {
    'log': 'delete',  # delete: 删除, comment: 注释, keep: 保留
    'error': 'keep',  # 保留错误日志
    'warn': 'keep',   # 保留警告日志
}

def clean_console_in_file(filepath, mode='safe'):
    """清理文件中的console语句"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        filename = os.path.basename(filepath)
        relative_path = filepath.replace(PROJECT_ROOT + os.sep, '')
        
        # 检查是否需要保留console.log
        keep_log = any(keep_file in relative_path for keep_file in KEEP_CONSOLE_LOG_FILES)
        
        modified = False
        new_lines = []
        stats = {'log_deleted': 0, 'log_commented': 0, 'error_kept': 0, 'warn_kept': 0}
        
        for i, line in enumerate(lines):
            original_line = line
            
            # 匹配console.log
            log_match = re.match(r'^(\s*)(console\.log\s*\([^)]*\)\s*;?\s*)(.*)$', line)
            if log_match:
                indent = log_match.group(1)
                console_stmt = log_match.group(2)
                comment = log_match.group(3)
                
                if keep_log and CLEAN_MODE['log'] == 'delete':
                    # 关键文件，只删除明显的调试语句
                    # 检查是否包含调试关键词
                    if any(keyword in console_stmt.lower() for keyword in ['debug', 'test', '临时', '测试']):
                        if CLEAN_MODE['log'] == 'comment':
                            new_lines.append(f"{indent}// {console_stmt}{comment}\n")
                            stats['log_commented'] += 1
                            modified = True
                        else:
                            # 删除
                            stats['log_deleted'] += 1
                            modified = True
                            if comment.strip():
                                new_lines.append(f"{indent}{comment}\n")
                            continue
                    else:
                        # 保留业务日志
                        new_lines.append(line)
                        continue
                else:
                    # 非关键文件，根据模式处理
                    if CLEAN_MODE['log'] == 'comment':
                        new_lines.append(f"{indent}// {console_stmt}{comment}\n")
                        stats['log_commented'] += 1
                        modified = True
                    elif CLEAN_MODE['log'] == 'delete':
                        stats['log_deleted'] += 1
                        modified = True
                        if comment.strip():
                            new_lines.append(f"{indent}{comment}\n")
                        continue
                    else:
                        new_lines.append(line)
                        continue
            
            # 匹配console.error（保留）
            error_match = re.match(r'^(\s*)(console\.error\s*\([^)]*\)\s*;?\s*)(.*)$', line)
            if error_match:
                stats['error_kept'] += 1
                new_lines.append(line)
                continue
            
            # 匹配console.warn（保留）
            warn_match = re.match(r'^(\s*)(console\.warn\s*\([^)]*\)\s*;?\s*)(.*)$', line)
            if warn_match:
                stats['warn_kept'] += 1
                new_lines.append(line)
                continue
            
            # 其他行保持不变
            new_lines.append(line)
        
        if modified:
            # 备份
            backup_path = filepath + '.console.bak'
            shutil.copy2(filepath, backup_path)
            
            # 写入新内容
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            return True, stats, None
        
        return False, stats, None
    
    except Exception as e:
        return False, {}, str(e)

def main():
    """主函数"""
    print("开始清理小程序console语句...\n")
    print(f"清理模式:")
    print(f"  console.log: {CLEAN_MODE['log']}")
    print(f"  console.error: {CLEAN_MODE['error']}")
    print(f"  console.warn: {CLEAN_MODE['warn']}")
    print(f"\n保留console.log的文件: {', '.join(KEEP_CONSOLE_LOG_FILES)}\n")
    
    # 查找所有需要处理的文件
    files_to_process = []
    for root, dirs, files in os.walk(MINIPROGRAM_DIR):
        if 'node_modules' in root:
            continue
        
        for file in files:
            if file.endswith(('.js', '.wxs')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        if 'console.' in f.read():
                            files_to_process.append(filepath)
                except:
                    pass
    
    print(f"找到 {len(files_to_process)} 个文件需要处理\n")
    
    total_stats = {
        'log_deleted': 0,
        'log_commented': 0,
        'error_kept': 0,
        'warn_kept': 0
    }
    
    success_count = 0
    error_count = 0
    modified_count = 0
    
    for filepath in files_to_process:
        relative_path = filepath.replace(PROJECT_ROOT + os.sep, '')
        modified, stats, error = clean_console_in_file(filepath)
        
        if error:
            print(f"[ERROR] {relative_path}: {error}")
            error_count += 1
        elif modified:
            print(f"[OK] {relative_path}: 删除{stats['log_deleted']}个log, 注释{stats['log_commented']}个log")
            modified_count += 1
            success_count += 1
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
        else:
            # 文件已处理但没有修改
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
    
    print(f"\n清理完成!")
    print(f"  处理文件: {len(files_to_process)} 个")
    print(f"  修改文件: {modified_count} 个")
    print(f"  成功: {success_count} 个")
    print(f"  错误: {error_count} 个")
    print(f"\n统计:")
    print(f"  删除console.log: {total_stats['log_deleted']} 处")
    print(f"  注释console.log: {total_stats['log_commented']} 处")
    print(f"  保留console.error: {total_stats['error_kept']} 处")
    print(f"  保留console.warn: {total_stats['warn_kept']} 处")
    print(f"\n备份文件: .console.bak")

if __name__ == '__main__':
    main()
