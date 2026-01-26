#!/bin/bash
# 启动脚本

# 激活虚拟环境（如果使用）
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动应用
gunicorn -c gunicorn.conf.py app:app

