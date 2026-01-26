#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从服务器数据库同步本地缺失的订单数据
"""

import sqlite3
import sys

if sys.platform == 'win32':
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

SOURCE_DB = 'instance/服务器pet_painting.db'
TARGET_DB = 'instance/pet_painting.db'

def get_table_columns(conn, table_name):
    """获取表的列信息"""
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info("{table_name}")')
    columns = cursor.fetchall()
    return [col[1] for col in columns]

def sync_missing_orders():
    """同步缺失的订单"""
    source_conn = sqlite3.connect(SOURCE_DB)
    target_conn = sqlite3.connect(TARGET_DB)
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    # 获取本地已有的订单号
    target_cursor.execute('SELECT order_number FROM "order"')
    existing_order_numbers = {row[0] for row in target_cursor.fetchall()}
    
    print(f"本地已有订单: {len(existing_order_numbers)} 个")
    
    # 获取服务器数据库中的所有订单
    source_cursor.execute('SELECT * FROM "order"')
    source_columns = [description[0] for description in source_cursor.description]
    
    # 获取目标表的列
    target_columns = get_table_columns(target_conn, 'order')
    # 排除id列，让数据库自动生成
    common_columns = [col for col in source_columns if col in target_columns and col != 'id']
    
    print(f"共同列: {len(common_columns)} 个（排除id列）")
    
    # 查找缺失的订单
    missing_orders = []
    all_orders = source_cursor.fetchall()
    
    for order_row in all_orders:
        order_dict = dict(zip(source_columns, order_row))
        order_number = order_dict.get('order_number')
        
        if order_number and order_number not in existing_order_numbers:
            missing_orders.append((order_dict, order_row))
    
    print(f"发现缺失的订单: {len(missing_orders)} 个")
    print()
    
    if not missing_orders:
        print("没有需要同步的订单")
        source_conn.close()
        target_conn.close()
        return
    
    # 显示缺失的订单信息
    print("缺失的订单列表:")
    print("-" * 80)
    for order_dict, _ in missing_orders[:20]:  # 只显示前20个
        print(f"  #{order_dict.get('id')} {order_dict.get('order_number')} - {order_dict.get('customer_name')} - {order_dict.get('created_at')} - 来源: {order_dict.get('source_type')} - 加盟商ID: {order_dict.get('franchisee_id')}")
    if len(missing_orders) > 20:
        print(f"  ... 还有 {len(missing_orders) - 20} 个订单")
    print()
    
    # 同步订单
    columns_str = ", ".join([f'"{col}"' for col in common_columns])
    placeholders = ", ".join(["?" for _ in common_columns])
    
    inserted_count = 0
    for order_dict, order_row in missing_orders:
        # 构建要插入的数据（只包含共同列，排除id）
        values = [order_dict.get(col) for col in common_columns]
        
        try:
            # 使用 INSERT OR REPLACE，如果订单号已存在则更新
            target_cursor.execute(
                f'INSERT OR REPLACE INTO "order" ({columns_str}) VALUES ({placeholders})',
                values
            )
            inserted_count += 1
            print(f"  已同步订单: {order_dict.get('order_number')} - {order_dict.get('customer_name')}")
        except Exception as e:
            print(f"插入订单失败 {order_dict.get('order_number')}: {str(e)}")
    
    target_conn.commit()
    print(f"已插入 {inserted_count} 个订单")
    print()
    
    # 同步订单图片
    if inserted_count > 0:
        print("同步订单图片...")
        print("-" * 80)
        
        # 获取新插入的订单ID映射（通过订单号）
        inserted_order_numbers = {order_dict.get('order_number') for order_dict, _ in missing_orders}
        
        # 获取服务器中这些订单的图片
        placeholders = ','.join(['?' for _ in inserted_order_numbers])
        source_cursor.execute(f'''
            SELECT oi.* FROM order_image oi
            INNER JOIN "order" o ON oi.order_id = o.id
            WHERE o.order_number IN ({placeholders})
        ''', list(inserted_order_numbers))
        
        order_images = source_cursor.fetchall()
        source_image_columns = [description[0] for description in source_cursor.description]
        
        # 获取目标表的列
        target_image_columns = get_table_columns(target_conn, 'order_image')
        # 排除id列
        common_image_columns = [col for col in source_image_columns if col in target_image_columns and col != 'id']
        
        print(f"找到 {len(order_images)} 条订单图片记录")
        print(f"共同列: {len(common_image_columns)} 个（排除id列）")
        
        if order_images:
            # 需要更新order_id，因为本地数据库的订单ID可能不同
            # 先获取订单号到ID的映射
            target_cursor.execute('SELECT id, order_number FROM "order" WHERE order_number IN ({})'.format(
                ','.join(['?' for _ in inserted_order_numbers])
            ), list(inserted_order_numbers))
            order_number_to_id = {row[1]: row[0] for row in target_cursor.fetchall()}
            
            image_columns_str = ", ".join([f'"{col}"' for col in common_image_columns])
            image_placeholders = ", ".join(["?" for _ in common_image_columns])
            
            image_inserted = 0
            for image_row in order_images:
                image_dict = dict(zip(source_image_columns, image_row))
                
                # 获取对应的订单号
                source_order_id = image_dict.get('order_id')
                source_cursor.execute('SELECT order_number FROM "order" WHERE id = ?', (source_order_id,))
                source_order_result = source_cursor.fetchone()
                
                if source_order_result:
                    source_order_number = source_order_result[0]
                    target_order_id = order_number_to_id.get(source_order_number)
                    
                    if target_order_id:
                        # 更新order_id
                        image_dict['order_id'] = target_order_id
                        values = [image_dict.get(col) for col in common_image_columns]
                        
                        try:
                            target_cursor.execute(
                                f'INSERT INTO order_image ({image_columns_str}) VALUES ({image_placeholders})',
                                values
                            )
                            image_inserted += 1
                        except Exception as e:
                            print(f"插入图片失败: {str(e)}")
            
            target_conn.commit()
            print(f"已插入 {image_inserted} 条订单图片记录")
    
    print()
    print("=" * 80)
    print("同步完成！")
    print("=" * 80)
    
    source_conn.close()
    target_conn.close()

if __name__ == '__main__':
    sync_missing_orders()

