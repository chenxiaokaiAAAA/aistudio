#!/bin/bash
# 服务器代码备份脚本
# 使用方法: bash scripts/deployment/服务器备份脚本.sh

set -e

cd /root

# 创建备份目录（带时间戳）
BACKUP_DIR="project_code_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "========================================"
echo "    开始备份项目代码"
echo "========================================"
echo ""
echo "备份目录: $BACKUP_DIR"
echo ""

# 检查项目目录是否存在
if [ ! -d "project_code" ]; then
    echo "[错误] 项目目录不存在: /root/project_code"
    exit 1
fi

# 备份整个项目目录
echo "[1/4] 备份项目代码..."
cp -r project_code/* "$BACKUP_DIR/" 2>/dev/null || true
echo "✅ 代码备份完成"

# 备份数据库（重要！）
echo ""
echo "[2/4] 备份数据库..."
if [ -f "project_code/instance/pet_painting.db" ]; then
    mkdir -p "$BACKUP_DIR/instance"
    cp project_code/instance/pet_painting.db "$BACKUP_DIR/instance/pet_painting.db"
    DB_SIZE=$(du -h "$BACKUP_DIR/instance/pet_painting.db" | cut -f1)
    echo "✅ 数据库已备份 ($DB_SIZE)"
else
    echo "⚠️  数据库文件不存在，跳过"
fi

# 备份图片目录
echo ""
echo "[3/4] 备份图片目录..."
IMAGE_DIRS=("uploads" "final_works" "hd_images")
for dir in "${IMAGE_DIRS[@]}"; do
    if [ -d "project_code/$dir" ]; then
        FILE_COUNT=$(find "project_code/$dir" -type f | wc -l)
        if [ "$FILE_COUNT" -gt 0 ]; then
            cp -r "project_code/$dir" "$BACKUP_DIR/" 2>/dev/null || true
            echo "✅ $dir 已备份 ($FILE_COUNT 个文件)"
        else
            echo "ℹ️  $dir 目录为空，跳过"
        fi
    fi
done

# 显示备份信息
echo ""
echo "[4/4] 备份信息..."
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "备份大小: $BACKUP_SIZE"
echo "备份位置: /root/$BACKUP_DIR"
echo ""

# 列出所有备份
echo "当前所有备份："
ls -lah /root | grep project_code_backup | awk '{print $9, "(" $5 ")"}'
echo ""

echo "========================================"
echo "    ✅ 备份完成"
echo "========================================"
echo ""
echo "备份目录: $BACKUP_DIR"
echo "备份大小: $BACKUP_SIZE"
echo ""
echo "提示：可以使用以下命令恢复："
echo "  bash scripts/deployment/服务器恢复脚本.sh $BACKUP_DIR"
echo ""
