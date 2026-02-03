@echo off
echo ========================================
echo 检查证书文件位置
echo ========================================
echo.

echo 配置文件指定的证书位置:
echo   - 证书文件: C:\nginx\ssl\photogooo.pem
echo   - 私钥文件: C:\nginx\ssl\photogooo.key
echo.

echo 检查配置文件位置 (C:\nginx\ssl\):
if exist "C:\nginx\ssl\photogooo.pem" (
    echo ✅ 找到证书: C:\nginx\ssl\photogooo.pem
    for %%A in ("C:\nginx\ssl\photogooo.pem") do echo    文件大小: %%~zA 字节
    for %%A in ("C:\nginx\ssl\photogooo.pem") do echo    修改时间: %%~tA
) else (
    echo ❌ 未找到: C:\nginx\ssl\photogooo.pem
)

if exist "C:\nginx\ssl\photogooo.key" (
    echo ✅ 找到私钥: C:\nginx\ssl\photogooo.key
    for %%A in ("C:\nginx\ssl\photogooo.key") do echo    文件大小: %%~zA 字节
    for %%A in ("C:\nginx\ssl\photogooo.key") do echo    修改时间: %%~tA
) else (
    echo ❌ 未找到: C:\nginx\ssl\photogooo.key
)

echo.
echo 检查您提到的位置 (C:\nginx\conf\):
if exist "C:\nginx\conf\*.pem" (
    echo ✅ 在C:\nginx\conf\找到.pem文件:
    dir /b "C:\nginx\conf\*.pem"
) else (
    echo ⚠️  在C:\nginx\conf\未找到.pem文件
)

if exist "C:\nginx\conf\*.key" (
    echo ✅ 在C:\nginx\conf\找到.key文件:
    dir /b "C:\nginx\conf\*.key"
) else (
    echo ⚠️  在C:\nginx\conf\未找到.key文件
)

echo.
echo ========================================
echo 说明:
echo ========================================
echo 如果证书文件在 C:\nginx\conf\ 目录下，您需要:
echo 1. 将证书文件复制到 C:\nginx\ssl\ 目录
echo 2. 或者修改 nginx.conf 配置文件中的证书路径
echo.
echo 建议: 将证书文件移动到 C:\nginx\ssl\ 目录
echo 然后运行 reload_nginx_cert.bat 重新加载配置
echo.
pause



