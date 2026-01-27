# PowerShell script: Package and upload full project
# Usage: .\scripts\deployment\package_and_upload.ps1

param(
    [string]$ServerIP = "121.43.143.59",
    [string]$ServerUser = "root",
    [string]$KeyPath = "aliyun-key"
)

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Package Full Project" -ForegroundColor Green
Write-Host "Server: $ServerIP" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Write-Host "[1/5] Preparing files..." -ForegroundColor Cyan

# Create temp directory
$tempDir = "temp_full_package_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Files and directories to include
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

Write-Host "  Copying core files..." -ForegroundColor Yellow
foreach ($item in $includeItems) {
    $sourcePath = Join-Path $PWD $item
    if (Test-Path $sourcePath) {
        $destPath = Join-Path $tempDir (Split-Path $item -Leaf)
        if (Test-Path $sourcePath -PathType Container) {
            Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
            Write-Host "    OK $item" -ForegroundColor Gray
        } else {
            Copy-Item -Path $sourcePath -Destination $destPath -Force
            Write-Host "    OK $item" -ForegroundColor Gray
        }
    }
}

# Copy all .py files in root
Write-Host "  Copying Python files..." -ForegroundColor Yellow
Get-ChildItem -Path . -Filter "*.py" -File | ForEach-Object {
    $destPath = Join-Path $tempDir $_.Name
    Copy-Item -Path $_.FullName -Destination $destPath -Force
    Write-Host "    OK $($_.Name)" -ForegroundColor Gray
}

# Copy config files if exist
Write-Host "  Copying config files..." -ForegroundColor Yellow
$configFiles = @("server_config.py", "printer_config.py", "sync_config_routes.py", "order_notification.py", "wechat_notification.py")
foreach ($configFile in $configFiles) {
    if (Test-Path $configFile) {
        Copy-Item -Path $configFile -Destination (Join-Path $tempDir $configFile) -Force
        Write-Host "    OK $configFile" -ForegroundColor Gray
    }
}

Write-Host "  Files copied successfully" -ForegroundColor Green
Write-Host ""

Write-Host "[2/5] Creating zip file..." -ForegroundColor Cyan
$zipFile = "aistudio_full_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipFile -Force
Write-Host "  Zip file created: $zipFile" -ForegroundColor Green

# Get file size
$fileSize = (Get-Item $zipFile).Length / 1MB
Write-Host "  File size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Yellow
Write-Host ""

Write-Host "[3/5] Cleaning temp files..." -ForegroundColor Cyan
Remove-Item -Path $tempDir -Recurse -Force
Write-Host "  Temp files cleaned" -ForegroundColor Green
Write-Host ""

Write-Host "[4/5] Upload to server..." -ForegroundColor Cyan
Write-Host "  Choose upload method:" -ForegroundColor Yellow
Write-Host "  1. Use SCP command (needs SSH key)" -ForegroundColor White
Write-Host "  2. Use WinSCP manually (Recommended)" -ForegroundColor White
Write-Host "  3. Upload later manually" -ForegroundColor White
Write-Host ""
$uploadChoice = Read-Host "Choose (1-3)"

if ($uploadChoice -eq "1") {
    Write-Host "  Uploading..." -ForegroundColor Yellow
    $keyFile = Get-ChildItem -Path $KeyPath -Filter "*.pem","*.key" -ErrorAction SilentlyContinue | Select-Object -First 1
    
    if ($keyFile) {
        scp -i $keyFile.FullName $zipFile "${ServerUser}@${ServerIP}:/root/project_code/"
    } else {
        scp $zipFile "${ServerUser}@${ServerIP}:/root/project_code/"
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Upload successful" -ForegroundColor Green
    } else {
        Write-Host "  Upload failed, please upload manually" -ForegroundColor Red
    }
} elseif ($uploadChoice -eq "2") {
    Write-Host ""
    Write-Host "  Please use WinSCP to upload:" -ForegroundColor Yellow
    Write-Host "    1. Open WinSCP" -ForegroundColor White
    Write-Host "    2. Connect to: $ServerUser@${ServerIP}" -ForegroundColor White
    Write-Host "    3. Upload file: $zipFile" -ForegroundColor White
    Write-Host "    4. Target path: /root/project_code/" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "  Zip file created: $zipFile" -ForegroundColor Yellow
    Write-Host "  Please upload manually later" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[5/5] Done!" -ForegroundColor Green
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Next steps (on server):" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "1. Backup current project (optional):" -ForegroundColor White
Write-Host "   cd /root/project_code" -ForegroundColor Gray
Write-Host "   mv project_code project_code_backup" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Extract files:" -ForegroundColor White
Write-Host "   cd /root/project_code" -ForegroundColor Gray
Write-Host "   unzip -o $zipFile" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Restart service:" -ForegroundColor White
Write-Host "   systemctl restart aistudio" -ForegroundColor Gray
Write-Host "   systemctl status aistudio" -ForegroundColor Gray
Write-Host ""
