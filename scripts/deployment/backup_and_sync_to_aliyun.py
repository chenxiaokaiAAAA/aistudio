#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云服务器备份+同步工具
1. 先在服务器上备份当前版本
2. 然后同步本地最新代码和数据到服务器
"""

import os
import sys
import subprocess
import datetime
import time
from pathlib import Path

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# -------------------------- 配置信息 --------------------------
LOCAL_PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REMOTE_HOST = "121.43.143.59"
REMOTE_USER = "root"
PEM_PATH = os.path.join(LOCAL_PROJECT_PATH, "aliyun-key", "aistudio.pem")
PPK_PATH = os.path.join(LOCAL_PROJECT_PATH, "aliyun-key", "aistudio.ppk")
KEY_PATH = PPK_PATH if os.path.exists(PPK_PATH) else PEM_PATH
REMOTE_PROJECT_PATH = "/root/project_code"

def execute_ssh_command(command, timeout=300):
    """执行SSH命令"""
    ssh_key = PEM_PATH if os.path.exists(PEM_PATH) else KEY_PATH
    if not os.path.exists(ssh_key):
        return False, "密钥文件不存在", ""
    
    pem_path_quoted = f'"{ssh_key}"'
    ssh_cmd = (
        f'ssh -i {pem_path_quoted} '
        f'-o StrictHostKeyChecking=no '
        f'-o ConnectTimeout=10 '
        f'-o BatchMode=yes '
        f'{REMOTE_USER}@{REMOTE_HOST} '
        f'"{command}"'
    )
    
    try:
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "命令执行超时"
    except Exception as e:
        return False, "", str(e)

def backup_remote_server():
    """在服务器上备份当前版本"""
    print("\n" + "="*60)
    print("步骤 1/2: 备份服务器当前版本")
    print("="*60)
    
    # 检查项目目录是否存在
    success, stdout, stderr = execute_ssh_command(f"test -d {REMOTE_PROJECT_PATH} && echo exists || echo not_exists")
    if not success or "not_exists" in stdout:
        print(f"⚠️  警告: 远程项目目录不存在: {REMOTE_PROJECT_PATH}")
        print("   将创建新目录")
    else:
        print(f"✅ 远程项目目录存在: {REMOTE_PROJECT_PATH}")
    
    # 创建备份目录（带时间戳和版本号）
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"/root/project_code_backup_{timestamp}"
    
    print(f"\n📦 创建备份目录: {backup_dir}")
    
    # 创建备份目录
    success, stdout, stderr = execute_ssh_command(f"mkdir -p {backup_dir}")
    if not success:
        print(f"❌ 创建备份目录失败: {stderr}")
        return False, None
    
    print("✅ 备份目录创建成功")
    
    # 备份项目代码
    print("\n📋 备份项目代码...")
    backup_cmd = f"""
    cd /root && \
    if [ -d "{REMOTE_PROJECT_PATH}" ]; then \
        echo "备份代码目录..." && \
        cp -r {REMOTE_PROJECT_PATH}/* {backup_dir}/ 2>/dev/null || true && \
        echo "✅ 代码备份完成" && \
        if [ -f "{REMOTE_PROJECT_PATH}/instance/pet_painting.db" ]; then \
            mkdir -p {backup_dir}/instance && \
            cp {REMOTE_PROJECT_PATH}/instance/pet_painting.db {backup_dir}/instance/pet_painting.db && \
            echo "✅ 数据库已备份" && \
        fi && \
        for dir in uploads final_works hd_images; do \
            if [ -d "{REMOTE_PROJECT_PATH}/$dir" ]; then \
                FILE_COUNT=$(find "{REMOTE_PROJECT_PATH}/$dir" -type f 2>/dev/null | wc -l) && \
                if [ "$FILE_COUNT" -gt 0 ]; then \
                    cp -r "{REMOTE_PROJECT_PATH}/$dir" {backup_dir}/ 2>/dev/null || true && \
                    echo "✅ $dir 已备份 ($FILE_COUNT 个文件)" && \
                fi && \
            fi && \
        done && \
        BACKUP_SIZE=$(du -sh {backup_dir} | cut -f1) && \
        echo "备份大小: $BACKUP_SIZE" && \
        echo "备份位置: {backup_dir}" && \
        echo "备份完成时间: $(date '+%Y-%m-%d %H:%M:%S')" && \
        echo "BACKUP_SUCCESS"; \
    else \
        echo "⚠️  项目目录不存在，创建空备份" && \
        echo "BACKUP_SUCCESS"; \
    fi
    """
    
    success, stdout, stderr = execute_ssh_command(backup_cmd, timeout=600)
    
    if success and "BACKUP_SUCCESS" in stdout:
        print("✅ 服务器备份完成")
        print("\n备份信息:")
        for line in stdout.split('\n'):
            if line.strip() and not line.startswith('备份完成时间'):
                print(f"   {line}")
        
        # 显示备份大小
        size_cmd = f"du -sh {backup_dir} | cut -f1"
        success_size, size_out, _ = execute_ssh_command(size_cmd)
        if success_size:
            print(f"\n📊 备份大小: {size_out.strip()}")
        
        return True, backup_dir
    else:
        print(f"❌ 备份失败: {stderr}")
        return False, None

def sync_to_server():
    """同步本地代码和数据到服务器"""
    print("\n" + "="*60)
    print("步骤 2/2: 同步本地最新代码和数据到服务器")
    print("="*60)
    
    # 导入同步脚本
    sync_script_path = os.path.join(LOCAL_PROJECT_PATH, "scripts", "deployment", "sync_to_aliyun.py")
    if not os.path.exists(sync_script_path):
        print(f"❌ 同步脚本不存在: {sync_script_path}")
        return False
    
    print("\n🔄 执行同步操作...")
    print("   提示: 将同步代码、数据库和图片")
    
    # 执行同步脚本（选择"同步全部"）
    try:
        # 使用subprocess执行同步脚本，自动选择"同步全部"
        process = subprocess.Popen(
            [sys.executable, sync_script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=LOCAL_PROJECT_PATH
        )
        
        # 发送"4"（同步全部）和确认"Y"
        input_data = "4\nY\n"
        stdout, stderr = process.communicate(input=input_data, timeout=3600)
        
        print(stdout)
        if stderr:
            print("错误输出:", stderr)
        
        if process.returncode == 0:
            print("\n✅ 同步完成")
            return True
        else:
            print(f"\n⚠️  同步可能有问题，返回码: {process.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 同步超时（超过1小时）")
        return False
    except Exception as e:
        print(f"❌ 同步过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print(f"\n{'='*60}")
    print("阿里云服务器备份+同步工具")
    print(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    print(f"\n📋 配置信息:")
    print(f"   本地路径: {LOCAL_PROJECT_PATH}")
    print(f"   服务器: {REMOTE_USER}@{REMOTE_HOST}")
    print(f"   远程路径: {REMOTE_PROJECT_PATH}")
    print(f"   密钥文件: {KEY_PATH}")
    
    # 确认操作
    print("\n⚠️  警告: 此操作将:")
    print("   1. 在服务器上备份当前版本")
    print("   2. 同步本地最新代码和数据到服务器（覆盖远程文件）")
    print("   3. 同步内容包括: 代码、数据库、图片")
    
    confirm = input("\n确认继续? (Y/N): ").strip().upper()
    if confirm != "Y":
        print("已取消操作")
        return
    
    # 步骤1: 备份服务器
    backup_success, backup_dir = backup_remote_server()
    if not backup_success:
        print("\n❌ 备份失败，停止同步操作")
        print("   提示: 请检查SSH连接和服务器状态")
        return
    
    print(f"\n✅ 备份成功，备份位置: {backup_dir}")
    
    # 步骤2: 同步到服务器
    sync_success = sync_to_server()
    
    # 最终报告
    print(f"\n{'='*60}")
    print("操作完成报告")
    print(f"{'='*60}")
    if backup_success:
        print(f"✅ 备份: 成功")
        print(f"   备份位置: {backup_dir}")
    else:
        print(f"❌ 备份: 失败")
    
    if sync_success:
        print(f"✅ 同步: 成功")
    else:
        print(f"❌ 同步: 失败或部分失败")
    
    print(f"{'='*60}\n")
    
    # 询问是否重启服务
    restart = input("是否重启服务器上的服务? (Y/N): ").strip().upper()
    if restart == "Y":
        print("\n🔄 重启服务...")
        success, stdout, stderr = execute_ssh_command("systemctl restart aistudio")
        if success:
            print("✅ 服务已重启")
        else:
            print(f"⚠️  服务重启失败: {stderr}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
