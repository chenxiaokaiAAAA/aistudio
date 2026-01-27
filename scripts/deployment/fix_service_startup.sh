#!/bin/bash
# -*- coding: utf-8 -*-

"""
修复 aistudio 服务启动失败
将 Type=notify 改为 Type=simple，并检查必要文件
"""

set -e

PROJECT_DIR="/root/project_code"
SERVICE_FILE="/etc/systemd/system/aistudio.service"

echo "=========================================="
echo "修复 aistudio 服务启动失败"
echo "=========================================="
echo ""

# 1. 备份原服务文件
if [ -f "$SERVICE_FILE" ]; then
    cp "$SERVICE_FILE" "${SERVICE_FILE}.bak"
    echo "✓ 已备份原服务文件"
fi

# 2. 创建新的服务文件（使用 Type=simple）
echo "创建新的服务配置文件..."
cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=AI Studio Gunicorn Application Server
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/root/project_code
Environment="PATH=/root/project_code/venv/bin"
EnvironmentFile=/root/project_code/.env
ExecStart=/root/project_code/venv/bin/python /root/project_code/start_production.py
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✓ 服务配置文件已更新"
echo ""

# 3. 确保 .env 文件存在
echo "检查 .env 文件..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cat > "$PROJECT_DIR/.env" << 'ENVEOF'
FLASK_ENV=production
SERVER_ENV=production
ENVEOF
    echo "✓ 已创建 .env 文件"
else
    echo "✓ .env 文件已存在"
fi
echo ""

# 4. 给启动脚本执行权限
echo "设置启动脚本权限..."
chmod +x "$PROJECT_DIR/start_production.py"
echo "✓ 启动脚本权限已设置"
echo ""

# 5. 检查虚拟环境
echo "检查虚拟环境..."
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "⚠️  虚拟环境不存在，请先创建虚拟环境"
    echo "   执行: cd $PROJECT_DIR && python3 -m venv venv"
else
    echo "✓ 虚拟环境存在"
    
    # 检查 Gunicorn
    if [ -f "$PROJECT_DIR/venv/bin/gunicorn" ]; then
        echo "✓ Gunicorn 已安装"
    else
        echo "⚠️  Gunicorn 未安装，正在安装..."
        source "$PROJECT_DIR/venv/bin/activate"
        pip install gunicorn
        echo "✓ Gunicorn 安装完成"
    fi
fi
echo ""

# 6. 重新加载 systemd
echo "重新加载 systemd..."
systemctl daemon-reload
echo "✓ systemd 已重新加载"
echo ""

# 7. 启动服务
echo "启动服务..."
systemctl start aistudio
sleep 2
echo ""

# 8. 查看状态
echo "=========================================="
echo "服务状态："
echo "=========================================="
systemctl status aistudio --no-pager -l || true
echo ""

# 9. 检查端口
echo "=========================================="
echo "端口监听检查："
echo "=========================================="
if netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo "✓ 8000 端口正在监听"
    netstat -tlnp | grep ":8000 "
else
    echo "⚠️  8000 端口未监听，服务可能未正常启动"
    echo ""
    echo "查看详细日志："
    echo "  journalctl -u aistudio -n 50 --no-pager"
fi
echo ""

# 10. 提供帮助信息
echo "=========================================="
echo "下一步操作："
echo "=========================================="
echo ""
echo "如果服务启动失败，请执行："
echo "  journalctl -u aistudio -n 100 --no-pager"
echo ""
echo "如果服务启动成功，测试访问："
echo "  curl http://localhost:8000/admin/"
echo "  curl http://121.43.143.59/admin/"
echo ""
echo "服务管理命令："
echo "  启动: systemctl start aistudio"
echo "  停止: systemctl stop aistudio"
echo "  重启: systemctl restart aistudio"
echo "  状态: systemctl status aistudio"
echo "  日志: journalctl -u aistudio -f"
echo ""
