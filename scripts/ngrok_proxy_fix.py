#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ngrok代理问题解决方案
"""

import os
import subprocess
import sys

def check_proxy_settings():
    """检查代理设置"""
    print("=== 检查代理设置 ===")
    
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']
    found_proxy = False
    
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"❌ 发现代理设置: {var} = {value}")
            found_proxy = True
    
    if not found_proxy:
        print("✅ 未发现环境变量代理设置")
    
    return found_proxy

def clear_proxy_settings():
    """清除代理设置"""
    print("=== 清除代理设置 ===")
    
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']
    
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]
            print(f"✅ 已清除: {var}")
    
    print("✅ 代理设置已清除")

def check_ngrok_config():
    """检查ngrok配置文件"""
    print("=== 检查ngrok配置文件 ===")
    
    # 获取ngrok配置目录
    home_dir = os.path.expanduser("~")
    ngrok_config_dir = os.path.join(home_dir, ".config", "ngrok")
    ngrok_config_file = os.path.join(ngrok_config_dir, "ngrok.yml")
    
    print(f"ngrok配置目录: {ngrok_config_dir}")
    print(f"ngrok配置文件: {ngrok_config_file}")
    
    if os.path.exists(ngrok_config_file):
        print("✅ ngrok配置文件存在")
        
        try:
            with open(ngrok_config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'proxy_url' in content:
                print("❌ 发现proxy_url配置")
                print("配置文件内容:")
                print(content)
                return True
            else:
                print("✅ 未发现proxy_url配置")
                return False
        except Exception as e:
            print(f"⚠️  读取配置文件失败: {e}")
            return False
    else:
        print("✅ ngrok配置文件不存在")
        return False

def create_clean_ngrok_config():
    """创建干净的ngrok配置"""
    print("=== 创建干净的ngrok配置 ===")
    
    home_dir = os.path.expanduser("~")
    ngrok_config_dir = os.path.join(home_dir, ".config", "ngrok")
    ngrok_config_file = os.path.join(ngrok_config_dir, "ngrok.yml")
    
    # 创建配置目录
    os.makedirs(ngrok_config_dir, exist_ok=True)
    
    # 创建干净的配置文件
    clean_config = """version: "2"
authtoken: YOUR_AUTHTOKEN_HERE
tunnels:
  web:
    proto: http
    addr: 8000
"""
    
    try:
        with open(ngrok_config_file, 'w', encoding='utf-8') as f:
            f.write(clean_config)
        print(f"✅ 已创建干净的配置文件: {ngrok_config_file}")
        return True
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return False

def test_ngrok_without_proxy():
    """在没有代理的情况下测试ngrok"""
    print("=== 测试ngrok（无代理） ===")
    
    # 清除代理环境变量
    clear_proxy_settings()
    
    try:
        # 测试ngrok版本
        result = subprocess.run(['ngrok', '--version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ ngrok版本: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ ngrok版本检查失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ ngrok响应超时")
        return False
    except Exception as e:
        print(f"❌ 测试ngrok失败: {e}")
        return False

def manual_ngrok_setup():
    """手动ngrok设置指南"""
    print("=== 手动ngrok设置指南 ===")
    print()
    print("如果自动设置失败，请按以下步骤手动操作：")
    print()
    print("1. 清除代理设置：")
    print("   - 关闭所有命令行窗口")
    print("   - 重新打开命令行")
    print("   - 确保没有设置http_proxy环境变量")
    print()
    print("2. 配置ngrok authtoken：")
    print("   ngrok config add-authtoken YOUR_AUTHTOKEN")
    print()
    print("3. 启动ngrok：")
    print("   ngrok http 8000")
    print()
    print("4. 如果仍然失败，尝试：")
    print("   ngrok http 8000 --log=stdout")
    print()
    print("5. 或者使用其他方案：")
    print("   - localtunnel: npm install -g localtunnel && lt --port 8000")
    print("   - natapp: https://natapp.cn/")

def alternative_solutions():
    """替代方案"""
    print("=== 替代方案 ===")
    print()
    print("如果ngrok无法使用，推荐以下替代方案：")
    print()
    print("🚀 方案一：localtunnel（推荐）")
    print("1. 安装Node.js: https://nodejs.org/")
    print("2. 运行: npm install -g localtunnel")
    print("3. 运行: lt --port 8000")
    print("4. 复制显示的地址")
    print()
    print("🚀 方案二：natapp（国内）")
    print("1. 访问: https://natapp.cn/")
    print("2. 注册账号")
    print("3. 下载客户端")
    print("4. 获取免费隧道")
    print()
    print("🚀 方案三：frp（自建）")
    print("1. 下载frp: https://github.com/fatedier/frp")
    print("2. 配置frpc.ini")
    print("3. 运行frp客户端")

def main():
    """主函数"""
    print("=== ngrok代理问题解决方案 ===")
    print()
    
    # 检查代理设置
    has_proxy = check_proxy_settings()
    print()
    
    # 检查ngrok配置
    has_proxy_config = check_ngrok_config()
    print()
    
    if has_proxy or has_proxy_config:
        print("🔧 发现代理问题，正在修复...")
        
        # 清除代理设置
        clear_proxy_settings()
        print()
        
        # 创建干净配置
        if has_proxy_config:
            create_clean_ngrok_config()
            print()
        
        # 测试ngrok
        if test_ngrok_without_proxy():
            print("✅ ngrok问题已修复")
            print("现在可以尝试启动ngrok:")
            print("ngrok http 8000")
        else:
            print("❌ ngrok仍有问题")
            print()
            alternative_solutions()
    else:
        print("✅ 未发现代理问题")
        print("ngrok应该可以正常使用")
        print("尝试运行: ngrok http 8000")
    
    print()
    manual_ngrok_setup()

if __name__ == '__main__':
    main()

