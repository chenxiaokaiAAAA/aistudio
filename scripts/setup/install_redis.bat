@echo off
chcp 65001 >nul
echo ========================================
echo Redis安装和配置脚本
echo ========================================
echo.

REM 检查是否已安装
where redis-server >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Redis已安装
    redis-server --version
    echo.
    goto :check_service
)

echo [WARN] Redis未安装
echo.
echo 请先下载并安装Redis:
echo   下载地址: https://github.com/tporadowski/redis/releases
echo   或: https://github.com/microsoftarchive/redis/releases
echo.
echo 安装步骤:
echo   1. 下载 Redis-x64-*.zip
echo   2. 解压到 C:\Redis (或其他目录)
echo   3. 将Redis目录添加到PATH环境变量
echo   4. 重新运行此脚本
echo.
pause
exit /b 1

:check_service
echo 检查Redis服务状态...
sc query Redis >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Redis服务已注册
    echo.
    sc query Redis | findstr "STATE"
    echo.
    echo 服务管理命令:
    echo   启动: redis-server.exe --service-start
    echo   停止: redis-server.exe --service-stop
    echo   状态: redis-server.exe --service-status
) else (
    echo [WARN] Redis服务未注册
    echo.
    echo 是否注册为Windows服务? (Y/N)
    set /p choice=
    if /i "%choice%"=="Y" (
        echo.
        echo 正在注册Redis服务...
        
        REM 查找Redis安装目录
        for /f "delims=" %%i in ('where redis-server') do set REDIS_PATH=%%~dpi
        
        if "%REDIS_PATH%"=="" (
            echo [ERROR] 无法找到Redis安装目录
            echo 请确保Redis已添加到PATH环境变量
            pause
            exit /b 1
        )
        
        echo Redis路径: %REDIS_PATH%
        cd /d "%REDIS_PATH%"
        
        REM 检查配置文件
        if exist redis.windows.conf (
            set CONFIG_FILE=redis.windows.conf
        ) else if exist redis.conf (
            set CONFIG_FILE=redis.conf
        ) else (
            echo [WARN] 未找到配置文件，使用默认配置
            set CONFIG_FILE=
        )
        
        REM 安装服务
        if "%CONFIG_FILE%"=="" (
            redis-server.exe --service-install
        ) else (
            redis-server.exe --service-install %CONFIG_FILE%
        )
        
        if %errorlevel% == 0 (
            echo [OK] Redis服务注册成功
            echo.
            echo 正在启动Redis服务...
            redis-server.exe --service-start
            if %errorlevel% == 0 (
                echo [OK] Redis服务启动成功
            ) else (
                echo [ERROR] Redis服务启动失败
                echo 请检查日志或手动启动服务
            )
        ) else (
            echo [ERROR] Redis服务注册失败
            echo 请以管理员身份运行此脚本
        )
    )
)

echo.
echo ========================================
echo 测试Redis连接
echo ========================================
echo.

REM 测试连接
redis-cli.exe ping >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Redis连接成功
    redis-cli.exe ping
) else (
    echo [WARN] Redis连接失败
    echo 请检查:
    echo   1. Redis服务是否正在运行
    echo   2. 端口6379是否被占用
    echo   3. 防火墙设置
)

echo.
echo ========================================
echo 完成
echo ========================================
echo.
echo 下一步:
echo   1. 运行 python scripts/test_cache.py 测试缓存功能
echo   2. 在 .env 文件中配置Redis连接信息
echo.
pause
