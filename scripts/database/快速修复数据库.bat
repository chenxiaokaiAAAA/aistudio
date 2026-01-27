@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd AI-studio
python scripts/fix_is_sync_api_field.py instance/pet_painting.db
pause
