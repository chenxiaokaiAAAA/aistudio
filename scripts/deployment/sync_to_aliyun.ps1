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
Write-Host "    Sync to Aliyun Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to find rsync command
function Find-RsyncCommand {
    # First, try to find rsync in PATH
    $rsyncCmd = Get-Command rsync -ErrorAction SilentlyContinue
    if ($rsyncCmd) {
        return $rsyncCmd.Source
    }
    
    # Check common rsync installation paths
    $rsyncPaths = @(
        "C:\Program Files\Git\usr\bin\rsync.exe",
        "C:\cygwin64\bin\rsync.exe",
        "C:\cygwin\bin\rsync.exe",
        "C:\cwRsync\bin\rsync.exe"
    )
    
    foreach ($path in $rsyncPaths) {
        if (Test-Path $path) {
            # Test if it's executable
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
    
    return $null
}

# Check tools
$rsyncPath = Find-RsyncCommand
if ($rsyncPath) {
    Write-Host "[OK] Found rsync: $rsyncPath" -ForegroundColor Green
    try {
        $rsyncVersion = & $rsyncPath --version 2>&1 | Select-Object -First 1
        Write-Host "      $rsyncVersion" -ForegroundColor Gray
    } catch {
        # Ignore version check errors
    }
} else {
    Write-Host "[Info] rsync not found, will use scp (slower but functional)" -ForegroundColor Yellow
    Write-Host "       Tip: Install Git for Windows or Cygwin to get rsync support" -ForegroundColor Gray
}
Write-Host ""

if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "[Error] scp command not found" -ForegroundColor Red
    exit 1
}

# Auto-detect SSH key if not found
if (-not (Test-Path $KeyPath)) {
    Write-Host "[Info] Key file not found: $KeyPath" -ForegroundColor Yellow
    Write-Host "[Info] Searching for key files in aliyun-key directory..." -ForegroundColor Yellow
    
    if (Test-Path "aliyun-key") {
        $foundKey = Get-ChildItem -Path "aliyun-key" -Filter "*.pem","*.key" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($foundKey) {
            $KeyPath = $foundKey.FullName
            Write-Host "[OK] Found key file: $KeyPath" -ForegroundColor Green
        } else {
            Write-Host "[Warning] No key file found in aliyun-key directory" -ForegroundColor Yellow
            Write-Host "[Info] Will attempt connection without key (password authentication)" -ForegroundColor Yellow
            $KeyPath = $null
        }
    } else {
        Write-Host "[Warning] aliyun-key directory not found" -ForegroundColor Yellow
        Write-Host "[Info] Will attempt connection without key (password authentication)" -ForegroundColor Yellow
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
    
    Write-Host "[Info] Fixing SSH key permissions..." -ForegroundColor Yellow
    
    # Step 1: Remove inheritance
    $result1 = & icacls $KeyFile /inheritance:r 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [Warning] Failed to remove inheritance" -ForegroundColor Yellow
    }
    
    # Step 2: Grant full control to current user only
    $currentUser = $env:USERNAME
    $result2 = & icacls $KeyFile /grant "${currentUser}:(F)" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [Error] Failed to grant permissions to current user" -ForegroundColor Red
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
        Write-Host "  [Warning] Some permissions may still be too open" -ForegroundColor Yellow
        return $false
    } else {
        Write-Host "  [OK] SSH key permissions fixed successfully" -ForegroundColor Green
        return $true
    }
}

# Fix SSH key permissions if key file exists (Windows only)
if ($KeyPath -and (Test-Path $KeyPath)) {
    # On Windows, always check and fix permissions
    if ($IsWindows -ne $false -or $env:OS -match "Windows") {
        Write-Host "[Info] Checking SSH key permissions..." -ForegroundColor Cyan
        
        # Test SSH connection first
        Write-Host "[Info] Testing SSH connection..." -ForegroundColor Cyan
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
                Write-Host "[Warning] SSH key permissions are too open, fixing..." -ForegroundColor Yellow
                $fixResult = Fix-SSHKeyPermissions -KeyFile $KeyPath
                if ($fixResult) {
                    # Test again after fixing
                    Write-Host "[Info] Testing SSH connection again..." -ForegroundColor Cyan
                    $testResult2 = ssh -i $KeyPath -o StrictHostKeyChecking=no -o ConnectTimeout=5 $ServerUser@$ServerIP $testCmd 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "[OK] SSH connection test passed" -ForegroundColor Green
                    } else {
                        Write-Host "[Warning] SSH connection still failing, but will attempt sync" -ForegroundColor Yellow
                        $connectionFailed = $true
                    }
                } else {
                    Write-Host "[Error] Failed to fix SSH key permissions automatically" -ForegroundColor Red
                    Write-Host "[Info] Please run: scripts\deployment\修复SSH密钥权限.ps1" -ForegroundColor Yellow
                    $connectionFailed = $true
                }
            } else {
                Write-Host "[Warning] SSH connection test failed: $errorOutput" -ForegroundColor Yellow
                $connectionFailed = $true
            }
        } else {
            Write-Host "[OK] SSH connection test passed" -ForegroundColor Green
        }
        
        # If connection failed but not due to permissions, try to fix permissions anyway
        if ($connectionFailed -and $testResult -notmatch "Permissions.*too open" -and $testResult -notmatch "UNPROTECTED PRIVATE KEY") {
            Write-Host "[Info] Proactively fixing SSH key permissions..." -ForegroundColor Cyan
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
    # If no option is specified, default to All
    $syncCode = $true
    $syncDatabase = $true
    $syncImages = $true
}

if (-not ($syncCode -or $syncDatabase -or $syncImages)) {
    Write-Host "[Error] Please specify sync content" -ForegroundColor Red
    exit 1
}

Write-Host "Sync Config:" -ForegroundColor Green
Write-Host "  Server: $ServerUser@$ServerIP" -ForegroundColor White
Write-Host "  Remote Path: $RemotePath" -ForegroundColor White
Write-Host "  Sync:" -ForegroundColor White
if ($syncCode) { Write-Host "    [OK] Code (via Git)" -ForegroundColor Green } else { Write-Host "    [SKIP] Code" -ForegroundColor Gray }
if ($syncDatabase) { Write-Host "    [OK] Database" -ForegroundColor Green } else { Write-Host "    [SKIP] Database" -ForegroundColor Gray }
if ($syncImages) { Write-Host "    [OK] Images" -ForegroundColor Green } else { Write-Host "    [SKIP] Images" -ForegroundColor Gray }
Write-Host ""

$confirm = Read-Host "Confirm? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Cancelled" -ForegroundColor Yellow
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
    Write-Host "[1/3] Syncing code..." -ForegroundColor Cyan
    
    $gitStatus = git status --porcelain 2>&1
    if ($gitStatus) {
        Write-Host "  Uncommitted changes detected" -ForegroundColor Yellow
        $commitConfirm = Read-Host "  Commit and push? (Y/N)"
        
        if ($commitConfirm -eq "Y" -or $commitConfirm -eq "y") {
            Write-Host "  Adding files..." -ForegroundColor White
            git add . 2>&1 | Out-Null
            
            $commitMsg = Read-Host "  Commit message (Enter for default)"
            if ([string]::IsNullOrWhiteSpace($commitMsg)) {
                $commitMsg = "Update code: sync to server"
            }
            
            Write-Host "  Committing..." -ForegroundColor White
            git commit -m $commitMsg 2>&1 | Out-Null
            
            Write-Host "  Pushing to GitHub..." -ForegroundColor White
            git push origin master 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                git push origin main 2>&1 | Out-Null
            }
            Write-Host "  [OK] Code pushed to GitHub" -ForegroundColor Green
        }
    }
    
    Write-Host ""
    Write-Host "  Pulling latest code on server..." -ForegroundColor White
    $sshCmd = "cd $RemotePath; git pull origin master 2>&1 || git pull origin main 2>&1"
    
    Invoke-SSHCommand -Command $sshCmd | Out-Host
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Code sync completed" -ForegroundColor Green
    } else {
        Write-Host "  [Warning] Code sync may have failed" -ForegroundColor Yellow
    }
}

# 2. Sync Database
if ($syncDatabase) {
    Write-Host ""
    Write-Host "[2/3] Syncing database..." -ForegroundColor Cyan
    
    $dbFile = "instance\pet_painting.db"
    if (Test-Path $dbFile) {
        $dbSize = (Get-Item $dbFile).Length / 1MB
        Write-Host "  Database: $dbFile ($([math]::Round($dbSize, 2)) MB)" -ForegroundColor White
        
        $remoteDbPath = "$RemotePath/instance/pet_painting.db"
        
        Write-Host "  Uploading..." -ForegroundColor White
        if ($KeyPath -and (Test-Path $KeyPath)) {
            scp -i $KeyPath $dbFile "${ServerUser}@${ServerIP}:${remoteDbPath}" 2>&1 | Out-Null
        } else {
            scp $dbFile "${ServerUser}@${ServerIP}:${remoteDbPath}" 2>&1 | Out-Null
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] Database sync completed" -ForegroundColor Green
            
            Write-Host "  Setting permissions..." -ForegroundColor White
            $permCmd = "chmod 644 $remoteDbPath; chown root:root $remoteDbPath"
            Invoke-SSHCommand -Command $permCmd | Out-Null
        } else {
            Write-Host "  [Warning] Database sync failed" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [Warning] Database file not found: $dbFile" -ForegroundColor Yellow
    }
}

# 3. Sync Images
if ($syncImages) {
    Write-Host ""
    Write-Host "[3/3] Syncing images..." -ForegroundColor Cyan
    
    $imageDirs = @("uploads", "final_works", "hd_images")
    
    foreach ($localPath in $imageDirs) {
        $remotePath = "$RemotePath/$localPath"
        
        if (Test-Path $localPath) {
            $files = Get-ChildItem -Path $localPath -Recurse -File -ErrorAction SilentlyContinue
            $fileCount = $files.Count
            if ($fileCount -gt 0) {
                Write-Host "  Syncing: $localPath ($fileCount files)..." -ForegroundColor White
                
                $syncSuccess = $false
                
                # Check for rsync (re-check in case it wasn't found at script start)
                if (-not $rsyncPath) {
                    $rsyncPath = Find-RsyncCommand
                }
                
                if ($rsyncPath) {
                    # Use rsync for better performance with detailed output
                    Write-Host "    Using rsync for incremental sync..." -ForegroundColor Cyan
                    if ($rsyncPath -match "cygwin") {
                        Write-Host "    [Info] Using Cygwin rsync: $rsyncPath" -ForegroundColor Gray
                    }
                    
                    # Count files before sync
                    $localFileCount = (Get-ChildItem -Path $localPath -Recurse -File).Count
                    $remoteFileCountCmd = Build-RemotePathCommand -RemotePath $remotePath
                    $remoteFileCountBefore = (Invoke-SSHCommand -Command $remoteFileCountCmd | Select-Object -First 1).Trim()
                    
                    $infoMsg = "    [Info] Local: $localFileCount files, Remote: $remoteFileCountBefore files"
                    Write-Host $infoMsg -ForegroundColor Gray
                    Write-Host "    Transferring files..." -ForegroundColor Gray
                    
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
                        Write-Host "    ┌─ Sync Statistics ──────────────────────────────┐" -ForegroundColor Cyan
                        Write-Host "    │ New Files: $($newFiles.Count)" -ForegroundColor Green
                        Write-Host "    │ Updated Files: $($updatedFiles.Count)" -ForegroundColor Yellow
                        Write-Host "    │ Skipped Files: $skippedFiles" -ForegroundColor Gray
                        Write-Host "    └──────────────────────────────────────────┘" -ForegroundColor Cyan
                        
                        if ($newFiles.Count -gt 0) {
                            Write-Host ""
                            Write-Host "    [New Files] ($($newFiles.Count)):" -ForegroundColor Green
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
                            Write-Host "    [Updated Files] ($($updatedFiles.Count)):" -ForegroundColor Yellow
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
                    Write-Host "    [Tip] Install rsync for better performance and incremental sync" -ForegroundColor Yellow
                    
                    # Use incremental sync with scp - compare files before syncing
                    Write-Host "    Analyzing files for incremental sync..." -ForegroundColor Gray
                    
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
                    Write-Host "    Checking remote files..." -ForegroundColor Gray
                    $remoteFilesInfo = @{}
                    $escapedPath = $remotePath.Replace("'", "''")
                    $statFormat = '%s|%Y|%n'
                    $getRemoteFilesCmd = "if [ -d '$escapedPath' ]; then find '$escapedPath' -type f -exec stat -c '$statFormat' {} \\; 2>/dev/null; fi"
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
                            # 文件已存在于远程服务器，检查是否需要更新
                            $remoteInfo = $remoteFilesInfo[$relPath]
                            $localMTime = [DateTimeOffset]$localFile.LastWriteTime
                            $localUnixTime = $localMTime.ToUnixTimeSeconds()
                            
                            # 增量同步逻辑：比较文件大小和修改时间
                            if ($localFile.Size -ne $remoteInfo.Size -or $localUnixTime -gt $remoteInfo.MTime) {
                                # 文件有变化，需要覆盖
                                $filesToSync += $localFile
                                $updatedFiles += $localFile
                            } else {
                                # 文件未变化，跳过（增量同步）
                                $filesToSkip += $localFile
                            }
                        } else {
                            # 新文件，需要同步
                            $filesToSync += $localFile
                            $newFiles += $localFile
                        }
                    }
                    
                    # Display sync summary
                    Write-Host ""
                    Write-Host "    ┌─ Sync Statistics (Incremental+Overwrite) ─────┐" -ForegroundColor Cyan
                    Write-Host "    │ Local Files: $($localFiles.Count)" -ForegroundColor White
                    Write-Host "    │ To Sync: $($filesToSync.Count) (will overwrite remote)" -ForegroundColor Yellow
                    Write-Host "    │   ├─ New Files: $($newFiles.Count)" -ForegroundColor Green
                    Write-Host "    │   └─ Updated Files: $($updatedFiles.Count) (overwrite modified)" -ForegroundColor Yellow
                    Write-Host "    │ Skipped (unchanged): $($filesToSkip.Count) (incremental sync, save time)" -ForegroundColor Gray
                    Write-Host "    └──────────────────────────────────────────┘" -ForegroundColor Cyan
                    Write-Host ""
                    
                    # Show new files
                    if ($newFiles.Count -gt 0) {
                        Write-Host "    [New Files] ($($newFiles.Count)):" -ForegroundColor Green
                        foreach ($file in $newFiles | Select-Object -First 10) {
                            Write-Host "      + $($file.RelativePath)" -ForegroundColor Green
                        }
                        if ($newFiles.Count -gt 10) {
                            $moreCount = $newFiles.Count - 10
                            Write-Host "      ... 还有 $moreCount 个新文件" -ForegroundColor DarkGreen
                        }
                        Write-Host ""
                    }
                    
                    # Show updated files
                    if ($updatedFiles.Count -gt 0) {
                        Write-Host "    [Updated Files] ($($updatedFiles.Count)):" -ForegroundColor Yellow
                        foreach ($file in $updatedFiles | Select-Object -First 10) {
                            Write-Host "      ~ $($file.RelativePath)" -ForegroundColor Yellow
                        }
                        if ($updatedFiles.Count -gt 10) {
                            $moreCount = $updatedFiles.Count - 10
                            Write-Host "      ... 还有 $moreCount 个文件被更新" -ForegroundColor DarkYellow
                        }
                        Write-Host ""
                    }
                    
                    # If no files to sync, skip
                    if ($filesToSync.Count -eq 0) {
                        Write-Host "    [OK] 所有文件都是最新的，跳过同步" -ForegroundColor Green
                        $syncSuccess = $true
                    } else {
                        # Create remote directory
                        Write-Host "    Creating remote directory..." -ForegroundColor Gray
                        $escapedMkdirPath = $remotePath.Replace("'", "''")
                        $mkdirCmd = "mkdir -p '$escapedMkdirPath'"
                        Invoke-SSHCommand -Command $mkdirCmd | Out-Null
                        
                        # Sync files one by one (or in batches for better performance)
                        Write-Host "    Transferring $($filesToSync.Count) files..." -ForegroundColor Gray
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
                            
                            # Transfer files in this directory (scp 默认会覆盖同名文件)
                            foreach ($file in $filesInDir) {
                                $leafName = Split-Path -Leaf $file.RelativePath
                                if ($dirPath -and $dirPath -ne ".") {
                                    $remoteFilePath = "$remotePath/$dirPath/$leafName"
                                } else {
                                    $remoteFilePath = "$remotePath/$leafName"
                                }
                                
                                # scp 会覆盖远程同名文件（增量+覆盖模式）
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
                Write-Host "    Verifying files on remote server..." -ForegroundColor Gray
                $verifyCmd = Build-RemotePathCommand -RemotePath $remotePath
                $fileCountRemote = (Invoke-SSHCommand -Command $verifyCmd | Select-Object -First 1).Trim()
                
                $fileCountRemote = ($fileCountRemote -split [Environment]::NewLine)[0].Trim()
                if ($fileCountRemote -match '^\d+$' -and [int]$fileCountRemote -gt 0) {
                    Write-Host "    [OK] Total files on server: $fileCountRemote" -ForegroundColor Green
                }
                
                if ($syncSuccess) {
                    Write-Host "    [OK] $localPath sync completed" -ForegroundColor Green
                } else {
                    Write-Host "    [Warning] $localPath sync may have failed, please check manually" -ForegroundColor Yellow
                }
            } else {
                Write-Host "  [Info] $localPath is empty, skipping" -ForegroundColor Gray
            }
        } else {
            Write-Host "  [Info] $localPath not found, skipping" -ForegroundColor Gray
        }
    }
}

# Complete
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Sync Completed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$restartConfirm = Read-Host "Restart service on server? (Y/N)"
if ($restartConfirm -eq "Y" -or $restartConfirm -eq "y") {
    Write-Host "Restarting service..." -ForegroundColor Cyan
    $restartCmd = "systemctl restart aistudio"
    Invoke-SSHCommand -Command $restartCmd | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Service restarted" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Sync completed successfully" -ForegroundColor Green
Write-Host ""
