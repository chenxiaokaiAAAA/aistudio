#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTTPS证书配置助手
帮助配置阿里云SSL证书
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime

def check_cert_files():
    """检查证书文件"""
    print("🔍 检查证书文件...")
    
    ssl_dir = r"C:\nginx\ssl"
    
    if not os.path.exists(ssl_dir):
        print(f"❌ SSL目录不存在: {ssl_dir}")
        return False
    
    # 检查文件
    files = os.listdir(ssl_dir)
    print(f"📁 SSL目录中的文件: {files}")
    
    # 检查私钥文件
    key_file = os.path.join(ssl_dir, "photogooo.key")
    if os.path.exists(key_file):
        print(f"✅ 私钥文件存在: {key_file}")
        # 检查私钥文件内容
        try:
            with open(key_file, 'r') as f:
                content = f.read()
                if "BEGIN PRIVATE KEY" in content or "BEGIN RSA PRIVATE KEY" in content:
                    print("✅ 私钥文件格式正确")
                else:
                    print("⚠️  私钥文件格式可能有问题")
        except Exception as e:
            print(f"❌ 读取私钥文件失败: {str(e)}")
    else:
        print(f"❌ 私钥文件不存在: {key_file}")
        return False
    
    # 检查证书文件
    cert_files = [f for f in files if f.endswith(('.crt', '.pem', '.cer'))]
    if cert_files:
        cert_file = os.path.join(ssl_dir, cert_files[0])
        print(f"✅ 证书文件存在: {cert_file}")
        # 检查证书文件内容
        try:
            with open(cert_file, 'r') as f:
                content = f.read()
                if "BEGIN CERTIFICATE" in content:
                    print("✅ 证书文件格式正确")
                else:
                    print("⚠️  证书文件格式可能有问题")
        except Exception as e:
            print(f"❌ 读取证书文件失败: {str(e)}")
    else:
        print("❌ 没有找到证书文件 (.crt, .pem, .cer)")
        print("请确保您已下载完整的SSL证书文件")
        return False
    
    return True

def create_nginx_config():
    """创建nginx配置文件"""
    print("\n🔧 创建nginx配置文件...")
    
    ssl_dir = r"C:\nginx\ssl"
    
    # 查找证书文件
    files = os.listdir(ssl_dir)
    cert_files = [f for f in files if f.endswith(('.crt', '.pem', '.cer'))]
    cert_file = os.path.join(ssl_dir, cert_files[0]) if cert_files else ""
    key_file = os.path.join(ssl_dir, "photogooo.key")
    
    nginx_config = f"""# HTTP服务器 - 重定向到HTTPS
server {{
    listen 80;
    server_name photogooo www.photogooo;  # AI自拍机-域名
    
    # 重定向所有HTTP请求到HTTPS
    return 301 https://$server_name$request_uri;
}}

# HTTPS服务器
server {{
    listen 443 ssl http2;
    server_name photogooo www.photogooo;  # AI自拍机-域名

    # SSL证书配置 - 阿里云证书
    ssl_certificate "{cert_file}";
    ssl_certificate_key "{key_file}";
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 静态文件处理
    location /static/ {{
        alias C:/new/pet-painting-system/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }}

    # 上传文件处理
    location /uploads/ {{
        alias C:/new/pet-painting-system/uploads/;
        expires 30d;
    }}

    # 高清图片处理
    location /hd_images/ {{
        alias C:/new/pet-painting-system/hd_images/;
        expires 30d;
    }}

    # 代理到Flask应用
    location / {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }}

    # 文件上传大小限制
    client_max_body_size 20M;
}}
"""
    
    # 备份原配置文件
    original_config = "nginx.conf"
    if os.path.exists(original_config):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_config = f"nginx_backup_{timestamp}.conf"
        shutil.copy2(original_config, backup_config)
        print(f"✅ 原配置文件已备份为: {backup_config}")
    
    # 写入新配置
    with open(original_config, 'w', encoding='utf-8') as f:
        f.write(nginx_config)
    
    print(f"✅ nginx配置文件已更新")
    return True

def test_nginx_config():
    """测试nginx配置"""
    print("\n🧪 测试nginx配置...")
    
    try:
        # 测试nginx配置语法
        result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ nginx配置语法正确")
            return True
        else:
            print(f"❌ nginx配置语法错误:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ 找不到nginx命令，请确保nginx已安装并在PATH中")
        return False
    except Exception as e:
        print(f"❌ 测试nginx配置失败: {str(e)}")
        return False

def restart_nginx():
    """重启nginx服务"""
    print("\n🔄 重启nginx服务...")
    
    try:
        # 停止nginx
        subprocess.run(['nginx', '-s', 'stop'], capture_output=True)
        print("✅ nginx已停止")
        
        # 启动nginx
        subprocess.run(['nginx'], capture_output=True)
        print("✅ nginx已启动")
        
        return True
        
    except FileNotFoundError:
        print("❌ 找不到nginx命令，请手动重启nginx服务")
        return False
    except Exception as e:
        print(f"❌ 重启nginx失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("🚀 HTTPS证书配置助手")
    print("=" * 50)
    
    # 1. 检查证书文件
    print("1️⃣ 检查证书文件...")
    if not check_cert_files():
        print("\n❌ 证书文件检查失败")
        print("请确保您已下载完整的SSL证书文件到 C:\\nginx\\ssl\\ 目录")
        print("需要的文件:")
        print("  - 证书文件 (.crt, .pem, .cer)")
        print("  - 私钥文件 (.key)")
        return
    
    # 2. 创建nginx配置
    print("\n2️⃣ 创建nginx配置...")
    if not create_nginx_config():
        print("❌ 创建nginx配置失败")
        return
    
    # 3. 测试nginx配置
    print("\n3️⃣ 测试nginx配置...")
    if not test_nginx_config():
        print("❌ nginx配置测试失败")
        return
    
    # 4. 重启nginx
    print("\n4️⃣ 重启nginx服务...")
    if not restart_nginx():
        print("❌ 重启nginx失败")
        return
    
    print("\n🎉 HTTPS证书配置完成！")
    print("现在您可以通过 https://photogooo 访问您的网站了")
    print("浏览器应该不再显示不安全提示")

if __name__ == "__main__":
    main()
