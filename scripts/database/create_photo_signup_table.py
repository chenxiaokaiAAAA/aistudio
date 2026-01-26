#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def create_photo_signup_table():
    """创建宠物摄影报名表"""
    db_file = 'instance/pet_painting.db'
    
    # 定义表结构
    table_sql = """
    CREATE TABLE IF NOT EXISTS photo_signup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL COMMENT '用户姓名',
        phone VARCHAR(20) NOT NULL COMMENT '联系电话',
        pet_breed VARCHAR(100) COMMENT '宠物品种',
        pet_weight VARCHAR(50) COMMENT '宠物体重',
        pet_age VARCHAR(50) COMMENT '宠物年龄',
        pet_character TEXT COMMENT '宠物性格描述',
        available_date VARCHAR(50) COMMENT '可预约日期',
        status VARCHAR(20) DEFAULT 'pending' COMMENT '报名状态',
        pet_images TEXT COMMENT '宠物图片JSON',
        user_id VARCHAR(50) COMMENT '用户ID',
        referrer_user_id VARCHAR(50) COMMENT '推荐人用户ID',
        referrer_promotion_code VARCHAR(50) COMMENT '推广码',
        source VARCHAR(50) DEFAULT 'miniprogram' COMMENT '来源',
        additional_notes TEXT COMMENT '其他备注',
        notes TEXT COMMENT '内部备注',
        submit_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
        contact_time DATETIME COMMENT '联系时间',
        schedule_time DATETIME COMMENT '预约时间',
        complete_time DATETIME COMMENT '完成时间'
    );
    """
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        print("🔧 创建宠物摄影报名表")
        print("=" * 50)
        
        # 检查表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='photo_signup';")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            print("   ⚠️  photo_signup表已存在")
            
            # 检查表结构
            cursor.execute("PRAGMA table_info('photo_signup');")
            columns = cursor.fetchall()
            existing_fields = [col[1] for col in columns]
            
            print(f"   📊 当前字段数: {len(columns)}")
            print(f"   现有字段: {', '.join(existing_fields[:10])}")
            
            # 检查关键字段是否存在
            critical_fields = ['name', 'phone', 'pet_images', 'pet_breed']
            missing_fields = [field for field in critical_fields if field not in existing_fields]
            
            if missing_fields:
                print(f"   ❌ 缺少关键字段: {', '.join(missing_fields)}")
                return False
            else:
                print(f"   ✅ 关键字段完整")
                return True
        else:
            # 创建新表
            cursor.execute(table_sql)
            conn.commit()
            
            print("   ✅ photo_signup表创建成功!")
            
            # 验证表结构
            cursor.execute("PRAGMA table_info('photo_signup');")
            columns = cursor.fetchall()
            print(f"   📊 字段数: {len(columns)}")
            
            # 显示主要字段
            print("   🏗️ 主要字段:")
            key_fields = ['id', 'name', 'phone', 'pet_breed', 'pet_images', 'status', 'submit_time']
            for field in key_fields:
                found_field = [col for col in columns if col[1] == field]
                if found_field:
                    field_info = found_field[0]
                    print(f"      ✅ {field_info[1]} ({field_info[2]})")
            
            conn.close()
            return True
            
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False

def add_test_data():
    """添加测试数据"""
    db_file = 'instance/pet_painting.db'
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 检查是否已有数据
        cursor.execute("SELECT COUNT(*) FROM photo_signup;")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"   ℹ️  photo_signup表已有 {count} 条记录")
            return True
        
        # 插入测试数据
        test_data = {
            'name': '张三',
            'phone': '13800138000',
            'pet_breed': '金毛',
            'pet_weight': '20kg',
            'pet_age': '2岁',
            'pet_character': '很乖，不咬人',
            'available_date': '2025-10-01',
            'status': 'pending',
            'pet_images': '[]',
            'additional_notes': '希望拍户外照'
        }
        
        insert_sql = """
        INSERT INTO photo_signup 
        (name, phone, pet_breed, pet_weight, pet_age, pet_character, 
         available_date, status, pet_images, additional_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_sql, (
            test_data['name'], test_data['phone'], test_data['pet_breed'],
            test_data['pet_weight'], test_data['pet_age'], test_data['pet_character'],
            test_data['available_date'], test_data['status'], test_data['pet_images'],
            test_data['additional_notes']
        ))
        
        conn.commit()
        conn.close()
        
        print("   ✅ 测试数据插入成功!")
        return True
        
    except Exception as e:
        print(f"❌ 插入测试数据失败: {e}")
        return False

def main():
    print("🎯 宠物摄影报名表初始化")
    print("=" * 60)
    
    # 创建表
    table_success = create_photo_signup_table()
    
    if table_success:
        print(f"\n🎨 添加测试数据...")
        data_success = add_test_data()
        
        if data_success:
            print(f"\n🎉 宠物摄影报名功能初始化完成!")
            print(f"   ✅ 数据库表已创建/验证")
            print(f"   ✅ 测试数据已添加")
            print(f"   💡 现在可以测试API接口了")
        else:
            print(f"\n⚠️ 表创建成功，但测试数据添加失败")
    
    return table_success

if __name__ == "__main__":
    main()
