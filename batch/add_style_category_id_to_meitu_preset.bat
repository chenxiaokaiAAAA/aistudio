@echo off
chcp 65001 >nul
echo ========================================
echo 美图API预设表迁移脚本
echo 添加 style_category_id 字段
echo ========================================
echo.

cd /d "%~dp0.."
python scripts\database\add_style_category_id_to_meitu_preset.py

pause
