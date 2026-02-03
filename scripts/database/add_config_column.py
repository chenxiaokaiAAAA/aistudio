#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def add_config_column():
    """Add config column to homepage_product_section table"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'instance', 'pet_painting.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(homepage_product_section)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'config' in columns:
            print("Column 'config' already exists")
            conn.close()
            return
        
        # Add column
        cursor.execute("ALTER TABLE homepage_product_section ADD COLUMN config TEXT")
        conn.commit()
        
        print("Successfully added 'config' column to homepage_product_section table")
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    add_config_column()
