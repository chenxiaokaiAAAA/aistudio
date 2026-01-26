@echo off
chcp 65001 >nul
echo ========================================
echo AI工作流数据库迁移脚本
echo ========================================
echo.

cd /d "%~dp0.."

python scripts/database/add_ai_workflow_fields.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 迁移完成！
    pause
) else (
    echo.
    echo ❌ 迁移失败！
    pause
    exit /b 1
)
