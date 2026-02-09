# -*- coding: utf-8 -*-
"""
修复N+1查询问题的脚本
生成优化建议和代码修改
"""
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_ai_tasks_api():
    """分析ai_tasks_api.py中的N+1查询问题"""
    filepath = os.path.join(PROJECT_ROOT, 'app', 'routes', 'ai_tasks_api.py')
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # 查找问题代码段（第82-93行）
    issue_start = 80
    issue_end = 95
    
    print("=" * 80)
    print("N+1查询问题分析：app/routes/ai_tasks_api.py")
    print("=" * 80)
    print("\n问题代码（第82-93行）：")
    for i in range(issue_start, min(issue_end, len(lines))):
        print(f"{i+1:4d} | {lines[i]}")
    
    print("\n问题说明：")
    print("  在循环中对每个task都执行了两次查询：")
    print("  - StyleCategory.query.get(task.style_category_id)")
    print("  - StyleImage.query.get(task.style_image_id)")
    print("  如果有100个任务，就会执行200次额外查询！")
    
    print("\n优化方案：")
    print("  使用joinedload或subqueryload预加载关联数据")
    print("  或者使用join查询一次性获取所有数据")
    
    return {
        'file': filepath,
        'issue_lines': list(range(issue_start, issue_end)),
        'solution': '使用joinedload预加载'
    }

def generate_optimized_code():
    """生成优化后的代码"""
    optimized_code = '''
# 优化方案1：使用joinedload预加载（推荐）
from sqlalchemy.orm import joinedload

# 在查询时预加载关联数据
query = AITask.query.options(
    joinedload(AITask.style_category),
    joinedload(AITask.style_image)
)

# 然后在循环中直接访问，不会触发额外查询
for task in pagination.items:
    style_category_name = task.style_category.name if task.style_category else None
    style_image_name = task.style_image.name if task.style_image else None

# 优化方案2：使用join查询（如果只需要名称）
from sqlalchemy import func

query = AITask.query.join(
    StyleCategory, AITask.style_category_id == StyleCategory.id, isouter=True
).join(
    StyleImage, AITask.style_image_id == StyleImage.id, isouter=True
).with_entities(
    AITask,
    StyleCategory.name.label('style_category_name'),
    StyleImage.name.label('style_image_name')
)

# 然后在循环中访问
for task, category_name, image_name in pagination.items:
    style_category_name = category_name
    style_image_name = image_name
'''
    return optimized_code

def main():
    """主函数"""
    print("分析N+1查询问题...\n")
    
    issue = analyze_ai_tasks_api()
    if issue:
        print("\n" + "=" * 80)
        print("优化代码示例：")
        print("=" * 80)
        print(generate_optimized_code())
    
    print("\n分析完成！")

if __name__ == '__main__':
    main()
