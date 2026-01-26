import sqlite3
import os
import shutil

# 恢复数据脚本
def restore_data():
    # 备份文件路径
    backup_file = 'pet_painting_backup_printer_20250915_120803.db'
    
    if not os.path.exists(backup_file):
        print("备份文件不存在！")
        return
    
    # 备份当前的空数据库
    shutil.copy('pet_painting.db', 'pet_painting_empty_backup.db')
    print("已备份当前空数据库")
    
    # 恢复数据
    shutil.copy(backup_file, 'pet_painting.db')
    print("数据已恢复！")
    
    # 验证恢复结果
    conn = sqlite3.connect('pet_painting.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM "order"')
    order_count = cursor.fetchone()[0]
    print(f'恢复后的订单数量: {order_count}')
    
    cursor.execute('SELECT COUNT(*) FROM user')
    user_count = cursor.fetchone()[0]
    print(f'恢复后的用户数量: {user_count}')
    
    conn.close()

if __name__ == '__main__':
    restore_data()

