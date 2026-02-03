#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量替换 test_server.py 中的 photogooo 地址为配置地址
"""
import re

# 读取文件
with open('test_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换模式
replacements = [
    # http://photogooo 替换为 get_base_url()
    (r'f"http://moeart\.cc([^"]*)"', r'f"{get_base_url()}\1"'),
    (r'"http://moeart\.cc([^"]*)"', r'f"{get_base_url()}\1"'),
    (r"'http://moeart\.cc([^']*)'", r'f"{get_base_url()}\1"'),
    
    # https://photogooo 替换为 get_base_url()（会自动处理https）
    (r'f"https://moeart\.cc([^"]*)"', r'f"{get_base_url()}\1"'),
    (r'"https://moeart\.cc([^"]*)"', r'f"{get_base_url()}\1"'),
    (r"'https://moeart\.cc([^']*)'", r'f"{get_base_url()}\1"'),
    
    # 特殊处理：media/original 使用 get_media_url()
    (r'f"https://moeart\.cc/media/original/([^"]*)"', r'f"{get_media_url()}/original/\1"'),
    (r'f"http://moeart\.cc/media/original/([^"]*)"', r'f"{get_media_url()}/original/\1"'),
    (r'f"https://moeart\.cc/media/final/([^"]*)"', r'f"{get_media_url()}/final/\1"'),
    (r'f"http://moeart\.cc/media/final/([^"]*)"', r'f"{get_media_url()}/final/\1"'),
    
    # 处理静态资源
    (r'f"http://moeart\.cc/static/([^"]*)"', r'f"{get_static_url()}/\1"'),
    (r'f"https://moeart\.cc/static/([^"]*)"', r'f"{get_static_url()}/\1"'),
    
    # 处理相对路径的情况
    (r'f"http://moeart\.cc([^"]*)"', r'f"{get_base_url()}\1"'),
    (r'f"https://moeart\.cc([^"]*)"', r'f"{get_base_url()}\1"'),
]

# 应用替换
modified = False
for pattern, replacement in replacements:
    new_content = re.sub(pattern, replacement, content)
    if new_content != content:
        modified = True
        content = new_content
        print(f"✅ 已替换模式: {pattern}")

# 写回文件
if modified:
    with open('test_server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n✅ 文件已更新！")
else:
    print("⚠️  没有找到需要替换的内容")
