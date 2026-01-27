# PowerShell脚本：打包项目代码并上传到服务器
# 使用方法: .\打包并上传到服务器.ps1

param(
    [string]$ServerIP = "121.43.143.59",
    [string]$ServerUser = "root"
)

Write-Host "==========================================" -ForegroundColor Green
Write-Host "打包项目代码并上传到服务器" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Write-Host "[1/4] 准备打包文件..." -ForegroundColor Cyan

# 要包含的文件和目录
$includeItems = @(
    "app",
    "templates",
    "static",
    "config",
    "docs",
    "scripts",
    "*.py",
    "requirements.txt",
    "gunicorn.conf.py",
    "start_production.py",
    ".gitignore",
    "README.md"
)

# 创建临时目录
$tempDir = "temp_package_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

Write-Host "  复制文件到临时目录..." -ForegroundColor Yellow
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

# 复制所有.py文件
Get-ChildItem -Path . -Filter "*.py" -File | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $tempDir -Force
}

Write-Host "  ✓ 文件复制完成" -ForegroundColor Green
Write-Host ""

Write-Host "[2/4] 创建压缩包..." -ForegroundColor Cyan
$zipFile = "aistudio_code_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipFile -Force
Write-Host "  ✓ 压缩包创建完成: $zipFile" -ForegroundColor Green

# 获取文件大小
$fileSize = (Get-Item $zipFile).Length / 1MB
Write-Host "  文件大小: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Yellow
Write-Host ""

Write-Host "[3/4] 清理临时文件..." -ForegroundColor Cyan
Remove-Item -Path $tempDir -Recurse -Force
Write-Host "  ✓ 临时文件已清理" -ForegroundColor Green
Write-Host ""

Write-Host "[4/4] 上传到服务器..." -ForegroundColor Cyan
Write-Host "  请选择上传方式:" -ForegroundColor Yellow
Write-Host "  1. 使用SCP命令上传（需要密码或SSH密钥）" -ForegroundColor White
Write-Host "  2. 使用WinSCP手动上传（推荐）" -ForegroundColor White
Write-Host "  3. 稍后手动上传" -ForegroundColor White
Write-Host ""
$uploadChoice = Read-Host "请选择 (1-3)"

if ($uploadChoice -eq "1") {
    Write-Host "  正在上传..." -ForegroundColor Yellow
    $keyFile = Get-ChildItem -Path "aliyun-key" -Filter "*.pem","*.key" -ErrorAction SilentlyContinue | Select-Object -First 1
    
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
Write-Host "==========================================" -ForegroundColor Green
Write-Host "打包完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "在服务器上解压:" -ForegroundColor Cyan
Write-Host "  cd /root/project_code" -ForegroundColor White
Write-Host "  unzip -o $zipFile" -ForegroundColor White
Write-Host ""
