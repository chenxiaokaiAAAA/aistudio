@echo off
echo 安装依赖并启动AI自拍机-系统...

REM 检查Python是否可用
python --version
if errorlevel 1 (
    echo Python未安装或不在PATH中
    pause
    exit /b 1
)

REM 检查pip是否可用
pip --version
if errorlevel 1 (
    echo 正在安装pip...
    python -m ensurepip --upgrade
)

REM 安装依赖
echo 正在安装依赖包...
pip install flask
pip install flask-sqlalchemy
pip install flask-login
pip install werkzeug
pip install qrcode
pip install pillow
pip install gunicorn

REM 启动应用
echo 启动应用...
python app.py

pause

