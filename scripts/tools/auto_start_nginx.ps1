# PowerShell版本的自动启动脚本
Write-Host "正在启动HTTPS服务..." -ForegroundColor Green
Write-Host ""

# 停止IIS相关服务
Write-Host "停止IIS服务..." -ForegroundColor Yellow
try {
    Stop-Service -Name "W3SVC" -Force -ErrorAction SilentlyContinue
    Stop-Service -Name "HTTP" -Force -ErrorAction SilentlyContinue
    Write-Host "IIS服务已停止" -ForegroundColor Green
} catch {
    Write-Host "停止IIS服务时出现错误: $($_.Exception.Message)" -ForegroundColor Red
}

# 等待服务完全停止
Start-Sleep -Seconds 3

# 检查并终止占用80端口的进程
Write-Host "检查端口占用..." -ForegroundColor Yellow
$port80Processes = netstat -ano | Select-String ":80" | Select-String "LISTENING"
foreach ($line in $port80Processes) {
    $pid = ($line -split '\s+')[4]
    if ($pid -and $pid -ne "0") {
        Write-Host "发现进程 $pid 占用80端口，正在终止..." -ForegroundColor Yellow
        try {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host "无法终止进程 $pid" -ForegroundColor Red
        }
    }
}

# 等待端口释放
Start-Sleep -Seconds 2

# 启动Nginx
Write-Host "启动Nginx服务..." -ForegroundColor Yellow
Set-Location "C:\new\pet-painting-system"
try {
    Start-Process -FilePath "C:\nginx\nginx.exe" -ArgumentList "-c", "C:\new\pet-painting-system\nginx.conf" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    
    # 检查Nginx是否启动成功
    $nginxRunning = netstat -ano | Select-String ":80" | Select-String "LISTENING"
    if ($nginxRunning) {
        Write-Host "✅ HTTPS服务启动成功！" -ForegroundColor Green
        Write-Host "可以通过 https://photogooo 访问您的网站" -ForegroundColor Cyan
    } else {
        Write-Host "❌ HTTPS服务启动失败，请检查日志" -ForegroundColor Red
    }
} catch {
    Write-Host "启动Nginx时出现错误: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
