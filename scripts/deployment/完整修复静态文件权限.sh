#!/bin/bash
# 完整修复静态文件 403 错误
# 在服务器上直接执行此脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "完整修复静态文件 403 错误"
echo "=========================================="
echo ""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 检查当前状态
echo -e "${YELLOW}[1/8] 检查当前状态...${NC}"
echo "Nginx 状态:"
systemctl status nginx --no-pager -l | head -3
echo ""

echo "Nginx 运行用户:"
ps aux | grep '[n]ginx: master' | awk '{print $1}'
echo ""

echo "当前 /root 权限:"
ls -ld /root
echo ""

# 2. 修复 /root 目录权限
echo -e "${YELLOW}[2/8] 修复 /root 目录权限...${NC}"
chmod 755 /root
echo -e "${GREEN}✅ /root 权限已设置为 755${NC}"
ls -ld /root
echo ""

# 3. 修复项目目录权限
echo -e "${YELLOW}[3/8] 修复项目目录权限...${NC}"
chmod 755 /root/project_code
chmod -R 755 /root/project_code/static
find /root/project_code/static -type f -exec chmod 644 {} \;
find /root/project_code/static -type d -exec chmod 755 {} \;
echo -e "${GREEN}✅ 项目目录权限已修复${NC}"
echo ""

# 4. 检查并创建符号链接
echo -e "${YELLOW}[4/8] 检查符号链接...${NC}"
if [ ! -L /var/www/static ]; then
    mkdir -p /var/www
    chmod 755 /var/www
    ln -sf /root/project_code/static /var/www/static
    echo -e "${GREEN}✅ 符号链接已创建${NC}"
else
    echo -e "${GREEN}✅ 符号链接已存在${NC}"
fi
ls -la /var/www/static | head -3
echo ""

# 5. 检查 Nginx 配置
echo -e "${YELLOW}[5/8] 检查 Nginx 配置...${NC}"
NGINX_CONFIG="/etc/nginx/sites-available/aistudio"
if [ -f "$NGINX_CONFIG" ]; then
    echo "当前 static location 配置:"
    grep -A 3 "location /static/" "$NGINX_CONFIG"
    
    # 确保使用 /var/www/static/
    if ! grep -q "alias /var/www/static/" "$NGINX_CONFIG"; then
        echo "更新 Nginx 配置..."
        sed -i 's|alias /root/project_code/static/;|alias /var/www/static/;|' "$NGINX_CONFIG"
        echo -e "${GREEN}✅ Nginx 配置已更新${NC}"
        grep -A 3 "location /static/" "$NGINX_CONFIG"
    else
        echo -e "${GREEN}✅ Nginx 配置正确${NC}"
    fi
else
    echo -e "${RED}❌ Nginx 配置文件不存在: $NGINX_CONFIG${NC}"
    exit 1
fi
echo ""

# 6. 检查 SELinux（如果启用）
echo -e "${YELLOW}[6/8] 检查 SELinux...${NC}"
if command -v getenforce &> /dev/null; then
    SELINUX_STATUS=$(getenforce 2>/dev/null || echo "Disabled")
    echo "SELinux 状态: $SELINUX_STATUS"
    if [ "$SELINUX_STATUS" = "Enforcing" ]; then
        echo -e "${YELLOW}⚠️  SELinux 已启用，可能需要额外配置${NC}"
        echo "如果仍然 403，可以尝试: setsebool -P httpd_read_user_content 1"
    fi
else
    echo -e "${GREEN}✅ SELinux 未启用（Ubuntu 默认）${NC}"
fi
echo ""

# 7. 测试 Nginx 配置
echo -e "${YELLOW}[7/8] 测试 Nginx 配置...${NC}"
if nginx -t; then
    echo -e "${GREEN}✅ Nginx 配置测试通过${NC}"
else
    echo -e "${RED}❌ Nginx 配置测试失败${NC}"
    exit 1
fi
echo ""

# 8. 重启 Nginx 并测试
echo -e "${YELLOW}[8/8] 重启 Nginx 并测试...${NC}"
systemctl restart nginx
sleep 2

echo "Nginx 状态:"
systemctl status nginx --no-pager -l | head -5
echo ""

echo "测试静态文件访问:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/static/css/bootstrap.min.css)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ 静态文件访问正常 (HTTP $HTTP_CODE)${NC}"
    curl -I http://localhost/static/css/bootstrap.min.css 2>&1 | head -3
else
    echo -e "${RED}❌ 静态文件访问失败 (HTTP $HTTP_CODE)${NC}"
    echo "检查错误日志:"
    tail -5 /var/log/nginx/error.log | grep -i "static\|permission" || echo "无相关错误"
fi
echo ""

# 9. 最终验证
echo "=========================================="
echo "最终验证"
echo "=========================================="
echo ""

echo "1. 目录权限:"
ls -ld /root
ls -ld /root/project_code
ls -ld /root/project_code/static
echo ""

echo "2. 符号链接:"
ls -la /var/www/static
echo ""

echo "3. 文件权限示例:"
ls -la /root/project_code/static/css/bootstrap.min.css
echo ""

echo "4. Nginx 配置:"
grep -A 3 "location /static/" /etc/nginx/sites-available/aistudio
echo ""

echo "=========================================="
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ 修复成功！${NC}"
    echo ""
    echo "现在请："
    echo "  1. 清除浏览器缓存（Ctrl + Shift + Delete）"
    echo "  2. 硬刷新页面（Ctrl + F5）"
    echo "  3. 检查浏览器控制台是否还有 403 错误"
else
    echo -e "${RED}❌ 修复未完全成功${NC}"
    echo ""
    echo "请检查："
    echo "  1. Nginx 错误日志: tail -f /var/log/nginx/error.log"
    echo "  2. 文件是否存在: ls -la /root/project_code/static/css/bootstrap.min.css"
    echo "  3. SELinux 状态（如果启用）: getenforce"
fi
echo "=========================================="
