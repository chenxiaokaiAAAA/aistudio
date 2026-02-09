# -*- coding: utf-8 -*-
"""
Swagger/OpenAPI 文档路由
提供 /apidocs 交互式文档和 /apispec.json OpenAPI 规范

文档随路由自动更新：启动时从 app.url_map 扫描所有接口并生成 Swagger 2.0 规范。
"""

import re
import logging

logger = logging.getLogger(__name__)

# 路径+方法 -> 中文说明（用于自动生成接口的 summary，未匹配的用 endpoint 转读）
_PATH_SUMMARY_MAP = {
    # 小程序
    ("/api/miniprogram", "get"): "小程序API信息",
    ("/api/miniprogram/product-categories", "get"): "获取产品分类",
    ("/api/miniprogram/products", "get"): "获取产品列表",
    ("/api/miniprogram/styles", "get"): "获取风格列表",
    ("/api/miniprogram/styles/refresh", "get"): "刷新风格列表",
    ("/api/miniprogram/banners", "get"): "获取轮播图",
    ("/api/miniprogram/homepage-config", "get"): "获取首页配置",
    ("/api/miniprogram/orders", "get"): "获取订单列表",
    ("/api/miniprogram/orders", "post"): "创建订单",
    ("/api/miniprogram/order/{order_number}", "get"): "按订单号获取订单",
    ("/api/miniprogram/order/check", "get"): "安卓APP核销检查订单",
    ("/api/miniprogram/order/qrcode", "get"): "获取订单二维码",
    ("/api/miniprogram/order/upload", "post"): "安卓APP上传拍摄照片",
    ("/api/miniprogram/orders/{order_id}/status", "put"): "更新订单状态",
    ("/api/miniprogram/orders/{order_id}/generate-qrcode", "post"): "生成订单二维码",
    ("/api/miniprogram/orders/{order_id}/update-order-mode", "post"): "更新订单模式",
    ("/api/miniprogram/orders/{order_id}/set-manual", "post"): "设为手动模式",
    ("/api/miniprogram/orders/{order_id}/images", "put"): "更新订单图片",
    ("/api/miniprogram/orders/{order_id}/images/delete", "delete"): "删除订单图片",
    ("/api/miniprogram/works", "get"): "获取作品列表",
    ("/api/miniprogram/shop/products", "get"): "获取商城产品列表",
    ("/api/miniprogram/shop/products/{product_id}", "get"): "获取商城产品详情",
    ("/api/miniprogram/shop/orders", "get"): "获取商城订单列表",
    ("/api/miniprogram/shop/orders", "post"): "创建商城订单",
    ("/api/miniprogram/share/record", "post"): "记录分享",
    ("/api/miniprogram/share/reward", "post"): "领取分享奖励",
    ("/api/miniprogram/third-party-groupon/query", "post"): "第三方团购查询",
    ("/api/miniprogram/third-party-groupon/verify", "post"): "第三方团购核销",
    ("/api/miniprogram/third-party-groupon/redeem", "post"): "第三方团购兑换",
    ("/api/miniprogram/digital-avatar/list", "get"): "获取数字人像列表",
    ("/api/miniprogram/groupon/check-staf", "get"): "团购核销检查店员权限",
    ("/api/miniprogram/groupon/check-staff", "get"): "团购核销检查店员权限",
    ("/api/miniprogram/groupon/packages", "get"): "获取团购套餐列表",
    ("/api/miniprogram/groupon/verify", "post"): "团购订单核销",
    ("/api/miniprogram/media/final/{filename}", "get"): "获取效果图",
    ("/api/miniprogram/media/original/{filename}", "get"): "获取原图",
    ("/api/miniprogram/refund/request", "post"): "申请退款",
    ("/api/miniprogram/refund/check-order", "get"): "校验退款订单",
    ("/api/miniprogram/refund/check-permission", "get"): "校验退款权限",
    # 选片
    ("/api/photo-selection/search-orders", "post"): "查询选片订单",
    ("/api/photo-selection/verify-token", "post"): "验证选片 Token",
    # 支付
    ("/api/payment/create", "post"): "创建支付订单",
    # 用户
    ("/api/user/visit", "post"): "提交访问记录",
    ("/api/user/visit/stats", "get"): "访问统计",
    ("/api/user/update-info", "post"): "更新用户信息",
    ("/api/user/phone", "post"): "绑定手机号",
    ("/api/user/update-phone", "post"): "更新手机号",
    ("/api/user/messages/unread-count", "get"): "未读消息数",
    ("/api/user/messages", "get"): "获取消息列表",
    ("/api/user/messages/check", "get"): "检查消息",
    ("/api/user/messages/read", "post"): "标记消息已读",
    ("/api/user/check-promotion-eligibility", "post"): "校验推广资格",
    ("/api/user/update-promotion-eligibility", "post"): "更新推广资格",
    ("/api/user/request-subscription-after-payment", "post"): "支付后请求订阅",
    ("/api/user/subscription-status", "post"): "订阅状态",
    ("/api/user/coupons/available-count", "get"): "可用优惠券数量",
    ("/api/user/commission", "get"): "分佣记录",
    ("/api/user/withdrawals", "get"): "提现记录",
    ("/api/user/check", "post"): "校验登录",
    ("/api/user/openid", "post"): "获取 OpenID",
    ("/api/user/register", "post"): "用户注册",
    # 管理后台 - 通用规则前缀
    ("/api/admin/homepage/banners", "get"): "获取首页轮播图",
    ("/api/admin/homepage/banners", "post"): "新增轮播图",
    ("/api/admin/homepage/banners/{banner_id}", "put"): "更新轮播图",
    ("/api/admin/homepage/banners/{banner_id}", "delete"): "删除轮播图",
    ("/api/admin/homepage/config", "get"): "获取首页配置",
    ("/api/admin/homepage/config", "put"): "更新首页配置",
    ("/api/admin/homepage/features", "put"): "更新首页功能开关",
    ("/api/admin/homepage/category-navs", "get"): "获取分类导航",
    ("/api/admin/homepage/category-navs", "post"): "新增分类导航",
    ("/api/admin/homepage/category-navs/{nav_id}", "put"): "更新分类导航",
    ("/api/admin/homepage/category-navs/{nav_id}", "delete"): "删除分类导航",
    ("/api/admin/homepage/product-sections", "get"): "获取产品区块",
    ("/api/admin/homepage/product-sections", "post"): "新增产品区块",
    ("/api/admin/homepage/product-sections/{section_id}", "put"): "更新产品区块",
    ("/api/admin/homepage/product-sections/{section_id}", "delete"): "删除产品区块",
    ("/api/admin/homepage/products", "get"): "获取首页产品",
    ("/api/admin/homepage/product-categories-tree", "get"): "产品分类树",
    ("/api/admin/upload-image", "post"): "上传图片",
    ("/api/admin/init-data", "post"): "初始化数据",
    ("/api/admin/clean-duplicates", "post"): "清理重复数据",
    ("/api/admin/update-cover-images", "post"): "更新封面图",
    ("/api/admin/miniprogram-config", "get"): "获取小程序配置",
    ("/api/admin/miniprogram-config", "post"): "保存小程序配置",
    ("/api/admin/mockup/templates", "get"): "获取样机模板列表",
    ("/api/admin/mockup/templates", "post"): "新增样机模板",
    ("/api/admin/mockup/templates/{template_id}", "put"): "更新样机模板",
    ("/api/admin/mockup/templates/{template_id}", "delete"): "删除样机模板",
    ("/api/admin/mockup/products", "get"): "获取样机产品",
    ("/api/admin/mockup/scan-psd", "get"): "扫描 PSD",
    ("/api/admin/mockup/order/{order_id}/templates", "get"): "订单样机模板",
    ("/api/admin/mockup/generate", "post"): "生成样机图",
    ("/api/admin/mockup/generate-test", "post"): "测试生成样机图",
    ("/api/admin/payment-config", "get"): "获取支付配置",
    ("/api/admin/payment-config", "post"): "保存支付配置",
    ("/api/admin/print-config/printer", "get"): "获取打印配置",
    ("/api/admin/print-config/printer", "post"): "保存打印配置",
    ("/api/admin/print-config/machines", "get"): "获取机器列表",
    ("/api/admin/print-config/machines", "post"): "保存机器配置",
    ("/api/admin/print-config/test-print", "post"): "测试打印",
    ("/api/admin/print-config/size", "get"): "获取尺寸配置",
    ("/api/admin/print-config/size", "post"): "保存尺寸配置",
    ("/api/admin/print-config/size/{config_id}", "delete"): "删除尺寸配置",
    ("/api/admin/printer/orders", "get"): "打印订单列表",
    ("/api/admin/printer/resend/{order_id}", "post"): "重新发送打印",
    ("/api/admin/products/{product_id}", "get"): "获取产品详情",
    # 管理后台 - 推广
    ("/admin/api/promotion/commissions", "get"): "分佣列表",
    ("/admin/api/promotion/users", "get"): "推广用户列表",
    ("/admin/api/promotion/user/own-orders", "get"): "用户订单",
    ("/admin/api/promotion/visits/detail", "get"): "访问详情",
    ("/admin/api/promotion/visits", "get"): "访问记录",
    ("/admin/api/promotion/commission/{commission_id}", "get"): "分佣详情",
    ("/admin/api/promotion/commission/{commission_id}", "delete"): "删除分佣",
    ("/admin/api/promotion/user/{user_id}", "delete"): "删除推广用户",
    # 加盟商
    ("/franchisee/api/qrcode-preview", "get"): "二维码预览",
}


def _get_chinese_summary(path, method):
    """获取接口中文说明，优先查表，否则根据路径推断"""
    key = (path, method)
    if key in _PATH_SUMMARY_MAP:
        return _PATH_SUMMARY_MAP[key]
    for (p, m), desc in _PATH_SUMMARY_MAP.items():
        if m != method or p != path:
            continue
        return desc
    # 路径含 {param} 时尝试匹配：如 /api/miniprogram/media/final/{filename} 匹配 media/final
    if "{" in path:
        base = re.sub(r"\{[^}]+\}", "{}", path)
        for (p, m), desc in _PATH_SUMMARY_MAP.items():
            if m != method:
                continue
            if "{" in p and re.sub(r"\{[^}]+\}", "{}", p) == base:
                return desc
    return _infer_chinese_summary(path, method)


def _infer_chinese_summary(path, method):
    """根据路径推断中文说明，避免泛泛的「获取接口」"""
    segs = [s for s in path.split("/") if s and not s.startswith("{")]
    action = {"get": "获取", "post": "提交", "put": "更新", "delete": "删除", "patch": "修改"}.get(
        method.lower(), "操作"
    )
    # 单段 -> 中文
    names = {
        "products": "产品",
        "orders": "订单",
        "users": "用户",
        "images": "图片",
        "config": "配置",
        "banners": "轮播图",
        "styles": "风格",
        "categories": "分类",
        "coupons": "优惠券",
        "promotion": "推广",
        "commission": "分佣",
        "messages": "消息",
        "visit": "访问",
        "refund": "退款",
        "shop": "商城",
        "mockup": "样机",
        "templates": "模板",
        "homepage": "首页",
        "admin": "管理",
        "payment": "支付",
        "print": "打印",
        "printer": "打印机",
        "list": "列表",
        "verify": "核销",
        "packages": "套餐",
        "original": "原图",
        "final": "效果图",
    }
    # 路径关键词 -> 中文（用于多段路径如 digital-avatar/list）
    path_names = {
        "digital-avatar": "数字人像",
        "groupon": "团购",
        "media": "媒体",
        "avatar": "人像",
        "staff": "店员",
        "staf": "店员",
    }
    for s in segs:
        if s in names:
            return f"{action}{names[s]}"
        if s in path_names:
            return f"{action}{path_names[s]}"
        if "-" in s and s.replace("-", "_") in path_names:
            return f"{action}{path_names[s.replace('-', '_')]}"
    # 从路径片段推断
    path_lower = path.lower()
    if "media/final" in path or "/final/" in path:
        return "获取效果图"
    if "media/original" in path or "/original/" in path:
        return "获取原图"
    if "media/hd" in path:
        return "获取高清图"
    if "groupon" in path_lower:
        return "获取团购信息" if action == "获取" else f"{action}团购"
    if "digital-avatar" in path_lower or "avatar" in path_lower:
        return "获取数字人像" if action == "获取" else f"{action}数字人像"
    for s in reversed(segs):
        if s in names:
            return f"{action}{names[s]}"
        if "list" in s:
            return f"{action}列表"
        if "verify" in s or "check" in s:
            return f"{action}校验"
        if "upload" in s:
            return "上传文件"
        if "download" in s:
            return "下载文件"
    return f"{action}数据"


# 安卓APP 相关接口路径（聚合小程序、管理后台中与安卓APP/自拍机相关的接口）
_ANDROID_APP_PATHS = frozenset([
    "/api/miniprogram/order/check",           # 核销检查（返回订单号、客户信息、门店等）
    "/api/miniprogram/order/upload",          # 上传拍摄照片
    "/api/miniprogram/order/{order_number}",  # 获取订单详情
    "/api/miniprogram/order/qrcode",          # 获取订单二维码（小程序生成，安卓扫描）
    "/api/miniprogram/orders/{order_id}/generate-qrcode",  # 生成拍摄核销二维码
    "/api/miniprogram/orders/{order_id}/status",           # 更新订单状态
    "/api/miniprogram/orders/{order_id}/images",           # 更新订单图片
    "/api/miniprogram/product-categories",    # 产品分类（如需展示）
    "/api/miniprogram/products",             # 产品列表（如需展示）
    "/api/miniprogram/styles",               # 风格列表（如需展示）
    "/api/miniprogram/banners",              # 轮播图（如需展示）
    "/api/admin/print-config/machines",      # 自拍机打印机配置(GET/POST)
])


def _path_in_android_app_set(path):
    """判断路径是否属于安卓APP相关（支持 {param} 模式匹配）"""
    if path in _ANDROID_APP_PATHS:
        return True
    # 支持路径模板匹配（如 order_id 与 id 等价）
    base = re.sub(r"\{[^}]+\}", "{}", path)
    for p in _ANDROID_APP_PATHS:
        if "{" in p and re.sub(r"\{[^}]+\}", "{}", p) == base:
            return True
    return False


# 路径前缀 -> 标签（用于分组显示，具体路径需在通用前缀之前）
_PATH_TAG_MAP = [
    ("/api/miniprogram/order/check", "安卓APP"),
    ("/api/miniprogram/order/upload", "安卓APP"),
    ("/api/miniprogram/order/", "安卓APP"),      # order/{order_number}, order/qrcode
    ("/api/miniprogram/orders/", "安卓APP"),    # orders/{id}/generate-qrcode, status, images
    ("/api/miniprogram/product-categories", "安卓APP"),
    ("/api/miniprogram/products", "安卓APP"),
    ("/api/miniprogram/styles", "安卓APP"),
    ("/api/miniprogram/banners", "安卓APP"),
    ("/api/admin/print-config/machines", "安卓APP"),
    ("/api/miniprogram", "小程序"),
    ("/api/photo-selection", "选片"),
    ("/api/payment", "支付"),
    ("/api/user", "用户"),
    ("/api/admin", "管理后台"),
    ("/franchisee/api", "加盟商"),
    ("/admin/", "管理后台"),
]


def _path_to_tag(path):
    """根据路径返回标签"""
    for prefix, tag in _PATH_TAG_MAP:
        if path.startswith(prefix):
            return tag
    return "其他"


def _rule_to_swagger_path(rule):
    """Flask rule 转为 Swagger path（<int:id> -> {id}）"""
    path = rule
    path = re.sub(r"<int:(\w+)>", r"{\1}", path)
    path = re.sub(r"<float:(\w+)>", r"{\1}", path)
    path = re.sub(r"<path:(\w+)>", r"{\1}", path)
    path = re.sub(r"<(\w+)>", r"{\1}", path)
    return path


def _build_paths_from_app(app):
    """从 Flask 应用扫描路由，生成 Swagger 2.0 paths"""
    paths = {}
    exclude_prefixes = ("/static", "/flasgger", "/apidocs", "/apispec")
    include_prefixes = ("/api/", "/franchisee/api/", "/admin/api/")

    for rule in app.url_map.iter_rules():
        r = rule.rule
        if any(r.startswith(p) for p in exclude_prefixes):
            continue
        if not any(r.startswith(p) for p in include_prefixes):
            continue
        methods = [m for m in rule.methods if m not in ("HEAD", "OPTIONS")]
        if not methods:
            continue

        path = _rule_to_swagger_path(r)
        tag = _path_to_tag(r)
        if path not in paths:
            paths[path] = {}

        for method in methods:
            summary = _get_chinese_summary(path, method) or (
                (rule.endpoint or "API").replace("_", " ").replace(".", " ")
            )
            # operationId 需唯一，用 path+method 生成
            safe_id = (path.replace("/", "_").replace("{", "").replace("}", "").strip("_") + "_" + method.lower()).strip("_")
            op = {
                "tags": [tag],
                "summary": summary[:60],
                "operationId": safe_id[:80],
                "responses": {"200": {"description": "成功"}},
            }
            if method in ("POST", "PUT", "PATCH") and "body" not in str(rule):
                op["parameters"] = [
                    {
                        "name": "body",
                        "in": "body",
                        "schema": {"type": "object"},
                    }
                ]
            paths[path][method.lower()] = op

    return dict(sorted(paths.items()))


# 手动维护的详细文档（含请求体 schema），会覆盖自动生成中同路径的条目
DETAILED_PATHS = {
        "/api/miniprogram/product-categories": {
            "get": {
                "tags": ["小程序"],
                "summary": "获取产品分类",
                "responses": {"200": {"description": "产品分类列表"}},
            }
        },
        "/api/miniprogram/products": {
            "get": {
                "tags": ["小程序"],
                "summary": "获取产品列表",
                "parameters": [
                    {"name": "category_id", "in": "query", "type": "integer"},
                ],
                "responses": {"200": {"description": "产品列表"}},
            }
        },
        "/api/miniprogram/styles": {
            "get": {
                "tags": ["小程序"],
                "summary": "获取风格列表",
                "responses": {"200": {"description": "风格列表"}},
            }
        },
        "/api/miniprogram/banners": {
            "get": {
                "tags": ["小程序"],
                "summary": "获取轮播图",
                "responses": {"200": {"description": "轮播图列表"}},
            }
        },
        "/api/miniprogram/orders": {
            "get": {
                "tags": ["小程序"],
                "summary": "获取订单列表",
                "parameters": [
                    {"name": "openid", "in": "query", "required": True, "type": "string"},
                    {"name": "page", "in": "query", "type": "integer"},
                ],
                "responses": {"200": {"description": "订单列表"}},
            },
            "post": {
                "tags": ["小程序"],
                "summary": "创建订单",
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["openid", "items", "customer_name", "customer_phone"],
                            "properties": {
                                "openid": {"type": "string"},
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "product_id": {"type": "integer"},
                                            "size_id": {"type": "integer"},
                                            "style_id": {"type": "integer"},
                                            "quantity": {"type": "integer"},
                                            "price": {"type": "number"},
                                        },
                                    },
                                },
                                "customer_name": {"type": "string"},
                                "customer_phone": {"type": "string"},
                                "order_mode": {"type": "string"},
                                "franchisee_id": {"type": "integer"},
                            },
                        },
                    }
                ],
                "responses": {
                    "200": {"description": "订单创建成功"},
                    "400": {"description": "参数错误"},
                },
            },
        },
        "/api/miniprogram/orders/{order_id}/status": {
            "put": {
                "tags": ["小程序"],
                "summary": "更新订单状态",
                "parameters": [
                    {"name": "order_id", "in": "path", "required": True, "type": "integer"},
                    {
                        "name": "body",
                        "in": "body",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "status": {"type": "string"},
                                "statusText": {"type": "string"},
                            },
                        },
                    },
                ],
                "responses": {"200": {"description": "更新成功"}},
            }
        },
        "/api/photo-selection/search-orders": {
            "post": {
                "tags": ["选片"],
                "summary": "查询选片订单",
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "phone": {"type": "string"},
                                "order_number": {"type": "string"},
                                "franchisee_id": {"type": "integer"},
                            },
                        },
                    }
                ],
                "responses": {"200": {"description": "订单列表"}},
            }
        },
        "/api/payment/create": {
            "post": {
                "tags": ["支付"],
                "summary": "创建支付订单",
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["order_number", "openid", "total_amount"],
                            "properties": {
                                "order_number": {"type": "string"},
                                "openid": {"type": "string"},
                                "total_amount": {"type": "number"},
                            },
                        },
                    }
                ],
                "responses": {"200": {"description": "支付参数"}},
            }
        },
}




def _build_swagger_template(app):
    """构建 Swagger 2.0 模板：自动扫描路由 + 合并详细文档"""
    auto_paths = _build_paths_from_app(app)
    # 详细文档覆盖自动生成
    for path, methods in DETAILED_PATHS.items():
        if path in auto_paths:
            for method, spec in methods.items():
                auto_paths[path][method] = spec
        else:
            auto_paths[path] = methods

    return {
        "swagger": "2.0",
        "info": {
            "title": "AI-Studio API",
            "description": """
AI-Studio 项目 API 接口文档（自动从路由生成）

## 模块说明
- **安卓APP** - 核销检查、上传拍摄照片
- **小程序** - 产品、风格、订单、支付等
- **选片** - 订单查询、选片确认
- **支付** - 微信支付创建、回调
- **管理后台** - 需登录，前缀 `/api/admin/`
- **用户** - 用户信息、优惠券、推广
- **加盟商** - 加盟商相关接口

## 相关文档
- docs/api/API错误码说明.md
- docs/api/API请求响应示例.md
- docs/api/API版本管理说明.md
            """,
            "version": "1.0.0",
            "contact": {"name": "AI-Studio"},
        },
        "host": "localhost:8000",
        "basePath": "/",
        "schemes": ["http"],
        "tags": [
            {"name": "安卓APP", "description": "安卓APP核销、上传拍摄照片"},
            {"name": "小程序", "description": "小程序端接口"},
            {"name": "选片", "description": "选片模块接口"},
            {"name": "支付", "description": "支付相关接口"},
            {"name": "用户", "description": "用户、优惠券、推广"},
            {"name": "管理后台", "description": "管理后台 API"},
            {"name": "加盟商", "description": "加盟商接口"},
            {"name": "其他", "description": "其他接口"},
        ],
        "paths": auto_paths,
    }


def _filter_spec_by_tag(spec, tag):
    """按标签过滤 spec 的 paths，仅保留指定 tag 的接口"""
    if not tag:
        return spec
    filtered_paths = {}
    for path, methods in spec.get("paths", {}).items():
        kept = {}
        for method, op in methods.items():
            if not isinstance(op, dict):
                continue
            # 安卓APP 使用 curated 路径列表，不依赖 operation.tags
            if tag == "安卓APP":
                if _path_in_android_app_set(path):
                    kept[method] = op
            elif op.get("tags") and tag in op["tags"]:
                kept[method] = op
        if kept:
            filtered_paths[path] = kept
    spec = dict(spec)
    spec["paths"] = filtered_paths
    spec["info"] = dict(spec.get("info", {}))
    spec["info"]["title"] = f"{spec['info'].get('title', 'API')} - {tag}"
    return spec


def init_swagger(app):
    """初始化 Flasgger Swagger，注册 /apidocs 和 /apispec.json，以及横向分类的 /docs 页面"""
    try:
        from flask import render_template, jsonify, request
        from flasgger import Swagger

        # 禁用自动解析，仅使用模板，避免 swagger + openapi 字段冲突
        # 必须显式设置 auth、ui_params 等，否则 Python None 被渲染成 JS 字面量 None 导致报错
        config = {
            "headers": [],
            "specs": [
                {
                    "endpoint": "apispec",
                    "route": "/apispec.json",
                    "rule_filter": lambda rule: False,  # 不自动扫描路由
                    "model_filter": lambda tag: True,
                }
            ],
            "static_url_path": "/flasgger_static",
            "swagger_ui": True,
            "specs_route": "/apidocs/",
            "auth": {},  # 避免 Flasgger 模板中 flasgger_config.get("auth") 输出 None 导致 JS 报错
            "ui_params": {},
            "doc_expansion": "list",
        }
        template = _build_swagger_template(app)
        Swagger(app, template=template, config=config)

        # 按标签过滤的 spec 接口（供 /docs 标签筛选使用）
        @app.route("/apispec-filtered.json")
        def apispec_filtered():
            tag = request.args.get("tag", "").strip()
            full_spec = _build_swagger_template(app)
            spec = _filter_spec_by_tag(full_spec, tag)
            return jsonify(spec)

        # 注册带横向标签的 /docs 入口（减轻纵向内容过多、便于按模块筛选）
        @app.route("/docs")
        def api_docs_page():
            return render_template("api_docs.html")

        logger.info("✅ Swagger/OpenAPI 文档已启用: /docs（横向筛选）, /apidocs（共 %d 个路径，自动更新）", len(template["paths"]))
        return True
    except ImportError as e:
        logger.warning(f"⚠️ Flasgger 未安装，Swagger 文档不可用: {e}")
        return False
