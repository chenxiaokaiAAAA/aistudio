#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成微信支付API密钥
"""

import random
import string

def generate_api_key(length=32):
    """生成指定长度的API密钥"""
    # 使用大写字母、小写字母和数字
    characters = string.ascii_letters + string.digits
    api_key = ''.join(random.choice(characters) for _ in range(length))
    return api_key

def generate_multiple_keys(count=5):
    """生成多个API密钥供选择"""
    print("🔑 生成32位微信支付API密钥:")
    print("=" * 50)
    
    for i in range(count):
        key = generate_api_key(32)
        print(f"{i+1}. {key}")
    
    print("=" * 50)
    print("💡 使用说明:")
    print("1. 选择其中一个密钥")
    print("2. 登录微信支付商户平台")
    print("3. 进入'账户中心' → 'API安全'")
    print("4. 设置API密钥为选择的密钥")
    print("5. 更新代码中的配置")

if __name__ == "__main__":
    generate_multiple_keys()

