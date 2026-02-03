#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
免费内网穿透方案推荐
"""

def free_tunnel_solutions():
    """免费内网穿透方案"""
    
    print("=== 免费内网穿透方案推荐 ===")
    print()
    
    print("🚀 方案一：ngrok（推荐）")
    print("✅ 优点：")
    print("   - 完全免费")
    print("   - 使用简单")
    print("   - 稳定可靠")
    print("   - 支持HTTPS")
    print()
    print("📋 使用步骤：")
    print("1. 访问: https://ngrok.com/")
    print("2. 注册免费账号")
    print("3. 下载ngrok客户端")
    print("4. 获取authtoken")
    print("5. 运行命令:")
    print("   ngrok config add-authtoken YOUR_AUTHTOKEN")
    print("   ngrok http 8000")
    print("6. 获得公网地址，如: https://abc123.ngrok.io")
    print()
    
    print("🚀 方案二：natapp（国内）")
    print("✅ 优点：")
    print("   - 国内服务，速度快")
    print("   - 免费版本可用")
    print("   - 中文界面")
    print()
    print("📋 使用步骤：")
    print("1. 访问: https://natapp.cn/")
    print("2. 注册账号")
    print("3. 下载客户端")
    print("4. 获取免费隧道")
    print("5. 运行命令:")
    print("   natapp -authtoken=YOUR_TOKEN")
    print()
    
    print("🚀 方案三：frp（自建）")
    print("✅ 优点：")
    print("   - 开源免费")
    print("   - 可自建服务器")
    print("   - 功能强大")
    print()
    print("📋 使用步骤：")
    print("1. 下载frp: https://github.com/fatedier/frp")
    print("2. 配置frpc.ini")
    print("3. 运行: ./frpc -c frpc.ini")
    print()
    
    print("🚀 方案四：localtunnel（最简单）")
    print("✅ 优点：")
    print("   - 无需注册")
    print("   - 一条命令启动")
    print("   - 完全免费")
    print()
    print("📋 使用步骤：")
    print("1. 安装: npm install -g localtunnel")
    print("2. 运行: lt --port 8000")
    print("3. 获得公网地址")
    print()

def create_ngrok_setup():
    """创建ngrok配置脚本"""
    
    setup_content = '''#!/bin/bash
# ngrok内网穿透配置脚本

echo "=== ngrok内网穿透配置 ==="

# 检查ngrok是否已安装
if ! command -v ngrok &> /dev/null; then
    echo "ngrok未安装，正在下载..."
    
    # Windows下载
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "检测到Windows系统"
        echo "请手动下载ngrok:"
        echo "1. 访问: https://ngrok.com/download"
        echo "2. 下载Windows版本"
        echo "3. 解压到系统PATH目录"
        echo "4. 重新运行此脚本"
        exit 1
    fi
    
    # Linux/Mac下载
    echo "正在下载ngrok..."
    curl -s https://ngrok.com/download | grep -o 'https://bin.equinox.io/c/[^"]*' | head -1 | xargs wget -O ngrok.zip
    unzip ngrok.zip
    chmod +x ngrok
    sudo mv ngrok /usr/local/bin/
    rm ngrok.zip
fi

echo "ngrok已安装"

# 检查authtoken
if [ -z "$NGROK_AUTHTOKEN" ]; then
    echo "请设置ngrok authtoken:"
    echo "1. 访问: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "2. 复制您的authtoken"
    echo "3. 运行: export NGROK_AUTHTOKEN=your_token_here"
    echo "4. 重新运行此脚本"
    exit 1
fi

# 配置authtoken
ngrok config add-authtoken $NGROK_AUTHTOKEN

echo "✅ ngrok配置完成"
echo "🚀 启动内网穿透..."
echo "访问地址将在下面显示"

# 启动ngrok
ngrok http 8000
'''
    
    with open('setup_ngrok.sh', 'w', encoding='utf-8') as f:
        f.write(setup_content)
    
    print("✅ ngrok配置脚本已创建: setup_ngrok.sh")

def create_localtunnel_setup():
    """创建localtunnel配置脚本"""
    
    setup_content = '''#!/bin/bash
# localtunnel内网穿透配置脚本

echo "=== localtunnel内网穿透配置 ==="

# 检查Node.js是否已安装
if ! command -v node &> /dev/null; then
    echo "Node.js未安装，请先安装Node.js:"
    echo "1. 访问: https://nodejs.org/"
    echo "2. 下载并安装Node.js"
    echo "3. 重新运行此脚本"
    exit 1
fi

# 检查localtunnel是否已安装
if ! command -v lt &> /dev/null; then
    echo "正在安装localtunnel..."
    npm install -g localtunnel
fi

echo "✅ localtunnel已安装"
echo "🚀 启动内网穿透..."
echo "访问地址将在下面显示"

# 启动localtunnel
lt --port 8000
'''
    
    with open('setup_localtunnel.sh', 'w', encoding='utf-8') as f:
        f.write(setup_content)
    
    print("✅ localtunnel配置脚本已创建: setup_localtunnel.sh")

def create_tunnel_test():
    """创建穿透测试脚本"""
    
    test_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内网穿透测试脚本
"""

import requests
import time
import os

def test_tunnel_connection(tunnel_url):
    """测试穿透连接"""
    
    print(f"=== 测试穿透连接: {tunnel_url} ===")
    
    # 测试基本连接
    try:
        response = requests.get(tunnel_url, timeout=10)
        if response.status_code == 200:
            print("✅ 基本连接测试成功")
        else:
            print(f"⚠️  连接测试返回状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接测试失败: {e}")
        return False
    
    # 测试文件访问
    test_file_url = f"{tunnel_url}/media/hd/test_image.jpg"
    try:
        response = requests.get(test_file_url, timeout=10)
        if response.status_code == 200:
            print("✅ 文件访问测试成功")
        elif response.status_code == 404:
            print("⚠️  文件不存在（这是正常的，因为测试文件不存在）")
        else:
            print(f"⚠️  文件访问返回状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 文件访问测试失败: {e}")
    
    return True

def update_printer_config(tunnel_url):
    """更新冲印系统配置"""
    
    config_file = 'printer_config.py'
    
    if not os.path.exists(config_file):
        print(f"❌ 配置文件不存在: {config_file}")
        return False
    
    # 读取配置文件
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新file_access_base_url
    old_url = "http://photogooo"
    new_content = content.replace(old_url, tunnel_url)
    
    # 写回配置文件
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ 配置文件已更新: {tunnel_url}")
    return True

def main():
    """主函数"""
    
    print("=== 内网穿透测试工具 ===")
    print()
    
    print("请选择测试方式:")
    print("1. 手动输入穿透地址")
    print("2. 使用ngrok")
    print("3. 使用localtunnel")
    
    choice = input("请输入选择 (1-3): ").strip()
    
    if choice == "1":
        tunnel_url = input("请输入穿透地址 (如: https://abc123.ngrok.io): ").strip()
        if not tunnel_url.startswith('http'):
            tunnel_url = 'https://' + tunnel_url
        
        if test_tunnel_connection(tunnel_url):
            update_choice = input("是否更新冲印系统配置? (y/n): ").strip().lower()
            if update_choice == 'y':
                update_printer_config(tunnel_url)
                print("✅ 配置更新完成，可以测试冲印系统了！")
    
    elif choice == "2":
        print("请先运行ngrok:")
        print("1. 访问: https://ngrok.com/")
        print("2. 注册并获取authtoken")
        print("3. 运行: ngrok http 8000")
        print("4. 复制显示的地址，重新运行此脚本选择选项1")
    
    elif choice == "3":
        print("请先运行localtunnel:")
        print("1. 安装: npm install -g localtunnel")
        print("2. 运行: lt --port 8000")
        print("3. 复制显示的地址，重新运行此脚本选择选项1")
    
    else:
        print("无效选择")

if __name__ == '__main__':
    main()
'''
    
    with open('tunnel_test.py', 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("✅ 穿透测试脚本已创建: tunnel_test.py")

def main():
    """主函数"""
    
    free_tunnel_solutions()
    print()
    
    print("=== 配置文件创建 ===")
    create_ngrok_setup()
    create_localtunnel_setup()
    create_tunnel_test()
    print()
    
    print("=== 推荐使用ngrok（最简单） ===")
    print("1. 访问: https://ngrok.com/")
    print("2. 注册免费账号")
    print("3. 下载ngrok客户端")
    print("4. 获取authtoken")
    print("5. 运行: ngrok http 8000")
    print("6. 复制显示的地址")
    print("7. 运行: python tunnel_test.py")
    print("8. 选择选项1，输入ngrok地址")
    print()
    
    print("=== 或者使用localtunnel（无需注册） ===")
    print("1. 安装Node.js: https://nodejs.org/")
    print("2. 运行: npm install -g localtunnel")
    print("3. 运行: lt --port 8000")
    print("4. 复制显示的地址")
    print("5. 运行: python tunnel_test.py")
    print("6. 选择选项1，输入localtunnel地址")

if __name__ == '__main__':
    main()

