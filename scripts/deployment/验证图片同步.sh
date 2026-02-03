#!/bin/bash
# 验证图片文件是否已同步到服务器

echo "========================================"
echo "    验证图片文件同步状态"
echo "========================================"
echo

PROJECT_DIR="/root/project_code"
IMAGE_DIRS=("uploads" "final_works" "hd_images")

for dir in "${IMAGE_DIRS[@]}"; do
    full_path="$PROJECT_DIR/$dir"
    echo "[检查] $dir"
    
    if [ -d "$full_path" ]; then
        file_count=$(find "$full_path" -type f 2>/dev/null | wc -l)
        dir_count=$(find "$full_path" -type d 2>/dev/null | wc -l)
        total_size=$(du -sh "$full_path" 2>/dev/null | cut -f1)
        
        echo "  ✅ 目录存在"
        echo "  📁 文件数: $file_count"
        echo "  📂 子目录数: $dir_count"
        echo "  💾 总大小: $total_size"
        
        if [ $file_count -gt 0 ]; then
            echo "  📋 最近5个文件:"
            find "$full_path" -type f -printf "%T@ %p\n" 2>/dev/null | sort -rn | head -5 | cut -d' ' -f2- | while read file; do
                echo "    - $(basename "$file")"
            done
        else
            echo "  ⚠️  目录为空"
        fi
    else
        echo "  ❌ 目录不存在: $full_path"
    fi
    echo
done

echo "========================================"
echo "验证完成"
echo "========================================"
