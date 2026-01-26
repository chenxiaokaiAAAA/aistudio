import sqlite3

def add_default_sizes():
    """为ProductSize表添加默认尺寸数据"""
    
    conn = sqlite3.connect('pet_painting.db')
    cursor = conn.cursor()
    
    # 检查是否已有数据
    cursor.execute('SELECT COUNT(*) FROM product_sizes')
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("添加默认尺寸数据...")
        
        # 添加默认尺寸
        default_sizes = [
            ('small', '小型 (30x40cm)', 50.0, 1),
            ('medium', '中型 (40x50cm)', 80.0, 2),
            ('large', '大型 (50x70cm)', 120.0, 3),
            ('xlarge', '超大型 (70x100cm)', 200.0, 4),
        ]
        
        for code, name, price, sort_order in default_sizes:
            cursor.execute('''
                INSERT INTO product_sizes (product_id, size_name, price, is_active, sort_order)
                VALUES (1, ?, ?, 1, ?)
            ''', (name, price, sort_order))
        
        conn.commit()
        print("默认尺寸数据添加完成！")
    else:
        print(f"ProductSize表已有 {count} 条数据")
    
    # 显示当前数据
    cursor.execute('SELECT id, size_name, price, sort_order FROM product_sizes ORDER BY sort_order')
    rows = cursor.fetchall()
    print("当前尺寸数据:")
    for row in rows:
        print(f"  ID: {row[0]}, 名称: {row[1]}, 价格: {row[2]}, 排序: {row[3]}")
    
    conn.close()

if __name__ == '__main__':
    add_default_sizes()

