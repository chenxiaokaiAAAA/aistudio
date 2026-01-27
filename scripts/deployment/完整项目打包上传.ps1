# PowerShell脚本：完整项目打包上传（包含所有必要文件）
# 使用方法: .\scripts\deployment\完整项目打包上传.ps1

param(
    [string]$ServerIP = "121.43.143.59",
    [string]$ServerUser = "root",
    [string]$KeyPath = "aliyun-key"
)

Write-Host "==========================================" -ForegroundColor Green
Write-Host "完整项目打包上传" -ForegroundColor Green
Write-Host "服务器: $ServerIP" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Write-Host "[1/5] 准备打包文件..." -ForegroundColor Cyan

# 创建临时目录
$tempDir = "temp_full_package_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# 要包含的目录和文件（排除不必要的）
$includeItems = @(
    "app",
    "templates",
    "static",
    "config",
    "docs",
    "scripts",
    "workflows",
    "*.py",
    "requirements.txt",
    "gunicorn.conf.py",
    "start_production.py",
    "start.py",
    ".gitignore",
    "README.md"
)

Write-Host "  复制核心文件..." -ForegroundColor Yellow
foreach ($item in $includeItems) {
    $sourcePath = Join-Path $PWD $item
    if (Test-Path $sourcePath) {
        $destPath = Join-Path $tempDir (Split-Path $item -Leaf)
        if (Test-Path $sourcePath -PathType Container) {
            Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
            Write-Host "    ✓ $item" -ForegroundColor Gray
        } else {
            Copy-Item -Path $sourcePath -Destination $destPath -Force
            Write-Host "    ✓ $item" -ForegroundColor Gray
        }
    }
}

# 复制所有根目录的 .py 文件
Write-Host "  复制Python文件..." -ForegroundColor Yellow
Get-ChildItem -Path . -Filter "*.py" -File | ForEach-Object {
    $destPath = Join-Path $tempDir $_.Name
    Copy-Item -Path $_.FullName -Destination $destPath -Force
    Write-Host "    ✓ $($_.Name)" -ForegroundColor Gray
}

# 复制配置文件（如果存在）
Write-Host "  复制配置文件..." -ForegroundColor Yellow
$configFiles = @("server_config.py", "printer_config.py", "sync_config_routes.py", "order_notification.py", "wechat_notification.py")
foreach ($configFile in $configFiles) {
    if (Test-Path $configFile) {
        Copy-Item -Path $configFile -Destination (Join-Path $tempDir $configFile) -Force
        Write-Host "    ✓ $configFile" -ForegroundColor Gray
    }
}

Write-Host "  ✓ 文件复制完成" -ForegroundColor Green
Write-Host ""

Write-Host "[2/5] 创建压缩包..." -ForegroundColor Cyan
$zipFile = "aistudio_full_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipFile -Force
Write-Host "  ✓ 压缩包创建完成: $zipFile" -ForegroundColor Green

# 获取文件大小
$fileSize = (Get-Item $zipFile).Length / 1MB
Write-Host "  文件大小: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Yellow
Write-Host ""

Write-Host "[3/5] 清理临时文件..." -ForegroundColor Cyan
Remove-Item -Path $tempDir -Recurse -Force
Write-Host "  ✓ 临时文件已清理" -ForegroundColor Green
Write-Host ""

Write-Host "[4/5] 上传到服务器..." -ForegroundColor Cyan
Write-Host "  请选择上传方式:" -ForegroundColor Yellow
Write-Host "  1. 使用SCP命令上传（需要SSH密钥）" -ForegroundColor White
Write-Host "  2. 使用WinSCP手动上传（推荐）" -ForegroundColor White
Write-Host "  3. 稍后手动上传" -ForegroundColor White
Write-Host ""
$uploadChoice = Read-Host "请选择 (1-3)"

if ($uploadChoice -eq "1") {
    Write-Host "  正在上传..." -ForegroundColor Yellow
    $keyFile = Get-ChildItem -Path $KeyPath -Filter "*.pem","*.key" -ErrorAction SilentlyContinue | Select-Object -First 1
    
    if ($keyFile) {
        scp -i $keyFile.FullName $zipFile "${ServerUser}@${ServerIP}:/root/project_code/"
    } else {
        scp $zipFile "${ServerUser}@${ServerIP}:/root/project_code/"
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ 上传成功" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 上传失败，请手动上传" -ForegroundColor Red
    }
} elseif ($uploadChoice -eq "2") {
    Write-Host ""
    Write-Host "  请使用WinSCP上传文件:" -ForegroundColor Yellow
    Write-Host "    1. 打开WinSCP" -ForegroundColor White
    Write-Host "    2. 连接到: $ServerUser@${ServerIP}" -ForegroundColor White
    Write-Host "    3. 上传文件: $zipFile" -ForegroundColor White
    Write-Host "    4. 目标路径: /root/project_code/" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "  压缩包已创建: $zipFile" -ForegroundColor Yellow
    Write-Host "  请稍后手动上传到服务器" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[5/5] 完成！" -ForegroundColor Green
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "下一步操作（在服务器上执行）：" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "1. 备份当前项目（可选）：" -ForegroundColor White
Write-Host "   cd /root/project_code" -ForegroundColor Gray
Write-Host "   mv project_code project_code_backup_$(Get-Date -Format 'yyyyMMdd')" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 解压新文件：" -ForegroundColor White
Write-Host "   cd /root/project_code" -ForegroundColor Gray
Write-Host "   unzip -o $zipFile" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 恢复数据库和图片（如果已上传）：" -ForegroundColor White
Write-Host "   # 数据库文件应该已经在 instance/ 目录" -ForegroundColor Gray
Write-Host "   # 图片文件应该已经在 project_data/user_images/ 目录" -ForegroundColor Gray
Write-Host ""
Write-Host "4. 重启服务：" -ForegroundColor White
Write-Host "   systemctl restart aistudio" -ForegroundColor Gray
Write-Host "   systemctl status aistudio" -ForegroundColor Gray
Write-Host ""
Write-Host "详细说明请查看: docs/deployment/完整项目上传部署指南.md" -ForegroundColor Yellow
