@echo off
echo 启动AI自拍机-系统（Gunicorn）...

REM 激活虚拟环境（如果使用）
REM call venv\Scripts\activate.bat

REM 安装依赖
pip install -r requirements.txt

REM 启动Gunicorn
gunicorn -c gunicorn.conf.py app:app

pause

