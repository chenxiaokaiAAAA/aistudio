# -*- coding: utf-8 -*-
"""
AI任务调试工具API路由模块
提供任务调试、查询、重新检查等功能
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
import os
import json
import sys
import requests
import base64
from urllib.parse import urlparse

from app.utils.admin_helpers import get_models

# 创建蓝图
ai_debug_api_bp = Blueprint('ai_debug_api', __name__)
