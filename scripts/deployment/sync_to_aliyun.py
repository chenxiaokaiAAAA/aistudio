#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云服务器同步工具
支持增量同步数据、图片、代码到阿里云服务器
"""

import os
import sys
import shutil
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
        # Python < 3.7
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# -------------------------- 配置信息 --------------------------
# 本地项目根目录（Windows路径格式）
LOCAL_PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# 阿里云服务器信息
REMOTE_HOST = "121.43.143.59"
REMOTE_USER = "root"
# 本地密钥路径（优先使用 PPK，如果没有则使用 PEM）
PPK_PATH = os.path.join(LOCAL_PROJECT_PATH, "aliyun-key", "aistudio.ppk")
PEM_PATH = os.path.join(LOCAL_PROJECT_PATH, "aliyun-key", "aistudio.pem")
# 实际使用的密钥路径（优先 PPK）
KEY_PATH = PPK_PATH if os.path.exists(PPK_PATH) else PEM_PATH
# 服务器上的项目根目录
REMOTE_PROJECT_PATH = "/root/project_code"

# 同步工具选择：WinSCP（推荐，Windows下更稳定）
USE_WINSCP = True
# 是否使用scp（如果WinSCP不可用）
USE_SCP = False

# 同步选项对应的目录映射
SYNC_OPTIONS = {
        "1": {
        "name": "仅同步数据库",
        "dirs": ["instance"],
        "description": "同步数据库 (PostgreSQL/SQLite)"
    },
    "2": {
        "name": "仅同步图片",
        "dirs": ["uploads", "final_works", "hd_images"],
        "description": "同步图片目录"
    },
    "3": {
        "name": "仅同步代码",
        "dirs": ["app", "batch", "config", "scripts", "static", "templates", "workflows"],
        "description": "同步代码目录（通过Git推送）"
    },
    "4": {
        "name": "同步全部",
        "dirs": ["app", "batch", "config", "scripts", "static", "templates", "workflows", "docs", "instance", "uploads", "final_works", "hd_images"],
        "description": "同步代码+数据库+图片（含API文档等全部更新）"
    }
}

def load_database_url():
    """从 .env 或环境变量加载 DATABASE_URL"""
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        env_path = os.path.join(LOCAL_PROJECT_PATH, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("DATABASE_URL="):
                        db_url = line.split("=", 1)[1].strip().strip("'\"")
                        break
    return db_url


def find_pg_dump():
    """查找 pg_dump 可执行文件路径"""
    # 1. 先查 PATH
    pg_dump = shutil.which("pg_dump")
    if pg_dump:
        return pg_dump
    # 2. 常见 PostgreSQL 安装路径 (Windows)
    for ver in ("18", "17", "16", "15", "14", "13", "12"):
        for drive in ("C", "D", "E"):
            path = f"{drive}:\\Program Files\\PostgreSQL\\{ver}\\bin\\pg_dump.exe"
            if os.path.exists(path):
                return path
    # 3. Program Files (x86)
    pf86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
    for ver in ("18", "17", "16", "15", "14"):
        path = os.path.join(pf86, f"PostgreSQL\\{ver}\\bin\\pg_dump.exe")
        if os.path.exists(path):
            return path
    return None


def sync_postgresql_to_remote():
    """使用 pg_dump + scp + psql 同步 PostgreSQL 到远程服务器"""
    db_url = load_database_url()
    if not db_url or "postgresql" not in db_url:
        return False
    try:
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        pg_user = parsed.username or "postgres"
        pg_pass = parsed.password or ""
        pg_host = parsed.hostname or "localhost"
        pg_port = parsed.port or 5432
        pg_db = parsed.path.lstrip("/").split("?")[0] or "pet_painting"
    except Exception as e:
        print(f"   [错误] 解析 DATABASE_URL 失败: {e}")
        return False
    pg_dump_exe = find_pg_dump()
    if not pg_dump_exe:
        print(f"   [错误] 未找到 pg_dump，请将 PostgreSQL 的 bin 目录加入系统 PATH")
        print(f"   例如: C:\\Program Files\\PostgreSQL\\16\\bin")
        return False
    dump_path = os.path.join(LOCAL_PROJECT_PATH, "instance", "pet_painting_dump_temp.sql")
    remote_dump = f"{REMOTE_PROJECT_PATH}/instance/pet_painting_dump_temp.sql"
    os.makedirs(os.path.dirname(dump_path), exist_ok=True)
    print(f"   数据库类型: PostgreSQL")
    print(f"   导出本地数据库...")
    env = os.environ.copy()
    env["PGPASSWORD"] = pg_pass
    # --clean --if-exists：导出时包含 DROP 语句，恢复时先删后建，确保服务器数据被本地完全覆盖
    r = subprocess.run(
        [pg_dump_exe, "-h", pg_host, "-p", str(pg_port), "-U", pg_user, "-d", pg_db, "-F", "p", "--clean", "--if-exists", "-f", dump_path],
        env=env, capture_output=True, text=True, timeout=3600, encoding="utf-8", errors="replace"
    )
    if r.returncode != 0:
        print(f"   [错误] pg_dump 失败: {r.stderr or r.stdout}")
        return False
    size_mb = os.path.getsize(dump_path) / (1024 * 1024)
    print(f"   导出完成: {size_mb:.2f} MB")
    print(f"   上传到服务器...")
    key_file = PEM_PATH if os.path.exists(PEM_PATH) else KEY_PATH
    ssh_key = f'-i "{key_file}"' if os.path.exists(key_file) and key_file.endswith(".pem") else ""
    scp_cmd = f'scp {ssh_key} "{dump_path}" {REMOTE_USER}@{REMOTE_HOST}:{remote_dump}'
    r2 = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True, timeout=300, cwd=LOCAL_PROJECT_PATH)
    try:
        os.remove(dump_path)
    except Exception:
        pass
    if r2.returncode != 0:
        print(f"   [错误] 上传失败: {r2.stderr or r2.stdout}")
        return False
    # 恢复时使用服务器 .env 中的密码（与本地可不同），避免覆盖服务器配置
    server_pass = pg_pass
    get_env_cmd = f'ssh {ssh_key} -o StrictHostKeyChecking=no {REMOTE_USER}@{REMOTE_HOST} "grep -E \'^DATABASE_URL=\' {REMOTE_PROJECT_PATH}/.env 2>/dev/null | head -1 | sed \'s/^DATABASE_URL=//\'"'
    r_env = subprocess.run(get_env_cmd, shell=True, capture_output=True, text=True, timeout=10, cwd=LOCAL_PROJECT_PATH)
    if r_env.returncode == 0 and r_env.stdout and "postgresql" in r_env.stdout:
        try:
            from urllib.parse import urlparse, unquote
            server_url = r_env.stdout.strip().strip('"').strip("'")
            p = urlparse(server_url)
            if p.password is not None:
                server_pass = unquote(p.password)
        except Exception:
            pass
    print(f"   在服务器上恢复...")
    pass_esc = server_pass.replace("'", "'\"'\"'")
    restore_cmd = f"cd {REMOTE_PROJECT_PATH} && PGPASSWORD='{pass_esc}' psql -h localhost -p {pg_port} -U {pg_user} -d {pg_db} -f instance/pet_painting_dump_temp.sql -q 2>/dev/null; rm -f instance/pet_painting_dump_temp.sql"
    ssh_cmd = f'ssh {ssh_key} -o StrictHostKeyChecking=no {REMOTE_USER}@{REMOTE_HOST} "{restore_cmd}"'
    r3 = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=600, cwd=LOCAL_PROJECT_PATH)
    if r3.returncode != 0:
        print(f"   [警告] 恢复可能未完全成功，请检查服务器")
        return True
    print(f"   [OK] PostgreSQL 同步完成")
    # 不再用本地 DATABASE_URL 覆盖服务器 .env（本地与服务器密码可不同，避免同步后服务器无法启动）
    print(f"   [提示] 服务器 .env 未修改，请保持服务器自己的 DATABASE_URL 与 PostgreSQL 密码一致")
    return True


def check_remote_rsync():
    """检查远程服务器是否安装了 rsync"""
    # 使用与用户手动测试完全相同的命令格式（shell=True）
    # 用户手动执行的命令：ssh -i "E:\AI-STUDIO\aistudio\aliyun-key\aistudio.pem" root@121.43.143.59 "rsync --version"
    
    # 构建 SSH 命令字符串（Windows 路径需要用双引号包裹）
    pem_path_quoted = f'"{PEM_PATH}"'  # 始终使用双引号包裹路径
    ssh_cmd = (
        f'ssh -i {pem_path_quoted} '
        f'-o StrictHostKeyChecking=no '
        f'-o ConnectTimeout=10 '
        f'{REMOTE_USER}@{REMOTE_HOST} '
        f'"rsync --version"'
    )
    
    try:
        # 使用 shell=True 执行命令（与用户手动执行方式一致）
        result = subprocess.run(
            ssh_cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=15
        )
        
        # 调试信息（可选，如果需要可以取消注释）
        # print(f"[DEBUG] Return code: {result.returncode}")
        # print(f"[DEBUG] Stdout: {result.stdout[:200]}")
        # print(f"[DEBUG] Stderr: {result.stderr[:200]}")
        
        # 检查返回码和输出
        if result.returncode == 0:
            output = result.stdout.strip()
            if not output:
                # 如果 stdout 为空，检查 stderr（某些情况下版本信息可能在 stderr）
                output = result.stderr.strip()
            
            # 查找版本信息（可能在输出的任何位置）
            if output:
                lines = output.split('\n')
                for line in lines:
                    line_lower = line.lower()
                    if "rsync version" in line_lower:
                        # 提取版本号（例如：rsync version 3.2.7）
                        version_line = line.strip()
                        return True, version_line
                
                # 如果输出包含 rsync 相关信息，即使没有明确的版本行，也认为已安装
                if "rsync" in output.lower() and ("protocol" in output.lower() or "copyright" in output.lower()):
                    # 尝试提取第一行作为版本信息
                    first_line = lines[0].strip() if lines else "rsync installed"
                    return True, first_line
        
        # 如果返回码非0，检查是否是"命令未找到"错误
        if result.returncode != 0:
            error_output = (result.stderr + result.stdout).lower()
            # 如果错误信息明确表示命令未找到，说明未安装
            if "command not found" in error_output or "not found" in error_output:
                return False, None
            # 其他错误（如连接错误）不一定是未安装，返回 False 让用户知道有问题
        
        return False, None
        
    except subprocess.TimeoutExpired:
        # 超时可能是连接问题
        return False, None
    except Exception as e:
        # 如果出现异常，返回 False
        # print(f"[DEBUG] Exception: {str(e)}")  # 调试用
        return False, None

def install_remote_rsync():
    """尝试在远程服务器上安装 rsync"""
    pem_path_escaped = PEM_PATH.replace("\\", "/")
    if " " in pem_path_escaped:
        pem_path_escaped = f'"{pem_path_escaped}"'
    
    print("\n🔧 尝试在远程服务器上安装 rsync...")
    
    # 检测系统类型并安装
    detect_cmd = (
        f"ssh -i {pem_path_escaped} "
        f"-o StrictHostKeyChecking=no "
        f"-o ConnectTimeout=10 "
        f"{REMOTE_USER}@{REMOTE_HOST} "
        f"'if command -v apt-get > /dev/null 2>&1; then echo ubuntu; elif command -v yum > /dev/null 2>&1; then echo centos; elif command -v dnf > /dev/null 2>&1; then echo fedora; else echo unknown; fi'"
    )
    
    try:
        result = subprocess.run(
            detect_cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        system_type = result.stdout.strip().lower()
        
        if system_type == "ubuntu" or system_type == "debian":
            install_cmd = (
                f"ssh -i {pem_path_escaped} "
                f"-o StrictHostKeyChecking=no "
                f"-o ConnectTimeout=30 "
                f"{REMOTE_USER}@{REMOTE_HOST} "
                f"'apt-get update && apt-get install -y rsync'"
            )
        elif system_type == "centos" or system_type == "rhel":
            install_cmd = (
                f"ssh -i {pem_path_escaped} "
                f"-o StrictHostKeyChecking=no "
                f"-o ConnectTimeout=30 "
                f"{REMOTE_USER}@{REMOTE_HOST} "
                f"'yum install -y rsync'"
            )
        elif system_type == "fedora":
            install_cmd = (
                f"ssh -i {pem_path_escaped} "
                f"-o StrictHostKeyChecking=no "
                f"-o ConnectTimeout=30 "
                f"{REMOTE_USER}@{REMOTE_HOST} "
                f"'dnf install -y rsync'"
            )
        else:
            print("❌ 无法自动检测系统类型，请手动安装 rsync")
            return False
        
        print(f"   检测到系统类型: {system_type}")
        print("   正在安装 rsync（需要 root 权限）...")
        
        install_result = subprocess.run(
            install_cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300
        )
        
        if install_result.returncode == 0:
            print("✅ rsync 安装成功！")
            return True
        else:
            print(f"❌ rsync 安装失败: {install_result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 安装过程出错: {str(e)}")
        return False

def check_dependencies():
    """检查必要的依赖"""
    global PEM_PATH, USE_SCP, USE_WINSCP
    
    # 检查 WinSCP（推荐，Windows下更稳定）
    winscp_found = False
    winscp_cmd_found = None
    
    # 扩展的 WinSCP 路径列表
    winscp_paths = [
        "C:\\Users\\Administrator\\AppData\\Local\\Programs\\WinSCP\\WinSCP.com",  # 用户提供的路径
        "C:\\Program Files\\WinSCP\\WinSCP.com",
        "C:\\Program Files (x86)\\WinSCP\\WinSCP.com",
        os.path.expanduser("~\\AppData\\Local\\Programs\\WinSCP\\WinSCP.com"),  # 通用用户路径
        "WinSCP.com"  # 如果在 PATH 中
    ]
    
    # 尝试从注册表查找（如果可用）
    if sys.platform == 'win32':
        try:
            import winreg
            # 检查注册表中的 WinSCP 安装路径
            reg_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WinSCP"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\WinSCP"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\WinSCP"),
            ]
            for hkey, path in reg_paths:
                try:
                    key = winreg.OpenKey(hkey, path)
                    install_dir = winreg.QueryValueEx(key, "InstallationDirectory")[0]
                    winscp_paths.insert(0, os.path.join(install_dir, "WinSCP.com"))
                    winreg.CloseKey(key)
                except:
                    pass
        except:
            pass
    
    for winscp_cmd in winscp_paths:
        # 先检查文件是否存在（对于具体路径）
        if winscp_cmd != "WinSCP.com":
            if not os.path.exists(winscp_cmd):
                continue
            # 确保是文件而不是目录
            if not os.path.isfile(winscp_cmd):
                continue
        
        # 尝试执行版本检查
        # 使用更简单的方法：只要能执行命令（不抛出 FileNotFoundError），就认为找到了
        try:
            result = subprocess.run([winscp_cmd, "/version"], 
                                   capture_output=True, timeout=5)
            # 只要命令能执行（不抛出 FileNotFoundError），就认为找到了
            # WinSCP /version 可能返回 0 或 1，都算正常
            winscp_found = True
            winscp_cmd_found = winscp_cmd
            USE_WINSCP = True
            USE_SCP = False
            print(f"✅ 找到 WinSCP: {winscp_cmd_found}")
            break
        except FileNotFoundError:
            # 文件不存在，继续下一个
            continue
        except subprocess.TimeoutExpired:
            # 超时也认为找到了（说明程序能运行，只是响应慢）
            winscp_found = True
            winscp_cmd_found = winscp_cmd
            USE_WINSCP = True
            USE_SCP = False
            print(f"✅ 找到 WinSCP: {winscp_cmd_found}")
            break
        except Exception:
            # 其他异常（如权限问题等），也继续尝试下一个路径
            continue
    
    # 如果 WinSCP 不可用，尝试让用户手动指定路径
    if not winscp_found:
        print("ℹ️  未找到 WinSCP，尝试手动查找...")
        # 尝试在常见位置搜索
        search_dirs = [
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            os.path.expanduser("~\\AppData\\Local\\Programs"),
        ]
        
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                try:
                    for item in os.listdir(search_dir):
                        winscp_dir = os.path.join(search_dir, item, "WinSCP")
                        winscp_exe = os.path.join(winscp_dir, "WinSCP.com")
                        if os.path.exists(winscp_exe):
                            try:
                                result = subprocess.run([winscp_exe, "/version"], 
                                                       capture_output=True, check=True, timeout=5)
                                winscp_found = True
                                winscp_cmd_found = winscp_exe
                                USE_WINSCP = True
                                USE_SCP = False
                                print(f"✅ 找到 WinSCP: {winscp_exe}")
                                break
                            except:
                                pass
                except:
                    pass
        
        if not winscp_found:
            print("   未在常见位置找到 WinSCP")
            print("   提示: 安装 WinSCP 可获得更好的同步体验（支持增量同步）")
            print("   下载: https://winscp.net/eng/download.php")
            print("   注意: 远程服务器无需安装任何软件（使用 SFTP/SCP 协议）")
            # 询问用户是否想手动指定路径
            manual_path = input("\n   如果 WinSCP 已安装，请输入 WinSCP.com 的完整路径（直接回车跳过）: ").strip()
            if manual_path and os.path.exists(manual_path):
                try:
                    result = subprocess.run([manual_path, "/version"], 
                                           capture_output=True, check=True, timeout=5)
                    winscp_found = True
                    winscp_cmd_found = manual_path
                    USE_WINSCP = True
                    USE_SCP = False
                    print(f"✅ 使用指定的 WinSCP: {manual_path}")
                except:
                    print("   ⚠️  指定的路径无效，将使用 scp")
            print()
        
        scp_found = False
        try:
            result = subprocess.run(["scp"], capture_output=True, timeout=5)
            scp_found = True
        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            scp_found = True
        
        if scp_found:
            USE_SCP = True
            USE_WINSCP = False
        else:
            print("❌ 错误: 未找到 WinSCP 或 scp 命令")
            print("\n请安装以下工具之一:")
            print("1. WinSCP (推荐，Windows下更稳定)")
            print("   - 下载: https://winscp.net/eng/download.php")
            print("   - 支持增量同步，跳过未修改文件")
            print("\n2. OpenSSH 客户端 (包含 scp)")
            print("   - Windows 10/11: 设置 -> 应用 -> 可选功能 -> OpenSSH 客户端")
            return False
    
    # 检查SSH密钥文件
    # 检查密钥文件（优先 PPK，其次 PEM）
    global KEY_PATH
    if not os.path.exists(KEY_PATH):
        # 尝试查找密钥文件
        key_dir = os.path.dirname(PPK_PATH)
        if os.path.exists(key_dir):
            key_files = [f for f in os.listdir(key_dir) if f.endswith(('.pem', '.key', '.ppk'))]
            if key_files:
                # 优先选择 PPK 文件
                ppk_files = [f for f in key_files if f.endswith('.ppk')]
                if ppk_files:
                    KEY_PATH = os.path.join(key_dir, ppk_files[0])
                    print(f"ℹ️  使用密钥文件: {KEY_PATH} (PPK)")
                else:
                    KEY_PATH = os.path.join(key_dir, key_files[0])
                    print(f"ℹ️  使用密钥文件: {KEY_PATH}")
            else:
                print(f"⚠️  警告: 未找到密钥文件")
                print(f"   请确保密钥文件存在于: {key_dir}")
                print(f"   推荐使用 PPK 格式（WinSCP 支持）")
        else:
            print(f"⚠️  警告: 密钥目录不存在: {key_dir}")
    
    print("\n📝 说明:")
    print("   - 本地需要: WinSCP 或 OpenSSH 客户端")
    print("   - 远程需要: 无需安装任何软件（使用标准 SFTP/SCP 协议）")
    
    return True

def get_sync_option():
    """让用户选择同步类型"""
    print("\n" + "="*50)
    print("请选择同步类型:")
    print("="*50)
    for key, value in SYNC_OPTIONS.items():
        print(f"{key}. {value['name']} - {value['description']}")
    print("0. 取消")
    print("="*50)
    
    while True:
        choice = input("请输入选项编号(0-4): ").strip()
        if choice == "0":
            return None
        if choice in SYNC_OPTIONS:
            return SYNC_OPTIONS[choice]
        print("❌ 无效选项，请重新输入")

def count_local_files(directory):
    """统计本地目录中的文件数量"""
    if not os.path.exists(directory):
        return 0
    count = 0
    try:
        for root, dirs, files in os.walk(directory):
            count += len(files)
    except Exception as e:
        print(f"    [警告] 统计本地文件时出错: {e}")
        return 0
    return count

def count_remote_files(remote_dir, show_debug=False):
    """通过 SSH 统计服务器上的文件数量"""
    # SSH 命令使用 PEM 文件（SSH 不支持 PPK，需要 PEM）
    ssh_key = PEM_PATH if os.path.exists(PEM_PATH) else KEY_PATH
    if not os.path.exists(ssh_key):
        if show_debug:
            print(f"    [调试] 密钥文件不存在: {ssh_key}")
        return -1  # 密钥文件不存在
    
    # 构建统计命令：使用 find 命令统计文件数量
    # Windows 上使用双引号包裹整个命令，远程命令中使用单引号包裹路径
    # 转义路径中的单引号
    escaped_path = remote_dir.replace("'", "'\"'\"'")
    # 使用双引号包裹整个 SSH 命令，远程命令用单引号
    cmd = f'ssh -i "{ssh_key}" -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes {REMOTE_USER}@{REMOTE_HOST} "find \'{escaped_path}\' -type f 2>/dev/null | wc -l"'
    
    if show_debug:
        print(f"    [调试] 执行统计命令: {cmd}")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=30
        )
        if show_debug:
            print(f"    [调试] 返回码: {result.returncode}")
            print(f"    [调试] 输出: {result.stdout}")
            print(f"    [调试] 错误: {result.stderr}")
        
        if result.returncode == 0:
            count_str = result.stdout.strip()
            # 移除可能的空白字符和换行符
            count_str = count_str.split()[0] if count_str.split() else count_str
            if count_str.isdigit():
                return int(count_str)
            elif show_debug:
                print(f"    [调试] 输出不是数字: '{count_str}'")
        
        # 如果命令失败，尝试更简单的方法
        # 先检查目录是否存在
        check_cmd = f'ssh -i "{ssh_key}" -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes {REMOTE_USER}@{REMOTE_HOST} "test -d \'{escaped_path}\' && echo exists || echo not_exists"'
        check_result = subprocess.run(
            check_cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        if check_result.returncode == 0 and 'not_exists' in check_result.stdout:
            return 0  # 目录不存在，文件数为0
        
        if show_debug:
            print(f"    [调试] 统计失败，返回码: {result.returncode}")
        return -1  # 表示无法获取
    except subprocess.TimeoutExpired:
        if show_debug:
            print(f"    [调试] 命令超时")
        return -1
    except Exception as e:
        if show_debug:
            print(f"    [调试] 执行异常: {e}")
        return -1

def run_winscp(local_dir, remote_dir, full_overwrite=False):
    """使用 WinSCP 同步目录，返回同步结果。
    full_overwrite: True=全量(同名一律覆盖)，False=增量(仅传时间/大小有变化的)
    """
    # 确保本地目录存在
    if not os.path.exists(local_dir):
        return 1, "", f"本地目录不存在: {local_dir}"
    
    # 查找 WinSCP（使用与 check_dependencies 相同的逻辑）
    winscp_paths = [
        "C:\\Users\\Administrator\\AppData\\Local\\Programs\\WinSCP\\WinSCP.com",  # 用户提供的路径
        "C:\\Program Files\\WinSCP\\WinSCP.com",
        "C:\\Program Files (x86)\\WinSCP\\WinSCP.com",
        os.path.expanduser("~\\AppData\\Local\\Programs\\WinSCP\\WinSCP.com"),  # 通用用户路径
        "WinSCP.com"
    ]
    
    # 尝试从注册表查找
    if sys.platform == 'win32':
        try:
            import winreg
            reg_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WinSCP"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\WinSCP"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\WinSCP"),
            ]
            for hkey, path in reg_paths:
                try:
                    key = winreg.OpenKey(hkey, path)
                    install_dir = winreg.QueryValueEx(key, "InstallationDirectory")[0]
                    winscp_paths.insert(0, os.path.join(install_dir, "WinSCP.com"))
                    winreg.CloseKey(key)
                except:
                    pass
        except:
            pass
    
    winscp_cmd = None
    for path in winscp_paths:
        # 先检查文件是否存在（对于具体路径）
        if path != "WinSCP.com":
            if not os.path.exists(path):
                continue
            if not os.path.isfile(path):
                continue
        
        # 尝试执行版本检查
        try:
            result = subprocess.run([path, "/version"], 
                                   capture_output=True, timeout=5)
            # 只要命令能执行（不抛出 FileNotFoundError），就认为找到了
            winscp_cmd = path
            break
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            # 超时也认为找到了
            winscp_cmd = path
            break
        except Exception:
            # 其他异常，继续尝试下一个
            continue
    
    if not winscp_cmd:
        return 1, "", "未找到 WinSCP，请先安装 WinSCP"
    
    # 转换路径格式
    local_path = os.path.abspath(local_dir).replace("\\", "/")
    remote_path = remote_dir.replace("\\", "/")
    
    # 构建 WinSCP 脚本
    # WinSCP 脚本语法：同步本地到远程，仅上传新文件和已修改文件
    # 注意：WinSCP 脚本中的路径需要使用正斜杠，密钥路径需要转义引号
    # 确保本地路径以斜杠结尾（目录同步需要）
    if not local_path.endswith("/"):
        local_path += "/"
    if not remote_path.endswith("/"):
        remote_path += "/"
    
    # WinSCP 优先使用 PPK 文件（如果存在），否则使用 PEM 文件
    # 转义密钥路径中的引号
    key_path_escaped = KEY_PATH.replace("\\", "/").replace('"', '\\"')
    if KEY_PATH.endswith(".ppk"):
        print(f"    [提示] 使用 PPK 密钥文件: {KEY_PATH}")
    else:
        print(f"    [警告] 使用 PEM 密钥文件（WinSCP 可能不支持，建议转换为 PPK）: {KEY_PATH}")
    
    # WinSCP 脚本格式：每行一个命令
    # full_overwrite: -criteria=none 同名一律覆盖；否则 -criteria=time,size 仅传有变化的
    criteria = "none" if full_overwrite else "time,size"
    winscp_script = f"""open sftp://{REMOTE_USER}@{REMOTE_HOST}/ -privatekey="{key_path_escaped}" -hostkey="*"
option batch abort
option confirm off
# 同步本地到远程；-criteria={criteria} {"(全量覆盖)" if full_overwrite else "(增量)"}
synchronize remote -delete -mirror -criteria={criteria} "{local_path}" "{remote_path}"
close
exit
"""
    
    # 将脚本写入临时文件
    script_file = os.path.join(LOCAL_PROJECT_PATH, ".winscp_temp_script.txt")
    try:
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(winscp_script)
        
        # 执行 WinSCP 脚本
        # 注意：WinSCP 在 Windows 上默认使用系统编码（通常是 GBK），需要指定编码
        log_file = script_file.replace(".txt", ".log")
        cmd = [winscp_cmd, "/script=" + script_file, "/log=" + log_file]
        # 使用 errors='ignore' 或 'replace' 来处理编码错误
        # 添加调试输出
        print(f"    [调试] 执行命令: {' '.join(cmd)}")
        print(f"    [调试] 本地路径: {local_path}")
        print(f"    [调试] 远程路径: {remote_path}")
        result = subprocess.run(cmd, capture_output=True, timeout=3600)
        
        # 读取日志文件
        log_output = ""
        if os.path.exists(log_file):
            try:
                # WinSCP 在 Windows 上默认使用 GBK 编码
                # 尝试多种编码方式
                encodings = ['gbk', 'utf-8', 'cp936', 'latin1']
                for encoding in encodings:
                    try:
                        with open(log_file, "r", encoding=encoding, errors='replace') as f:
                            log_output = f.read()
                            break
                    except:
                        continue
            except:
                pass
        
        # 解码 subprocess 输出（如果日志文件读取失败）
        stdout_text = ""
        stderr_text = ""
        if result.stdout:
            try:
                stdout_text = result.stdout.decode('gbk', errors='replace')
            except:
                try:
                    stdout_text = result.stdout.decode('utf-8', errors='replace')
                except:
                    stdout_text = str(result.stdout)
        if result.stderr:
            try:
                stderr_text = result.stderr.decode('gbk', errors='replace')
            except:
                try:
                    stderr_text = result.stderr.decode('utf-8', errors='replace')
                except:
                    stderr_text = str(result.stderr)
        
        # 解析日志文件中的统计信息
        uploaded_count = 0
        skipped_count = 0
        
        # 尝试从日志文件中解析文件传输信息
        if os.path.exists(log_file) and log_output:
            import re
            # WinSCP 日志中可能包含的文件传输信息
            # 查找 "Uploading" 或 "Copying" 等关键词
            upload_lines = re.findall(r'(?:Uploading|Copying|Transferring).*?(\d+)\s+files?', log_output, re.IGNORECASE)
            if upload_lines:
                uploaded_count = sum(int(x) for x in upload_lines)
            
            # 查找跳过的文件
            skip_lines = re.findall(r'(?:Skipping|Skipped).*?(\d+)\s+files?', log_output, re.IGNORECASE)
            if skip_lines:
                skipped_count = sum(int(x) for x in skip_lines)
            
            # 如果没有找到统计信息，尝试计算 ">" 开头的行（表示上传的文件）
            if uploaded_count == 0:
                upload_markers = re.findall(r'^>\s+.*', log_output, re.MULTILINE)
                uploaded_count = len(upload_markers)
        
        # 如果失败，保留日志文件以便调试（成功时也保留以便查看统计）
        if result.returncode == 0:
            try:
                if os.path.exists(script_file):
                    os.remove(script_file)
                # 保留日志文件以便查看统计信息（可选：成功时也删除）
                # if os.path.exists(log_file):
                #     os.remove(log_file)
            except:
                pass
        else:
            # 失败时保留日志文件，但删除脚本文件
            try:
                if os.path.exists(script_file):
                    os.remove(script_file)
                # 保留日志文件，方便调试
                if os.path.exists(log_file):
                    print(f"    [调试] WinSCP 日志文件已保存: {log_file}")
            except:
                pass
        
        # 检查返回码和日志
        if result.returncode == 0:
            # 返回成功，包含统计信息
            stats_info = ""
            if uploaded_count > 0 or skipped_count > 0:
                stats_info = f"上传 {uploaded_count} 个文件，跳过 {skipped_count} 个文件"
            return 0, log_output or stdout_text, stats_info
        else:
            # 返回错误信息，优先使用日志文件中的错误信息
            error_msg = stderr_text or log_output or stdout_text or "WinSCP 执行失败"
            # 如果日志文件存在，尝试提取错误信息
            if os.path.exists(log_file):
                try:
                    # 读取最后几行日志，通常错误信息在最后
                    with open(log_file, "r", encoding='gbk', errors='replace') as f:
                        lines = f.readlines()
                        # 查找错误相关的行
                        error_lines = [line for line in lines[-20:] if 'error' in line.lower() or '失败' in line or '失败' in line or 'failed' in line.lower()]
                        if error_lines:
                            error_msg = "".join(error_lines[-3:]).strip()  # 取最后3行错误信息
                except:
                    pass
            return result.returncode, log_output or stdout_text, error_msg
            
    except Exception as e:
        # 清理临时文件
        try:
            if os.path.exists(script_file):
                os.remove(script_file)
        except:
            pass
        return 1, "", f"执行异常: {str(e)}"

# 保留旧的 rsync 函数作为备用（已禁用）
def run_rsync_old(local_dir, remote_dir):
    """执行rsync同步命令，返回同步结果"""
    # 确保本地目录存在
    if not os.path.exists(local_dir):
        return 1, "", f"本地目录不存在: {local_dir}"
    
    # 构建rsync命令
    # rsync参数说明：
    # -a: 归档模式，保留权限、时间等属性
    # -v: 显示详细输出
    # -z: 传输时压缩
    # --update: 仅更新比远程新的文件
    # --progress: 显示传输进度
    # --itemize-changes: 显示详细的变更信息
    
    # 转换本地路径格式
    local_path_abs = os.path.abspath(local_dir)
    
    # 检查是否是 Cygwin rsync
    if "cygwin" in RSYNC_CMD.lower():
        # 对于 Cygwin rsync，需要转换为 Cygwin 路径格式
        # E:\AI-STUDIO\aistudio\uploads -> /cygdrive/e/AI-STUDIO/aistudio/uploads
        drive_letter = local_path_abs[0].lower()
        path_without_drive = local_path_abs[3:]  # 移除 "E:\"
        local_path = f"/cygdrive/{drive_letter}/" + path_without_drive.replace("\\", "/")
    else:
        # 对于 Git Bash rsync 或其他，使用正斜杠
        local_path = local_path_abs.replace("\\", "/")
    
    if not local_path.endswith("/"):
        local_path += "/"
    
    # 确保远程路径使用正斜杠（os.path.join 在 Windows 上可能产生反斜杠）
    remote_path = remote_dir.replace("\\", "/")
    if not remote_path.endswith("/"):
        remote_path += "/"
    
    # 构建更稳定的 SSH 选项
    # ServerAliveInterval: 每60秒发送一次保活信号
    # ServerAliveCountMax: 最多发送3次，如果3次都失败则断开
    # TCPKeepAlive: 启用 TCP keepalive
    # Compression: 启用压缩（已经在 rsync 的 -z 中启用，但 SSH 层面也可以启用）
    # 注意：PEM_PATH 可能包含空格，需要正确转义
    pem_path_escaped = PEM_PATH.replace("\\", "/")  # 统一使用正斜杠
    if " " in pem_path_escaped:
        pem_path_escaped = f'"{pem_path_escaped}"'
    
    # 增强 SSH 连接稳定性
    # ServerAliveInterval: 每30秒发送保活信号（更频繁）
    # ServerAliveCountMax: 最多发送10次（更宽松）
    # 这样可以保持连接在长时间传输中不断开
    ssh_options_str = (
        f"ssh -i {pem_path_escaped} "
        f"-o StrictHostKeyChecking=no "
        f"-o ConnectTimeout=30 "
        f"-o ServerAliveInterval=30 "  # 改为30秒（更频繁的保活）
        f"-o ServerAliveCountMax=10 "  # 改为10次（更宽松）
        f"-o TCPKeepAlive=yes "
        f"-o Compression=yes "
        f"-o BatchMode=yes "
        f"-o LogLevel=ERROR"  # 减少日志输出，避免干扰
    )
    
    # 简化 rsync 参数，使用最稳定的配置
    # 移除 --inplace（某些情况下可能导致问题）
    # 移除 --bwlimit（让系统自动管理）
    cmd = [
        RSYNC_CMD, 
        "-avz",  # 归档、详细、压缩
        "--update",  # 仅更新较新的文件
        "--progress",  # 显示进度
        "--partial",  # 保留部分传输的文件，支持断点续传
        "--timeout=600",  # rsync I/O 超时时间（10分钟）
        "-e", ssh_options_str,
        local_path,
        f"{REMOTE_USER}@{REMOTE_HOST}:{remote_path}"
    ]
    
    # 尝试最多3次
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                wait_time = 3 * attempt  # 递增等待时间：6秒、9秒
                print(f"    [重试] 第 {attempt} 次尝试（等待 {wait_time} 秒后）...")
                time.sleep(wait_time)
            
            # 显示正在执行的命令（调试用）
            if attempt == 1:
                print(f"    [执行] rsync 同步命令...")
                # 显示实际命令（简化版，用于调试）
                print(f"    [调试] 本地路径: {local_path[:80]}...")
                print(f"    [调试] 远程路径: {REMOTE_USER}@{REMOTE_HOST}:{remote_path}")
            
            # 使用实时输出模式，这样可以看到进度
            # 但为了捕获错误，仍然使用 capture_output
            print(f"    [提示] 开始传输，请稍候...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            
            # 如果有输出，显示部分内容（避免输出过多）
            if result.stdout:
                # 只显示最后几行输出
                output_lines = result.stdout.strip().split('\n')
                if len(output_lines) > 5:
                    print(f"    [输出] ... (省略中间部分)")
                    for line in output_lines[-5:]:
                        if line.strip():
                            print(f"           {line[:80]}")
                else:
                    for line in output_lines:
                        if line.strip():
                            print(f"           {line[:80]}")
            
            if result.returncode == 0:
                return result.returncode, result.stdout, result.stderr
            
            # 分析错误类型
            error_output = (result.stderr + result.stdout).lower()
            
            # 如果是连接错误，可以重试
            if ("connection unexpectedly closed" in error_output or 
                "connection closed" in error_output or
                "broken pipe" in error_output) and attempt < max_retries:
                print(f"    [警告] 连接中断，将重试...")
                continue
            
            # 如果是权限错误或其他非网络错误，不重试
            if "permission denied" in error_output or "access denied" in error_output:
                print(f"    [错误] 权限错误，无法继续")
                return result.returncode, result.stdout, result.stderr
            
            # 其他错误，显示详细信息
            if attempt == max_retries:
                # 最后一次尝试失败，显示详细错误
                error_msg = result.stderr.strip() or result.stdout.strip() or "未知错误"
                print(f"    [错误详情] {error_msg[:200]}")  # 只显示前200个字符
                return result.returncode, result.stdout, result.stderr
            else:
                # 还有重试机会，显示简要错误信息
                error_preview = result.stderr.strip()[:100] if result.stderr else "未知错误"
                print(f"    [警告] 同步失败: {error_preview}...")
                continue
                
        except subprocess.TimeoutExpired:
            if attempt < max_retries:
                print(f"    [超时] 等待后重试...")
                time.sleep(5)
                continue
            return 1, "", "同步超时（超过2小时）"
        except Exception as e:
            if attempt < max_retries:
                print(f"    [错误] {str(e)}，等待后重试...")
                time.sleep(3 * attempt)
                continue
            return 1, "", str(e)
    
    return 1, "", "同步失败：已达到最大重试次数"

def run_scp(local_dir, remote_dir):
    """使用scp递归同步目录，返回同步结果"""
    # 确保本地目录存在
    if not os.path.exists(local_dir):
        return 1, "", f"本地目录不存在: {local_dir}"
    
    # 使用scp -r递归复制
    # -r: 递归复制目录
    # -i: 指定SSH密钥
    local_path = local_dir.replace("\\", "/")
    if not local_path.endswith("/"):
        local_path += "/"
    
    # 确保远程路径使用正斜杠
    remote_path = remote_dir.replace("\\", "/")
    if not remote_path.endswith("/"):
        remote_path += "/"
    
    # scp需要先创建远程目录
    pem_path_escaped = PEM_PATH.replace("\\", "/")
    ssh_cmd = (
        f"ssh -i {pem_path_escaped} "
        f"-o StrictHostKeyChecking=no "
        f"-o ConnectTimeout=30 "
        f"-o ServerAliveInterval=60 "
        f"-o ServerAliveCountMax=3 "
        f"-o TCPKeepAlive=yes "
        f"{REMOTE_USER}@{REMOTE_HOST} 'mkdir -p {remote_path}'"
    )
    subprocess.run(ssh_cmd, shell=True, capture_output=True)
    
    # 执行scp，添加稳定性选项
    cmd = [
        "scp", "-r", "-i", PEM_PATH,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=30",
        "-o", "ServerAliveInterval=60",
        "-o", "ServerAliveCountMax=3",
        "-o", "TCPKeepAlive=yes",
        local_path,
        f"{REMOTE_USER}@{REMOTE_HOST}:{remote_path}"
    ]
    
    # 尝试最多3次
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                print(f"    [重试] 第 {attempt} 次尝试...")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                return result.returncode, result.stdout, result.stderr
            elif attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            else:
                return result.returncode, result.stdout, result.stderr
                
        except subprocess.TimeoutExpired:
            if attempt < max_retries:
                time.sleep(5)
                continue
            return 1, "", "同步超时（超过1小时）"
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            return 1, "", str(e)
    
    return 1, "", "同步失败：已达到最大重试次数"

def sync_code_via_git():
    """通过Git同步代码"""
    print("\n📦 同步代码（通过Git）...")
    
    # 检查是否有未提交的更改
    try:
        # 使用UTF-8编码，避免Windows GBK编码问题
        result = subprocess.run(
            ["git", "status", "--porcelain"], 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=LOCAL_PROJECT_PATH
        )
        if result.stdout and result.stdout.strip():
            print("⚠️  检测到未提交的更改")
            commit = input("是否提交并推送? (Y/N): ").strip().upper()
            if commit == "Y":
                # 添加文件（排除 aistudio-小程序v2，不随同步提交）
                subprocess.run(
                    ["git", "add", "."], 
                    cwd=LOCAL_PROJECT_PATH,
                    encoding='utf-8',
                    errors='replace'
                )
                subprocess.run(
                    ["git", "reset", "aistudio-小程序v2"],
                    cwd=LOCAL_PROJECT_PATH,
                    capture_output=True,
                )
                # 提交
                commit_msg = input("请输入提交说明/版本号（用于 Git 记录，如 2026V2，回车用默认）: ").strip()
                if not commit_msg:
                    commit_msg = f"Update code: sync to server {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                subprocess.run(
                    ["git", "commit", "-m", commit_msg], 
                    cwd=LOCAL_PROJECT_PATH,
                    encoding='utf-8',
                    errors='replace'
                )
                # 推送（只推当前分支，避免 main 不存在时报错）
                push_result = subprocess.run(
                    ["git", "push", "origin", "master"], 
                    cwd=LOCAL_PROJECT_PATH,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                if push_result.returncode != 0:
                    push_result = subprocess.run(
                        ["git", "push", "origin", "main"], 
                        cwd=LOCAL_PROJECT_PATH,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace'
                    )
                if push_result.returncode == 0:
                    print("✅ 代码已推送到GitHub")
                else:
                    err = (push_result.stderr or push_result.stdout or "").strip()
                    print(f"⚠️  Git推送失败: {err[:150]}")
    except Exception as e:
        print(f"⚠️  Git操作失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 在服务器上拉取最新代码
    print("🔄 在服务器上拉取最新代码...")
    ssh_key = PEM_PATH if os.path.exists(PEM_PATH) else KEY_PATH
    ssh_key_unix = ssh_key.replace("\\", "/")  # 避免 Windows 路径转义问题
    remote_cmd = f"cd {REMOTE_PROJECT_PATH} && (git pull origin master 2>&1 || git pull origin main 2>&1)"
    try:
        # 使用列表参数避免 shell 引号转义问题
        result = subprocess.run(
            ["ssh", "-i", ssh_key_unix, "-o", "StrictHostKeyChecking=no",
             f"{REMOTE_USER}@{REMOTE_HOST}", remote_cmd],
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=60
        )
        if result.returncode == 0:
            print("✅ 服务器代码已更新")
            if result.stdout:
                print(f"   输出: {result.stdout.strip()[:200]}")
        else:
            error_msg = (result.stderr or result.stdout or "未知错误").strip()
            if "not a git repository" in error_msg.lower():
                print("⚠️  服务器目录不是 Git 仓库，git pull 已跳过")
                print("   提示: 若需在服务器用 Git 更新，请先执行: cd /root/project_code && git init && git remote add origin <你的仓库URL>")
                print("   或者: 服务器可能是通过文件同步部署的，代码已推送到 GitHub，可手动处理")
            else:
                print(f"⚠️  服务器代码更新可能失败: {error_msg[:200]}")
    except Exception as e:
        print(f"⚠️  SSH连接失败: {e}")
        print("   提示: 请检查SSH密钥权限和服务器连接")

def main():
    print(f"\n{'='*50}")
    print(f"阿里云服务器同步工具")
    print(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 显示配置信息
    print(f"\n📋 配置信息:")
    print(f"   本地路径: {LOCAL_PROJECT_PATH}")
    print(f"   服务器: {REMOTE_USER}@{REMOTE_HOST}")
    print(f"   远程路径: {REMOTE_PROJECT_PATH}")
    print(f"   密钥文件: {KEY_PATH} ({'PPK' if KEY_PATH.endswith('.ppk') else 'PEM'})")
    
    # 获取用户选择的同步目录
    option = get_sync_option()
    if not option:
        print("已取消同步")
        return
    
    print(f"\n✅ 已选择: {option['name']}")
    print(f"   将同步目录: {', '.join(option['dirs'])}")
    
    # 有文件目录需要 WinSCP 时，询问同步模式（增量 / 全量）
    # “同步全部”时默认全量，避免增量误判导致全部跳过、服务器未更新
    sync_mode_full = (option["name"] == "同步全部")
    file_dirs = [d for d in option['dirs'] if d != "instance"]
    if USE_WINSCP and file_dirs:
        print("\n📂 文件同步模式:")
        print("   1. 增量 - 仅传有变化的文件（快，推荐日常使用）")
        print("   2. 全量 - 覆盖所有同名文件（慢，确保与本地完全一致）")
        if option["name"] == "同步全部":
            default_mode = "2"
            prompt_suffix = "，直接回车=全量"
        else:
            default_mode = "1"
            prompt_suffix = "，直接回车=增量"
        mode_choice = input(f"请选择 (1/2{prompt_suffix}): ").strip() or default_mode
        sync_mode_full = (mode_choice == "2")
        print(f"   使用: {'全量覆盖' if sync_mode_full else '增量同步'}")
    
    confirm = input("\n确认开始同步? (Y/N): ").strip().upper()
    if confirm != "Y":
        print("已取消同步")
        return
    
    total_uploaded = 0
    total_skipped = 0
    sync_log = []
    
    # 如果是代码同步，使用Git
    if option['name'] == "仅同步代码" or option['name'] == "同步全部":
        sync_code_via_git()
    
    # 逐个目录同步
    for dir_name in option['dirs']:
        local_dir = os.path.join(LOCAL_PROJECT_PATH, dir_name)
        # 远程路径使用正斜杠（避免 Windows 的 os.path.join 产生反斜杠）
        remote_dir = f"{REMOTE_PROJECT_PATH}/{dir_name}"
        
        # 数据库目录：根据 DATABASE_URL 判断 PostgreSQL 或 SQLite
        if dir_name == "instance":
            db_url = load_database_url()
            if db_url and "postgresql" in db_url:
                print(f"\n🔄 正在同步: {dir_name} (PostgreSQL)")
                if sync_postgresql_to_remote():
                    sync_log.append(f"✅  {dir_name}: PostgreSQL 同步成功")
                else:
                    sync_log.append(f"⚠️  {dir_name}: PostgreSQL 同步失败")
                continue
            # SQLite: 继续下面的目录同步逻辑
            if not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
        
        if not os.path.exists(local_dir):
            print(f"\n⚠️  本地目录 {dir_name} 不存在，跳过同步")
            sync_log.append(f"⚠️  {dir_name}: 本地目录不存在，已跳过")
            continue
        
        print(f"\n🔄 正在同步: {dir_name}")
        print(f"   本地: {local_dir}")
        print(f"   远程: {REMOTE_USER}@{REMOTE_HOST}:{remote_dir}")
        
        # 同步前统计文件数量
        local_count_before = count_local_files(local_dir)
        remote_count_before = count_remote_files(remote_dir, show_debug=False)
        print(f"   📊 同步前统计:")
        print(f"      本地文件数: {local_count_before}")
        if remote_count_before >= 0:
            print(f"      远程文件数: {remote_count_before}")
            diff_before = local_count_before - remote_count_before
            if diff_before > 0:
                print(f"      差异: 本地多 {diff_before} 个文件（需要上传）")
            elif diff_before < 0:
                print(f"      差异: 远程多 {abs(diff_before)} 个文件")
            else:
                print(f"      差异: 文件数量一致")
        else:
            print(f"      远程文件数: 无法获取（正在重试...）")
            # 如果第一次失败，尝试再次统计（可能是网络问题）
            remote_count_before = count_remote_files(remote_dir, show_debug=True)
            if remote_count_before >= 0:
                print(f"      远程文件数（重试后）: {remote_count_before}")
            else:
                print(f"      远程文件数: 无法获取（请检查 SSH 连接）")
        
        # 根据可用工具选择同步方法
        if USE_WINSCP:
            code, stdout, stderr = run_winscp(local_dir, remote_dir, full_overwrite=sync_mode_full)
            if code == 0:
                # WinSCP 同步完成
                # 从 stderr 中获取统计信息（run_winscp 返回的统计信息在 stderr 中）
                uploaded = 0
                skipped = 0
                
                # 尝试从 stderr 中解析统计信息（格式：上传 X 个文件，跳过 Y 个文件）
                if stderr:
                    import re
                    stats_match = re.search(r'上传\s+(\d+)\s+个文件[，,]\s*跳过\s+(\d+)\s+个文件', stderr)
                    if stats_match:
                        uploaded = int(stats_match.group(1))
                        skipped = int(stats_match.group(2))
                    else:
                        # 尝试其他格式
                        uploaded_match = re.search(r'上传\s+(\d+)', stderr)
                        skipped_match = re.search(r'跳过\s+(\d+)', stderr)
                        if uploaded_match:
                            uploaded = int(uploaded_match.group(1))
                        if skipped_match:
                            skipped = int(skipped_match.group(1))
                
                # 如果从 stderr 中没有找到，尝试从 stdout 中解析
                if uploaded == 0 and skipped == 0 and stdout:
                    import re
                    uploaded_match = re.search(r'(?:Uploaded|上传了?)\s+(\d+)\s+files?', stdout, re.IGNORECASE)
                    skipped_match = re.search(r'(?:Skipped|跳过)\s+(\d+)\s+files?', stdout, re.IGNORECASE)
                    if uploaded_match:
                        uploaded = int(uploaded_match.group(1))
                    if skipped_match:
                        skipped = int(skipped_match.group(1))
                
                # 同步后统计文件数量
                local_count_after = count_local_files(local_dir)
                remote_count_after = count_remote_files(remote_dir, show_debug=False)
                
                print(f"   📊 同步后统计:")
                print(f"      本地文件数: {local_count_after}")
                if remote_count_after >= 0:
                    print(f"      远程文件数: {remote_count_after}")
                    diff_after = local_count_after - remote_count_after
                    if diff_after == 0:
                        print(f"      ✅ 文件数量一致，同步成功")
                    elif diff_after > 0:
                        print(f"      ⚠️  本地仍多 {diff_after} 个文件（可能未完全同步）")
                    else:
                        print(f"      ⚠️  远程多 {abs(diff_after)} 个文件（可能服务器上有额外文件）")
                    
                    # 计算实际同步的文件数
                    if remote_count_before >= 0:
                        actual_uploaded = remote_count_after - remote_count_before
                        if actual_uploaded > 0:
                            print(f"      📤 实际新增: {actual_uploaded} 个文件")
                else:
                    print(f"      远程文件数: 无法获取")
                
                # 同步后统计文件数量
                local_count_after = count_local_files(local_dir)
                remote_count_after = count_remote_files(remote_dir, show_debug=False)
                
                print(f"   📊 同步后统计:")
                print(f"      本地文件数: {local_count_after}")
                if remote_count_after >= 0:
                    print(f"      远程文件数: {remote_count_after}")
                    diff_after = local_count_after - remote_count_after
                    if diff_after == 0:
                        print(f"      ✅ 文件数量一致，同步成功")
                    elif diff_after > 0:
                        print(f"      ⚠️  本地仍多 {diff_after} 个文件（可能未完全同步）")
                    else:
                        print(f"      ⚠️  远程多 {abs(diff_after)} 个文件（可能服务器上有额外文件）")
                    
                    # 计算实际同步的文件数（优先使用实际文件数量对比）
                    if remote_count_before >= 0:
                        actual_uploaded = remote_count_after - remote_count_before
                        if actual_uploaded > 0:
                            print(f"      📤 实际新增: {actual_uploaded} 个文件")
                            # 使用实际统计的数量，而不是日志解析的数量
                            uploaded = actual_uploaded
                            skipped = 0
                        elif actual_uploaded == 0:
                            print(f"      ℹ️  没有新增文件（文件已是最新）")
                            # 如果实际没有新增，即使日志说有上传，也应该是0
                            uploaded = 0
                            skipped = local_count_after  # 假设所有文件都被跳过（未修改）
                        else:
                            # 远程文件数减少了（不应该发生，但处理一下）
                            uploaded = 0
                            skipped = 0
                else:
                    print(f"      远程文件数: 无法获取")
                    # 如果无法获取远程文件数，使用日志解析的结果（但可能不准确）
                    # 保持 uploaded 和 skipped 的值不变
                
                # 记录同步结果
                if uploaded > 0 or skipped > 0:
                    sync_log.append(f"✅ {dir_name}: 同步完成（上传 {uploaded} 个文件，跳过 {skipped} 个文件）")
                else:
                    sync_log.append(f"✅ {dir_name}: 同步完成（没有新增文件）")
                total_uploaded += uploaded
                total_skipped += skipped
            else:
                # 显示详细的错误信息
                error_msg = stderr.strip() if stderr else (stdout.strip() if stdout else "未知错误")
                if not error_msg or error_msg == "未知错误":
                    # 如果错误信息为空，尝试提供更多信息
                    error_msg = f"WinSCP 返回码: {code}"
                    if stdout:
                        error_msg += f", 输出: {stdout[:100]}"
                sync_log.append(f"❌ {dir_name}: 同步失败 - {error_msg}")
                print(f"❌ 错误: {error_msg}")
                # 如果错误信息较长，只显示前200个字符
                if len(error_msg) > 200:
                    print(f"   详细错误: {error_msg[:200]}...")
        elif USE_SCP:
            code, stdout, stderr = run_scp(local_dir, remote_dir)
            if code == 0:
                # scp不提供详细统计，估算文件数
                file_count = sum(1 for _ in os.walk(local_dir))
                uploaded = file_count
                total_uploaded += uploaded
                sync_log.append(f"✅ {dir_name}: 同步完成（使用scp，约 {uploaded} 个文件）")
            else:
                error_msg = stderr.strip() if stderr else "未知错误"
                sync_log.append(f"❌ {dir_name}: 同步失败 - {error_msg}")
                print(f"❌ 错误: {error_msg}")
        else:
            # 如果都不行，提示用户
            print(f"❌ 错误: 未找到可用的同步工具")
            sync_log.append(f"❌ {dir_name}: 同步失败 - 未找到可用的同步工具")
            
        # 旧代码（已禁用 rsync，已移除）
    
    # 输出最终报告
    print(f"\n{'='*50}")
    print("同步完成报告")
    print(f"{'='*50}")
    for log in sync_log:
        print(f"  {log}")
    if option['name'] == "仅同步数据库" and any("PostgreSQL" in log or "instance" in log for log in sync_log):
        print(f"\n📊 数据库已覆盖恢复（仅同步数据库时无文件计数）")
    else:
        print(f"\n📊 总计: 新增/更新 {total_uploaded} 个文件，跳过 {total_skipped} 个未修改文件")
    print(f"{'='*50}")
    print("💡 若后台数据与本地不一致，请：(1) 下面选 Y 重启服务器应用；(2) 确认服务器 .env 里 DATABASE_URL 与恢复的数据库一致。")
    print(f"{'='*50}\n")
    
    # 询问是否重启服务
    restart = input("是否重启服务器上的服务? (Y/N): ").strip().upper()
    if restart == "Y":
        # SSH 命令使用 PEM 文件（SSH 不支持 PPK，需要 PEM）
        ssh_key = PEM_PATH if os.path.exists(PEM_PATH) else KEY_PATH
        ssh_cmd = f'ssh -i "{ssh_key}" -o StrictHostKeyChecking=no {REMOTE_USER}@{REMOTE_HOST} "systemctl restart aistudio"'
        result = subprocess.run(
            ssh_cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            print("✅ 服务已重启")
        else:
            print(f"⚠️  服务重启失败: {result.stderr}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消同步")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
