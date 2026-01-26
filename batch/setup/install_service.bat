@echo off
echo 安装AI自拍机-系统为Windows服务...

REM 使用nssm工具安装服务
REM 首先需要下载nssm: https://nssm.cc/download

REM 安装服务
nssm install PetPaintingSystem "C:\Python\python.exe" "C:\path\to\your\project\app.py"
nssm set PetPaintingSystem AppDirectory "C:\path\to\your\project"
nssm set PetPaintingSystem DisplayName "AI拍照机系统"
nssm set PetPaintingSystem Description "AI拍照机定制服务系统"

REM 启动服务
nssm start PetPaintingSystem

echo 服务安装完成！
pause

