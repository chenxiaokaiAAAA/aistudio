# -*- coding: utf-8 -*-
"""
AI任务调试工具API路由模块
提供任务调试、查询、重新检查等功能
"""

import logging

logger = logging.getLogger(__name__)
import base64
import json
import os
import sys
from datetime import datetime
from urllib.parse import urlparse

import requests
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.utils.admin_helpers import get_models

# 创建蓝图
ai_debug_api_bp = Blueprint("ai_debug_api", __name__)
