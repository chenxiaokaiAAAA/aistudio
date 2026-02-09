#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL数据库备份脚本
支持自动备份、备份历史管理、自动清理旧备份
"""

import os
import sys
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path

# 默认配置
DEFAULT_BACKUP_DIR = 'data/backups/postgresql'
DEFAULT_RETENTION_DAYS = 30  # 保留30天的备份
DEFAULT_DB_NAME = 'pet_painting'
DEFAULT_DB_USER = 'aistudio_user'
DEFAULT_DB_HOST = 'localhost'
DEFAULT_DB_PORT = '5432'

class PostgreSQLBackup:
    """PostgreSQL数据库备份管理器"""
    
    def __init__(self, backup_dir=None, retention_days=None, db_name=None, 
                 db_user=None, db_password=None, db_host=None, db_port=None):
        """
        初始化备份管理器
        
        Args:
            backup_dir: 备份目录路径
            retention_days: 保留天数
            db_name: 数据库名称
            db_user: 数据库用户名
            db_password: 数据库密码
            db_host: 数据库主机
            db_port: 数据库端口
        """
        # 从环境变量或参数获取配置
        self.backup_dir = backup_dir or os.environ.get('PG_BACKUP_DIR', DEFAULT_BACKUP_DIR)
        self.retention_days = retention_days or int(os.environ.get('PG_BACKUP_RETENTION_DAYS', DEFAULT_RETENTION_DAYS))
        self.db_name = db_name or os.environ.get('PG_DATABASE', DEFAULT_DB_NAME)
        self.db_user = db_user or os.environ.get('PG_USER', DEFAULT_DB_USER)
        self.db_password = db_password or os.environ.get('PG_PASSWORD', '')
        self.db_host = db_host or os.environ.get('PG_HOST', DEFAULT_DB_HOST)
        self.db_port = db_port or os.environ.get('PG_PORT', DEFAULT_DB_PORT)
        
        # 从DATABASE_URL解析（如果存在）
        database_url = os.environ.get('DATABASE_URL', '')
        if database_url and database_url.startswith('postgresql://'):
            self._parse_database_url(database_url)
        
        # 确保备份目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 日志文件
        self.log_file = os.path.join(self.backup_dir, 'backup_log.json')
    
    def _parse_database_url(self, url):
        """从DATABASE_URL解析数据库连接信息"""
        try:
            # postgresql://user:password@host:port/database
            url = url.replace('postgresql://', '')
            if '@' in url:
                auth, rest = url.split('@', 1)
                if ':' in auth:
                    self.db_user, self.db_password = auth.split(':', 1)
                else:
                    self.db_user = auth
                
                if '/' in rest:
                    host_port, self.db_name = rest.rsplit('/', 1)
                    if ':' in host_port:
                        self.db_host, self.db_port = host_port.split(':', 1)
                    else:
                        self.db_host = host_port
        except Exception as e:
            print(f"⚠️  解析DATABASE_URL失败: {e}")
    
    def check_pg_dump(self):
        """检查pg_dump命令是否可用"""
        try:
            result = subprocess.run(['pg_dump', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ 找到 pg_dump: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            print("❌ 错误: 未找到 pg_dump 命令")
            print("   请确保PostgreSQL已安装并添加到PATH环境变量")
            print("   Windows: 通常位于 C:\\Program Files\\PostgreSQL\\XX\\bin\\")
            print("   Linux: sudo apt-get install postgresql-client")
            return False
        except Exception as e:
            print(f"❌ 检查pg_dump失败: {e}")
            return False
    
    def backup_database(self, backup_type='full'):
        """
        备份数据库
        
        Args:
            backup_type: 备份类型
                - 'full': 完整备份（默认）
                - 'schema': 只备份表结构
                - 'data': 只备份数据
        
        Returns:
            dict: 备份信息，失败返回None
        """
        if not self.check_pg_dump():
            return None
        
        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if backup_type == 'schema':
                backup_filename = f"{self.db_name}_schema_{timestamp}.sql"
            elif backup_type == 'data':
                backup_filename = f"{self.db_name}_data_{timestamp}.sql"
            else:
                backup_filename = f"{self.db_name}_full_{timestamp}.sql"
            
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # 构建pg_dump命令
            cmd = ['pg_dump']
            
            # 添加连接参数
            if self.db_host:
                cmd.extend(['-h', self.db_host])
            if self.db_port:
                cmd.extend(['-p', str(self.db_port)])
            if self.db_user:
                cmd.extend(['-U', self.db_user])
            cmd.extend(['-d', self.db_name])
            
            # 根据备份类型添加选项
            if backup_type == 'schema':
                cmd.append('--schema-only')
            elif backup_type == 'data':
                cmd.append('--data-only')
            
            # 添加其他选项
            cmd.extend(['-F', 'p'])  # 纯文本格式
            cmd.extend(['-f', backup_path])
            
            # 设置环境变量（用于密码）
            env = os.environ.copy()
            if self.db_password:
                env['PGPASSWORD'] = self.db_password
            
            print(f"📦 开始备份数据库: {self.db_name}")
            print(f"   备份类型: {backup_type}")
            print(f"   备份文件: {backup_filename}")
            
            # 执行备份
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=3600)
            
            if result.returncode != 0:
                print(f"❌ 备份失败:")
                print(f"   错误信息: {result.stderr}")
                return None
            
            # 获取文件大小
            file_size = os.path.getsize(backup_path)
            file_size_mb = file_size / (1024 * 1024)
            
            print(f"✅ 备份成功: {backup_filename}")
            print(f"   文件大小: {file_size_mb:.2f} MB ({file_size:,} 字节)")
            print(f"   保存位置: {backup_path}")
            
            # 记录备份信息
            backup_info = {
                'backup_name': backup_filename,
                'backup_path': backup_path,
                'backup_type': backup_type,
                'database': self.db_name,
                'size': file_size,
                'size_mb': round(file_size_mb, 2),
                'timestamp': timestamp,
                'datetime': datetime.now().isoformat()
            }
            
            self.save_log(backup_info)
            
            return backup_info
            
        except subprocess.TimeoutExpired:
            print("❌ 备份超时（超过1小时）")
            return None
        except Exception as e:
            print(f"❌ 备份失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_log(self):
        """加载备份日志"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  加载日志失败: {e}")
        return []
    
    def save_log(self, backup_info):
        """保存备份日志"""
        try:
            log = self.load_log()
            log.append(backup_info)
            
            # 只保留最近N天的日志
            cutoff_date = datetime.now() - timedelta(days=self.retention_days * 2)
            log = [l for l in log if datetime.fromisoformat(l['datetime']) > cutoff_date]
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存日志失败: {e}")
    
    def cleanup_old_backups(self):
        """清理旧备份文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_count = 0
            deleted_size = 0
            
            for filename in os.listdir(self.backup_dir):
                if not filename.endswith('.sql'):
                    continue
                
                file_path = os.path.join(self.backup_dir, filename)
                
                # 获取文件修改时间
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_time < cutoff_date:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_count += 1
                    deleted_size += file_size
                    print(f"🗑️  删除旧备份: {filename}")
            
            if deleted_count > 0:
                deleted_size_mb = deleted_size / (1024 * 1024)
                print(f"✅ 清理完成: 删除了 {deleted_count} 个旧备份文件 ({deleted_size_mb:.2f} MB)")
            else:
                print("ℹ️  没有需要清理的旧备份")
            
            return deleted_count, deleted_size
            
        except Exception as e:
            print(f"⚠️  清理旧备份失败: {e}")
            return 0, 0
    
    def list_backups(self):
        """列出所有备份文件"""
        try:
            backups = []
            total_size = 0
            
            for filename in os.listdir(self.backup_dir):
                if not filename.endswith('.sql'):
                    continue
                
                file_path = os.path.join(self.backup_dir, filename)
                file_size = os.path.getsize(file_path)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                backups.append({
                    'filename': filename,
                    'size': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'datetime': file_time.isoformat(),
                    'date': file_time.strftime('%Y-%m-%d %H:%M:%S')
                })
                total_size += file_size
            
            # 按时间排序（最新的在前）
            backups.sort(key=lambda x: x['datetime'], reverse=True)
            
            return backups, total_size
            
        except Exception as e:
            print(f"⚠️  列出备份失败: {e}")
            return [], 0
    
    def show_statistics(self):
        """显示备份统计信息"""
        backups, total_size = self.list_backups()
        total_size_mb = total_size / (1024 * 1024)
        
        print("\n" + "=" * 60)
        print("📊 备份统计信息")
        print("=" * 60)
        print(f"备份目录: {self.backup_dir}")
        print(f"备份文件数: {len(backups)}")
        print(f"总大小: {total_size_mb:.2f} MB ({total_size:,} 字节)")
        print(f"保留天数: {self.retention_days} 天")
        
        if backups:
            print(f"\n最新备份:")
            for i, backup in enumerate(backups[:5], 1):
                print(f"  {i}. {backup['filename']}")
                print(f"     时间: {backup['date']}")
                print(f"     大小: {backup['size_mb']} MB")
        
        print("=" * 60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PostgreSQL数据库备份工具')
    parser.add_argument('--backup', action='store_true', help='执行备份')
    parser.add_argument('--type', choices=['full', 'schema', 'data'], default='full',
                       help='备份类型: full(完整), schema(仅结构), data(仅数据)')
    parser.add_argument('--cleanup', action='store_true', help='清理旧备份')
    parser.add_argument('--list', action='store_true', help='列出所有备份')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--backup-dir', help='备份目录路径')
    parser.add_argument('--retention-days', type=int, help='保留天数')
    
    args = parser.parse_args()
    
    # 如果没有指定任何操作，默认执行备份
    if not any([args.backup, args.cleanup, args.list, args.stats]):
        args.backup = True
    
    # 创建备份管理器
    backup_manager = PostgreSQLBackup(
        backup_dir=args.backup_dir,
        retention_days=args.retention_days
    )
    
    print("=" * 60)
    print("🗄️  PostgreSQL数据库备份工具")
    print("=" * 60)
    print(f"数据库: {backup_manager.db_name}")
    print(f"用户: {backup_manager.db_user}")
    print(f"主机: {backup_manager.db_host}:{backup_manager.db_port}")
    print(f"备份目录: {backup_manager.backup_dir}")
    print("=" * 60)
    print()
    
    # 执行备份
    if args.backup:
        backup_info = backup_manager.backup_database(backup_type=args.type)
        if backup_info:
            print("\n✅ 备份任务完成")
        else:
            print("\n❌ 备份任务失败")
            sys.exit(1)
    
    # 清理旧备份
    if args.cleanup:
        backup_manager.cleanup_old_backups()
    
    # 列出备份
    if args.list:
        backups, total_size = backup_manager.list_backups()
        total_size_mb = total_size / (1024 * 1024)
        print(f"\n📋 备份文件列表 (共 {len(backups)} 个, 总计 {total_size_mb:.2f} MB):")
        for i, backup in enumerate(backups, 1):
            print(f"  {i}. {backup['filename']}")
            print(f"     时间: {backup['date']}")
            print(f"     大小: {backup['size_mb']} MB")
    
    # 显示统计信息
    if args.stats:
        backup_manager.show_statistics()


if __name__ == '__main__':
    main()
