#!/bin/bash
# 修复 styles.html 模板中的空值检查问题

echo "修复 styles.html 中的空值检查..."

cd /root/project_code

# 备份
cp templates/admin/styles.html templates/admin/styles.html.bak.$(date +%Y%m%d_%H%M%S)

# 使用 Python 脚本修复
python3 << 'PYEOF'
import re

with open('templates/admin/styles.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复模式1: document.getElementById('xxx').style.display = '...'
# 替换为安全的版本
patterns = [
    # 分类封面图片相关
    (r"document\.getElementById\('categoryCoverImagePreview'\)\.style\.display = 'block'",
     "const el = document.getElementById('categoryCoverImagePreview'); if (el) el.style.display = 'block'"),
    (r"document\.getElementById\('categoryCoverImagePreview'\)\.style\.display = 'none'",
     "const el = document.getElementById('categoryCoverImagePreview'); if (el) el.style.display = 'none'"),
    (r"document\.getElementById\('categoryCoverImageUpload'\)\.style\.display = 'block'",
     "const el = document.getElementById('categoryCoverImageUpload'); if (el) el.style.display = 'block'"),
    (r"document\.getElementById\('categoryCoverImageUpload'\)\.style\.display = 'none'",
     "const el = document.getElementById('categoryCoverImageUpload'); if (el) el.style.display = 'none'"),
    
    # 图片上传相关
    (r"document\.getElementById\('imagePreview'\)\.style\.display = 'block'",
     "const el = document.getElementById('imagePreview'); if (el) el.style.display = 'block'"),
    (r"document\.getElementById\('imagePreview'\)\.style\.display = 'none'",
     "const el = document.getElementById('imagePreview'); if (el) el.style.display = 'none'"),
    (r"document\.getElementById\('imageUploadArea'\)\.style\.display = 'block'",
     "const el = document.getElementById('imageUploadArea'); if (el) el.style.display = 'block'"),
    (r"document\.getElementById\('imageUploadArea'\)\.style\.display = 'none'",
     "const el = document.getElementById('imageUploadArea'); if (el) el.style.display = 'none'"),
    
    # 设计图片相关
    (r"document\.getElementById\('designImagePreview'\)\.style\.display = 'block'",
     "const el = document.getElementById('designImagePreview'); if (el) el.style.display = 'block'"),
    (r"document\.getElementById\('designImagePreview'\)\.style\.display = 'none'",
     "const el = document.getElementById('designImagePreview'); if (el) el.style.display = 'none'"),
    (r"document\.getElementById\('designImageUploadArea'\)\.style\.display = 'block'",
     "const el = document.getElementById('designImageUploadArea'); if (el) el.style.display = 'block'"),
    (r"document\.getElementById\('designImageUploadArea'\)\.style\.display = 'none'",
     "const el = document.getElementById('designImageUploadArea'); if (el) el.style.display = 'none'"),
    
    # 测试图片相关
    (r"document\.getElementById\('testImagePreview'\)\.style\.display = 'none'",
     "const el = document.getElementById('testImagePreview'); if (el) el.style.display = 'none'"),
    (r"document\.getElementById\('testImageUploadArea'\)\.style\.display = 'block'",
     "const el = document.getElementById('testImageUploadArea'); if (el) el.style.display = 'block'"),
    (r"document\.getElementById\('testResult'\)\.style\.display = 'none'",
     "const el = document.getElementById('testResult'); if (el) el.style.display = 'none'"),
    (r"document\.getElementById\('testResult'\)\.style\.display = 'block'",
     "const el = document.getElementById('testResult'); if (el) el.style.display = 'block'"),
    (r"document\.getElementById\('testProgress'\)\.style\.display = 'none'",
     "const el = document.getElementById('testProgress'); if (el) el.style.display = 'none'"),
    (r"document\.getElementById\('testProgress'\)\.style\.display = 'block'",
     "const el = document.getElementById('testProgress'); if (el) el.style.display = 'block'"),
]

# 应用所有修复
for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

with open('templates/admin/styles.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已修复所有空值检查问题")
PYEOF

echo "✅ 修复完成"
echo ""
echo "请重启服务："
echo "  systemctl restart aistudio"
