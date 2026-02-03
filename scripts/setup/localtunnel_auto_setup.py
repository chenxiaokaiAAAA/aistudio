#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
localtunnel自动化配置脚本
"""

import subprocess
import sys
import os
import requests
import time
import json

def check_nodejs_installed():
    """检查Node.js是否已安装"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js已安装，版本: {result.stdout.strip()}")
            return True
        else:
            print("❌ Node.js未正确安装")
            return False
    except FileNotFoundError:
        print("❌ Node.js未找到，请先安装Node.js")
        return False

def install_localtunnel():
    """安装localtunnel"""
    print("=== 安装localtunnel ===")
    
    try:
        print("正在安装localtunnel...")
        result = subprocess.run(['npm', 'install', '-g', 'localtunnel'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ localtunnel安装成功")
            return True
        else:
            print(f"❌ localtunnel安装失败: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ 安装超时，请检查网络连接")
        return False
    except Exception as e:
        print(f"❌ 安装失败: {e}")
        return False

def start_localtunnel():
    """启动localtunnel"""
    print("=== 启动localtunnel ===")
    print("正在启动localtunnel...")
    print("请等待几秒钟...")
    
    try:
        # 启动localtunnel
        process = subprocess.Popen(['lt', '--port', '8000'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE, 
                                 text=True)
        
        # 等待localtunnel启动
        time.sleep(5)
        
        # 读取输出
        try:
            stdout, stderr = process.communicate(timeout=2)
            
            if stdout:
                print("localtunnel输出:")
                print(stdout)
                
                # 从输出中提取URL
                lines = stdout.split('\n')
                for line in lines:
                    if 'https://' in line and '.loca.lt' in line:
                        tunnel_url = line.strip()
                        print(f"✅ localtunnel已启动")
                        print(f"🌐 公网地址: {tunnel_url}")
                        return tunnel_url
                
                print("⚠️  未找到公网地址")
                return None
            else:
                print("⚠️  未获得输出")
                return None
                
        except subprocess.TimeoutExpired:
            print("⚠️  读取输出超时，但localtunnel可能已启动")
            print("请检查localtunnel窗口中的地址")
            return None
            
    except Exception as e:
        print(f"❌ 启动localtunnel失败: {e}")
        return None

def test_tunnel_connection(tunnel_url):
    """测试隧道连接"""
    print(f"=== 测试隧道连接: {tunnel_url} ===")
    
    try:
        response = requests.get(tunnel_url, timeout=15)
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

def create_test_script():
    """创建测试脚本"""
    test_script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冲印系统测试脚本
"""

import requests
import json
from printer_config import PRINTER_SYSTEM_CONFIG

def test_printer_system():
    """测试冲印系统"""
    print("=== 冲印系统测试 ===")
    
    # 检查配置
    if PRINTER_SYSTEM_CONFIG['shop_id'] == 'YOUR_SHOP_ID':
        print("❌ 请先配置 shop_id 和 shop_name")
        return False
    
    print(f"API地址: {PRINTER_SYSTEM_CONFIG['api_url']}")
    print(f"文件访问地址: {PRINTER_SYSTEM_CONFIG['file_access_base_url']}")
    print()
    
    # 测试API连接
    try:
        test_data = {
            "source_app_id": PRINTER_SYSTEM_CONFIG['source_app_id'],
            "test": True
        }
        
        response = requests.post(
            PRINTER_SYSTEM_CONFIG['api_url'],
            json=test_data,
            timeout=30
        )
        
        print(f"API响应状态码: {response.status_code}")
        print(f"API响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 冲印系统API连接成功")
            return True
        else:
            print("❌ 冲印系统API连接失败")
            return False
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

if __name__ == '__main__':
    test_printer_system()
'''
    
    with open('test_printer_system.py', 'w', encoding='utf-8') as f:
        f.write(test_script_content)
    
    print("✅ 测试脚本已创建: test_printer_system.py")

def main():
    """主函数"""
    print("=== localtunnel自动化配置工具 ===")
    print()
    
    # 检查Node.js
    if not check_nodejs_installed():
        print("请先安装Node.js:")
        print("1. 访问: https://nodejs.org/")
        print("2. 下载并安装Node.js")
        print("3. 重新运行此脚本")
        return
    
    # 安装localtunnel
    if not install_localtunnel():
        print("localtunnel安装失败，请手动安装:")
        print("npm install -g localtunnel")
        return
    
    # 启动隧道
    tunnel_url = start_localtunnel()
    if not tunnel_url:
        print("❌ 启动隧道失败")
        print("请手动运行: lt --port 8000")
        return
    
    # 测试连接
    if not test_tunnel_connection(tunnel_url):
        print("⚠️  隧道连接测试失败，但可能仍然可用")
    
    # 更新配置
    if update_printer_config(tunnel_url):
        print()
        print("🎉 配置完成！")
        print("现在可以测试冲印系统了：")
        print()
        print("1. 确保服务器正在运行: python start.py")
        print("2. 在管理后台上传高清图片")
        print("3. 将订单状态改为'高清放大'")
        print("4. 系统会自动发送到冲印系统")
        print()
        print("📝 重要提示：")
        print("- localtunnel隧道会一直运行，按Ctrl+C停止")
        print("- 免费版本每次重启会获得新的地址")
        print("- 记得先配置厂家的shop_id和shop_name")
    
    # 创建测试脚本
    create_test_script()
    print()
    print("💡 提示：运行 python test_printer_system.py 测试冲印系统连接")

if __name__ == '__main__':
    main()

