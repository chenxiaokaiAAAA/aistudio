#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速重启localtunnel脚本
"""

import subprocess
import time
import requests

def restart_localtunnel():
    """重启localtunnel"""
    print("=== 重启localtunnel ===")
    
    try:
        # 启动localtunnel
        process = subprocess.Popen(['lt', '--port', '8000'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE, 
                                 text=True)
        
        # 等待启动
        time.sleep(5)
        
        # 读取输出
        try:
            stdout, stderr = process.communicate(timeout=2)
            
            if stdout:
                print("localtunnel输出:")
                print(stdout)
                
                # 提取URL
                lines = stdout.split('\n')
                for line in lines:
                    if 'https://' in line and '.loca.lt' in line:
                        tunnel_url = line.strip()
                        print(f"✅ 新地址: {tunnel_url}")
                        return tunnel_url
                
                print("⚠️  未找到新地址")
                return None
            else:
                print("⚠️  未获得输出")
                return None
                
        except subprocess.TimeoutExpired:
            print("⚠️  读取输出超时")
            return None
            
    except Exception as e:
        print(f"❌ 重启失败: {e}")
        return None

def update_config(new_url):
    """更新配置文件"""
    config_file = 'printer_config.py'
    
    try:
        # 读取配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找并替换URL
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "'file_access_base_url':" in line:
                lines[i] = f"    'file_access_base_url': '{new_url}',  # 外部可访问的文件基础URL"
                break
        
        # 写回文件
        new_content = '\n'.join(lines)
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 配置文件已更新: {new_url}")
        return True
        
    except Exception as e:
        print(f"❌ 更新配置失败: {e}")
        return False

def main():
    """主函数"""
    print("=== localtunnel快速重启工具 ===")
    print()
    
    # 重启localtunnel
    new_url = restart_localtunnel()
    
    if new_url:
        # 更新配置
        if update_config(new_url):
            print()
            print("🎉 重启完成！")
            print(f"新地址: {new_url}")
            print("请重新获取密码: https://loca.lt/mytunnelpassword")
        else:
            print("❌ 配置更新失败")
    else:
        print("❌ 重启失败")
        print("请手动运行: lt --port 8000")

if __name__ == '__main__':
    main()

