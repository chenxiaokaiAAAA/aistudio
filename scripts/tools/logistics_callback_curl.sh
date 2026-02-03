#!/bin/bash

# 物流回调测试脚本 - 针对订单 PET17582664981342618
# 使用方法: bash logistics_callback_curl.sh

echo "🚚 物流回调测试脚本 - curl版本"
echo "=================================================="

# 接口配置
API_URL="https://photogooo/api/logistics/callback"
ORDER_NUMBER="PET17582664981342618"

echo "📦 目标订单: $ORDER_NUMBER"
echo "🌐 接口地址: $API_URL"
echo ""

# 测试用例1: 顺丰速运
echo "🧪 测试用例 1: 顺丰速运"
echo "----------------------------------------"
echo "📤 请求数据:"
cat << EOF
{
    "order_number": "$ORDER_NUMBER",
    "tracking_number": "SF1234567890",
    "logistics_company": "顺丰速运",
    "estimated_delivery": "2025-09-21",
    "status": "已发货",
    "remark": "商品已发出，请注意查收"
}
EOF

echo ""
echo "🚀 发送请求..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "'$ORDER_NUMBER'",
    "tracking_number": "SF1234567890",
    "logistics_company": "顺丰速运",
    "estimated_delivery": "2025-09-21",
    "status": "已发货",
    "remark": "商品已发出，请注意查收"
  }' \
  --connect-timeout 30 \
  --max-time 60

echo ""
echo ""

# 测试用例2: 圆通速递
echo "🧪 测试用例 2: 圆通速递"
echo "----------------------------------------"
echo "📤 请求数据:"
cat << EOF
{
    "order_number": "$ORDER_NUMBER",
    "tracking_number": "YT9876543210",
    "logistics_company": "圆通速递",
    "estimated_delivery": "2025-09-22",
    "status": "已发货",
    "remark": "包裹已发出"
}
EOF

echo ""
echo "🚀 发送请求..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "'$ORDER_NUMBER'",
    "tracking_number": "YT9876543210",
    "logistics_company": "圆通速递",
    "estimated_delivery": "2025-09-22",
    "status": "已发货",
    "remark": "包裹已发出"
  }' \
  --connect-timeout 30 \
  --max-time 60

echo ""
echo ""

# 测试用例3: 简化格式
echo "🧪 测试用例 3: 简化格式"
echo "----------------------------------------"
echo "📤 请求数据:"
cat << EOF
{
    "order_number": "$ORDER_NUMBER",
    "tracking_number": "JD8889990001",
    "logistics_company": "京东物流"
}
EOF

echo ""
echo "🚀 发送请求..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "'$ORDER_NUMBER'",
    "tracking_number": "JD8889990001",
    "logistics_company": "京东物流"
  }' \
  --connect-timeout 30 \
  --max-time 60

echo ""
echo "=================================================="
echo "🎉 所有测试完成!"
echo ""
echo "📝 测试说明:"
echo "1. 每个测试用例都会更新订单的物流信息"
echo "2. 订单状态会更新为 'processing'（已发货）"
echo "3. 可以在后台管理界面查看更新结果"
echo "4. 建议按顺序执行，观察每次的变化"
