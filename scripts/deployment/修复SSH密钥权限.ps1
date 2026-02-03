# 修复SSH密钥文件权限
# 解决 "Permissions for 'aliyun-key/aistudio.pem' are too open" 错误

# 自动检测密钥文件
$KeyFile = $null
$possiblePaths = @(
    "aliyun-key\aistudio.pem",
    "aliyun-key\*.pem",
    "aliyun-key\*.key"
)

foreach ($path in $possiblePaths) {
    if ($path -match "\*") {
        # 通配符路径
        $found = Get-ChildItem -Path (Split-Path $path) -Filter (Split-Path -Leaf $path) -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $KeyFile = $found.FullName
            break
        }
    } else {
        if (Test-Path $path) {
            $KeyFile = Resolve-Path $path
            break
        }
    }
}

if (-not $KeyFile) {
    Write-Host "[错误] 找不到密钥文件" -ForegroundColor Red
    Write-Host "请确保密钥文件位于以下位置之一：" -ForegroundColor Yellow
    foreach ($path in $possiblePaths) {
        Write-Host "  - $path" -ForegroundColor Gray
    }
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    修复SSH密钥文件权限" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "密钥文件: $KeyFile" -ForegroundColor White
Write-Host ""

Write-Host "[步骤1] 检查当前权限..." -ForegroundColor Yellow
icacls $KeyFile
Write-Host ""

Write-Host "[步骤2] 设置正确的权限（仅当前用户可访问）..." -ForegroundColor Yellow
Write-Host ""

# 移除继承权限
$result1 = & icacls $KeyFile /inheritance:r 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] 已移除继承权限" -ForegroundColor Green
} else {
    Write-Host "  [警告] 移除继承权限失败: $result1" -ForegroundColor Yellow
}

# 给当前用户完全控制权限
$currentUser = $env:USERNAME
$result2 = & icacls $KeyFile /grant "${currentUser}:(F)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] 已授予当前用户完全控制权限" -ForegroundColor Green
} else {
    Write-Host "  [错误] 授予权限失败: $result2" -ForegroundColor Red
    Write-Host "  请手动运行: icacls `"$KeyFile`" /grant `${env:USERNAME}:(F)" -ForegroundColor Yellow
    exit 1
}

# 移除其他用户组权限
$groupsToRemove = @("Users", "Everyone", "Authenticated Users", "BUILTIN\Users")
foreach ($group in $groupsToRemove) {
    $result = & icacls $KeyFile /remove $group 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] 已移除 $group 的权限" -ForegroundColor Green
    }
}

# 移除其他可能有读取权限的用户/组
$acl = Get-Acl $KeyFile
foreach ($access in $acl.Access) {
    $identity = $access.IdentityReference.Value
    if ($identity -ne $currentUser -and 
        $identity -ne "$env:USERDOMAIN\$currentUser" -and
        $identity -ne "BUILTIN\Administrators" -and
        $identity -ne "NT AUTHORITY\SYSTEM" -and
        $access.FileSystemRights -match "Read|FullControl") {
        $result = & icacls $KeyFile /remove $identity 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] 已移除 $identity 的权限" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "[步骤3] 验证权限设置..." -ForegroundColor Yellow
icacls $KeyFile
Write-Host ""

# 验证权限是否正确
$finalAcl = Get-Acl $KeyFile
$hasOpenPermissions = $false
foreach ($access in $finalAcl.Access) {
    $identity = $access.IdentityReference.Value
    if ($identity -ne $currentUser -and 
        $identity -ne "$env:USERDOMAIN\$currentUser" -and
        $identity -ne "BUILTIN\Administrators" -and
        $identity -ne "NT AUTHORITY\SYSTEM" -and
        $access.FileSystemRights -match "Read|FullControl") {
        Write-Host "  [警告] $identity 仍有读取权限" -ForegroundColor Yellow
        $hasOpenPermissions = $true
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($hasOpenPermissions) {
    Write-Host "    权限修复完成（部分权限可能仍需手动处理）" -ForegroundColor Yellow
} else {
    Write-Host "    权限修复完成" -ForegroundColor Cyan
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 测试 SSH 连接
Write-Host "[步骤4] 测试 SSH 连接..." -ForegroundColor Yellow
$testServer = "121.43.143.59"
$testUser = "root"
$testCmd = "echo 'test'"

Write-Host "  正在测试连接到 $testUser@$testServer..." -ForegroundColor White
$testResult = ssh -i $KeyFile -o StrictHostKeyChecking=no -o ConnectTimeout=5 $testUser@$testServer $testCmd 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] SSH 连接测试成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "现在可以重新运行同步脚本了。" -ForegroundColor Green
} else {
    $errorMsg = $testResult -join " "
    if ($errorMsg -match "Permissions.*too open" -or $errorMsg -match "UNPROTECTED PRIVATE KEY") {
        Write-Host "  [错误] 权限仍然过宽，请检查权限设置" -ForegroundColor Red
        Write-Host "  错误信息: $errorMsg" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "建议手动运行以下命令修复权限：" -ForegroundColor Yellow
        Write-Host "  icacls `"$KeyFile`" /inheritance:r" -ForegroundColor Gray
        Write-Host "  icacls `"$KeyFile`" /grant `${env:USERNAME}:(F)" -ForegroundColor Gray
        Write-Host "  icacls `"$KeyFile`" /remove Users" -ForegroundColor Gray
        Write-Host "  icacls `"$KeyFile`" /remove Everyone" -ForegroundColor Gray
    } else {
        Write-Host "  [警告] SSH 连接测试失败（可能是网络或服务器问题）" -ForegroundColor Yellow
        Write-Host "  错误信息: $errorMsg" -ForegroundColor Gray
        Write-Host ""
        Write-Host "权限已修复，但连接测试失败。请检查网络连接和服务器状态。" -ForegroundColor Yellow
    }
}

Write-Host ""
