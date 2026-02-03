# 物流回调测试脚本 - PowerShell版本
# 针对订单 PET17582664981342618
# 使用方法: .\logistics_callback_powershell.ps1

Write-Host "🚚 物流回调测试脚本 - PowerShell版本" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# 接口配置
$API_URL = "https://photogooo/api/logistics/callback"
$ORDER_NUMBER = "PET17582664981342618"

Write-Host "📦 目标订单: $ORDER_NUMBER" -ForegroundColor Yellow
Write-Host "🌐 接口地址: $API_URL" -ForegroundColor Yellow
Write-Host ""

# 测试用例1: 顺丰速运
Write-Host "🧪 测试用例 1: 顺丰速运" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Cyan

$testData1 = @{
    order_number = $ORDER_NUMBER
    tracking_number = "SF1234567890"
    logistics_company = "顺丰速运"
    estimated_delivery = "2025-09-21"
    status = "已发货"
    remark = "商品已发出，请注意查收"
} | ConvertTo-Json -Depth 3

Write-Host "📤 请求数据:" -ForegroundColor White
Write-Host $testData1 -ForegroundColor Gray

Write-Host ""
Write-Host "🚀 发送请求..." -ForegroundColor Yellow

try {
    $response1 = Invoke-RestMethod -Uri $API_URL -Method POST -Body $testData1 -ContentType "application/json" -TimeoutSec 30
    Write-Host "📥 响应数据:" -ForegroundColor White
    $response1 | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Green
    
    if ($response1.success) {
        Write-Host "✅ 测试成功!" -ForegroundColor Green
        Write-Host "   📦 订单号: $($response1.data.order_number)" -ForegroundColor White
        Write-Host "   🚚 快递公司: $($response1.data.logistics_company)" -ForegroundColor White
        Write-Host "   📋 快递单号: $($response1.data.tracking_number)" -ForegroundColor White
        Write-Host "   📊 订单状态: $($response1.data.status)" -ForegroundColor White
    } else {
        Write-Host "❌ 测试失败!" -ForegroundColor Red
        Write-Host "   错误信息: $($response1.message)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ 请求异常: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host ""

# 测试用例2: 圆通速递
Write-Host "🧪 测试用例 2: 圆通速递" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Cyan

$testData2 = @{
    order_number = $ORDER_NUMBER
    tracking_number = "YT9876543210"
    logistics_company = "圆通速递"
    estimated_delivery = "2025-09-22"
    status = "已发货"
    remark = "包裹已发出"
} | ConvertTo-Json -Depth 3

Write-Host "📤 请求数据:" -ForegroundColor White
Write-Host $testData2 -ForegroundColor Gray

Write-Host ""
Write-Host "🚀 发送请求..." -ForegroundColor Yellow

try {
    $response2 = Invoke-RestMethod -Uri $API_URL -Method POST -Body $testData2 -ContentType "application/json" -TimeoutSec 30
    Write-Host "📥 响应数据:" -ForegroundColor White
    $response2 | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Green
    
    if ($response2.success) {
        Write-Host "✅ 测试成功!" -ForegroundColor Green
        Write-Host "   📦 订单号: $($response2.data.order_number)" -ForegroundColor White
        Write-Host "   🚚 快递公司: $($response2.data.logistics_company)" -ForegroundColor White
        Write-Host "   📋 快递单号: $($response2.data.tracking_number)" -ForegroundColor White
        Write-Host "   📊 订单状态: $($response2.data.status)" -ForegroundColor White
    } else {
        Write-Host "❌ 测试失败!" -ForegroundColor Red
        Write-Host "   错误信息: $($response2.message)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ 请求异常: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host ""

# 测试用例3: 简化格式
Write-Host "🧪 测试用例 3: 简化格式" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Cyan

$testData3 = @{
    order_number = $ORDER_NUMBER
    tracking_number = "JD8889990001"
    logistics_company = "京东物流"
} | ConvertTo-Json -Depth 3

Write-Host "📤 请求数据:" -ForegroundColor White
Write-Host $testData3 -ForegroundColor Gray

Write-Host ""
Write-Host "🚀 发送请求..." -ForegroundColor Yellow

try {
    $response3 = Invoke-RestMethod -Uri $API_URL -Method POST -Body $testData3 -ContentType "application/json" -TimeoutSec 30
    Write-Host "📥 响应数据:" -ForegroundColor White
    $response3 | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Green
    
    if ($response3.success) {
        Write-Host "✅ 测试成功!" -ForegroundColor Green
        Write-Host "   📦 订单号: $($response3.data.order_number)" -ForegroundColor White
        Write-Host "   🚚 快递公司: $($response3.data.logistics_company)" -ForegroundColor White
        Write-Host "   📋 快递单号: $($response3.data.tracking_number)" -ForegroundColor White
        Write-Host "   📊 订单状态: $($response3.data.status)" -ForegroundColor White
    } else {
        Write-Host "❌ 测试失败!" -ForegroundColor Red
        Write-Host "   错误信息: $($response3.message)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ 请求异常: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "🎉 所有测试完成!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 测试说明:" -ForegroundColor Yellow
Write-Host "1. 每个测试用例都会更新订单的物流信息" -ForegroundColor White
Write-Host "2. 订单状态会更新为 'processing'（已发货）" -ForegroundColor White
Write-Host "3. 可以在后台管理界面查看更新结果" -ForegroundColor White
Write-Host "4. 建议按顺序执行，观察每次的变化" -ForegroundColor White
