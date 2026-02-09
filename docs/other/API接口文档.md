# API接口文档

## 📋 目录

1. [小程序API接口](#小程序api接口)
2. [管理后台API接口](#管理后台api接口)
3. [自拍机对接接口](#自拍机对接接口)
4. [接口调用说明](#接口调用说明)

---

## 一、小程序API接口

### 1.1 产品相关接口

**文件位置：** `app/routes/miniprogram/catalog.py`

| 接口路径 | 方法 | 说明 | 调用位置 |
|---------|------|------|---------|
| `/api/miniprogram/product-categories` | GET | 获取产品分类（一级/二级） | `pages/product/product.js` |
| `/api/miniprogram/products` | GET | 获取产品列表 | `pages/product/product.js` |
| `/api/miniprogram/styles` | GET | 获取风格分类和风格图片 | `pages/product-detail/product-detail.js` |
| `/api/miniprogram/banners` | GET | 获取首页轮播图 | `pages/index/index.js` |

---

### 1.2 订单相关接口

**文件位置：** `app/routes/miniprogram/orders.py`

| 接口路径 | 方法 | 说明 | 调用位置 |
|---------|------|------|---------|
| `/api/miniprogram/orders` | POST | 创建订单 | `pages/payment/payment.js` |
| `/api/miniprogram/orders` | GET | 获取订单列表 | `pages/orders/orders.js` |
| `/api/miniprogram/order/<order_number>` | GET | 获取订单详情 | `pages/order-detail/order-detail.js` |
| `/api/miniprogram/orders/<order_id>/update-order-mode` | POST | 更新订单类型（立即拍摄/立即制作） | `pages/payment/payment.js` |
| `/api/miniprogram/orders/<order_id>/generate-qrcode` | POST | 生成核销二维码 | `pages/order-detail/order-detail.js` |
| `/api/miniprogram/order/upload` | POST | 上传订单图片 | `pages/order-detail/order-detail.js` |

---

### 1.3 用户相关接口

**文件位置：** `app/routes/user_api.py`

| 接口路径 | 方法 | 说明 | 调用位置 |
|---------|------|------|---------|
| `/api/user/visit` | POST | 用户访问追踪 | `utils/visitTracker.js` |
| `/api/user/info` | GET/POST | 获取/更新用户信息 | `pages/mine/mine.js` |
| `/api/user/messages/check` | GET | 检查新消息 | `utils/visitTracker.js` |
| `/api/user/coupons/available-count` | GET | 获取可领取优惠券数量 | `pages/mine/mine.js` |

---

### 1.4 优惠券相关接口

**文件位置：** `app/routes/coupon_api.py`

| 接口路径 | 方法 | 说明 | 调用位置 |
|---------|------|------|---------|
| `/api/coupons/available` | GET | 获取可领取优惠券列表 | `pages/coupons/coupons.js` |
| `/api/coupons/user/<user_id>` | GET | 获取用户优惠券列表 | `pages/coupons/coupons.js` |
| `/api/coupons/get` | POST | 领取优惠券 | `pages/coupons/coupons.js` |

---

### 1.5 支付相关接口

**文件位置：** `app/routes/payment.py`

| 接口路径 | 方法 | 说明 | 调用位置 |
|---------|------|------|---------|
| `/api/payment/create` | POST | 创建支付订单 | `pages/payment/payment.js` |
| `/api/payment/notify` | POST | 支付回调 | 微信支付回调 |

---

### 1.6 其他接口

| 接口路径 | 方法 | 说明 | 调用位置 |
|---------|------|------|---------|
| `/api/miniprogram/promotion` | GET | 获取推广信息 | `pages/promotion/promotion.js` |
| `/api/miniprogram/works` | GET | 获取作品列表 | `pages/works/works.js` |
| `/api/miniprogram/shop` | GET | 获取商城信息 | `pages/shop/shop.js` |

---

## 二、管理后台API接口

### 2.1 产品管理接口

**文件位置：** `app/routes/admin_products_api.py`

| 接口路径 | 方法 | 说明 | 用途 |
|---------|------|------|------|
| `/admin/api/products` | GET | 获取产品列表 | 产品管理页面 |
| `/admin/api/products` | POST | 创建产品 | 新增产品 |
| `/admin/api/products/<product_id>` | GET | 获取产品详情 | 编辑产品 |
| `/admin/api/products/<product_id>` | PUT | 更新产品 | 保存产品修改 |
| `/admin/api/products/<product_id>` | DELETE | 删除产品 | 删除产品 |

---

### 2.2 产品分类管理接口

**文件位置：** `app/routes/admin_product_categories_api.py`

| 接口路径 | 方法 | 说明 | 用途 |
|---------|------|------|------|
| `/admin/api/product-categories` | GET | 获取产品分类列表 | 分类管理 |
| `/admin/api/product-categories` | POST | 创建产品分类 | 新增分类 |
| `/admin/api/product-categories/<category_id>` | PUT | 更新产品分类 | 编辑分类 |
| `/admin/api/product-categories/<category_id>` | DELETE | 删除产品分类 | 删除分类 |

---

### 2.3 风格管理接口

**文件位置：** `app/routes/admin_styles_api.py`

| 接口路径 | 方法 | 说明 | 用途 |
|---------|------|------|------|
| `/admin/api/styles` | GET | 获取风格列表 | 风格管理 |
| `/admin/api/styles` | POST | 创建风格 | 新增风格 |
| `/admin/api/styles/<style_id>` | PUT | 更新风格 | 编辑风格 |
| `/admin/api/styles/<style_id>` | DELETE | 删除风格 | 删除风格 |

---

### 2.4 订单管理接口

**文件位置：** `app/routes/admin_orders.py`

| 接口路径 | 方法 | 说明 | 用途 |
|---------|------|------|------|
| `/admin/api/orders` | GET | 获取订单列表 | 订单管理 |
| `/admin/api/orders/<order_id>` | GET | 获取订单详情 | 查看订单 |
| `/admin/api/orders/<order_id>/status` | PUT | 更新订单状态 | 修改订单状态 |

---

### 2.5 用户管理接口

**文件位置：** `app/routes/admin_users_api.py`

| 接口路径 | 方法 | 说明 | 用途 |
|---------|------|------|------|
| `/admin/api/users` | GET | 获取用户列表 | 用户管理 |
| `/admin/api/users/<user_id>` | GET | 获取用户详情 | 查看用户信息 |

---

### 2.6 其他管理接口

| 文件 | 接口路径 | 说明 |
|------|---------|------|
| `admin_coupon_api.py` | `/admin/api/coupons/*` | 优惠券管理 |
| `admin_promotion_api.py` | `/admin/api/promotion/*` | 推广管理 |
| `admin_homepage_api.py` | `/admin/api/homepage/*` | 首页管理 |
| `admin_dashboard_api.py` | `/admin/api/dashboard/*` | 仪表盘数据 |
| `admin_shop_api.py` | `/admin/api/shop/*` | 商城管理 |
| `admin_groupon_api.py` | `/admin/api/groupon/*` | 团购管理 |
| `admin_third_party_groupon_api.py` | `/admin/api/third-party-groupon/*` | 第三方团购管理 |

---

## 三、自拍机对接接口

### 3.1 二维码核销接口

**文件位置：** `app/routes/qrcode_api.py`

| 接口路径 | 方法 | 说明 | 用途 |
|---------|------|------|------|
| `/api/qrcode/generate` | POST | 生成核销二维码 | 生成订单核销码 |
| `/api/qrcode/verify` | POST | 验证核销二维码 | 自拍机扫码核销 |
| `/api/qrcode/status` | GET | 查询二维码状态 | 查询核销状态 |

**核销流程：**
1. 用户在小程序生成订单核销二维码
2. 自拍机扫描二维码
3. 自拍机调用 `/api/qrcode/verify` 验证并核销
4. 订单状态更新为"已核销"

---

### 3.2 订单状态更新接口

**文件位置：** `app/routes/miniprogram/orders.py`

| 接口路径 | 方法 | 说明 | 用途 |
|---------|------|------|------|
| `/api/miniprogram/orders/<order_id>/status` | PUT | 更新订单状态 | 自拍机更新订单状态 |
| `/api/miniprogram/orders/<order_id>/upload-image` | POST | 上传拍摄图片 | 自拍机上传拍摄结果 |

**自拍机对接流程：**
1. 自拍机扫描核销二维码
2. 验证二维码有效性
3. 开始拍摄流程
4. 拍摄完成后上传图片到 `/api/miniprogram/orders/<order_id>/upload-image`
5. 更新订单状态为"拍摄完成"

---

### 3.3 设备状态接口

**文件位置：** `app/routes/admin_polling_config_api.py`

| 接口路径 | 方法 | 说明 | 用途 |
|---------|------|------|------|
| `/admin/api/polling/config` | GET | 获取轮询配置 | 获取设备轮询配置 |
| `/admin/api/polling/config` | POST | 更新轮询配置 | 配置设备轮询参数 |

**说明：** 用于配置自拍机的任务轮询和状态同步。

---

## 四、接口调用说明

### 4.1 小程序调用方式

**使用工具函数：** `utils/api.js`

```javascript
const config = require('../../config');
const { convertToHttps } = require('../../utils/api');

// 调用API
wx.request({
  url: `${config.getApiUrl()}/api/miniprogram/products`,
  method: 'GET',
  success: (res) => {
    console.log(res.data);
  }
});
```

### 4.2 接口认证

**小程序接口：**
- 使用 `openid` 或 `userId` 进行用户认证
- 通过 `wx.request` 的 `header` 传递认证信息

**管理后台接口：**
- 使用Session认证
- 需要管理员登录

### 4.3 错误处理

**统一错误格式：**
```json
{
  "success": false,
  "message": "错误信息",
  "code": "ERROR_CODE"
}
```

**成功响应格式：**
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}
```

---

## 五、接口文件位置汇总

### 小程序接口文件

| 文件 | 路径 | 说明 |
|------|------|------|
| `catalog.py` | `app/routes/miniprogram/catalog.py` | 产品、风格、轮播图 |
| `orders.py` | `app/routes/miniprogram/orders.py` | 订单相关 |
| `common.py` | `app/routes/miniprogram/common.py` | 通用接口 |
| `promotion.py` | `app/routes/miniprogram/promotion.py` | 推广相关 |
| `works.py` | `app/routes/miniprogram/works.py` | 作品相关 |
| `shop.py` | `app/routes/miniprogram/shop.py` | 商城相关 |

### 管理后台接口文件

| 文件 | 路径 | 说明 |
|------|------|------|
| `admin_products_api.py` | `app/routes/admin_products_api.py` | 产品管理 |
| `admin_product_categories_api.py` | `app/routes/admin_product_categories_api.py` | 产品分类管理 |
| `admin_styles_api.py` | `app/routes/admin_styles_api.py` | 风格管理 |
| `admin_orders.py` | `app/routes/admin_orders.py` | 订单管理 |
| `admin_users_api.py` | `app/routes/admin_users_api.py` | 用户管理 |
| `admin_coupon_api.py` | `app/routes/admin_coupon_api.py` | 优惠券管理 |

### 自拍机对接接口文件

| 文件 | 路径 | 说明 |
|------|------|------|
| `qrcode_api.py` | `app/routes/qrcode_api.py` | 二维码生成和核销 |
| `admin_polling_config_api.py` | `app/routes/admin_polling_config_api.py` | 设备轮询配置 |

---

## 六、接口调用示例

### 6.1 小程序获取产品列表

```javascript
// pages/product/product.js
const config = require('../../config');

Page({
  loadProducts() {
    wx.request({
      url: `${config.getApiUrl()}/api/miniprogram/products`,
      method: 'GET',
      data: {
        category_id: this.data.categoryId
      },
      success: (res) => {
        if (res.data.success) {
          this.setData({
            products: res.data.data
          });
        }
      }
    });
  }
});
```

### 6.2 创建订单

```javascript
// pages/payment/payment.js
const OrderCreator = require('../../utils/payment/order-creator');

// 创建订单
OrderCreator.createOrder(cartItems, couponId)
  .then(order => {
    console.log('订单创建成功:', order);
  })
  .catch(err => {
    console.error('订单创建失败:', err);
  });
```

### 6.3 生成核销二维码

```javascript
// pages/order-detail/order-detail.js
const config = require('../../config');

showQRCode() {
  wx.request({
    url: `${config.getApiUrl()}/api/miniprogram/orders/${orderId}/generate-qrcode`,
    method: 'POST',
    success: (res) => {
      if (res.data.success) {
        // 显示二维码
        this.setData({
          qrcodeUrl: res.data.data.qrcode_url
        });
      }
    }
  });
}
```

---

**最后更新：** 2026-01-31
