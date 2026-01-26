#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def restore_photo_signup_banner():
    """恢复宠物摄影报名页轮播图"""
    current_db = 'instance/pet_painting.db'
    
    # 从当前备份文件中恢复这个轮播图配置
    backup_db = 'instance/pet_painting_current_backup_20250929_113522.db'
    
    try:
        # 连接备份数据库
        backup_conn = sqlite3.connect(backup_db)
        backup_cursor = backup_conn.cursor()
        
        # 获取宠物摄影报名页轮播图数据
        backup_cursor.execute("SELECT * FROM homepage_banner WHERE id = 3;")
        banner_data = backup_cursor.fetchone()
        
        backup_conn.close()
        
        if not banner_data:
            print("❌ 在备份中未找到宠物摄影报名页轮播图")
            return False
        
        print("🔍 找到宠物摄影报名页轮播图:")
        print(f"   ID: {banner_data[0]}")
        print(f"   标题: {banner_data[1]}")
        print(f"   图片: {banner_data[3]}")
        print(f"   链接: {banner_data[4]}")
        print(f"   排序: {banner_data[5]}")
        print(f"   状态: {'启用' if banner_data[6] else '禁用'}")
        
        # 连接当前数据库
        current_conn = sqlite3.connect(current_db)
        current_cursor = current_conn.cursor()
        
        # 检查是否存在
        current_cursor.execute("SELECT id FROM homepage_banner WHERE title = '宠物摄影报名页';")
        existing = current_cursor.fetchone()
        
        if existing:
            print("✅ 宠物摄影报名页轮播图已存在")
            current_conn.close()
            return True
        
        # 插入轮播图
        insert_sql = """
        INSERT INTO homepage_banner (title, subtitle, image_url, link, sort_order, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        current_cursor.execute(insert_sql, banner_data[1:])  # 跳过ID字段
        current_conn.commit()
        current_conn.close()
        
        print("✅ 宠物摄影报名页轮播图已恢复!")
        print(f"   🎯 链接: /pages/photo-signup/photo-signup")
        print(f"   🖼️ 可以在首页轮播图中看到")
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        return False

def verify_restoration():
    """验证轮播图恢复结果"""
    db_file = 'instance/pet_painting.db'
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM homepage_banner;")
        total_banners = cursor.fetchone()[0]
        
        cursor.execute("SELECT * FROM homepage_banner ORDER BY sort_order;")
        banners = cursor.fetchall()
        
        print(f"\n📊 当前轮播图情况:")
        print(f"   总数: {total_banners}")
        
        for banner in banners:
            print(f"   🎠 ID:{banner[0]} '{banner[1]}' -> {banner[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")

def main():
    print("🎯 恢复宠物摄影报名页轮播图")
    print("=" * 60)
    print("📋 说明:")
    print("   用户在恢复数据库时丢失了宠物摄影报名页轮播图")
    print("   现在从备份中恢复这个轮播图配置")
    print()
    
    success = restore_photo_signup_banner()
    
    if success:
        verify_restoration()
        print(f"\n🎉 恢复完成!")
        print(f"   💡 现在可以在管理后台查看轮播图")
        print(f"   📱 前端小程序可以看到宠物摄影报名页入口")
    else:
        print(f"\n❌ 恢复失败")

if __name__ == "__main__":
    main()
