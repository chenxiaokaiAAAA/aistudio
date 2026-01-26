@echo off
echo 启动AI自拍机-系统（端口5000）...

REM 激活虚拟环境（如果使用）
REM call venv\Scripts\activate.bat

REM 安装依赖
pip install -r requirements.txt

REM 启动应用
python app.py

echo 应用已启动，访问地址：http://your-server-ip:5000
pause
