#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 admin_sizes 路由的残留函数体（最终清理）
"""
import os

def cleanup_final():
    file_path = 'test_server.py'
    if not os.path.exists(file_path):
        print(f"错误: 文件 '{file_path}' 不存在。")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 删除第621行到第1273行（索引从0开始，所以是620到1272）
    new_lines = lines[:620] + lines[1273:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✓ 已删除第621-1273行，共{1273-621+1}行残留代码")

if __name__ == '__main__':
    cleanup_final()
