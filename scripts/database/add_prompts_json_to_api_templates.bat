@echo off
chcp 65001 >nul
echo ========================================
echo 数据库迁移：添加 prompts_json 字段
echo ========================================
echo.
echo 此脚本将为 api_templates 表添加 prompts_json 字段
echo 用于支持批量提示词功能
echo.
echo 按任意键继续，或按 Ctrl+C 取消...
pause >nul
echo.

cd /d %~dp0\..\..
python scripts/database/add_prompts_json_to_api_templates.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ 迁移成功完成
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ❌ 迁移失败，请检查错误信息
    echo ========================================
)

pause
