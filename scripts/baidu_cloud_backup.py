#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
百度云备份和恢复功能
支持将清理的高清图片备份到百度云，并支持恢复
"""

import os
import sys
import json
import requests
import hashlib
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class BaiduCloudBackup:
    """百度云备份管理器"""
    
    def __init__(self):
        self.config_file = 'baidu_cloud_config.json'
        self.backup_log_file = 'image_cleanup_log.json'
        self.config = self.load_config()
        
    def load_config(self):
        """加载百度云配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载百度云配置失败: {e}")
        
        # 默认配置
        default_config = {
            "access_token": "",
            "refresh_token": "",
            "app_key": "",
            "secret_key": "",
            "backup_folder": "/pet_painting_backup",
            "auto_backup": True,
            "backup_retention_days": 365
        }
        
        # 保存默认配置
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config=None):
        """保存百度云配置"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存百度云配置失败: {e}")
    
    def setup_baidu_cloud(self):
        """设置百度云配置"""
        print("🔧 百度云配置设置")
        print("=" * 40)
        
        print("请访问百度云开放平台获取以下信息:")
        print("1. 应用Key (app_key)")
        print("2. 应用Secret (secret_key)")
        print("3. 授权码 (authorization_code)")
        print()
        
        app_key = input("请输入应用Key: ").strip()
        secret_key = input("请输入应用Secret: ").strip()
        auth_code = input("请输入授权码: ").strip()
        
        if not all([app_key, secret_key, auth_code]):
            print("❌ 配置信息不完整")
            return False
        
        # 获取访问令牌
        access_token, refresh_token = self._get_access_token(app_key, secret_key, auth_code)
        
        if access_token:
            self.config.update({
                "app_key": app_key,
                "secret_key": secret_key,
                "access_token": access_token,
                "refresh_token": refresh_token
            })
            
            self.save_config()
            print("✅ 百度云配置设置成功")
            return True
        else:
            print("❌ 获取访问令牌失败")
            return False
    
    def _get_access_token(self, app_key, secret_key, auth_code):
        """获取访问令牌"""
        try:
            url = "https://openapi.baidu.com/oauth/2.0/token"
            params = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": app_key,
                "client_secret": secret_key,
                "redirect_uri": "oob"
            }
            
            response = requests.post(url, data=params)
            result = response.json()
            
            if "access_token" in result:
                return result["access_token"], result.get("refresh_token", "")
            else:
                print(f"获取令牌失败: {result}")
                return None, None
                
        except Exception as e:
            print(f"获取访问令牌异常: {e}")
            return None, None
    
    def refresh_access_token(self):
        """刷新访问令牌"""
        try:
            if not self.config.get("refresh_token"):
                print("❌ 没有刷新令牌")
                return False
            
            url = "https://openapi.baidu.com/oauth/2.0/token"
            params = {
                "grant_type": "refresh_token",
                "refresh_token": self.config["refresh_token"],
                "client_id": self.config["app_key"],
                "client_secret": self.config["secret_key"]
            }
            
            response = requests.post(url, data=params)
            result = response.json()
            
            if "access_token" in result:
                self.config["access_token"] = result["access_token"]
                self.config["refresh_token"] = result.get("refresh_token", self.config["refresh_token"])
                self.save_config()
                print("✅ 访问令牌刷新成功")
                return True
            else:
                print(f"刷新令牌失败: {result}")
                return False
                
        except Exception as e:
            print(f"刷新访问令牌异常: {e}")
            return False
    
    def upload_to_baidu_cloud(self, local_file_path, remote_path):
        """上传文件到百度云"""
        try:
            if not self.config.get("access_token"):
                print("❌ 没有有效的访问令牌")
                return False
            
            # 检查文件是否存在
            if not os.path.exists(local_file_path):
                print(f"❌ 文件不存在: {local_file_path}")
                return False
            
            # 获取上传URL
            upload_url = self._get_upload_url(remote_path)
            if not upload_url:
                return False
            
            # 上传文件
            with open(local_file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(upload_url, files=files)
            
            if response.status_code == 200:
                print(f"✅ 文件上传成功: {remote_path}")
                return True
            else:
                print(f"❌ 文件上传失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"上传文件异常: {e}")
            return False
    
    def _get_upload_url(self, remote_path):
        """获取上传URL"""
        try:
            url = "https://pan.baidu.com/rest/2.0/xpan/file"
            params = {
                "method": "precreate",
                "access_token": self.config["access_token"]
            }
            
            data = {
                "path": remote_path,
                "size": os.path.getsize(remote_path),
                "isdir": 0
            }
            
            response = requests.post(url, params=params, data=data)
            result = response.json()
            
            if result.get("errno") == 0:
                return result.get("uploadid")
            else:
                print(f"获取上传URL失败: {result}")
                return None
                
        except Exception as e:
            print(f"获取上传URL异常: {e}")
            return None
    
    def download_from_baidu_cloud(self, remote_path, local_file_path):
        """从百度云下载文件"""
        try:
            if not self.config.get("access_token"):
                print("❌ 没有有效的访问令牌")
                return False
            
            # 获取下载URL
            download_url = self._get_download_url(remote_path)
            if not download_url:
                return False
            
            # 下载文件
            response = requests.get(download_url)
            if response.status_code == 200:
                with open(local_file_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ 文件下载成功: {local_file_path}")
                return True
            else:
                print(f"❌ 文件下载失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"下载文件异常: {e}")
            return False
    
    def _get_download_url(self, remote_path):
        """获取下载URL"""
        try:
            url = "https://pan.baidu.com/rest/2.0/xpan/file"
            params = {
                "method": "download",
                "access_token": self.config["access_token"],
                "path": remote_path
            }
            
            response = requests.get(url, params=params)
            result = response.json()
            
            if result.get("errno") == 0:
                return result.get("download_url")
            else:
                print(f"获取下载URL失败: {result}")
                return None
                
        except Exception as e:
            print(f"获取下载URL异常: {e}")
            return None
    
    def backup_cleaned_images(self):
        """备份已清理的图片到百度云"""
        try:
            if not self.config.get("auto_backup", True):
                print("⏭️  自动备份已禁用")
                return 0
            
            # 加载清理日志
            if not os.path.exists(self.backup_log_file):
                print("📋 没有清理日志文件")
                return 0
            
            with open(self.backup_log_file, 'r', encoding='utf-8') as f:
                cleanup_log = json.load(f)
            
            backup_folder = self.config.get("backup_folder", "/pet_painting_backup")
            backed_up_count = 0
            
            for order_number, info in cleanup_log.items():
                if info.get("backup_status") == "pending":
                    # 检查本地是否还有文件（可能已经被清理）
                    hd_filename = info["hd_image_filename"]
                    local_path = os.path.join("hd_images", hd_filename)
                    
                    if os.path.exists(local_path):
                        # 上传到百度云
                        remote_path = f"{backup_folder}/hd_images/{hd_filename}"
                        
                        if self.upload_to_baidu_cloud(local_path, remote_path):
                            # 更新备份状态
                            info["backup_status"] = "completed"
                            info["backup_time"] = datetime.now().isoformat()
                            info["backup_path"] = remote_path
                            backed_up_count += 1
                        else:
                            info["backup_status"] = "failed"
                            info["backup_error"] = "上传失败"
                    else:
                        print(f"⚠️  文件已不存在，跳过备份: {hd_filename}")
                        info["backup_status"] = "skipped"
            
            # 保存更新的日志
            with open(self.backup_log_file, 'w', encoding='utf-8') as f:
                json.dump(cleanup_log, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 备份完成，共备份 {backed_up_count} 个文件")
            return backed_up_count
            
        except Exception as e:
            print(f"备份图片异常: {e}")
            return 0
    
    def restore_image_from_backup(self, order_number, local_restore_path=None):
        """从百度云恢复图片"""
        try:
            # 加载清理日志
            if not os.path.exists(self.backup_log_file):
                print("📋 没有清理日志文件")
                return False
            
            with open(self.backup_log_file, 'r', encoding='utf-8') as f:
                cleanup_log = json.load(f)
            
            if order_number not in cleanup_log:
                print(f"❌ 订单 {order_number} 没有备份记录")
                return False
            
            info = cleanup_log[order_number]
            if info.get("backup_status") != "completed":
                print(f"❌ 订单 {order_number} 的备份状态不是已完成")
                return False
            
            backup_path = info.get("backup_path")
            if not backup_path:
                print(f"❌ 订单 {order_number} 没有备份路径")
                return False
            
            # 确定本地恢复路径
            if not local_restore_path:
                hd_filename = info["hd_image_filename"]
                local_restore_path = os.path.join("hd_images", f"restored_{hd_filename}")
            
            # 从百度云下载
            if self.download_from_baidu_cloud(backup_path, local_restore_path):
                print(f"✅ 图片恢复成功: {local_restore_path}")
                return True
            else:
                print(f"❌ 图片恢复失败")
                return False
                
        except Exception as e:
            print(f"恢复图片异常: {e}")
            return False
    
    def list_backup_status(self):
        """列出备份状态"""
        try:
            if not os.path.exists(self.backup_log_file):
                print("📋 没有清理日志文件")
                return
            
            with open(self.backup_log_file, 'r', encoding='utf-8') as f:
                cleanup_log = json.load(f)
            
            if not cleanup_log:
                print("📋 备份日志为空")
                return
            
            print(f"📋 备份状态 (共 {len(cleanup_log)} 条记录):")
            print("-" * 80)
            
            status_count = {"pending": 0, "completed": 0, "failed": 0, "skipped": 0}
            
            for order_number, info in cleanup_log.items():
                status = info.get("backup_status", "unknown")
                status_count[status] = status_count.get(status, 0) + 1
                
                print(f"订单号: {order_number}")
                print(f"客户: {info['customer_name']}")
                print(f"高清图片: {info['hd_image_filename']}")
                print(f"备份状态: {status}")
                if status == "completed":
                    print(f"备份时间: {info.get('backup_time', 'N/A')}")
                    print(f"备份路径: {info.get('backup_path', 'N/A')}")
                elif status == "failed":
                    print(f"错误信息: {info.get('backup_error', 'N/A')}")
                print("-" * 80)
            
            print(f"\n📊 备份统计:")
            for status, count in status_count.items():
                print(f"  {status}: {count}")
                
        except Exception as e:
            print(f"列出备份状态失败: {e}")

def main():
    """主函数"""
    print("☁️  百度云备份管理器")
    print("=" * 40)
    
    backup = BaiduCloudBackup()
    
    while True:
        print("\n请选择操作:")
        print("1. 设置百度云配置")
        print("2. 刷新访问令牌")
        print("3. 备份已清理的图片")
        print("4. 恢复图片")
        print("5. 查看备份状态")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-5): ").strip()
        
        if choice == "1":
            backup.setup_baidu_cloud()
        elif choice == "2":
            backup.refresh_access_token()
        elif choice == "3":
            backup.backup_cleaned_images()
        elif choice == "4":
            order_number = input("请输入订单号: ").strip()
            backup.restore_image_from_backup(order_number)
        elif choice == "5":
            backup.list_backup_status()
        elif choice == "0":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择")

if __name__ == '__main__':
    main()




