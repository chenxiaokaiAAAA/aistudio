#!/bin/bash
# 服务器代码恢复脚本
# 使用方法: bash scripts/deployment/服务器恢复脚本.sh <备份目录名>

set -e

if [ -z "$1" ]; then
    echo "========================================"
    echo "    服务器代码恢复脚本"
    echo "========================================"
    echo ""
    echo "用法: $0 <备份目录名>"
    echo ""
    echo "可用的备份："
    ls -lah /root | grep project_code_backup | awk '{print "  - " $9}'
    echo ""
    echo "示例:"
    echo "  $0 project_code_backup_20260127_140000"
    echo ""
    exit 1
fi

BACKUP_DIR="/root/$1"

# 检查备份目录是否存在
if [ ! -d "$BACKUP_DIR" ]; then
    echo "[错误] 备份目录不存在: $BACKUP_DIR"
    echo ""
    echo "可用的备份："
    ls -lah /root | grep project_code_backup | awk '{print "  - " $9}'
    exit 1
fi

echo "========================================"
echo "    恢复项目代码"
echo "========================================"
echo ""
echo "备份目录: $BACKUP_DIR"
echo "目标目录: /root/project_code"
echo ""

# 确认
read -p "确认恢复？这将覆盖当前项目代码！(Y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 停止服务
echo ""
echo "[1/5] 停止服务..."
systemctl stop aistudio
sleep 2
echo "✅ 服务已停止"

# 备份当前版本（以防万一）
CURRENT_BACKUP="project_code_current_$(date +%Y%m%d_%H%M%S)"
echo ""
echo "[2/5] 备份当前版本（以防万一）..."
mkdir -p "/root/$CURRENT_BACKUP"
cp -r /root/project_code/* "/root/$CURRENT_BACKUP/" 2>/dev/null || true
echo "✅ 当前版本已备份到: $CURRENT_BACKUP"

# 恢复代码
echo ""
echo "[3/5] 恢复项目代码..."
rm -rf /root/project_code/*
cp -r "$BACKUP_DIR"/* /root/project_code/
echo "✅ 代码恢复完成"

# 恢复数据库
echo ""
echo "[4/5] 恢复数据库..."
if [ -f "$BACKUP_DIR/instance/pet_painting.db" ]; then
    mkdir -p /root/project_code/instance
    cp "$BACKUP_DIR/instance/pet_painting.db" /root/project_code/instance/pet_painting.db
    chmod 644 /root/project_code/instance/pet_painting.db
    chown root:root /root/project_code/instance/pet_painting.db
    echo "✅ 数据库恢复完成"
else
    echo "⚠️  备份中没有数据库文件"
fi

# 设置权限
echo ""
echo "[5/5] 设置文件权限..."
chmod -R 755 /root/project_code
find /root/project_code -type f -exec chmod 644 {} \;
chmod 755 /root/project_code/instance 2>/dev/null || true
chmod 644 /root/project_code/instance/pet_painting.db 2>/dev/null || true
echo "✅ 权限设置完成"

# 重启服务
echo ""
echo "重启服务..."
systemctl start aistudio
sleep 3

# 检查服务状态
if systemctl is-active --quiet aistudio; then
    echo "✅ 服务已启动并运行正常"
else
    echo "⚠️  服务启动可能有问题，请检查日志："
    echo "  journalctl -u aistudio -n 50"
fi

echo ""
echo "========================================"
echo "    ✅ 恢复完成"
echo "========================================"
echo ""
echo "当前版本备份: $CURRENT_BACKUP"
echo "恢复的备份: $BACKUP_DIR"
echo ""
echo "查看服务状态:"
echo "  systemctl status aistudio"
echo ""
echo "查看服务日志:"
echo "  journalctl -u aistudio -f"
echo ""
