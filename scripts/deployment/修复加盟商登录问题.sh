#!/bin/bash
# 修复加盟商登录无反应问题
# 问题：登录后没有反应，可能是Cookie配置或Session问题

echo "=========================================="
echo "修复加盟商登录问题"
echo "=========================================="
echo ""

cd /root/project_code || exit 1

# 备份原文件
echo "[1/5] 备份原文件..."
cp test_server.py test_server.py.bak_$(date +%Y%m%d_%H%M%S)
echo "✅ 已备份"

# 检查当前Cookie配置
echo ""
echo "[2/5] 检查当前Cookie配置..."
grep -A 5 "is_production" test_server.py | head -10

# 检查是否使用HTTPS
echo ""
echo "[3/5] 检查环境配置..."
echo "FLASK_ENV: ${FLASK_ENV:-未设置}"
echo "ENV: ${ENV:-未设置}"
echo "USE_HTTPS: ${USE_HTTPS:-未设置}"

# 修复Cookie配置（如果是HTTP环境，禁用Secure Cookie）
echo ""
echo "[4/5] 修复Cookie配置..."
python3 << 'PYEOF'
import re
import os

with open('test_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查是否使用HTTPS
use_https = os.environ.get('USE_HTTPS', 'false').lower() == 'true'
is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('ENV') == 'production'

# 查找Cookie配置部分
pattern = r"(if is_production:\s+app\.config\['SESSION_COOKIE_SECURE'\] = True\s+app\.config\['REMEMBER_COOKIE_SECURE'\] = True)"

# 替换为更智能的配置
if use_https and is_production:
    # 使用HTTPS，启用Secure Cookie
    replacement = """if is_production and use_https:
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = True
else:
    # HTTP环境下禁用Secure Cookie（否则Cookie无法设置）
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['REMEMBER_COOKIE_SECURE'] = False"""
else:
    # 默认HTTP环境，禁用Secure Cookie
    replacement = """# HTTP环境下禁用Secure Cookie（否则Cookie无法设置）
# 如果后续配置了HTTPS，设置环境变量 USE_HTTPS=true 并重启服务
app.config['SESSION_COOKIE_SECURE'] = False
app.config['REMEMBER_COOKIE_SECURE'] = False"""

# 检查是否已经有use_https变量定义
if 'use_https = os.environ.get' not in content:
    # 在is_production定义后添加use_https
    content = re.sub(
        r"(is_production = os\.environ\.get\('FLASK_ENV'\) == 'production' or os\.environ\.get\('ENV'\) == 'production')",
        r"\1\nuse_https = os.environ.get('USE_HTTPS', 'false').lower() == 'true'",
        content
    )

# 替换Cookie配置
content = re.sub(pattern, replacement, content)

with open('test_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Cookie配置已修复")
PYEOF

# 添加登录调试日志
echo ""
echo "[5/5] 添加登录调试日志..."
python3 << 'PYEOF'
import re

with open('app/routes/franchisee/frontend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 在登录函数中添加调试日志
login_function = """@bp.route('/login', methods=['GET', 'POST'])
def franchisee_login():
    \"\"\"加盟商登录页面\"\"\"
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return render_template('franchisee/login.html')

    
    FranchiseeAccount = models['FranchiseeAccount']
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 添加调试日志
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f\"[加盟商登录] 尝试登录: username={username}\")
        
        if not username or not password:
            logger.warning(f\"[加盟商登录] 用户名或密码为空\")
            flash('请输入用户名和密码', 'error')
            return render_template('franchisee/login.html')
        
        account = FranchiseeAccount.query.filter_by(username=username).first()
        
        if account and check_password_hash(account.password, password):
            if account.status != 'active':
                logger.warning(f\"[加盟商登录] 账户被禁用: username={username}\")
                flash('账户已被禁用，请联系管理员', 'error')
                return render_template('franchisee/login.html')
            
            session['franchisee_id'] = account.id
            session['franchisee_username'] = account.username
            session['franchisee_company'] = account.company_name
            
            logger.info(f\"[加盟商登录] 登录成功: username={username}, franchisee_id={account.id}\")
            logger.info(f\"[加盟商登录] Session设置: franchisee_id={session.get('franchisee_id')}\")
            
            flash(f'欢迎回来，{account.company_name}', 'success')
            return redirect(url_for('franchisee.franchisee_frontend.dashboard'))
        else:
            logger.warning(f\"[加盟商登录] 用户名或密码错误: username={username}\")
            flash('用户名或密码错误', 'error')
    
    return render_template('franchisee/login.html')"""

# 替换登录函数
pattern = r"@bp\.route\('/login', methods=\['GET', 'POST'\]\)\s+def franchisee_login\(\):.*?return render_template\('franchisee/login\.html'\)"
content = re.sub(pattern, login_function, content, flags=re.DOTALL)

with open('app/routes/franchisee/frontend.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 登录调试日志已添加")
PYEOF

echo ""
echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 重启服务: systemctl restart aistudio"
echo "2. 查看日志: journalctl -u aistudio -f"
echo "3. 尝试登录，观察日志输出"
echo ""
