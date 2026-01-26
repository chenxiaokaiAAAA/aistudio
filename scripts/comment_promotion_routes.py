#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量注释推广管理相关路由的脚本
"""
import re

def comment_promotion_routes():
    """注释test_server.py中的推广管理路由"""
    file_path = 'test_server.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 需要注释的路由函数列表
    routes_to_comment = [
        (r'# 获取分佣记录列表\n@app\.route\([\'"]/api/admin/promotion/commissions[\'"].*?\n    \}\), 500\n\n# 获取推广用户列表', 
         r'# ⭐ 推广管理API已迁移到 app.routes.admin_promotion_api\n# 获取分佣记录列表\n# @app.route(\'/api/admin/promotion/commissions\', methods=[\'GET\'])\n# @login_required\n# def get_admin_commissions():'),
        (r'# 获取推广用户列表\n@app\.route\([\'"]/api/admin/promotion/users[\'"].*?\n    \}\), 500\n\n# 获取用户自己的订单',
         r'# ⭐ 推广管理API已迁移到 app.routes.admin_promotion_api\n# 获取推广用户列表\n# @app.route(\'/api/admin/promotion/users\', methods=[\'GET\'])\n# @login_required\n# def get_admin_promotion_users():'),
    ]
    
    # 由于代码复杂，我们采用更简单的方法：直接查找并注释整个函数块
    # 先标记需要注释的行范围
    
    lines = content.split('\n')
    new_lines = []
    in_promotion_route = False
    indent_level = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 检查是否是推广管理路由
        if re.match(r'^# 获取分佣记录列表|^# 获取推广用户列表|^# 获取用户自己的订单|^# 获取推广访问详细记录|^# 获取推广访问统计|^# 获取分佣详情|^# 更新分佣状态|^# 删除分佣记录|^# 删除推广用户', line):
            # 如果已经有注释标记，跳过
            if i > 0 and '⭐ 推广管理API已迁移' in lines[i-1]:
                new_lines.append(line)
                i += 1
                continue
            
            # 检查下一行是否是@app.route
            if i + 1 < len(lines) and '@app.route' in lines[i+1] and '/api/admin/promotion' in lines[i+1]:
                # 添加迁移注释
                new_lines.append('# ⭐ 推广管理API已迁移到 app.routes.admin_promotion_api')
                new_lines.append(line.replace('# ', '# # '))
                i += 1
                # 注释接下来的函数定义和函数体
                while i < len(lines):
                    current_line = lines[i]
                    # 如果是下一个路由的开始，停止注释
                    if current_line.strip() and not current_line.strip().startswith('#') and '@app.route' in current_line and '/api/admin/promotion' not in current_line:
                        break
                    if current_line.strip() and not current_line.strip().startswith('#') and current_line.strip().startswith('def ') and 'promotion' not in current_line.lower():
                        break
                    # 注释这一行
                    if current_line.strip() and not current_line.strip().startswith('#'):
                        new_lines.append('#' + current_line)
                    else:
                        new_lines.append(current_line)
                    i += 1
                continue
        
        new_lines.append(line)
        i += 1
    
    new_content = '\n'.join(new_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 推广管理路由已注释")

if __name__ == '__main__':
    comment_promotion_routes()
