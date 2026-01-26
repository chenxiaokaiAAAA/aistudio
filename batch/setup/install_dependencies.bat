@echo off
chcp 65001 >nul
echo ========================================
echo 正在安装 Python 依赖包...
echo ========================================
echo.

cd /d "%~dp0"

echo 正在升级 pip...
python -m pip install --upgrade pip
echo.

echo 正在安装依赖包...
python -m pip install Flask==2.3.3
python -m pip install Flask-SQLAlchemy==3.0.5
python -m pip install Flask-Login==0.6.3
python -m pip install Werkzeug==2.3.7
python -m pip install qrcode==7.4.2
python -m pip install Pillow==10.0.1
python -m pip install gunicorn==21.2.0
python -m pip install requests==2.31.0
python -m pip install plyer==2.1.0
python -m pip install pyttsx3==2.90

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
pause
