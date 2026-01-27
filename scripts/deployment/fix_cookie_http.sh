#!/bin/bash
# 修复 HTTP 环境下的 Cookie 问题
# 问题：生产环境启用了 SESSION_COOKIE_SECURE，但当前使用 HTTP，导致 Cookie 无法设置

echo "=========================================="
echo "修复 HTTP 环境下的 Cookie 问题"
echo "=========================================="
echo ""

cd /root/project_code || exit 1
source venv/bin/activate || exit 1

# 备份原文件
echo "[1/3] 备份原文件..."
cp test_server.py test_server.py.bak
echo "✅ 已备份到 test_server.py.bak"

# 修改配置
echo ""
echo "[2/3] 修改 Cookie 配置..."
python3 << 'PYEOF'
with open('test_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到并替换 Cookie 配置
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # 找到 if is_production: 行
    if 'if is_production:' in line and i + 2 < len(lines):
        # 检查后面两行是否是 Cookie 配置
        if 'SESSION_COOKIE_SECURE' in lines[i+1] and 'REMEMBER_COOKIE_SECURE' in lines[i+2]:
            # 替换为禁用 Secure Cookie
            new_lines.append("# HTTP 环境下禁用 Secure Cookie（因为当前使用 HTTP，不是 HTTPS）\n")
            new_lines.append("# 如果后续配置了 HTTPS，可以取消注释下面的代码并注释掉 False 设置\n")
            new_lines.append("# if is_production:\n")
            new_lines.append("#     app.config['SESSION_COOKIE_SECURE'] = True\n")
            new_lines.append("#     app.config['REMEMBER_COOKIE_SECURE'] = True\n")
            new_lines.append("app.config['SESSION_COOKIE_SECURE'] = False\n")
            new_lines.append("app.config['REMEMBER_COOKIE_SECURE'] = False\n")
            i += 3  # 跳过原三行
            continue
    
    new_lines.append(line)
    i += 1

with open('test_server.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Cookie 配置已修改")
PYEOF

# 验证修改
echo ""
echo "验证修改..."
if grep -q "SESSION_COOKIE_SECURE.*= False" test_server.py; then
    echo "✅ 修改成功：已禁用 Secure Cookie"
else
    echo "⚠️  修改可能未生效，请手动检查"
fi

# 重启服务
echo ""
echo "[3/3] 重启服务..."
systemctl restart aistudio
sleep 3

echo ""
echo "检查服务状态..."
systemctl status aistudio --no-pager -l | head -15

echo ""
echo "=========================================="
echo "修复完成！"
echo "=========================================="
echo ""
echo "现在请："
echo "  1. 清除浏览器 Cookie（重要！）"
echo "  2. 重新访问: http://121.43.143.59/login"
echo "  3. 使用 admin/admin123 登录"
echo ""
echo "如果仍然不行，检查："
echo "  - 服务是否正常运行: systemctl status aistudio"
echo "  - 端口是否监听: netstat -tlnp | grep 8000"
echo "  - 查看日志: journalctl -u aistudio -n 50"
