# -*- coding: utf-8 -*-
"""
数据库索引优化脚本
分析常用查询字段并添加索引
"""
import os
import sys
import re
from pathlib import Path
from datetime import datetime

# 设置项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def analyze_query_patterns():
    """分析代码中的查询模式，找出常用查询字段"""
    routes_dir = project_root / 'app' / 'routes'
    
    # 统计查询模式
    query_patterns = {}
    
    for py_file in routes_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找 filter_by 和 filter 中的字段
            # 模式1: Model.query.filter_by(field=value)
            pattern1 = r'(\w+)\.query\.filter_by\(([^)]+)\)'
            matches1 = re.finditer(pattern1, content)
            for match in matches1:
                model_name = match.group(1)
                filters = match.group(2)
                # 提取字段名
                field_matches = re.findall(r'(\w+)\s*=', filters)
                for field in field_matches:
                    key = f"{model_name}.{field}"
                    query_patterns[key] = query_patterns.get(key, 0) + 1
            
            # 模式2: Model.query.filter(Model.field == value)
            pattern2 = r'(\w+)\.query\.filter\((\w+)\.(\w+)\s*[=!<>]'
            matches2 = re.finditer(pattern2, content)
            for match in matches2:
                model_name = match.group(1)
                field = match.group(3)
                key = f"{model_name}.{field}"
                query_patterns[key] = query_patterns.get(key, 0) + 1
            
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return query_patterns

def get_recommended_indexes():
    """获取推荐的索引配置"""
    # 基于代码分析和最佳实践
    recommended_indexes = {
        'Order': [
            ('order_number', '订单号查询'),
            ('status', '订单状态查询'),
            ('created_at', '创建时间排序'),
            ('franchisee_id', '加盟商订单查询'),
            ('merchant_id', '商户订单查询'),
            ('openid', '用户订单查询'),
            ('customer_phone', '客户电话查询'),
            ('completed_at', '完成时间查询'),
            ('source_type', '来源类型查询'),
            ('order_mode', '订单模式查询'),
        ],
        'AITask': [
            ('order_id', '订单关联查询'),
            ('status', '任务状态查询'),
            ('created_at', '创建时间排序'),
            ('order_number', '订单号查询'),
            ('style_category_id', '风格分类查询'),
            ('style_image_id', '风格图片查询'),
            ('completed_at', '完成时间查询'),
        ],
        'OrderImage': [
            ('order_id', '订单图片查询'),
            ('is_main', '主图查询'),
        ],
        'Product': [
            ('is_active', '激活产品查询'),
            ('category_id', '分类查询'),
            ('subcategory_id', '子分类查询'),
            ('sort_order', '排序查询'),
        ],
        'ProductSize': [
            ('product_id', '产品尺寸查询'),
            ('is_active', '激活尺寸查询'),
        ],
        'ProductImage': [
            ('product_id', '产品图片查询'),
            ('is_active', '激活图片查询'),
        ],
        'ProductStyleCategory': [
            ('product_id', '产品风格绑定查询'),
            ('style_category_id', '风格分类绑定查询'),
        ],
        'StyleCategory': [
            ('is_active', '激活风格查询'),
            ('sort_order', '排序查询'),
        ],
        'StyleImage': [
            ('category_id', '风格分类图片查询'),
            ('is_active', '激活图片查询'),
        ],
        'FranchiseeAccount': [
            ('status', '账户状态查询'),
            ('username', '用户名查询'),
            ('qr_code', '二维码查询'),
        ],
        'FranchiseeRecharge': [
            ('franchisee_id', '加盟商充值记录查询'),
            ('created_at', '创建时间排序'),
        ],
        'ShopOrder': [
            ('order_number', '订单号查询'),
            ('original_order_id', '原始订单查询'),
            ('original_order_number', '原始订单号查询'),
            ('status', '订单状态查询'),
            ('product_id', '产品查询'),
        ],
        'ShopProduct': [
            ('is_active', '激活产品查询'),
            ('sort_order', '排序查询'),
        ],
        'ShopProductSize': [
            ('product_id', '产品尺寸查询'),
            ('is_active', '激活尺寸查询'),
        ],
        'ShopProductImage': [
            ('product_id', '产品图片查询'),
            ('is_active', '激活图片查询'),
        ],
        'Coupon': [
            ('status', '优惠券状态查询'),
            ('source_type', '来源类型查询'),
        ],
        'UserCoupon': [
            ('user_id', '用户优惠券查询'),
            ('coupon_id', '优惠券查询'),
            ('status', '状态查询'),
        ],
        'PromotionUser': [
            ('promotion_code', '推广码查询'),
            ('open_id', '用户查询'),
            ('user_id', '用户ID查询'),
        ],
        'Commission': [
            ('user_id', '用户佣金查询'),
            ('order_id', '订单佣金查询'),
            ('status', '状态查询'),
        ],
        'UserVisit': [
            ('user_id', '用户访问查询'),
            ('visit_time', '访问时间查询'),
            ('is_authorized', '授权状态查询'),
        ],
        'SelfieMachine': [
            ('franchisee_id', '加盟商设备查询'),
            ('machine_serial_number', '设备序列号查询'),
        ],
    }
    
    return recommended_indexes

def check_existing_indexes():
    """检查现有索引"""
    models_file = project_root / 'app' / 'models.py'
    
    existing_indexes = {}
    
    try:
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找 __table_args__ 中的索引
        pattern = r'class\s+(\w+).*?__table_args__\s*=\s*\((.*?)\)'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            model_name = match.group(1)
            table_args = match.group(2)
            
            # 提取索引
            index_pattern = r'db\.Index\([^,]+,\s*[\'"](\w+)[\'"]'
            indexes = re.findall(index_pattern, table_args)
            existing_indexes[model_name] = indexes
            
    except Exception as e:
        print(f"Error reading models.py: {e}")
    
    return existing_indexes

def generate_index_sql():
    """生成索引SQL语句"""
    recommended = get_recommended_indexes()
    existing = check_existing_indexes()
    
    sql_statements = []
    
    for model_name, indexes in recommended.items():
        existing_indexes = existing.get(model_name, [])
        
        for field, description in indexes:
            # 检查索引是否已存在
            if field in existing_indexes:
                continue
            
            # 生成索引名
            index_name = f'idx_{model_name.lower()}_{field}'
            
            # 获取表名（通常是模型名的小写复数形式）
            table_name = model_name.lower()
            if table_name == 'order':
                table_name = 'orders'
            elif table_name == 'user':
                table_name = 'user'
            elif table_name.endswith('y'):
                table_name = table_name[:-1] + 'ies'
            elif not table_name.endswith('s'):
                table_name = table_name + 's'
            
            # 生成SQL（PostgreSQL语法）
            sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({field}); -- {description}"
            sql_statements.append(sql)
    
    return sql_statements

if __name__ == '__main__':
    print("=" * 80)
    print("数据库索引优化分析")
    print("=" * 80)
    
    # 分析查询模式
    print("\n1. 分析代码中的查询模式...")
    query_patterns = analyze_query_patterns()
    
    # 显示最常用的查询字段
    print(f"\n找到 {len(query_patterns)} 个查询模式")
    print("\n最常用的查询字段（前20个）：")
    sorted_patterns = sorted(query_patterns.items(), key=lambda x: x[1], reverse=True)
    for pattern, count in sorted_patterns[:20]:
        print(f"  {pattern}: {count} 次")
    
    # 检查现有索引
    print("\n2. 检查现有索引...")
    existing_indexes = check_existing_indexes()
    print(f"\n已存在的索引：")
    for model, indexes in existing_indexes.items():
        if indexes:
            print(f"  {model}: {', '.join(indexes)}")
    
    # 生成推荐的索引SQL
    print("\n3. 生成推荐的索引SQL...")
    sql_statements = generate_index_sql()
    
    if sql_statements:
        print(f"\n建议添加 {len(sql_statements)} 个索引：")
        print("\nSQL语句：")
        print("-" * 80)
        for sql in sql_statements:
            print(sql)
        print("-" * 80)
        
        # 保存到文件
        output_file = project_root / 'scripts' / 'optimization' / 'database_indexes.sql'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("-- 数据库索引优化SQL\n")
            f.write("-- 生成时间: " + str(datetime.now()) + "\n")
            f.write("-- 说明: 这些索引用于优化常用查询字段的性能\n\n")
            for sql in sql_statements:
                f.write(sql + "\n")
        
        print(f"\nSQL语句已保存到: {output_file}")
    else:
        print("\n✅ 所有推荐的索引都已存在！")
    
    print("\n" + "=" * 80)
