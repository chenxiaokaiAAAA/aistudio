#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
接口文档自动化生成脚本

从 Flask 应用路由中提取所有 API 端点，生成 OpenAPI 3.0 规范 JSON 文件。
可用于：
- 更新 docs/api/openapi_spec.json
- 与 Swagger UI 配合使用
- 导入 Postman / 其他 API 工具

用法:
    python scripts/tools/generate_openapi_spec.py
    或
    python -m scripts.tools.generate_openapi_spec
"""

import json
import os
import sys

# 确保项目根目录在 Python 路径中
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


def get_flask_app():
    """获取已注册路由的 Flask 应用"""
    try:
        import test_server
        return test_server.app
    except ImportError:
        # 备用：尝试从 app 模块创建
        from app import create_app
        return create_app()


def extract_path_from_rule(rule):
    """将 Flask rule 转为 OpenAPI path（如 /api/miniprogram/orders/<int:order_id> -> /api/miniprogram/orders/{order_id}）"""
    import re
    path = rule
    # <int:order_id> -> {order_id}
    path = re.sub(r'<int:(\w+)>', r'{\1}', path)
    path = re.sub(r'<float:(\w+)>', r'{\1}', path)
    path = re.sub(r'<path:(\w+)>', r'{\1}', path)
    path = re.sub(r'<(\w+)>', r'{\1}', path)
    return path


def generate_openapi_spec(app, base_url="http://localhost:8000"):
    """从 Flask 应用生成 OpenAPI 3.0 规范"""
    paths = {}
    api_rules = []  # 仅收集 /api 开头的路由

    for rule in app.url_map.iter_rules():
        if rule.rule.startswith("/api/") and "static" not in rule.rule:
            methods = [m for m in rule.methods if m not in ("HEAD", "OPTIONS")]
            if not methods:
                continue
            path = extract_path_from_rule(rule.rule)
            if path not in paths:
                paths[path] = {}

            for method in methods:
                if method == "GET":
                    paths[path][method.lower()] = {
                        "summary": f"{rule.endpoint or 'API'}",
                        "operationId": rule.endpoint.replace(".", "_") if rule.endpoint else path.replace("/", "_"),
                        "responses": {"200": {"description": "成功"}},
                    }
                else:
                    paths[path][method.lower()] = {
                        "summary": f"{rule.endpoint or 'API'}",
                        "operationId": rule.endpoint.replace(".", "_") if rule.endpoint else path.replace("/", "_"),
                        "requestBody": {
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "responses": {"200": {"description": "成功"}},
                    }

    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "AI-Studio API",
            "description": "从 Flask 路由自动生成的 API 规范，详见 docs/api/",
            "version": "1.0.0",
        },
        "servers": [{"url": base_url, "description": "API 服务器"}],
        "paths": dict(sorted(paths.items())),
    }
    return spec


def main():
    print("正在加载 Flask 应用...")
    app = get_flask_app()

    with app.app_context():
        spec = generate_openapi_spec(app)
        output_path = os.path.join(_project_root, "docs", "api", "openapi_spec.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
        print(f"✅ OpenAPI 规范已生成: {output_path}")
        print(f"   共 {len(spec['paths'])} 个路径")


if __name__ == "__main__":
    main()
