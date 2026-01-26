#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import os
from datetime import datetime

def create_safe_backup():
    """创建当前数据库的安全备份"""
    current_db = 'instance/pet_painting.db'
    
    if not os.path.exists(current_db):
        print("❌ 当前数据库文件不存在")
        return False
    
    # 创建带时间戳的备份文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'pet_painting_current_backup_{timestamp}.db'
    backup_path = f'instance/{backup_name}'
    
    try:
        # 复制当前数据库文件
        shutil.copy2(current_db, backup_path)
        
        print(f"✅ 当前数据库已备份为: {backup_name}")
        print(f"   位置: {backup_path}")
        
        # 检查备份文件大小
        backup_size = os.path.getsize(backup_path)
        print(f"   大小: {backup_size:,} 字节")
        
        return True
        
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return False

def main():
    print("🛡️ 创建当前数据库安全备份")
    print("=" * 40)
    
    if create_safe_backup():
        print("\n✅ 备份创建成功！你的数据已安全保存")
    else:
        print("\n❌ 备份创建失败")

if __name__ == "__main__":
    main()
