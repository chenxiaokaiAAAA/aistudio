# -*- coding: utf-8 -*-
"""
自动拆分 miniprogram.py 为多个子模块
"""
import os
import re

# 读取原文件
with open('app/routes/miniprogram.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 创建目录
os.makedirs('app/routes/miniprogram', exist_ok=True)

# 提取各部分代码
lines = content.split('\n')

# 找到各个部分的起始行
orders_start = 0
orders_end = 567
media_start = 589
media_end = 684
catalog_start = 726
catalog_end = 1136
orders2_start = 1139
orders2_end = 1643
works_start = 1646
works_end = 1738
promotion_start = 1741
promotion_end = 1825

# 提取各部分
orders_lines = lines[orders_start:orders_end]
media_lines = lines[media_start:media_end]
catalog_lines = lines[catalog_start:catalog_end]
orders2_lines = lines[orders2_start:orders2_end]
works_lines = lines[works_start:works_end]
promotion_lines = lines[promotion_start:promotion_end]

# 创建订单模块（合并两部分）
orders_content = '\n'.join(orders_lines + [''] + orders2_lines)
orders_content = orders_content.replace('@miniprogram_bp.route', '@bp.route')
orders_content = orders_content.replace('from flask import Blueprint, request, jsonify, send_from_directory, current_app', 'from flask import Blueprint, request, jsonify, send_from_directory, current_app\nfrom app.routes.miniprogram.common import get_models, get_helper_functions')
orders_content = 'from flask import Blueprint, request, jsonify\nfrom app.services.order_service import (\n    create_miniprogram_order,\n    get_order_by_number,\n    check_order_for_verification,\n    upload_order_photos\n)\nimport qrcode\nimport base64\nfrom io import BytesIO\nimport threading\nfrom app.routes.miniprogram.common import get_models, get_helper_functions\n\nbp = Blueprint(\'orders\', __name__)\n\n' + orders_content

# 创建媒体模块
media_content = '\n'.join(media_lines)
media_content = media_content.replace('@miniprogram_bp.route', '@bp.route')
media_content = 'from flask import Blueprint, request, jsonify, send_from_directory, current_app\nfrom server_config import get_media_url\n\nbp = Blueprint(\'media\', __name__)\n\n' + media_content

# 创建目录模块
catalog_content = '\n'.join(catalog_lines)
catalog_content = catalog_content.replace('@miniprogram_bp.route', '@bp.route')
catalog_content = catalog_content.replace('def get_models():', '# get_models moved to common.py')
catalog_content = catalog_content.replace('def get_helper_functions():', '# get_helper_functions moved to common.py')
catalog_content = 'from flask import Blueprint, request, jsonify\nfrom app.routes.miniprogram.common import get_models, get_helper_functions\nimport json\n\nbp = Blueprint(\'catalog\', __name__)\n\n' + catalog_content

# 创建作品模块
works_content = '\n'.join(works_lines)
works_content = works_content.replace('@miniprogram_bp.route', '@bp.route')
works_content = 'from flask import Blueprint, request, jsonify\nfrom app.routes.miniprogram.common import get_models, get_helper_functions\nfrom datetime import datetime\n\nbp = Blueprint(\'works\', __name__)\n\n' + works_content

# 创建推广模块
promotion_content = '\n'.join(promotion_lines)
promotion_content = promotion_content.replace('@miniprogram_bp.route', '@bp.route')
promotion_content = 'from flask import Blueprint, request, jsonify\nfrom app.routes.miniprogram.common import get_helper_functions\nimport hashlib\nimport requests\nimport base64\n\nbp = Blueprint(\'promotion\', __name__)\n\n' + promotion_content

# 写入文件
with open('app/routes/miniprogram/orders.py', 'w', encoding='utf-8') as f:
    f.write(orders_content)

with open('app/routes/miniprogram/media.py', 'w', encoding='utf-8') as f:
    f.write(media_content)

with open('app/routes/miniprogram/catalog.py', 'w', encoding='utf-8') as f:
    f.write(catalog_content)

with open('app/routes/miniprogram/works.py', 'w', encoding='utf-8') as f:
    f.write(works_content)

with open('app/routes/miniprogram/promotion.py', 'w', encoding='utf-8') as f:
    f.write(promotion_content)

print("✅ 拆分完成！")
