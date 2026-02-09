# Sync to Aliyun Server
# Usage: .\scripts\deployment\sync_to_aliyun.ps1 -CodeOnly

param(
    [string]$ServerIP = "121.43.143.59",
    [string]$ServerUser = "root",
    [string]$KeyPath = "aliyun-key\aistudio.pem",
    [string]$RemotePath = "/root/project_code",
    [switch]$CodeOnly,
    [switch]$DatabaseOnly,
    [switch]$ImagesOnly,
    [switch]$All
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    同步到阿里云服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to find rsync command
function Find-RsyncCommand {
    # First, try to find rsync in PATH
    $rsyncCmd = Get-Command rsync -ErrorAction SilentlyContinue
    if ($rsyncCmd) {
        return $rsyncCmd.Source
    }
    
    # Check common rsync installation paths (including different drives)
    $rsyncPaths = @(
        "C:\Program Files\Git\usr\bin\rsync.exe",
        "C:\Program Files (x86)\Git\usr\bin\rsync.exe",
        "D:\Program Files\Git\usr\bin\rsync.exe",
        "E:\Program Files\Git\usr\bin\rsync.exe",
        "C:\cygwin64\bin\rsync.exe",
        "C:\cygwin\bin\rsync.exe",
        "D:\cygwin64\bin\rsync.exe",
        "C:\cwRsync\bin\rsync.exe",
        "C:\msys64\usr\bin\rsync.exe",
        "C:\msys2\usr\bin\rsync.exe"
    )
    
    foreach ($path in $rsyncPaths) {
        if (Test-Path $path) {
            try {
                $version = & $path --version 2>&1 | Select-Object -First 1
                if ($version -match "rsync version") {
                    return $path
                }
            } catch {
                continue
            }
        }
    }
    
    # Search in Program Files for Git
    $pfPath = [Environment]::GetFolderPath("ProgramFiles")
    $pfPathX86 = ${env:ProgramFiles(x86)}
    foreach ($base in @($pfPath, $pfPathX86)) {
        if ($base) {
            $gitRsync = Join-Path $base "Git\usr\bin\rsync.exe"
            if (Test-Path $gitRsync) {
                try {
                    $version = & $gitRsync --version 2>&1 | Select-Object -First 1
                    if ($version -match "rsync version") { return $gitRsync }
                } catch { }
            }
        }
    }
    
    return $null
}

# Check tools
$rsyncPath = Find-RsyncCommand
if ($rsyncPath) {
    Write-Host "[OK] 已找到 rsync: $rsyncPath" -ForegroundColor Green
    try {
        $rsyncVersion = & $rsyncPath --version 2>&1 | Select-Object -First 1
        Write-Host "      $rsyncVersion" -ForegroundColor Gray
    } catch {
        # Ignore version check errors
    }
} else {
    Write-Host "[信息] 未找到 rsync，将使用 scp（较慢但可用）" -ForegroundColor Yellow
    Write-Host "       提示: 若已安装 Git/Cygwin，请将其 usr\bin 加入系统 PATH" -ForegroundColor Gray
}
Write-Host ""

if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "[错误] 未找到 scp 命令" -ForegroundColor Red
    exit 1
}

# Auto-detect SSH key if not found
if (-not (Test-Path $KeyPath)) {
    Write-Host "[信息] 未找到密钥文件: $KeyPath" -ForegroundColor Yellow
    Write-Host "[信息] 正在 aliyun-key 目录中搜索密钥..." -ForegroundColor Yellow
    
    if (Test-Path "aliyun-key") {
        $foundKey = Get-ChildItem -Path "aliyun-key" -Filter "*.pem","*.key" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($foundKey) {
            $KeyPath = $foundKey.FullName
            Write-Host "[OK] 已找到密钥: $KeyPath" -ForegroundColor Green
        } else {
            Write-Host "[警告] aliyun-key 目录中未找到密钥" -ForegroundColor Yellow
            Write-Host "[信息] 将尝试密码认证连接" -ForegroundColor Yellow
            $KeyPath = $null
        }
    } else {
        Write-Host "[警告] 未找到 aliyun-key 目录" -ForegroundColor Yellow
        Write-Host "[信息] 将尝试密码认证连接" -ForegroundColor Yellow
        $KeyPath = $null
    }
    Write-Host ""
}

# Function to fix SSH key permissions
function Fix-SSHKeyPermissions {
    param([string]$KeyFile)
    
    if (-not (Test-Path $KeyFile)) {
        return $false
    }
    
    Write-Host "[信息] 正在修复 SSH 密钥权限..." -ForegroundColor Yellow
    
    # Step 1: Remove inheritance
    $result1 = & icacls $KeyFile /inheritance:r 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [警告] 移除继承失败" -ForegroundColor Yellow
    }
    
    # Step 2: Grant full control to current user only
    $currentUser = $env:USERNAME
    $result2 = & icacls $KeyFile /grant "${currentUser}:(F)" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [错误] 授权当前用户失败" -ForegroundColor Red
        return $false
    }
    
    # Step 3: Remove all other users and groups
    $groupsToRemove = @("Users", "Everyone", "Authenticated Users", "BUILTIN\Users")
    foreach ($group in $groupsToRemove) {
        & icacls $KeyFile /remove $group 2>&1 | Out-Null
    }
    
    # Step 4: Remove Administrators and System if they're not needed (keep them for safety)
    # Only remove if they have read access (SSH requires strict permissions)
    $acl = Get-Acl $KeyFile
    foreach ($access in $acl.Access) {
        $identity = $access.IdentityReference.Value
        if ($identity -ne $currentUser -and 
            $identity -ne "$env:USERDOMAIN\$currentUser" -and
            $access.FileSystemRights -match "Read|FullControl") {
            # Try to remove, but don't fail if it doesn't work
            & icacls $KeyFile /remove $identity 2>&1 | Out-Null
        }
    }
    
    # Step 5: Verify permissions
    $finalAcl = Get-Acl $KeyFile
    $hasOpenPermissions = $false
    foreach ($access in $finalAcl.Access) {
        $identity = $access.IdentityReference.Value
        if ($identity -ne $currentUser -and 
            $identity -ne "$env:USERDOMAIN\$currentUser" -and
            $identity -ne "BUILTIN\Administrators" -and
            $identity -ne "NT AUTHORITY\SYSTEM" -and
            $access.FileSystemRights -match "Read|FullControl") {
            $hasOpenPermissions = $true
            break
        }
    }
    
    if ($hasOpenPermissions) {
        Write-Host "  [警告] 部分权限可能仍过于开放" -ForegroundColor Yellow
        return $false
    } else {
        Write-Host "  [OK] SSH 密钥权限已修复" -ForegroundColor Green
        return $true
    }
}

# Fix SSH key permissions if key file exists (Windows only)
if ($KeyPath -and (Test-Path $KeyPath)) {
    # On Windows, always check and fix permissions
    if ($IsWindows -ne $false -or $env:OS -match "Windows") {
        Write-Host "[信息] 正在检查 SSH 密钥权限..." -ForegroundColor Cyan
        
        # Test SSH connection first
        Write-Host "[信息] 正在测试 SSH 连接..." -ForegroundColor Cyan
        $testCmd = "echo 'test'"
        $testResult = if ($KeyPath -and (Test-Path $KeyPath)) {
            ssh -i $KeyPath -o StrictHostKeyChecking=no -o ConnectTimeout=5 $ServerUser@$ServerIP $testCmd 2>&1
        } else {
            ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 $ServerUser@$ServerIP $testCmd 2>&1
        }
        
        $connectionFailed = $false
        if ($LASTEXITCODE -ne 0) {
            $errorOutput = $testResult -join " "
            if ($errorOutput -match "Permissions.*too open" -or $errorOutput -match "UNPROTECTED PRIVATE KEY") {
                Write-Host "[警告] SSH 密钥权限过于开放，正在修复..." -ForegroundColor Yellow
                $fixResult = Fix-SSHKeyPermissions -KeyFile $KeyPath
                if ($fixResult) {
                    # Test again after fixing
                    Write-Host "[信息] 正在重新测试 SSH 连接..." -ForegroundColor Cyan
                    $testResult2 = ssh -i $KeyPath -o StrictHostKeyChecking=no -o ConnectTimeout=5 $ServerUser@$ServerIP $testCmd 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "[OK] SSH 连接测试通过" -ForegroundColor Green
                    } else {
                        Write-Host "[警告] SSH 连接仍失败，但将继续尝试同步" -ForegroundColor Yellow
                        $connectionFailed = $true
                    }
                } else {
                    Write-Host "[错误] 自动修复 SSH 密钥权限失败" -ForegroundColor Red
                    Write-Host "[信息] 请运行 scripts/deployment/ 下的 SSH 密钥修复脚本" -ForegroundColor Yellow
                    $connectionFailed = $true
                }
            } else {
                Write-Host "[警告] SSH 连接测试失败: $errorOutput" -ForegroundColor Yellow
                $connectionFailed = $true
            }
        } else {
            Write-Host "[OK] SSH 连接测试通过" -ForegroundColor Green
        }
        
        # If connection failed but not due to permissions, try to fix permissions anyway
        if ($connectionFailed -and $testResult -notmatch "Permissions.*too open" -and $testResult -notmatch "UNPROTECTED PRIVATE KEY") {
            Write-Host "[信息] 正在主动修复 SSH 密钥权限..." -ForegroundColor Cyan
            Fix-SSHKeyPermissions -KeyFile $KeyPath | Out-Null
        }
        
        Write-Host ""
    }
}

# Determine sync content
# Check which options were explicitly provided
$hasCodeOnly = $CodeOnly
$hasDatabaseOnly = $DatabaseOnly
$hasImagesOnly = $ImagesOnly
$hasAll = $All

# If no option specified via parameter, show interactive menu
if (-not ($hasCodeOnly -or $hasDatabaseOnly -or $hasImagesOnly -or $hasAll)) {
    Write-Host ""
    Write-Host "请选择同步内容:" -ForegroundColor Yellow
    Write-Host "  1. 仅同步代码 (通过 Git)" -ForegroundColor White
    Write-Host "  2. 仅同步数据库" -ForegroundColor White
    Write-Host "  3. 仅同步图片" -ForegroundColor White
    Write-Host "  4. 同步全部 (代码+数据库+图片)" -ForegroundColor White
    Write-Host "  0. 取消" -ForegroundColor Gray
    Write-Host ""
    $menuChoice = Read-Host "请输入选项 (1-4, 直接回车=4)"
    if ($menuChoice -eq "0") {
        Write-Host "已取消" -ForegroundColor Yellow
        exit 0
    }
    if ([string]::IsNullOrWhiteSpace($menuChoice) -or $menuChoice -eq "4") {
        $hasAll = $true
    } elseif ($menuChoice -eq "1") { $hasCodeOnly = $true }
    elseif ($menuChoice -eq "2") { $hasDatabaseOnly = $true }
    elseif ($menuChoice -eq "3") { $hasImagesOnly = $true }
    else {
        Write-Host "[警告] 无效选项，使用默认: 同步全部" -ForegroundColor Yellow
        $hasAll = $true
    }
    Write-Host ""
}

# If All is explicitly specified, sync everything
if ($hasAll) {
    $syncCode = $true
    $syncDatabase = $true
    $syncImages = $true
} elseif ($hasCodeOnly -or $hasDatabaseOnly -or $hasImagesOnly) {
    # If any specific option is provided, only sync that
    $syncCode = $hasCodeOnly
    $syncDatabase = $hasDatabaseOnly
    $syncImages = $hasImagesOnly
} else {
    # Fallback default to All
    $syncCode = $true
    $syncDatabase = $true
    $syncImages = $true
}

if (-not ($syncCode -or $syncDatabase -or $syncImages)) {
    Write-Host "[错误] 请指定同步内容" -ForegroundColor Red
    exit 1
}

Write-Host "同步配置:" -ForegroundColor Green
Write-Host "  服务器: $ServerUser@$ServerIP" -ForegroundColor White
Write-Host "  远程路径: $RemotePath" -ForegroundColor White
Write-Host "  Sync:" -ForegroundColor White
if ($syncCode) { Write-Host "    [OK] 代码 (via Git)" -ForegroundColor Green } else { Write-Host "    [跳过] 代码" -ForegroundColor Gray }
if ($syncDatabase) { Write-Host "    [OK] 数据库" -ForegroundColor Green } else { Write-Host "    [跳过] 数据库" -ForegroundColor Gray }
if ($syncImages) { Write-Host "    [OK] 图片" -ForegroundColor Green } else { Write-Host "    [跳过] 图片" -ForegroundColor Gray }
Write-Host ""

$confirm = Read-Host "确认? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "已取消" -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# Helper function to build SSH command
function Build-SSHCommand {
    param([string]$Command)
    
    if ($KeyPath -and (Test-Path $KeyPath)) {
        return "ssh -i $KeyPath $ServerUser@$ServerIP $Command"
    } else {
        return "ssh $ServerUser@$ServerIP $Command"
    }
}

# Helper function to execute SSH command
function Invoke-SSHCommand {
    param([string]$Command)
    
    if ($KeyPath -and (Test-Path $KeyPath)) {
        $result = ssh -i $KeyPath $ServerUser@$ServerIP $Command 2>&1
    } else {
        $result = ssh $ServerUser@$ServerIP $Command 2>&1
    }
    return $result
}

# Helper function to build remote path command (avoid escaping issues)
function Build-RemotePathCommand {
    param([string]$RemotePath)
    
    # Use single quotes in bash command to avoid escaping issues
    $escapedPath = $RemotePath.Replace("'", "''")
    $cmd = "if [ -d '$escapedPath' ]; then find '$escapedPath' -type f 2>/dev/null | wc -l; else echo '0'; fi"
    return $cmd
}

# 1. Sync Code
if ($syncCode) {
    Write-Host "[1/3] 同步代码..." -ForegroundColor Cyan
    
    $gitStatus = git status --porcelain 2>&1
    if ($gitStatus) {
        Write-Host "  检测到未提交的更改" -ForegroundColor Yellow
        $commitConfirm = Read-Host "  是否提交并推送? (Y/N)"
        
        if ($commitConfirm -eq "Y" -or $commitConfirm -eq "y") {
            Write-Host "  正在添加文件..." -ForegroundColor White
            git add . 2>&1 | Out-Null
            
            $commitMsg = Read-Host "  提交信息 (回车使用默认)"
            if ([string]::IsNullOrWhiteSpace($commitMsg)) {
                $commitMsg = "Update code: sync to server"
            }
            
            Write-Host "  正在提交..." -ForegroundColor White
            git commit -m $commitMsg 2>&1 | Out-Null
            
            Write-Host "  正在推送到 GitHub..." -ForegroundColor White
            git push origin master 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                git push origin main 2>&1 | Out-Null
            }
            Write-Host "  [OK] 代码已推送到 GitHub" -ForegroundColor Green
        }
    }
    
    Write-Host ""
    Write-Host "  正在服务器上拉取最新代码..." -ForegroundColor White
    $sshCmd = "cd $RemotePath; git pull origin master 2>&1 || git pull origin main 2>&1"
    
    Invoke-SSHCommand -Command $sshCmd | Out-Host
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] 代码同步完成" -ForegroundColor Green
    } else {
        Write-Host "  [警告] 代码同步可能失败" -ForegroundColor Yellow
    }
}

# 2. Sync Database
if ($syncDatabase) {
    Write-Host ""
    Write-Host "[2/3] 同步数据库..." -ForegroundColor Cyan
    
    # Check if using PostgreSQL (from .env)
    $dbUrl = $env:DATABASE_URL
    if (-not $dbUrl -and (Test-Path ".env")) {
        $envContent = Get-Content ".env" -Raw -ErrorAction SilentlyContinue
        if ($envContent -match 'DATABASE_URL=(.+)') {
            $dbUrl = $matches[1].Trim()
        }
    }
    
    if ($dbUrl -and $dbUrl -match 'postgresql') {
        # PostgreSQL: pg_dump -> scp -> psql restore
        Write-Host "  Database type: PostgreSQL" -ForegroundColor White
        $pgDump = Get-Command pg_dump -ErrorAction SilentlyContinue
        if (-not $pgDump) {
            Write-Host "  [错误] 未找到 pg_dump，请安装 PostgreSQL 客户端或加入 PATH" -ForegroundColor Red
        } else {
            $dumpFile = "instance\pet_painting_dump_temp.sql"
            $remoteDumpPath = "$RemotePath/instance/pet_painting_dump_temp.sql"
            Write-Host "  Dumping local PostgreSQL..." -ForegroundColor White
            $env:PGPASSWORD = $null
            if ($dbUrl -match 'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/([^\?]+)') {
                $pgUser = $matches[1]
                $pgPass = $matches[2] -replace "'", "''"
                $pgHost = $matches[3]
                $pgPort = $matches[4]
                $pgDb = $matches[5]
                $env:PGPASSWORD = $matches[2]
                & pg_dump -h $pgHost -p $pgPort -U $pgUser -d $pgDb -F p -f $dumpFile 2>&1 | Out-Null
            } else {
                Write-Host "  [错误] 无法解析 DATABASE_URL" -ForegroundColor Red
            }
            if ($LASTEXITCODE -eq 0 -and (Test-Path $dumpFile)) {
                $dbSize = (Get-Item $dumpFile).Length / 1MB
                Write-Host "  Dump: $dumpFile ($([math]::Round($dbSize, 2)) MB)" -ForegroundColor White
                Write-Host "  正在上传..." -ForegroundColor White
                if ($KeyPath -and (Test-Path $KeyPath)) {
                    scp -i $KeyPath $dumpFile "${ServerUser}@${ServerIP}:${remoteDumpPath}" 2>&1 | Out-Null
                } else {
                    scp $dumpFile "${ServerUser}@${ServerIP}:${remoteDumpPath}" 2>&1 | Out-Null
                }
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  Restoring on server..." -ForegroundColor White
                    $restoreCmd = "cd $RemotePath && PGPASSWORD='$pgPass' psql -h localhost -p $pgPort -U $pgUser -d $pgDb -f instance/pet_painting_dump_temp.sql -q 2>/dev/null; rm -f instance/pet_painting_dump_temp.sql"
                    Invoke-SSHCommand -Command $restoreCmd | Out-Null
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "  [OK] PostgreSQL 同步完成" -ForegroundColor Green
                    } else {
                        Write-Host "  [警告] 恢复可能失败，请检查服务器" -ForegroundColor Yellow
                    }
                } else {
                    Write-Host "  [警告] 上传失败" -ForegroundColor Yellow
                }
                Remove-Item $dumpFile -Force -ErrorAction SilentlyContinue
            } else {
                Write-Host "  [错误] pg_dump 失败" -ForegroundColor Red
            }
            $env:PGPASSWORD = $null
        }
    } else {
        # SQLite: sync pet_painting.db file
        $dbFile = "instance\pet_painting.db"
        if (Test-Path $dbFile) {
            $dbSize = (Get-Item $dbFile).Length / 1MB
            Write-Host "  Database: $dbFile (SQLite, $([math]::Round($dbSize, 2)) MB)" -ForegroundColor White
            $remoteDbPath = "$RemotePath/instance/pet_painting.db"
            Write-Host "  正在上传..." -ForegroundColor White
            if ($KeyPath -and (Test-Path $KeyPath)) {
                scp -i $KeyPath $dbFile "${ServerUser}@${ServerIP}:${remoteDbPath}" 2>&1 | Out-Null
            } else {
                scp $dbFile "${ServerUser}@${ServerIP}:${remoteDbPath}" 2>&1 | Out-Null
            }
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [OK] 数据库同步完成" -ForegroundColor Green
                Write-Host "  正在设置权限..." -ForegroundColor White
                $permCmd = "chmod 644 $remoteDbPath; chown root:root $remoteDbPath"
                Invoke-SSHCommand -Command $permCmd | Out-Null
            } else {
                Write-Host "  [警告] 数据库同步失败" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  [警告] 未找到数据库文件: $dbFile" -ForegroundColor Yellow
        }
    }
}

# 3. Sync Images
if ($syncImages) {
    Write-Host ""
    Write-Host "[3/3] 同步图片..." -ForegroundColor Cyan
    
    $imageDirs = @("uploads", "final_works", "hd_images")
    
    foreach ($localPath in $imageDirs) {
        $remotePath = "$RemotePath/$localPath"
        
        if (Test-Path $localPath) {
            $files = Get-ChildItem -Path $localPath -Recurse -File -ErrorAction SilentlyContinue
            $fileCount = $files.Count
            if ($fileCount -gt 0) {
                Write-Host "  同步中: $localPath ($fileCount 个文件)..." -ForegroundColor White
                
                $syncSuccess = $false
                
                # Check for rsync (re-check in case it wasn't found at script start)
                if (-not $rsyncPath) {
                    $rsyncPath = Find-RsyncCommand
                }
                
                if ($rsyncPath) {
                    # Use rsync for better performance with detailed output
                    Write-Host "    使用 rsync 增量同步..." -ForegroundColor Cyan
                    if ($rsyncPath -match "cygwin") {
                        Write-Host "    [信息] 使用 Cygwin rsync: $rsyncPath" -ForegroundColor Gray
                    }
                    
                    # Count files before sync
                    $localFileCount = (Get-ChildItem -Path $localPath -Recurse -File).Count
                    $remoteFileCountCmd = Build-RemotePathCommand -RemotePath $remotePath
                    $remoteFileCountBefore = (Invoke-SSHCommand -Command $remoteFileCountCmd | Select-Object -First 1).Trim()
                    
                    $infoMsg = "    [信息] 本地: $localFileCount 个文件, 远程: $remoteFileCountBefore 个文件"
                    Write-Host $infoMsg -ForegroundColor Gray
                    Write-Host "    正在传输文件..." -ForegroundColor Gray
                    
                    # Convert Windows path to appropriate format for rsync
                    $localPathAbsolute = (Resolve-Path $localPath).Path
                    
                    if ($rsyncPath -match "cygwin") {
                        # For Cygwin rsync, convert Windows path to Cygwin format
                        # E:\AI-STUDIO\aistudio\uploads -> /cygdrive/e/AI-STUDIO/aistudio/uploads
                        $driveLetter = $localPathAbsolute.Substring(0, 1).ToLower()
                        $pathWithoutDrive = $localPathAbsolute.Substring(3)  # Remove "E:\"
                        $localPathForRsync = "/cygdrive/$driveLetter/" + $pathWithoutDrive.Replace("\", "/")
                    } else {
                        # For Git Bash rsync or other, use forward slashes
                        $localPathForRsync = $localPathAbsolute.Replace("\", "/")
                    }
                    
                    # Ensure trailing slash for directory sync
                    if (-not $localPathForRsync.EndsWith("/")) {
                        $localPathForRsync += "/"
                    }
                    
                    # Ensure remote path uses forward slashes only
                    $remotePathForRsync = $remotePath.Replace("\", "/")
                    if (-not $remotePathForRsync.EndsWith("/")) {
                        $remotePathForRsync += "/"
                    }
                    
                    $rsyncOutput = if ($KeyPath -and (Test-Path $KeyPath)) {
                        $sshCmd = "ssh -i $KeyPath"
                        & $rsyncPath -avz --progress --itemize-changes -e $sshCmd "$localPathForRsync" "${ServerUser}@${ServerIP}:${remotePathForRsync}" 2>&1
                    } else {
                        & $rsyncPath -avz --progress --itemize-changes "$localPathForRsync" "${ServerUser}@${ServerIP}:${remotePathForRsync}" 2>&1
                    }
                    
                    # Parse rsync output to show what changed
                    $newFiles = @()
                    $updatedFiles = @()
                    $skippedFiles = 0
                    
                    foreach ($line in ($rsyncOutput -split [Environment]::NewLine)) {
                        $trimmed = $line.Trim()
                        if ($trimmed -match '^>f\s+(.+)$') {
                            $updatedFiles += $matches[1]
                        } elseif ($trimmed -match '^>f\+\s+(.+)$') {
                            $newFiles += $matches[1]
                        } elseif ($trimmed -match '^\.d') {
                            $skippedFiles++
                        }
                    }
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host ""
                        Write-Host "    +-- 同步统计 --------------------------------+" -ForegroundColor Cyan
                        Write-Host "    | 新增: $($newFiles.Count)" -ForegroundColor Green
                        Write-Host "    | 更新: $($updatedFiles.Count)" -ForegroundColor Yellow
                        Write-Host "    | 跳过: $skippedFiles" -ForegroundColor Gray
                        Write-Host "    +--------------------------------------------------+" -ForegroundColor Cyan
                        
                        if ($newFiles.Count -gt 0) {
                            Write-Host ""
                            Write-Host "    [新增文件] ($($newFiles.Count)):" -ForegroundColor Green
                            foreach ($file in $newFiles | Select-Object -First 10) {
                                Write-Host "      + $file" -ForegroundColor Green
                            }
                            if ($newFiles.Count -gt 10) {
                                $moreCount = $newFiles.Count - 10
                                Write-Host "      ... and $moreCount more new files" -ForegroundColor DarkGreen
                            }
                        }
                        
                        if ($updatedFiles.Count -gt 0) {
                            Write-Host ""
                            Write-Host "    [更新文件] ($($updatedFiles.Count)):" -ForegroundColor Yellow
                            foreach ($file in $updatedFiles | Select-Object -First 10) {
                                Write-Host "      ~ $file" -ForegroundColor Yellow
                            }
                            if ($updatedFiles.Count -gt 10) {
                                $moreCount = $updatedFiles.Count - 10
                                Write-Host "      ... and $moreCount more files updated" -ForegroundColor DarkYellow
                            }
                        }
                        
                        $syncSuccess = $true
                    } else {
                        Write-Host "    [错误] rsync 同步失败" -ForegroundColor Red
                        Write-Host $rsyncOutput -ForegroundColor Red
                    }
                } else {
                    Write-Host "    [提示] 安装 rsync 可提升速度和增量同步" -ForegroundColor Yellow
                    
                    # Use incremental sync with scp - compare files before syncing
                    Write-Host "    正在分析文件以增量同步..." -ForegroundColor Gray
                    
                    # Get local files with size and modification time
                    $localFiles = Get-ChildItem -Path $localPath -Recurse -File | ForEach-Object {
                        $basePath = (Resolve-Path $localPath).Path
                        $relativePath = $_.FullName.Replace($basePath, "").Replace([char]92, "/")
                        [PSCustomObject]@{
                            RelativePath = $relativePath
                            FullPath = $_.FullName
                            Size = $_.Length
                            LastWriteTime = $_.LastWriteTime
                            Name = $_.Name
                        }
                    }
                    
                    # Get remote files info (if directory exists)
                    Write-Host "    正在检查远程文件..." -ForegroundColor Gray
                    $remoteFilesInfo = @{}
                    $escapedPath = $remotePath.Replace("'", "''")
                    $statFormat = '%s|%Y|%n'
                    $getRemoteFilesCmd = ("if [ -d '{0}' ]; then find '{0}' -type f -exec stat -c '{1}' {{}} \; 2>/dev/null; fi" -f $escapedPath, $statFormat)
                    $remoteFilesOutput = Invoke-SSHCommand -Command $getRemoteFilesCmd
                    
                    if ($remoteFilesOutput -and $LASTEXITCODE -eq 0) {
                        foreach ($line in ($remoteFilesOutput -split [Environment]::NewLine | Where-Object { $_.Trim() -ne "" })) {
                            if ($line -match '^(\d+)\|(\d+)\|(.+)$') {
                                $size = [long]$matches[1]
                                $mtime = [long]$matches[2]
                                $filePath = $matches[3]
                                $relativePath = $filePath.Replace($remotePath, "").TrimStart('/')
                                $remoteFilesInfo[$relativePath] = @{
                                    Size = $size
                                    MTime = $mtime
                                }
                            }
                        }
                    }
                    
                    # Compare files and determine what needs to be synced
                    $filesToSync = @()
                    $filesToSkip = @()
                    $newFiles = @()
                    $updatedFiles = @()
                    
                    foreach ($localFile in $localFiles) {
                        $relPath = $localFile.RelativePath
                        if ($remoteFilesInfo.ContainsKey($relPath)) {
                            # File exists on remote, check if update needed
                            $remoteInfo = $remoteFilesInfo[$relPath]
                            $localMTime = [DateTimeOffset]$localFile.LastWriteTime
                            $localUnixTime = $localMTime.ToUnixTimeSeconds()
                            
                            # Incremental sync: compare size and mtime
                            if ($localFile.Size -ne $remoteInfo.Size -or $localUnixTime -gt $remoteInfo.MTime) {
                                # File changed, need overwrite
                                $filesToSync += $localFile
                                $updatedFiles += $localFile
                            } else {
                                # File unchanged, skip (incremental)
                                $filesToSkip += $localFile
                            }
                        } else {
                            # New file, need sync
                            $filesToSync += $localFile
                            $newFiles += $localFile
                        }
                    }
                    
                    # Display sync summary
                    Write-Host ""
                    Write-Host "    +-- 同步统计 (增量+覆盖) ---------+" -ForegroundColor Cyan
                    Write-Host "    | 本地: $($localFiles.Count) 个文件" -ForegroundColor White
                    Write-Host "    | 待同步: $($filesToSync.Count) (覆盖远程)" -ForegroundColor Yellow
                    Write-Host "    |   +- 新增: $($newFiles.Count)" -ForegroundColor Green
                    Write-Host "    |   +- 更新: $($updatedFiles.Count)" -ForegroundColor Yellow
                    Write-Host "    | 跳过(未变化): $($filesToSkip.Count)" -ForegroundColor Gray
                    Write-Host "    +--------------------------------------------------+" -ForegroundColor Cyan
                    Write-Host ""
                    
                    # Show new files
                    if ($newFiles.Count -gt 0) {
                        Write-Host "    [新增文件] ($($newFiles.Count)):" -ForegroundColor Green
                        foreach ($file in $newFiles | Select-Object -First 10) {
                            Write-Host "      + $($file.RelativePath)" -ForegroundColor Green
                        }
                        if ($newFiles.Count -gt 10) {
                            $moreCount = $newFiles.Count - 10
                            Write-Host "      ... and $moreCount more new files" -ForegroundColor DarkGreen
                        }
                        Write-Host ""
                    }
                    
                    # Show updated files
                    if ($updatedFiles.Count -gt 0) {
                        Write-Host "    [更新文件] ($($updatedFiles.Count)):" -ForegroundColor Yellow
                        foreach ($file in $updatedFiles | Select-Object -First 10) {
                            Write-Host "      ~ $($file.RelativePath)" -ForegroundColor Yellow
                        }
                        if ($updatedFiles.Count -gt 10) {
                            $moreCount = $updatedFiles.Count - 10
                            Write-Host "      ... and $moreCount more files updated" -ForegroundColor DarkYellow
                        }
                        Write-Host ""
                    }
                    
                    # If no files to sync, skip
                    if ($filesToSync.Count -eq 0) {
                        Write-Host "    [OK] 所有文件都是最新的，跳过同步" -ForegroundColor Green
                        $syncSuccess = $true
                    } else {
                        # Create remote directory
                        Write-Host "    正在创建远程目录..." -ForegroundColor Gray
                        $escapedMkdirPath = $remotePath.Replace("'", "''")
                        $mkdirCmd = "mkdir -p '$escapedMkdirPath'"
                        Invoke-SSHCommand -Command $mkdirCmd | Out-Null
                        
                        # Sync files one by one (or in batches for better performance)
                        Write-Host "    正在传输 $($filesToSync.Count) 个文件..." -ForegroundColor Gray
                        $transferredCount = 0
                        $failedCount = 0
                        
                        # Group files by directory for batch transfer
                        $filesByDir = $filesToSync | Group-Object { Split-Path -Parent $_.RelativePath }
                        
                        foreach ($dirGroup in $filesByDir) {
                            $dirPath = $dirGroup.Name
                            $filesInDir = $dirGroup.Group
                            
                            # Create subdirectory on remote if needed
                            if ($dirPath -and $dirPath -ne ".") {
                                $subDirFullPath = "$remotePath/$dirPath"
                                $escapedSubDirPath = $subDirFullPath.Replace("'", "''")
                                $subDirCmd = "mkdir -p '$escapedSubDirPath'"
                                Invoke-SSHCommand -Command $subDirCmd | Out-Null
                            }
                            
                            # Transfer files (scp overwrites by default)
                            foreach ($file in $filesInDir) {
                                $leafName = Split-Path -Leaf $file.RelativePath
                                if ($dirPath -and $dirPath -ne ".") {
                                    $remoteFilePath = "$remotePath/$dirPath/$leafName"
                                } else {
                                    $remoteFilePath = "$remotePath/$leafName"
                                }
                                
                                # scp overwrites remote files (incremental+overwrite)
                                if ($KeyPath -and (Test-Path $KeyPath)) {
                                    $scpTarget = "${ServerUser}@${ServerIP}:${remoteFilePath}"
                                    scp -i $KeyPath $file.FullPath $scpTarget 2>&1 | Out-Null
                                } else {
                                    $scpTarget = "${ServerUser}@${ServerIP}:${remoteFilePath}"
                                    scp $file.FullPath $scpTarget 2>&1 | Out-Null
                                }
                                
                                if ($LASTEXITCODE -eq 0) {
                                    $transferredCount++
                                    if ($transferredCount % 10 -eq 0) {
                                        Write-Host "      [进度] 已传输 $transferredCount/$($filesToSync.Count) 个文件..." -ForegroundColor DarkGray
                                    }
                                } else {
                                    $failedCount++
                                    Write-Host "      [错误] 传输失败: $($file.RelativePath)" -ForegroundColor Red
                                }
                            }
                        }
                        
                        Write-Host ""
                        if ($transferredCount -gt 0) {
                            Write-Host "    [OK] 成功传输 $transferredCount 个文件" -ForegroundColor Green
                        }
                        if ($failedCount -gt 0) {
                            Write-Host "    [警告] $failedCount 个文件传输失败" -ForegroundColor Yellow
                        }
                        
                        $syncSuccess = ($failedCount -eq 0)
                    }
                }
                
                # Verify final file count (outside rsync/scp blocks, but inside fileCount > 0 block)
                Write-Host "    正在验证服务器文件..." -ForegroundColor Gray
                $verifyCmd = Build-RemotePathCommand -RemotePath $remotePath
                $fileCountRemote = (Invoke-SSHCommand -Command $verifyCmd | Select-Object -First 1).Trim()
                
                $fileCountRemote = ($fileCountRemote -split [Environment]::NewLine)[0].Trim()
                if ($fileCountRemote -match '^\d+$' -and [int]$fileCountRemote -gt 0) {
                    Write-Host "    [OK] 服务器总文件数: $fileCountRemote" -ForegroundColor Green
                }
                
                if ($syncSuccess) {
                    Write-Host "    [OK] $localPath 同步完成" -ForegroundColor Green
                } else {
                    Write-Host "    [警告] $localPath 同步可能失败，请手动检查" -ForegroundColor Yellow
                }
            } else {
                Write-Host "  [信息] $localPath 为空，跳过" -ForegroundColor Gray
            }
        } else {
            Write-Host "  [信息] 未找到 $localPath，跳过" -ForegroundColor Gray
        }
    }
}

# Complete
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    同步完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$restartConfirm = Read-Host "是否重启服务器上的服务? (Y/N)"
if ($restartConfirm -eq "Y" -or $restartConfirm -eq "y") {
    Write-Host "正在重启服务..." -ForegroundColor Cyan
    $restartCmd = "systemctl restart aistudio"
    Invoke-SSHCommand -Command $restartCmd | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] 服务已重启" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "同步完成" -ForegroundColor Green
Write-Host ""
