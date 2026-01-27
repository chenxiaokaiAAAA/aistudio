# -*- coding: utf-8 -*-
# 完整同步工具：代码 + 数据库 + 图片到阿里云服务器
# 使用方法：.\scripts\deployment\同步到阿里云服务器.ps1

param(
    [string]$ServerIP = "121.43.143.59",
    [string]$ServerUser = "root",
    [string]$KeyPath = "aliyun-key\your-key.pem",
    [string]$RemotePath = "/root/project_code",
    [switch]$CodeOnly = $false,      # 只同步代码
    [switch]$DatabaseOnly = $false,  # 只同步数据库
    [switch]$ImagesOnly = $false,    # 只同步图片
    [switch]$All = $true             # 同步所有（默认）
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    同步到阿里云服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查必要工具
if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "[错误] 未找到 scp 命令，请安装 OpenSSH 客户端" -ForegroundColor Red
    Write-Host "Windows 10/11: 设置 -> 应用 -> 可选功能 -> OpenSSH 客户端" -ForegroundColor Yellow
    exit 1
}

# 确定同步内容
$syncCode = $All -or $CodeOnly
$syncDatabase = $All -or $DatabaseOnly
$syncImages = $All -or $ImagesOnly

if (-not ($syncCode -or $syncDatabase -or $syncImages)) {
    Write-Host "[错误] 请指定要同步的内容" -ForegroundColor Red
    Write-Host "   -CodeOnly     只同步代码（通过Git）" -ForegroundColor Yellow
    Write-Host "   -DatabaseOnly 只同步数据库" -ForegroundColor Yellow
    Write-Host "   -ImagesOnly   只同步图片" -ForegroundColor Yellow
    Write-Host "   -All          同步所有（默认）" -ForegroundColor Yellow
    exit 1
}

Write-Host "同步配置：" -ForegroundColor Green
Write-Host "  服务器: $ServerUser@$ServerIP" -ForegroundColor White
Write-Host "  远程路径: $RemotePath" -ForegroundColor White
Write-Host "  同步内容:" -ForegroundColor White
if ($syncCode) { Write-Host "    ✅ 代码文件（通过Git）" -ForegroundColor Green }
if ($syncDatabase) { Write-Host "    ✅ 数据库文件" -ForegroundColor Green }
if ($syncImages) { Write-Host "    ✅ 图片文件" -ForegroundColor Green }
Write-Host ""

$confirm = Read-Host "确认开始同步？(Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "已取消" -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# ==================== 1. 同步代码（通过Git） ====================
if ($syncCode) {
    Write-Host "[1/3] 同步代码到GitHub..." -ForegroundColor Cyan
    
    # 检查Git状态
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        Write-Host "  检测到未提交的更改，是否先提交到GitHub？" -ForegroundColor Yellow
        $commitConfirm = Read-Host "  提交并推送？(Y/N，直接回车跳过)"
        
        if ($commitConfirm -eq "Y" -or $commitConfirm -eq "y") {
            Write-Host "  添加文件..." -ForegroundColor White
            git add .
            
            $commitMsg = Read-Host "  请输入提交信息（直接回车使用默认）"
            if ([string]::IsNullOrWhiteSpace($commitMsg)) {
                $commitMsg = "更新代码：同步到服务器"
            }
            
            Write-Host "  提交更改..." -ForegroundColor White
            git commit -m $commitMsg
            
            Write-Host "  推送到GitHub..." -ForegroundColor White
            git push origin master
            if ($LASTEXITCODE -ne 0) {
                git push origin main
            }
            Write-Host "  ✅ 代码已推送到GitHub" -ForegroundColor Green
        }
    } else {
        Write-Host "  ℹ️  没有未提交的更改" -ForegroundColor Gray
    }
    
    # 在服务器上拉取最新代码
    Write-Host ""
    Write-Host "  在服务器上拉取最新代码..." -ForegroundColor White
    $sshCmd = "cd $RemotePath && git pull origin master || git pull origin main"
    
    if (Test-Path $KeyPath) {
        ssh -i $KeyPath $ServerUser@$ServerIP $sshCmd
    } else {
        ssh $ServerUser@$ServerIP $sshCmd
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 代码同步完成" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  代码同步可能失败，请检查服务器连接" -ForegroundColor Yellow
    }
}

# ==================== 2. 同步数据库 ====================
if ($syncDatabase) {
    Write-Host ""
    Write-Host "[2/3] 同步数据库文件..." -ForegroundColor Cyan
    
    $dbFile = "instance\pet_painting.db"
    if (Test-Path $dbFile) {
        $dbSize = (Get-Item $dbFile).Length / 1MB
        Write-Host "  数据库文件: $dbFile ($([math]::Round($dbSize, 2)) MB)" -ForegroundColor White
        
        $remoteDbPath = "$RemotePath/instance/pet_painting.db"
        
        Write-Host "  正在上传..." -ForegroundColor White
        if (Test-Path $KeyPath) {
            scp -i $KeyPath $dbFile "${ServerUser}@${ServerIP}:${remoteDbPath}"
        } else {
            scp $dbFile "${ServerUser}@${ServerIP}:${remoteDbPath}"
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ 数据库同步完成" -ForegroundColor Green
            
            # 设置权限
            Write-Host "  设置文件权限..." -ForegroundColor White
            $permCmd = "chmod 644 $remoteDbPath && chown root:root $remoteDbPath"
            if (Test-Path $KeyPath) {
                ssh -i $KeyPath $ServerUser@$ServerIP $permCmd
            } else {
                ssh $ServerUser@$ServerIP $permCmd
            }
        } else {
            Write-Host "  ⚠️  数据库同步失败" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⚠️  数据库文件不存在: $dbFile" -ForegroundColor Yellow
    }
}

# ==================== 3. 同步图片 ====================
if ($syncImages) {
    Write-Host ""
    Write-Host "[3/3] 同步图片文件..." -ForegroundColor Cyan
    
    $imageDirs = @(
        @{Local = "uploads"; Remote = "$RemotePath/uploads"},
        @{Local = "final_works"; Remote = "$RemotePath/final_works"},
        @{Local = "hd_images"; Remote = "$RemotePath/hd_images"}
    )
    
    foreach ($dir in $imageDirs) {
        $localPath = $dir.Local
        $remotePath = $dir.Remote
        
        if (Test-Path $localPath) {
            $fileCount = (Get-ChildItem -Path $localPath -Recurse -File).Count
            if ($fileCount -gt 0) {
                Write-Host "  同步目录: $localPath ($fileCount 个文件)..." -ForegroundColor White
                
                # 使用 rsync 或 scp -r
                if (Get-Command rsync -ErrorAction SilentlyContinue) {
                    # 使用 rsync（更高效）
                    if (Test-Path $KeyPath) {
                        rsync -avz -e "ssh -i $KeyPath" "$localPath/" "${ServerUser}@${ServerIP}:${remotePath}/"
                    } else {
                        rsync -avz "$localPath/" "${ServerUser}@${ServerIP}:${remotePath}/"
                    }
                } else {
                    # 使用 scp -r（较慢但兼容性好）
                    Write-Host "    ⚠️  建议安装 rsync 以提高同步效率" -ForegroundColor Yellow
                    if (Test-Path $KeyPath) {
                        scp -r -i $KeyPath "$localPath" "${ServerUser}@${ServerIP}:${remotePath}/../"
                    } else {
                        scp -r "$localPath" "${ServerUser}@${ServerIP}:${remotePath}/../"
                    }
                }
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "    ✅ $localPath 同步完成" -ForegroundColor Green
                } else {
                    Write-Host "    ⚠️  $localPath 同步可能失败" -ForegroundColor Yellow
                }
            } else {
                Write-Host "  ℹ️  $localPath 目录为空，跳过" -ForegroundColor Gray
            }
        } else {
            Write-Host "  ℹ️  $localPath 目录不存在，跳过" -ForegroundColor Gray
        }
    }
}

# ==================== 完成 ====================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    同步完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 询问是否重启服务
$restartConfirm = Read-Host "是否重启服务器上的应用服务？(Y/N)"
if ($restartConfirm -eq "Y" -or $restartConfirm -eq "y") {
    Write-Host "重启服务..." -ForegroundColor Cyan
    $restartCmd = "systemctl restart aistudio"
    if (Test-Path $KeyPath) {
        ssh -i $KeyPath $ServerUser@$ServerIP $restartCmd
    } else {
        ssh $ServerUser@$ServerIP $restartCmd
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 服务已重启" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "提示：可以访问服务器查看日志：" -ForegroundColor Yellow
Write-Host "  ssh $ServerUser@$ServerIP 'journalctl -u aistudio -f'" -ForegroundColor Gray
Write-Host ""
