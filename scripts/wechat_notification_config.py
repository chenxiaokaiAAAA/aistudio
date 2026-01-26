#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
微信通知配置文件
"""

# 是否启用微信通知
WECHAT_NOTIFICATION_ENABLED = True  # 已启用

# 微信类型: 'enterprise' (企业微信) 或 'mp' (微信公众号)
WECHAT_TYPE = 'enterprise'

# ================================
# 企业微信机器人配置
# ================================
# 如何获取企业微信机器人webhook：
# 1. 在企业微信群聊中添加"群机器人"
# 2. 获取webhook地址，格式类似：
#    https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxx
ENTERPRISE_WEBHOOK_URL = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=334cbf17-ce3c-4d76-8d94-55e2a877122d'

# ================================
# 微信公众号配置（可选）
# ================================
# 如需使用微信公众号模板消息，请配置以下信息
MP_TOKEN = ''  # 公众号Token
MP_APP_ID = ''  # 公众号AppID
MP_APP_SECRET = ''  # 公众号AppSecret
MP_TEMPLATE_ID = ''  # 模板消息ID

# 使用说明：
# 1. 企业微信：最简单，只需配置ENTERPRISE_WEBHOOK_URL
# 2. 微信公众号：需要公众号开发权限，配置四个参数

