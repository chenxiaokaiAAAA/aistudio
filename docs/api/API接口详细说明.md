# API 接口详细说明

> 按模板格式补充各接口的请求参数、类型、必填、响应格式。  
> 本文档聚焦核心接口，完整清单见 `API请求响应示例.md` 及 Swagger `/docs`。

---

## 一、小程序核心接口

### 1.1 创建订单

**接口路径**: `POST /api/miniprogram/orders`  
**请求方法**: `POST`  
**功能说明**: 小程序用户创建订单

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| openid | string | 是 | 用户 OpenID |
| items | array | 是 | 订单项列表 |
| items[].product_id | int | 是 | 产品ID |
| items[].size_id | int | 是 | 尺寸ID |
| items[].style_id | int | 是 | 风格ID |
| items[].quantity | int | 是 | 数量 |
| items[].price | float | 是 | 单价 |
| customer_name | string | 是 | 客户姓名 |
| customer_phone | string | 是 | 客户电话 |
| order_mode | string | 否 | 订单模式：making（立即制作）/ shooting（立即拍摄） |
| franchisee_id | int | 否 | 加盟商ID（扫码下单时） |

**成功响应** (200):
```json
{
  "status": "success",
  "order_number": "MP20260206001"
}
```

**失败响应** (400/500):
```json
{
  "status": "error",
  "message": "错误信息"
}
```

---

### 1.2 核销检查（安卓APP）

**接口路径**: `GET /api/miniprogram/order/check`  
**请求方法**: `GET`  
**功能说明**: 安卓APP扫码后检查订单是否可核销

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| orderId / order_id | string | 是 | 订单号 |
| machineSerialNumber / machine_serial_number / selfie_machine_id | string | 建议 | 设备序列号（用于关联加盟商） |

**成功响应** (200):
```json
{
  "success": true,
  "order": {
    "order_id": "MP20260206001",
    "order_number": "MP20260206001",
    "customer_name": "张三",
    "customer_phone": "13800138000",
    "product_name": "证件照",
    "status": "paid",
    "is_paid": true,
    "amount": 29.9,
    "store_name": "厦门SM商城",
    "machine_serial_number": "XMSM_001",
    "machine_name": "SM商城-1号机"
  }
}
```

**失败响应** (400/404/500):
```json
{
  "success": false,
  "message": "订单不存在"
}
```

---

### 1.3 上传拍摄照片（安卓APP）

**接口路径**: `POST /api/miniprogram/order/upload`  
**请求方法**: `POST`  
**Content-Type**: `multipart/form-data`  
**功能说明**: 安卓APP拍摄完成后上传照片

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| orderId / order_id | string | 是 | 订单号 |
| machineSerialNumber / machine_serial_number | string | 建议 | 设备序列号 |
| photos | file[] | 是 | 图片文件数组（字段名必须是 photos） |

**成功响应** (200):
```json
{
  "success": true,
  "orderId": "MP20260206001",
  "uploadedFiles": [{"filename": "xxx.jpg", "path": "/uploads/xxx.jpg"}],
  "message": "照片上传成功"
}
```

---

### 1.4 获取订单列表

**接口路径**: `GET /api/miniprogram/orders`  
**请求方法**: `GET`  
**功能说明**: 按 openid 获取用户订单列表

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| openid | string | 是 | 用户 OpenID |
| page | int | 否 | 页码，默认 1 |
| per_page | int | 否 | 每页条数，默认 20 |

**成功响应** (200):
```json
{
  "status": "success",
  "orders": [
    {
      "orderId": "MP20260206001",
      "orderId_db": 123,
      "customerName": "张三",
      "status": "paid",
      "statusText": "待制作",
      "totalPrice": 99.0,
      "createTime": "2026-02-06T10:00:00"
    }
  ]
}
```

---

## 二、选片接口

### 2.1 查询订单（选片用）

**接口路径**: `POST /api/photo-selection/search-orders`  
**请求方法**: `POST`  
**功能说明**: 通过手机号或订单号查询订单

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| phone | string | 二选一 | 手机号 |
| order_number | string | 二选一 | 订单号 |
| franchisee_id | int | 否 | 加盟商ID（筛选） |

**成功响应** (200):
```json
{
  "success": true,
  "orders": [
    {
      "order_number": "MP20260206001",
      "status": "paid",
      "customer_name": "张三",
      "customer_phone": "13800138000"
    }
  ]
}
```

---

## 三、支付接口

### 3.1 创建支付订单

**接口路径**: `POST /api/payment/create`  
**请求方法**: `POST`  
**功能说明**: 创建微信支付预支付订单

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| order_number | string | 是 | 订单号 |
| openid | string | 是 | 用户 OpenID |
| total_amount | float | 是 | 支付金额（元） |

**成功响应** (200):
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

## 四、错误码

| 错误码 | 说明 |
|--------|------|
| 400 | 参数错误 |
| 401 | 未授权 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 五、相关文档

- **API请求响应示例.md** - 更多接口示例与 curl
- **API错误码说明.md** - 错误码详解
- **Swagger** - 启动服务后访问 `/docs` 查看完整接口

---

**最后更新**: 2026-02-09
