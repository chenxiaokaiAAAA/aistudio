import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def add_style_redirect_page_column():
    """为product_categories表添加style_redirect_page字段"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'instance', 'pet_painting.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查列是否存在
        cursor.execute("PRAGMA table_info(product_categories)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'style_redirect_page' not in columns:
            print("正在添加 style_redirect_page 字段到 product_categories 表...")
            cursor.execute("ALTER TABLE product_categories ADD COLUMN style_redirect_page VARCHAR(50)")
            conn.commit()
            print("[成功] 成功添加 style_redirect_page 字段")
        else:
            print("[警告] style_redirect_page 字段已存在")
        
        conn.close()
        print("[成功] 数据库迁移完成")
        
    except sqlite3.Error as e:
        print(f"[错误] SQLite错误: {e}")
    except Exception as e:
        print(f"[错误] 发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    add_style_redirect_page_column()
