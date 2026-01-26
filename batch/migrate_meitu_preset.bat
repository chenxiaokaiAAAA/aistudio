@echo off
chcp 65001 >nul
echo ========================================
echo 美图API预设表迁移脚本
echo 将 product_id 改为 style_image_id
echo ========================================
echo.

cd /d "%~dp0.."
python scripts\database\migrate_meitu_preset_to_style_image.py

pause
