#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import os
from datetime import datetime

def restore_from_latest_backup():
    """从最新备份恢复数据库"""
    current_db = 'instance/pet_painting.db'
    source_backup = 'instance/pet_painting_backup_20250923_214156.db'
    
    print("🔄 开始从备份恢复数据库")
    print("=" * 50)
    
    # 检查备份文件是否存在
    if not os.path.exists(source_backup):
        print(f"❌ 备份文件不存在: {source_backup}")
        return False
    
    # 检查当前数据库文件
    current_exists = os.path.exists(current_db)
    if current_exists:
        current_size = os.path.getsize(current_db)
        print(f"📍 当前数据库: {current_db} (已备份, 大小: {current_size:,} 字节)")
    
    # 备份文件信息
    backup_size = os.path.getsize(source_backup)
    print(f"📁 源备份文件: {source_backup}")
    print(f"   大小: {backup_size:,} 字节")
    
    try:
        # 复制备份文件来替换当前数据库
        shutil.copy2(source_backup, current_db)
        
        print(f"\n✅ 数据库恢复成功!")
        print(f"   从: {source_backup}")
        print(f"   到: {current_db}")
        
        # 验证恢复结果
        new_size = os.path.getsize(current_db)
        print(f"   新大小: {new_size:,} 字节")
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        return False

def verify_restoration():
    """验证数据库恢复结果"""
    import sqlite3
    
    db_file = 'instance/pet_painting.db'
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 获取表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"\n🔍 验证数据库恢复结果:")
        print("-" * 30)
        print(f"   表数量: {len(tables)}")
        print(f"   主要表: {', '.join(tables[:10])}")
        if len(tables) > 10:
            print(f"   ... 还有 {len(tables) - 10} 个表")
        
        # 检查关键表的数据
        key_tables = ['homepage_banner', 'homepage_config']
        for table in key_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM '{table}';")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table}: {count} 条记录")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def main():
    print("📋 数据库恢复方案")
    print("=" * 60)
    print("🎯 目标: 从最新备份恢复完整的业务数据库")
    print("💡 理由: 确保轮播图、订单等功能正常工作")
    print("🛡️ 安全: 当前数据库已备份保存")
    print()
    
    success = restore_from_latest_backup()
    
    if success:
        verify_restoration()
        print(f"\n🎉 恢复完成! 现在可以添加宠物摄影报名功能了")
        
    return success

if __name__ == "__main__":
    main()
