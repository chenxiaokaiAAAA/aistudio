@echo off
chcp 65001 >nul
echo ========================================
echo 从 bk-photo 导入 API 服务商配置
echo ========================================
echo.

cd /d "%~dp0.."

REM 默认 bk-photo 数据库路径（相对于 AI-studio 项目根目录）
REM 优先使用 pet_painting.db（bk-photo 的默认数据库）
set BKPHOTO_DB=..\bk-photo\instance\pet_painting.db

REM 检查数据库文件是否存在
if not exist "%BKPHOTO_DB%" (
    echo ❌ 错误：bk-photo 数据库文件不存在
    echo 路径: %BKPHOTO_DB%
    echo.
    echo 请手动指定 bk-photo 数据库路径：
    echo python scripts\database\import_api_provider_configs_from_bkphoto.py --bkphoto-db "路径\database.db"
    pause
    exit /b 1
)

echo 📂 bk-photo 数据库路径: %BKPHOTO_DB%
echo.

python scripts\database\import_api_provider_configs_from_bkphoto.py --bkphoto-db "%BKPHOTO_DB%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 导入完成！
) else (
    echo.
    echo ❌ 导入失败！
)

pause
