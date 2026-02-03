# -*- coding: utf-8 -*-
"""最终版本：从V16备份提取并替换工作流函数代码"""
import re

# 文件路径
backup_file = r'e:\AI-STUDIO\aistudio -V16\app\routes\admin_styles_api.py'
target_file = 'app/routes/admin_styles_workflow_api.py'

# 读取V16备份文件
print('Reading backup file...')
with open(backup_file, 'r', encoding='utf-8') as f:
    backup_lines = f.readlines()

# 读取目标文件
print('Reading target file...')
with open(target_file, 'r', encoding='utf-8') as f:
    target_lines = f.readlines()

# 函数定义和行号范围（从V16备份）
functions_info = [
    {'name': 'test_workflow', 'start': 767, 'end': 1140},
    {'name': 'test_workflow_category', 'start': 1141, 'end': 1394},
    {'name': 'get_test_workflow_result', 'start': 1395, 'end': 1499},
    {'name': 'get_api_template', 'start': 1616, 'end': 1666},
    {'name': 'save_api_template', 'start': 1669, 'end': 1832},
    {'name': 'delete_api_template', 'start': 1835, 'end': 1869},
    {'name': 'test_api', 'start': 1870, 'end': 2155},
    {'name': 'test_api_comfyui', 'start': 2156, 'end': 2342},
    {'name': 'get_comfyui_task_status', 'start': 2343, 'end': 2495},
    {'name': 'upload_to_grsai', 'start': 2496, 'end': 2713},
    {'name': 'get_api_task_status', 'start': 2714, 'end': 2765}
]

# 提取所有函数代码
extracted_functions = {}
for func_info in functions_info:
    func_name = func_info['name']
    start = func_info['start'] - 1  # 转换为0-based索引
    end = func_info['end']
    
    # 提取函数代码（包括装饰器）
    func_lines = backup_lines[start:end]
    func_code = ''.join(func_lines)
    
    # 替换蓝图名称
    func_code = func_code.replace('@admin_styles_api_bp.route', '@admin_styles_workflow_bp.route')
    
    # 替换get_models()调用（如果需要）
    func_code = func_code.replace('models = get_models()', "models = get_models(['StyleCategory', 'StyleImage', 'AIConfig', 'User', 'Order', 'OrderImage', 'AITask', 'APITemplate', 'db'])")
    
    extracted_functions[func_name] = func_code
    print(f'Extracted: {func_name} ({len(func_lines)} lines)')

# 构建新的目标文件内容
new_target_lines = []
i = 0
while i < len(target_lines):
    line = target_lines[i]
    
    # 检查是否是函数定义行
    for func_name, func_code in extracted_functions.items():
        # 查找函数定义模式
        if re.match(rf'@admin_styles_workflow_bp\.route\([^)]+\)\s*', line) and i + 1 < len(target_lines):
            # 检查下一行是否是@login_required
            if i + 1 < len(target_lines) and '@login_required' in target_lines[i + 1]:
                # 检查函数名是否匹配
                if i + 2 < len(target_lines) and f'def {func_name}(' in target_lines[i + 2]:
                    print(f'Found function definition: {func_name} at line {i+1}')
                    
                    # 找到函数结束位置（下一个@admin_styles_workflow_bp.route或文件结尾）
                    func_start = i
                    func_end = i + 3  # 跳过装饰器和def行
                    
                    # 跳过TODO注释和pass
                    while func_end < len(target_lines):
                        if target_lines[func_end].strip() == 'pass':
                            func_end += 1
                            break
                        if '@admin_styles_workflow_bp.route' in target_lines[func_end]:
                            break
                        func_end += 1
                    
                    # 添加提取的函数代码
                    new_target_lines.append(func_code.rstrip() + '\n\n')
                    i = func_end
                    print(f'Replaced function: {func_name}')
                    break
    
    if i < len(target_lines):
        # 如果这一行没有被替换，保留原行
        if not any(f'def {func_name}(' in line and func_name in extracted_functions for func_name in extracted_functions.keys()):
            new_target_lines.append(line)
        i += 1

# 保存到目标文件
print('Writing to target file...')
with open(target_file, 'w', encoding='utf-8') as f:
    f.writelines(new_target_lines)

print('All functions extracted and replaced successfully!')
