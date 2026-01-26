@echo off
chcp 65001 >nul
cd /d "%~dp0"
python fix_hd_image_filenames.py
pause
