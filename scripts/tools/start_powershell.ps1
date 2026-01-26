# AI自拍机-系统启动脚本 (PowerShell)

Write-Host "启动AI自拍机-系统..." -ForegroundColor Green

# 设置环境变量
$env:FLASK_ENV = "production"
$env:SECRET_KEY = "your-secret-key-here"
$env:UPLOAD_FOLDER = "C:\data\petapp\uploads"
$env:FINAL_FOLDER = "C:\data\petapp\final_works"
$env:MAX_CONTENT_LENGTH_MB = "50"

Write-Host "环境变量已设置" -ForegroundColor Yellow

# 启动应用 - 监听所有IP地址
Write-Host "启动应用，监听地址: 0.0.0.0:8000" -ForegroundColor Cyan
python -m waitress --listen=0.0.0.0:8000 app:app

