@echo off
echo ========================================
echo 启动打印代理服务
echo ========================================
echo.

REM 设置打印机路径（请根据实际情况修改）
set LOCAL_PRINTER_PATH=\\sm003\HP OfficeJet Pro 7730 series

REM 设置服务端口
set PRINT_PROXY_PORT=8888

REM 设置API密钥（可选，用于安全验证）
set PRINT_PROXY_API_KEY=test-key-123

echo 配置信息：
echo   打印机路径: %LOCAL_PRINTER_PATH%
echo   服务端口: %PRINT_PROXY_PORT%
echo   API密钥: %PRINT_PROXY_API_KEY%
echo.
echo 正在启动服务...
echo.

REM 运行打印代理服务
python print_proxy_server.py

REM 如果服务退出，暂停以便查看错误信息
pause
