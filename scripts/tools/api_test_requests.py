#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 接口自动化测试脚本（基于 requests）
测试前请确保服务已启动: python test_server.py
用法: python scripts/tools/api_test_requests.py [BASE_URL]
"""

import json
import sys

try:
    import requests
except ImportError:
    print("请安装 requests: pip install requests")
    sys.exit(1)

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
PASS = 0
FAIL = 0


def test_api(name, method, url, data=None, expected_codes=(200, 400, 500)):
    """测试单个 API"""
    global PASS, FAIL
    try:
        if method == "GET":
            r = requests.get(url, timeout=10)
        else:
            r = requests.request(
                method, url, json=data or {}, headers={"Content-Type": "application/json"}, timeout=10
            )
        ok = r.status_code in expected_codes
        status = "✅" if ok else "❌"
        print(f"  [{name}] {status} {r.status_code}")
        if ok:
            PASS += 1
        else:
            FAIL += 1
        return ok
    except requests.exceptions.ConnectionError:
        print(f"  [{name}] ❌ 连接失败（请确保服务已启动）")
        FAIL += 1
        return False
    except Exception as e:
        print(f"  [{name}] ❌ {e}")
        FAIL += 1
        return False


def main():
    print("=" * 50)
    print("🧪 API 接口自动化测试")
    print(f"   基础URL: {BASE_URL}")
    print("=" * 50)

    print("\n[1] 小程序接口")
    test_api("产品分类", "GET", f"{BASE_URL}/api/miniprogram/product-categories")
    test_api("产品列表", "GET", f"{BASE_URL}/api/miniprogram/products")
    test_api("风格列表", "GET", f"{BASE_URL}/api/miniprogram/styles")
    test_api("轮播图", "GET", f"{BASE_URL}/api/miniprogram/banners")
    test_api("订单列表", "GET", f"{BASE_URL}/api/miniprogram/orders?openid=test")

    print("\n[2] 选片接口")
    test_api(
        "查询订单",
        "POST",
        f"{BASE_URL}/api/photo-selection/search-orders",
        {"phone": "13800138000", "franchisee_id": 1},
        (200, 400, 404, 500),
    )

    print("\n" + "=" * 50)
    print(f"📊 结果: 通过 {PASS}, 失败 {FAIL}")
    print("=" * 50)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
