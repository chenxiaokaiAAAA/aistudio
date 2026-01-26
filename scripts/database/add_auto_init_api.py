#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为服务器添加自动初始化API的代码
这段代码需要手动添加到test_server.py中
"""

auto_init_code = '''
# ============== 自动数据表初始化API ================

@app.route('/api/admin/init-photo-signup-table', methods=['POST'])
@login_required
def init_photo_signup_table():
    """初始化宠物摄影报名表"""
    try:
        from sqlalchemy import text
        
        # 检查表是否存在
        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='photo_signup'"))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            # 创建表
            db.session.execute(text('''
                CREATE TABLE photo_signup (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(50) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    pet_breed VARCHAR(50) NOT NULL,
                    pet_weight VARCHAR(50) NOT NULL,
                    pet_age VARCHAR(50) NOT NULL,
                    pet_character VARCHAR(500),
                    available_date VARCHAR(50),
                    additional_notes VARCHAR(500),
                    pet_images TEXT,
                    user_id VARCHAR(100),
                    referrer_user_id VARCHAR(100),
                    referrer_promotion_code VARCHAR(50),
                    source VARCHAR(50) DEFAULT 'miniprogram_carousel',
                    status VARCHAR(20) DEFAULT 'pending',
                    notes VARCHAR(1000),
                    submit_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    contact_time DATETIME,
                    schedule_time DATETIME,
                    complete_time DATETIME
                )
            '''))
            
            db.session.commit()
            message = "表创建成功"
        else:
            message = "表已存在"
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"初始化表失败: {e}")
        return jsonify({
            'success': False,
            'message': f'初始化失败: {str(e)}'
        }), 500
'''

print("自动初始化API代码:")
print(auto_init_code)
print("\n请将此代码添加到test_server.py文件中。")
