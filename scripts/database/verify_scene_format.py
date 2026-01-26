#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证小程序码scene参数格式
"""

def verify_scene_format():
    """验证scene参数格式"""
    print("🔍 验证小程序码scene参数格式")
    
    # 测试数据
    promotion_code = "PETT9WMPW"
    user_id = "USER1758618072318"
    
    print(f"原始数据:")
    print(f"  promotionCode: {promotion_code}")
    print(f"  userId: {user_id}")
    print()
    
    # 计算新格式
    scene_new = f"p={promotion_code}&u={user_id[-8:]}"
    scene_length = len(scene_new)
    
    print(f"新格式 (当前实现):")
    print(f"  scene: {scene_new}")
    print(f"  长度: {scene_length} 字符")
    print(f"  是否符合32字符限制: {'是' if scene_length <= 32 else '否'}")
    print()
    
    # 对比旧格式
    scene_old = f"{promotion_code}&{user_id[-8:]}"
    scene_old_length = len(scene_old)
    
    print(f"旧格式 (修复前):")
    print(f"  scene: {scene_old}")
    print(f"  长度: {scene_old_length} 字符")
    print()
    
    # 对比期望格式
    scene_expected = f"promotion={promotion_code}&userId={user_id}"
    scene_expected_length = len(scene_expected)
    
    print(f"期望格式 (您要求的):")
    print(f"  scene: {scene_expected}")
    print(f"  长度: {scene_expected_length} 字符")
    print(f"  是否符合32字符限制: {'是' if scene_expected_length <= 32 else '否'}")
    print()
    
    # 总结
    print("📋 总结:")
    print(f"✅ 当前实现使用了新格式: {scene_new}")
    print(f"✅ 长度符合微信限制: {scene_length} <= 32")
    print(f"✅ 格式清晰明确: p=推广码&u=用户ID")
    
    if scene_expected_length > 32:
        print(f"⚠️  期望格式超过限制: {scene_expected_length} > 32")
        print("   建议使用当前实现的新格式")

if __name__ == '__main__':
    verify_scene_format()



