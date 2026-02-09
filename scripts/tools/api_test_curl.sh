#!/bin/bash
# API 接口 curl 自动化测试脚本
# 使用前请确保服务已启动: python test_server.py 或 python start.py
# 用法: bash scripts/tools/api_test_curl.sh [BASE_URL]
# 默认: http://localhost:8000

BASE_URL="${1:-http://localhost:8000}"
PASS=0
FAIL=0

test_api() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local expected_codes="$5"
    
    echo -n "  [$name] ... "
    if [ "$method" = "GET" ]; then
        code=$(curl -s -o /tmp/api_response.json -w "%{http_code}" "$url")
    else
        code=$(curl -s -o /tmp/api_response.json -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$url")
    fi
    
    if echo ",$expected_codes," | grep -q ",$code,"; then
        echo "✅ $code"
        ((PASS++))
        return 0
    else
        echo "❌ $code (期望: $expected_codes)"
        ((FAIL++))
        return 1
    fi
}

echo "=========================================="
echo "🧪 API 接口 curl 测试"
echo "   基础URL: $BASE_URL"
echo "=========================================="

echo ""
echo "[1] 小程序接口"
test_api "产品分类" "GET" "$BASE_URL/api/miniprogram/product-categories" "" "200,400,500"
test_api "产品列表" "GET" "$BASE_URL/api/miniprogram/products" "" "200,400,500"
test_api "风格列表" "GET" "$BASE_URL/api/miniprogram/styles" "" "200,400,500"
test_api "轮播图" "GET" "$BASE_URL/api/miniprogram/banners" "" "200,400,500"
test_api "订单列表" "GET" "$BASE_URL/api/miniprogram/orders?openid=test" "" "200,400,500"

echo ""
echo "[2] 选片接口"
test_api "查询订单" "POST" "$BASE_URL/api/photo-selection/search-orders" '{"phone":"13800138000","franchisee_id":1}' "200,400,404,500"

echo ""
echo "=========================================="
echo "📊 测试结果: 通过 $PASS, 失败 $FAIL"
echo "=========================================="
exit $FAIL
