# API 请求响应示例

> 本文档提供主要 API 的请求/响应示例及 curl 命令，便于快速对接和测试。

---

## 一、小程序接口

### 1.1 创建订单

**请求**：
```http
POST /api/miniprogram/orders
Content-Type: application/json
```

```json
{
  "openid": "oXXXX_user_openid",
  "items": [
    {
      "product_id": 1,
      "size_id": 1,
      "style_id": 1,
      "quantity": 1,
      "price": 99.00
    }
  ],
  "customer_name": "张三",
  "customer_phone": "13800138000",
  "order_mode": "making",
  "franchisee_id": 1
}
```

**成功响应** (200)：
```json
{
  "status": "success",
  "order_number": "MP20260206001"
}
```

**curl 示例**：
```bash
curl -X POST "http://localhost:8000/api/miniprogram/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "openid": "oXXXX",
    "items": [{"product_id": 1, "size_id": 1, "style_id": 1, "quantity": 1, "price": 99}],
    "customer_name": "张三",
    "customer_phone": "13800138000",
    "order_mode": "making",
    "franchisee_id": 1
  }'
```

---

### 1.2 获取订单列表

**请求**：
```http
GET /api/miniprogram/orders?openid=oXXXX
```

**成功响应** (200)：
```json
{
  "status": "success",
  "orders": [
    {
      "orderId": "MP20260206001",
      "orderId_db": 123,
      "customerName": "张三",
      "status": "pending",
      "statusText": "待制作",
      "totalPrice": 99.0,
      "createTime": "2026-02-06T10:00:00",
      "images": []
    }
  ]
}
```

**curl 示例**：
```bash
curl "http://localhost:8000/api/miniprogram/orders?openid=oXXXX"
```

---

### 1.3 更新订单状态

**请求**：
```http
PUT /api/miniprogram/orders/123/status
Content-Type: application/json
```

```json
{
  "status": "manufacturing",
  "statusText": "制作中"
}
```

**成功响应** (200)：
```json
{
  "status": "success",
  "message": "订单状态更新成功",
  "orderId": "MP20260206001",
  "orderStatus": "manufacturing",
  "statusText": "制作中"
}
```

**curl 示例**：
```bash
curl -X PUT "http://localhost:8000/api/miniprogram/orders/123/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "manufacturing", "statusText": "制作中"}'
```

---

### 1.4 获取产品列表

**请求**：
```http
GET /api/miniprogram/products?category_id=1
```

**成功响应** (200)：
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "艺术钥匙扣",
      "price": 99.0,
      "category_id": 1
    }
  ]
}
```

---

## 二、管理后台接口

### 2.1 获取订单列表（需登录）

**请求**：
```http
GET /admin/api/orders?page=1&per_page=20
Cookie: session=xxx
```

**成功响应** (200)：
```json
{
  "status": "success",
  "orders": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  }
}
```

---

### 2.2 更新订单状态（需登录）

**请求**：
```http
PUT /admin/api/orders/123/status
Content-Type: application/json
Cookie: session=xxx
```

```json
{
  "status": "pending_selection",
  "status_text": "待选片"
}
```

---

## 三、选片接口

### 3.1 查询订单（选片用）

**请求**：
```http
POST /api/photo-selection/search-orders
Content-Type: application/json
```

```json
{
  "phone": "13800138000",
  "order_number": "MP20260206001",
  "franchisee_id": 1
}
```

**成功响应** (200)：
```json
{
  "success": true,
  "orders": [
    {
      "order_number": "MP20260206001",
      "status": "paid",
      "customer_name": "张三"
    }
  ]
}
```

---

## 四、支付接口

### 4.1 创建支付订单

**请求**：
```http
POST /api/payment/create
Content-Type: application/json
```

```json
{
  "order_number": "MP20260206001",
  "openid": "oXXXX",
  "total_amount": 99.00
}
```

**成功响应** (200)：
```json
{
  "success": true,
  "payment_params": {
    "timeStamp": "xxx",
    "nonceStr": "xxx",
    "package": "prepay_id=xxx",
    "signType": "RSA",
    "paySign": "xxx"
  }
}
```

---

## 五、错误响应示例

### 5.1 参数错误 (400)

```json
{
  "status": "error",
  "message": "openid不能为空",
  "error_code": "VALIDATION_ERROR"
}
```

### 5.2 未授权 (401)

```json
{
  "status": "error",
  "message": "未登录"
}
```

### 5.3 资源不存在 (404)

```json
{
  "status": "error",
  "message": "订单不存在"
}
```

### 5.4 服务器错误 (500)

```json
{
  "status": "error",
  "message": "服务器内部错误"
}
```

---

## 六、相关文档

- **API错误码说明.md** - 错误码说明
- **小程序API接口说明文档.md** - 小程序API清单
- **管理后台API接口说明文档.md** - 管理后台API接口

---

**最后更新**: 2026-02-06
