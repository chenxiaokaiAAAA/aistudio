# 将 CDN 上的 Bootstrap Icons、Font Awesome、SortableJS 下载到项目 static 目录
# 在项目根目录执行: .\scripts\download_static_assets.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path "$root\static")) { New-Item -ItemType Directory -Path "$root\static" -Force | Out-Null }
$static = "$root\static"

Write-Host "=== Download static assets to $static ===" -ForegroundColor Cyan

# 1. Bootstrap Icons (CSS + 字体)
Write-Host "`n1. Bootstrap Icons..." -ForegroundColor Yellow
$biCss = "$static\css\bootstrap-icons.css"
$biFonts = "$static\css\fonts"
if (-not (Test-Path $biFonts)) { New-Item -ItemType Directory -Path $biFonts -Force | Out-Null }
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" -OutFile $biCss -UseBasicParsing
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/fonts/bootstrap-icons.woff2" -OutFile "$biFonts\bootstrap-icons.woff2" -UseBasicParsing
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/fonts/bootstrap-icons.woff" -OutFile "$biFonts\bootstrap-icons.woff" -UseBasicParsing
# 确保 CSS 里字体路径为 ./fonts/
(Get-Content $biCss -Raw) -replace 'url\("\./fonts/', 'url("./fonts/' | Set-Content $biCss -NoNewline
Write-Host "   OK: css/bootstrap-icons.css, css/fonts/*.woff2|woff" -ForegroundColor Green

# 2. Font Awesome 6.0.0 (CSS + 字体)
Write-Host "`n2. Font Awesome 6.0.0..." -ForegroundColor Yellow
$faCss = "$static\css\font-awesome.min.css"
$faWebfonts = "$static\webfonts"
if (-not (Test-Path $faWebfonts)) { New-Item -ItemType Directory -Path $faWebfonts -Force | Out-Null }
Invoke-WebRequest -Uri "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" -OutFile $faCss -UseBasicParsing
$faFiles = @(
    "fa-solid-900.woff2", "fa-solid-900.ttf",
    "fa-regular-400.woff2", "fa-regular-400.ttf",
    "fa-brands-400.woff2", "fa-brands-400.ttf"
)
foreach ($f in $faFiles) {
    Invoke-WebRequest -Uri "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/$f" -OutFile "$faWebfonts\$f" -UseBasicParsing
}
# all.min.css 里路径为 ../webfonts/ ，放在 static/css/ 时需改为 /static/webfonts/
(Get-Content $faCss -Raw) -replace '\.\./webfonts/', '/static/webfonts/' | Set-Content $faCss -NoNewline
Write-Host "   OK: css/font-awesome.min.css, webfonts/*" -ForegroundColor Green

# 3. SortableJS
Write-Host "`n3. SortableJS..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js" -OutFile "$static\js\Sortable.min.js" -UseBasicParsing
Write-Host "   OK: js/Sortable.min.js" -ForegroundColor Green

Write-Host "`n=== Done ===" -ForegroundColor Cyan
Write-Host "Templates should use local paths (see docs if needed)." -ForegroundColor Gray
