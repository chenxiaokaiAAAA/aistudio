#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
内网穿透配置脚本
使用ngrok或localtunnel提供公网访问
"""

import subprocess
import time
import requests
import json

def setup_ngrok():
    """设置ngrok内网穿透"""
    try:
        # 检查ngrok是否已安装
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ ngrok未安装，请先安装ngrok")
            return None
        
        # 启动ngrok
        print("🚀 启动ngrok内网穿透...")
        process = subprocess.Popen(['ngrok', 'http', '8000'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # 等待ngrok启动
        time.sleep(3)
        
        # 获取公网URL
        try:
            response = requests.get('http://localhost:4040/api/tunnels')
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                if tunnels:
                    public_url = tunnels[0]['public_url']
                    print(f"✅ ngrok启动成功！")
                    print(f"公网URL: {public_url}")
                    return public_url
        except:
            pass
        
        print("❌ 无法获取ngrok公网URL")
        return None
        
    except Exception as e:
        print(f"❌ ngrok启动失败: {e}")
        return None

def setup_localtunnel():
    """设置localtunnel内网穿透"""
    try:
        # 检查localtunnel是否已安装
        result = subprocess.run(['npx', 'localtunnel', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ localtunnel未安装，请先安装: npm install -g localtunnel")
            return None
        
        # 启动localtunnel
        print("🚀 启动localtunnel内网穿透...")
        process = subprocess.Popen(['npx', 'localtunnel', '--port', '8000'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # 等待localtunnel启动
        time.sleep(5)
        
        # 读取输出获取公网URL
        stdout, stderr = process.communicate(timeout=10)
        output = stdout.decode('utf-8')
        
        if 'your url is:' in output.lower():
            lines = output.split('\n')
            for line in lines:
                if 'your url is:' in line.lower():
                    public_url = line.split('your url is:')[1].strip()
                    print(f"✅ localtunnel启动成功！")
                    print(f"公网URL: {public_url}")
                    return public_url
        
        print("❌ 无法获取localtunnel公网URL")
        return None
        
    except Exception as e:
        print(f"❌ localtunnel启动失败: {e}")
        return None

def update_miniprogram_config(public_url):
    """更新小程序配置使用公网URL"""
    if not public_url:
        return
    
    # 更新app.js中的serverUrl
    app_js_path = "app.js"
    try:
        with open(app_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换serverUrl
        new_content = content.replace(
            "serverUrl: 'http://photogooo'",
            f"serverUrl: '{public_url}'"
        )
        
        with open(app_js_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 已更新小程序配置使用公网URL: {public_url}")
        
    except Exception as e:
        print(f"❌ 更新小程序配置失败: {e}")

def main():
    """主函数"""
    print("🔧 内网穿透配置工具")
    print("=" * 50)
    
    # 尝试使用ngrok
    public_url = setup_ngrok()
    
    # 如果ngrok失败，尝试localtunnel
    if not public_url:
        public_url = setup_localtunnel()
    
    if public_url:
        # 更新小程序配置
        update_miniprogram_config(public_url)
        
        print("\n📱 使用说明:")
        print("1. 重新编译小程序")
        print("2. 重新扫码测试")
        print("3. 图片应该可以正常显示了")
    else:
        print("\n❌ 内网穿透设置失败")
        print("请手动安装ngrok或localtunnel")

if __name__ == "__main__":
    main()
