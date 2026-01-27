# PowerShell脚本：上传数据库和图片到阿里云服务器
# 使用方法: .\scripts\deployment\upload_to_aliyun.ps1

param(
    [string]$ServerIP = "121.43.143.59",
    [string]$KeyPath = "aliyun-key\your-key.pem",
    [string]$ServerUser = "root"
)

Write-Host "==========================================" -ForegroundColor Green
Write-Host "上传文件到阿里云服务器" -ForegroundColor Green
Write-Host "服务器: $ServerIP" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# 检查密钥文件
if (-not (Test-Path $KeyPath)) {
    Write-Host "错误: 找不到密钥文件: $KeyPath" -ForegroundColor Red
    Write-Host "请将SSH密钥文件放在 aliyun-key 目录下" -ForegroundColor Yellow
    Write-Host "或修改脚本中的 KeyPath 参数" -ForegroundColor Yellow
    exit 1
}

# 检查SCP命令（需要安装OpenSSH客户端）
$scpCommand = Get-Command scp -ErrorAction SilentlyContinue
if (-not $scpCommand) {
    Write-Host "错误: 未找到 scp 命令" -ForegroundColor Red
    Write-Host "请安装 OpenSSH 客户端:" -ForegroundColor Yellow
    Write-Host "  Windows 10/11: 设置 -> 应用 -> 可选功能 -> 添加 OpenSSH 客户端" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/5] 检查本地文件..." -ForegroundColor Cyan

# 检查数据库文件
$dbFile = "instance\pet_painting.db"
if (Test-Path $dbFile) {
    Write-Host "  ✓ 找到数据库文件: $dbFile" -ForegroundColor Green
} else {
    Write-Host "  ⚠ 未找到数据库文件: $dbFile" -ForegroundColor Yellow
}

# 检查图片目录
$imageDirs = @("uploads", "final_works", "hd_images")
$foundDirs = @()
foreach ($dir in $imageDirs) {
    if (Test-Path $dir) {
        $fileCount = (Get-ChildItem $dir -Recurse -File).Count
        Write-Host "  ✓ 找到图片目录: $dir ($fileCount 个文件)" -ForegroundColor Green
        $foundDirs += $dir
    } else {
        Write-Host "  ⚠ 未找到图片目录: $dir" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[2/5] 选择要上传的内容..." -ForegroundColor Cyan
Write-Host "1. 只上传数据库文件" -ForegroundColor White
Write-Host "2. 只上传图片文件" -ForegroundColor White
Write-Host "3. 上传数据库和图片文件" -ForegroundColor White
Write-Host "4. 取消" -ForegroundColor White
$choice = Read-Host "请选择 (1-4)"

$uploadDB = $false
$uploadImages = $false

switch ($choice) {
    "1" { $uploadDB = $true }
    "2" { $uploadImages = $true }
    "3" { $uploadDB = $true; $uploadImages = $true }
    "4" { Write-Host "已取消" -ForegroundColor Yellow; exit 0 }
    default { Write-Host "无效选择" -ForegroundColor Red; exit 1 }
}

Write-Host ""
Write-Host "[3/5] 上传文件..." -ForegroundColor Cyan

# 上传数据库文件
if ($uploadDB -and (Test-Path $dbFile)) {
    Write-Host "  上传数据库文件..." -ForegroundColor Yellow
    $remotePath = "$ServerUser@${ServerIP}:/root/project_code/instance/"
    scp -i $KeyPath $dbFile "${remotePath}pet_painting.db"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ 数据库文件上传成功" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 数据库文件上传失败" -ForegroundColor Red
    }
}

# 上传图片文件（压缩后上传）
if ($uploadImages -and $foundDirs.Count -gt 0) {
    Write-Host "  压缩图片文件..." -ForegroundColor Yellow
    
    $tempDir = "temp_upload_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    
    foreach ($dir in $foundDirs) {
        $zipFile = "$tempDir\$dir.zip"
        Write-Host "    压缩 $dir..." -ForegroundColor Gray
        Compress-Archive -Path $dir -DestinationPath $zipFile -Force
        Write-Host "    ✓ $dir 压缩完成" -ForegroundColor Green
    }
    
    Write-Host "  上传图片压缩包..." -ForegroundColor Yellow
    foreach ($dir in $foundDirs) {
        $zipFile = "$tempDir\$dir.zip"
        if (Test-Path $zipFile) {
            $remotePath = "$ServerUser@${ServerIP}:/root/project_data/"
            scp -i $KeyPath $zipFile "${remotePath}$dir.zip"
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    ✓ $dir.zip 上传成功" -ForegroundColor Green
            } else {
                Write-Host "    ✗ $dir.zip 上传失败" -ForegroundColor Red
            }
        }
    }
    
    # 清理临时文件
    Write-Host "  清理临时文件..." -ForegroundColor Yellow
    Remove-Item -Path $tempDir -Recurse -Force
    Write-Host "  ✓ 临时文件已清理" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "  请在服务器上解压文件:" -ForegroundColor Cyan
    Write-Host "    ssh -i $KeyPath $ServerUser@${ServerIP}" -ForegroundColor White
    Write-Host "    cd /root/project_data" -ForegroundColor White
    foreach ($dir in $foundDirs) {
        Write-Host "    unzip $dir.zip -d user_images/" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "[4/5] 验证上传..." -ForegroundColor Cyan
Write-Host "  请手动验证文件是否已正确上传到服务器" -ForegroundColor Yellow

Write-Host ""
Write-Host "[5/5] 完成！" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Cyan
Write-Host "  1. 连接到服务器: ssh -i $KeyPath $ServerUser@${ServerIP}" -ForegroundColor White
Write-Host "  2. 解压图片文件（如果上传了）" -ForegroundColor White
Write-Host "  3. 配置环境变量和启动服务" -ForegroundColor White
Write-Host ""
Write-Host "详细说明请查看: docs/deployment/阿里云服务器部署完整指南.md" -ForegroundColor Yellow
