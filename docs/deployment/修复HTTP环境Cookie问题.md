# 修复 HTTP 环境下的 Cookie 问题

## 🔍 问题根源

在 `test_server.py` 第 160-162 行：

```python
if is_production:
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = True
```

**问题**：
- 当环境变量 `FLASK_ENV=production` 或 `ENV=production` 时，Cookie 被设置为 `Secure`
- `Secure` Cookie **只能通过 HTTPS 传输**
- 但你现在使用的是 **HTTP** (`http://121.43.143.59`)
- 所以 Cookie 无法设置，导致登录状态无法保持

---

## 🔧 立即修复

### 方案1：临时禁用 Secure Cookie（推荐，适用于 HTTP 环境）

```bash
cd /root/project_code
source venv/bin/activate

# 备份原文件
cp test_server.py test_server.py.bak

# 修改配置：只在真正使用 HTTPS 时才启用 Secure Cookie
python << 'PYEOF'
import re

with open('test_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 Cookie 配置逻辑
old_pattern = r"if is_production:\s+app\.config\['SESSION_COOKIE_SECURE'\] = True\s+app\.config\['REMEMBER_COOKIE_SECURE'\] = True"

new_config = """# 只在真正使用 HTTPS 时才启用 Secure Cookie
# 检查是否使用 HTTPS（通过环境变量或请求头）
use_https = os.environ.get('USE_HTTPS', 'false').lower() == 'true'
if is_production and use_https:
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = True
else:
    # HTTP 环境下禁用 Secure Cookie
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['REMEMBER_COOKIE_SECURE'] = False"""

content = re.sub(old_pattern, new_config, content)

with open('test_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已修复 Cookie 配置")
PYEOF
```

### 方案2：直接禁用 Secure Cookie（最简单）

```bash
cd /root/project_code
source venv/bin/activate

# 备份原文件
cp test_server.py test_server.py.bak

# 直接注释掉 Secure Cookie 设置
sed -i 's/app\.config\[\x27SESSION_COOKIE_SECURE\x27\] = True/# app.config[\x27SESSION_COOKIE_SECURE\x27] = False  # 临时禁用，HTTP环境需要/' test_server.py
sed -i 's/app\.config\[\x27REMEMBER_COOKIE_SECURE\x27\] = True/# app.config[\x27REMEMBER_COOKIE_SECURE\x27] = False  # 临时禁用，HTTP环境需要/' test_server.py

# 添加显式禁用
python << 'PYEOF'
with open('test_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到 is_production 判断的位置
for i, line in enumerate(lines):
    if 'if is_production:' in line:
        # 在 if 块后添加显式禁用
        indent = len(line) - len(line.lstrip())
        lines.insert(i + 1, ' ' * (indent + 4) + '# HTTP 环境下禁用 Secure Cookie\n')
        lines.insert(i + 2, ' ' * (indent + 4) + 'app.config[\'SESSION_COOKIE_SECURE\'] = False\n')
        lines.insert(i + 3, ' ' * (indent + 4) + 'app.config[\'REMEMBER_COOKIE_SECURE\'] = False\n')
        break

with open('test_server.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ 已禁用 Secure Cookie")
PYEOF
```

---

## 📋 完整修复脚本（推荐使用）

```bash
#!/bin/bash
echo "=========================================="
echo "修复 HTTP 环境下的 Cookie 问题"
echo "=========================================="
echo ""

cd /root/project_code
source venv/bin/activate

# 备份原文件
echo "[1/3] 备份原文件..."
cp test_server.py test_server.py.bak
echo "✅ 已备份到 test_server.py.bak"

# 修改配置
echo ""
echo "[2/3] 修改 Cookie 配置..."
python << 'PYEOF'
import re

with open('test_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并替换 Cookie 配置
old_pattern = r"(if is_production:\s+app\.config\['SESSION_COOKIE_SECURE'\] = True\s+app\.config\['REMEMBER_COOKIE_SECURE'\] = True)"

new_config = """# HTTP 环境下禁用 Secure Cookie（因为当前使用 HTTP，不是 HTTPS）
# 如果后续配置了 HTTPS，可以取消注释下面的代码并注释掉 False 设置
# if is_production:
#     app.config['SESSION_COOKIE_SECURE'] = True
#     app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['REMEMBER_COOKIE_SECURE'] = False"""

content = re.sub(old_pattern, new_config, content, flags=re.MULTILINE)

with open('test_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Cookie 配置已修改")
PYEOF

# 重启服务
echo ""
echo "[3/3] 重启服务..."
systemctl restart aistudio
sleep 3
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
```

---

## 🎯 立即执行

**在服务器上执行上面的完整修复脚本**，它会：
1. 备份原文件
2. 禁用 Secure Cookie（因为使用 HTTP）
3. 重启服务

---

## 🌐 浏览器端操作

修复后，**必须清除浏览器 Cookie**：

1. **清除 Cookie**：
   - 按 `F12` 打开开发者工具
   - Application 标签 → Cookies → 删除所有
   - 或按 `Ctrl + Shift + Delete` 清除

2. **重新登录**：
   - 访问：`http://121.43.143.59/login`
   - 使用 `admin` / `admin123` 登录

---

## 📝 后续配置 HTTPS

如果将来配置了 HTTPS，可以：
1. 取消注释 `SESSION_COOKIE_SECURE = True`
2. 注释掉 `SESSION_COOKIE_SECURE = False`
3. 重启服务

---

## ⚠️ 注意事项

- **HTTP 环境下禁用 Secure Cookie 是正常的**，因为 HTTP 本身就不安全
- 如果将来使用 HTTPS，**必须启用 Secure Cookie** 以保护用户会话
- 当前修复是临时方案，适用于 HTTP 环境
