# 安卓APP订单检查问题修复说明

## 问题描述

在安卓APP中输入小程序创建的订单号时，提示出错，无法进行核销。

## 问题原因

1. **订单状态判断不完整**：
   - 后端接口 `/api/miniprogram/order/check` 在判断订单是否已支付时，没有包含 `paid` 状态
   - 只检查了 `pending`, `manufacturing`, `completed`, `shipped`, `delivered` 状态

2. **开发模式支付跳过后订单状态未更新**：
   - 前端在开发模式下调用 `/api/payment/create` 时传递了 `skipPayment: true`
   - 但后端没有处理这个参数，导致订单状态仍然是 `unpaid`
   - 安卓APP检查时认为订单未支付，无法进行核销

3. **安卓APP判断逻辑不完整**：
   - `OrderActivity.isOrderPaid()` 方法只检查状态是否为 `"paid"`
   - 没有使用后端返回的 `is_paid` 字段
   - 没有考虑其他已支付状态

## 修复内容

### 1. 后端订单检查接口 (`AI-studio/test_server.py`)

**修改位置：** 第 6418-6424 行

**修改前：**
```python
elif order.status in ['pending', 'manufacturing', 'completed', 'shipped', 'delivered']:
    is_paid = True
```

**修改后：**
```python
elif order.status in ['paid', 'pending', 'manufacturing', 'completed', 'shipped', 'delivered']:
    is_paid = True
```

### 2. 后端支付接口支持开发模式 (`AI-studio/test_server.py`)

**修改位置：** 第 4147 行开始

**新增功能：**
- 检测 `skipPayment` 参数
- 如果为 `true`，直接标记订单为已支付（状态改为 `paid`，设置支付时间和交易ID）
- 返回成功响应，不调用微信支付接口

**代码：**
```python
# 开发模式：如果skipPayment为true，直接标记订单为已支付
if skip_payment:
    print(f"⚠️ 开发模式：跳过支付，直接标记订单为已支付")
    try:
        order.status = 'paid'
        order.payment_time = datetime.now()
        order.transaction_id = f"DEV_{order_id}_{int(time.time())}"
        db.session.commit()
        print(f"✅ 开发模式：订单已标记为已支付")
        return jsonify({
            'success': True,
            'message': '开发模式：订单已标记为已支付',
            'isZeroPayment': True,
            'data': {
                'orderId': order_id,
                'status': 'paid',
                'paymentTime': order.payment_time.isoformat(),
                'transactionId': order.transaction_id
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"❌ 开发模式：标记订单为已支付失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'开发模式：标记订单为已支付失败: {str(e)}'
        }), 500
```

### 3. 安卓APP订单状态判断优化 (`OrderActivity.java`)

**修改位置：** `isOrderPaid()` 方法

**修改前：**
```java
private boolean isOrderPaid() {
    try {
        return "paid".equals(orderData.getString("status"));
    } catch (Exception e) {
        return false;
    }
}
```

**修改后：**
```java
private boolean isOrderPaid() {
    try {
        // 优先使用is_paid字段，如果没有则检查status
        if (orderData.has("is_paid")) {
            return orderData.getBoolean("is_paid");
        }
        String status = orderData.getString("status");
        return "paid".equals(status) || 
               "pending".equals(status) || 
               "manufacturing".equals(status) || 
               "completed".equals(status);
    } catch (Exception e) {
        e.printStackTrace();
        return false;
    }
}
```

## 需要重启的服务

### 后端服务（必须重启）
```bash
cd AI-studio
python start.py
```

### 安卓APP（需要重新编译）
在Android Studio中：
1. 点击 "Build" → "Rebuild Project"
2. 或者直接运行APP

## 修复后的流程

1. **小程序创建订单**：
   - 订单状态初始为 `unpaid`
   - 调用 `/api/payment/create`，传递 `skipPayment: true`

2. **后端处理支付（开发模式）**：
   - 检测到 `skipPayment: true`
   - 将订单状态改为 `paid`
   - 设置支付时间和交易ID
   - 返回成功响应

3. **安卓APP检查订单**：
   - 调用 `/api/miniprogram/order/check?orderId=xxx`
   - 后端返回 `is_paid: true` 和 `status: "paid"`
   - 安卓APP使用 `is_paid` 字段判断，允许进入拍摄页面

## 测试步骤

1. **重启后端服务**

2. **在小程序中创建新订单**：
   - 选择证件照产品
   - 填写订单信息
   - 确认支付（开发模式会跳过真实支付）
   - 订单应该显示为"已支付"

3. **在安卓APP中测试**：
   - 打开APP
   - 点击"手动输入订单号"
   - 输入订单号（如：`PET17683014185584524`）
   - 应该能成功检查订单并进入拍摄页面

## 注意事项

1. **开发模式标志**：
   - 前端：`SKIP_REAL_PAYMENT = true`
   - 后端：自动处理 `skipPayment` 参数
   - 上线前需要改为 `false`

2. **订单状态**：
   - 开发模式下，订单创建后会立即标记为 `paid`
   - 生产环境下，需要真实支付成功后才会标记为 `paid`

3. **安卓APP兼容性**：
   - 现在同时支持 `is_paid` 字段和 `status` 字段判断
   - 兼容性更好，不容易出错
