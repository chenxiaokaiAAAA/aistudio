#!/bin/bash
# 清理服务器上重复的目录结构
# 使用方法：在服务器上执行此脚本

PROJECT_DIR="/root/project_code"

echo "========================================"
echo "    清理重复目录结构"
echo "========================================"
echo

# 检查 uploads 目录下是否有重复的 final_works 和 uploads 子目录
UPLOADS_DIR="$PROJECT_DIR/uploads"

if [ -d "$UPLOADS_DIR/final_works" ]; then
    echo "[警告] 发现 uploads 目录下有 final_works 子目录"
    echo "  路径: $UPLOADS_DIR/final_works"
    read -p "是否删除? (y/n): " confirm
    if [ "$confirm" = "y" ]; then
        rm -rf "$UPLOADS_DIR/final_works"
        echo "  ✅ 已删除"
    fi
fi

if [ -d "$UPLOADS_DIR/uploads" ]; then
    echo "[警告] 发现 uploads 目录下有 uploads 子目录（重复）"
    echo "  路径: $UPLOADS_DIR/uploads"
    read -p "是否删除? (y/n): " confirm
    if [ "$confirm" = "y" ]; then
        rm -rf "$UPLOADS_DIR/uploads"
        echo "  ✅ 已删除"
    fi
fi

# 检查 final_works 目录下是否有重复
FINAL_WORKS_DIR="$PROJECT_DIR/final_works"
if [ -d "$FINAL_WORKS_DIR/uploads" ]; then
    echo "[警告] 发现 final_works 目录下有 uploads 子目录"
    echo "  路径: $FINAL_WORKS_DIR/uploads"
    read -p "是否删除? (y/n): " confirm
    if [ "$confirm" = "y" ]; then
        rm -rf "$FINAL_WORKS_DIR/uploads"
        echo "  ✅ 已删除"
    fi
fi

if [ -d "$FINAL_WORKS_DIR/final_works" ]; then
    echo "[警告] 发现 final_works 目录下有 final_works 子目录（重复）"
    echo "  路径: $FINAL_WORKS_DIR/final_works"
    read -p "是否删除? (y/n): " confirm
    if [ "$confirm" = "y" ]; then
        rm -rf "$FINAL_WORKS_DIR/final_works"
        echo "  ✅ 已删除"
    fi
fi

echo
echo "========================================"
echo "清理完成"
echo "========================================"
