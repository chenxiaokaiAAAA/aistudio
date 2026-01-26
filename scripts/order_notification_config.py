#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
订单通知配置文件
修改此文件来自定义通知行为
"""

# 通知总开关
ENABLE_NOTIFICATION = True

# 桌面通知开关
ENABLE_DESKTOP_NOTIFICATION = True

# 语音播报开关
ENABLE_VOICE_NOTIFICATION = True

# 音效提醒开关
ENABLE_SOUND_NOTIFICATION = True

# TTS语音引擎设置
TTS_RATE = 150  # 语速 (50-300, 默认150)
TTS_VOLUME = 1.0  # 音量 (0.0-1.0, 默认1.0)
TTS_LANGUAGE = 'chinese'  # 语言设置: 'chinese', 'english'

# 桌面通知显示时长（秒）
NOTIFICATION_TIMEOUT = 10

# 通知来源配置
NOTIFICATION_SOURCES = {
    '小程序': True,      # 是否接收小程序订单通知
    '管理后台': True,    # 是否接收管理后台订单通知
    '网站': True,        # 是否接收网站订单通知
}

# 通知音效配置（Windows系统）
SOUND_TYPES = {
    'new_order': 'MB_ICONASTERISK',      # 新订单音效
    'paid_order': 'MB_ICONEXCLAMATION',  # 已支付订单音效
}

# 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = 'INFO'


