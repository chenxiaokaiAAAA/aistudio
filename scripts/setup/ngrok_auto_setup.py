#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ngrok自动化配置脚本
"""

import subprocess
import sys
import os
import requests
import time

def check_ngrok_installed():
    """检查ngrok是否已安装"""
    try:
        result = subprocess.run(['ngrok', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ngrok已安装，版本: {result.stdout.strip()}")
            return True
        else:
            print("❌ ngrok未正确安装")
            return False
    except FileNotFoundError:
        print("❌ ngrok未找到，请确保ngrok在系统PATH中")
        return False

def configure_ngrok_auth():
    """配置ngrok authtoken"""
    print("=== 配置ngrok authtoken ===")
    print()
    print("请按以下步骤操作：")
    print("1. 访问: https://dashboard.ngrok.com/")
    print("2. 登录您的谷歌账号")
    print("3. 点击 'Your Authtoken'")
    print("4. 复制您的authtoken")
    print()
    
    authtoken = input("请输入您的authtoken: ").strip()
    
    if not authtoken:
        print("❌ authtoken不能为空")
        return False
    
    try:
        # 配置authtoken
        result = subprocess.run(['ngrok', 'config', 'add-authtoken', authtoken], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ authtoken配置成功")
            return True
        else:
            print(f"❌ authtoken配置失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 配置失败: {e}")
        return False

def start_ngrok_tunnel():
    """启动ngrok隧道"""
    print("=== 启动ngrok隧道 ===")
    print()
    print("正在启动ngrok...")
    print("请等待几秒钟，ngrok会显示公网地址")
    print()
    
    try:
        # 启动ngrok
        process = subprocess.Popen(['ngrok', 'http', '8000'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE, 
                                 text=True)
        
        # 等待ngrok启动
        time.sleep(3)
        
        # 获取ngrok状态
        try:
            response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                
                if tunnels:
                    for tunnel in tunnels:
                        if tunnel.get('proto') == 'https':
                            public_url = tunnel.get('public_url')
                            if public_url:
                                print(f"✅ ngrok隧道已启动")
                                print(f"🌐 公网地址: {public_url}")
                                print(f"🔗 本地地址: http://localhost:8000")
                                print()
                                return public_url
                
                print("⚠️  未找到HTTPS隧道，请检查ngrok状态")
                return None
            else:
                print("⚠️  无法获取ngrok状态")
                return None
        except requests.exceptions.RequestException:
            print("⚠️  无法连接到ngrok API")
            return None
            
    except Exception as e:
        print(f"❌ 启动ngrok失败: {e}")
        return None

def test_tunnel_connection(tunnel_url):
    """测试隧道连接"""
    print(f"=== 测试隧道连接: {tunnel_url} ===")
    
    try:
        response = requests.get(tunnel_url, timeout=10)
        if response.status_code == 200:
            print("✅ 隧道连接测试成功")
            return True
        else:
            print(f"⚠️  连接测试返回状态码: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 隧道连接测试失败: {e}")
        return False

def update_printer_config(tunnel_url):
    """更新冲印系统配置"""
    config_file = 'printer_config.py'
    
    if not os.path.exists(config_file):
        print(f"❌ 配置文件不存在: {config_file}")
        return False
    
    try:
        # 读取配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新file_access_base_url
        old_url = "http://photogooo"
        new_content = content.replace(old_url, tunnel_url)
        
        # 写回配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 冲印系统配置已更新")
        print(f"   文件访问地址: {tunnel_url}")
        return True
        
    except Exception as e:
        print(f"❌ 更新配置失败: {e}")
        return False

def main():
    """主函数"""
    print("=== ngrok自动化配置工具 ===")
    print()
    
    # 检查ngrok是否已安装
    if not check_ngrok_installed():
        print("请先安装ngrok:")
        print("1. 访问: https://ngrok.com/download")
        print("2. 下载Windows版本")
        print("3. 解压到系统PATH目录")
        return
    
    # 配置authtoken
    if not configure_ngrok_auth():
        return
    
    # 启动隧道
    tunnel_url = start_ngrok_tunnel()
    if not tunnel_url:
        print("❌ 启动隧道失败")
        return
    
    # 测试连接
    if not test_tunnel_connection(tunnel_url):
        print("⚠️  隧道连接测试失败，但可能仍然可用")
    
    # 更新配置
    update_choice = input("是否更新冲印系统配置? (y/n): ").strip().lower()
    if update_choice == 'y':
        if update_printer_config(tunnel_url):
            print()
            print("🎉 配置完成！")
            print("现在可以测试冲印系统了：")
            print("1. 确保服务器正在运行: python start.py")
            print("2. 在管理后台上传高清图片")
            print("3. 将订单状态改为'高清放大'")
            print("4. 系统会自动发送到冲印系统")
        else:
            print("❌ 配置更新失败")
    
    print()
    print("📝 重要提示：")
    print("- ngrok隧道会一直运行，按Ctrl+C停止")
    print("- 免费版本每次重启会获得新的地址")
    print("- 生产环境建议使用固定域名")

if __name__ == '__main__':
    main()

