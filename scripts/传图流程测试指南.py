#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
传图流程测试指南
"""

def test_upload_flow():
    """传图流程测试指南"""
    
    from app.utils.config_loader import get_brand_name
    brand_name = get_brand_name()
    print(f"=== {brand_name}传图流程测试指南 ===")
    print()
    
    print("🌐 您的网站地址: https://shiny-baboons-shave.loca.lt/")
    print("🔑 访问密码: 103.180.29.82")
    print()
    
    print("📋 测试步骤:")
    print()
    
    print("第一步：访问网站")
    print("1. 打开浏览器")
    print("2. 访问: https://shiny-baboons-shave.loca.lt/")
    print("3. 输入密码: 103.180.29.82")
    print("4. 点击提交")
    print()
    
    print("第二步：测试传图功能")
    print("1. 点击'传图入口'")
    print("2. 上传一张宠物照片")
    print("3. 选择风格（如：拟人风格）")
    print("4. 选择产品（如：钥匙扣）")
    print("5. 填写客户信息")
    print("6. 提交订单")
    print()
    
    print("第三步：测试管理后台")
    print("1. 访问: https://shiny-baboons-shave.loca.lt/admin/")
    print("2. 使用管理员账号登录")
    print("3. 查看新创建的订单")
    print("4. 上传成品图")
    print("5. 上传高清图")
    print("6. 将状态改为'高清放大'")
    print()
    
    print("第四步：测试冲印系统发送")
    print("1. 检查订单详情页面的'冲印系统发送状态'")
    print("2. 确认状态变为'发送中'")
    print("3. 查看发送结果（成功/失败）")
    print("4. 如果失败，查看错误信息")
    print()
    
    print("⚠️  注意事项:")
    print("- 确保localtunnel一直运行")
    print("- 确保Flask服务器一直运行")
    print("- 厂家需要配置shop_id和shop_name才能成功发送")
    print()

def create_test_order():
    """创建测试订单"""
    
    print("=== 创建测试订单 ===")
    print()
    
    print("方法一：通过网站创建（推荐）")
    print("1. 访问: https://shiny-baboons-shave.loca.lt/")
    print("2. 输入密码: 103.180.29.82")
    print("3. 点击'传图入口'")
    print("4. 上传测试图片")
    print("5. 填写测试信息:")
    print("   - 客户姓名: 测试客户")
    print("   - 客户电话: 13800138000")
    print("   - 选择风格: 拟人风格")
    print("   - 选择产品: 钥匙扣")
    print("6. 提交订单")
    print()
    
    print("方法二：通过管理后台创建")
    print("1. 访问: https://shiny-baboons-shave.loca.lt/admin/")
    print("2. 登录管理后台")
    print("3. 手动创建订单")
    print("4. 上传测试图片")
    print()

def test_printer_system():
    """测试冲印系统"""
    
    print("=== 测试冲印系统 ===")
    print()
    
    print("当前配置状态:")
    print("✅ API地址: http://xmdmsm.xicp.cn:5995/api/ODSGate/NewOrder")
    print("✅ 系统代号: ZPG")
    print("❌ 影楼编号: 需要厂家提供")
    print("❌ 影楼名称: 需要厂家提供")
    print("✅ 文件访问地址: https://shiny-baboons-shave.loca.lt")
    print()
    
    print("测试步骤:")
    print("1. 创建测试订单")
    print("2. 上传高清图片")
    print("3. 将状态改为'高清放大'")
    print("4. 观察发送状态")
    print()
    
    print("预期结果:")
    print("- 如果配置完整: 状态显示'发送成功'")
    print("- 如果配置不完整: 状态显示'发送失败'，显示具体错误")
    print()

def main():
    """主函数"""
    
    test_upload_flow()
    print()
    create_test_order()
    print()
    test_printer_system()
    print()
    
    print("🎯 开始测试:")
    print("1. 确保服务器运行: python start.py")
    print("2. 确保localtunnel运行: lt --port 8000")
    print("3. 访问网站开始测试")
    print()
    
    print("📞 需要帮助时:")
    print("- 查看服务器日志了解错误信息")
    print("- 检查订单详情页面的发送状态")
    print("- 联系厂家获取shop_id和shop_name")

if __name__ == '__main__':
    main()

