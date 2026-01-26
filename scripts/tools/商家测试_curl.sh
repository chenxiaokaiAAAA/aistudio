#!/bin/bash

# 商家物流回调测试 - 超精简版
# 使用方法: bash 商家测试_curl.sh

API_URL="https://moeart.cc/api/logistics/callback"
ORDER_NUMBER="PET17582664981342618"  # 替换为实际订单号

echo "🚚 测试订单: $ORDER_NUMBER"
echo "📤 发送请求..."

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "'$ORDER_NUMBER'",
    "tracking_number": "SF1234567890",
    "logistics_company": "顺丰速运"
  }' \
  --connect-timeout 10 \
  --max-time 30

echo ""
echo "✅ 测试完成!"
