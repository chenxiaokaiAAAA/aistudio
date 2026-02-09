# API接口文档

> **文档索引**：详见 `docs/api/API文档索引与复用说明.md`  
> **错误码**：`docs/api/API错误码说明.md` | **请求示例**：`docs/api/API请求响应示例.md`

## 📋 目录

1. [小程序API接口](#一小程序api接口)
2. [管理后台API接口](#二管理后台api接口)
3. [自拍机对接接口](#三自拍机对接接口)
4. [加盟商/选片/AI/美图接口](#四加盟商选片ai美图接口)
5. [接口调用说明](#五接口调用说明)

**路径说明**：管理后台存在 `/admin/`（页面）与 `/api/admin/`（纯 API）两类路径。

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
| `/admin/products` | GET | 产品管理页面 | 产品列表（HTML） |
| `/admin/sizes` | GET/POST | 尺寸配置页面 | 产品尺寸管理 |
| `/api/admin/products/<product_id>` | GET | 获取产品详情 | 编辑产品（JSON） |

---

### 2.2 产品分类管理接口

**文件位置：** `app/routes/admin_product_categories_api.py`

| 接口路径 | 方法 | 说明 |
|---------|------|------|
| `/api/admin/product-categories` | GET/POST | 一级分类列表/创建 |
| `/api/admin/product-subcategories` | GET/POST | 二级分类列表/创建 |

---

### 2.3 风格管理接口

**文件位置：** `app/routes/admin_styles_api.py`（含 categories、workflow、images 子模块）

| 接口路径 | 方法 | 说明 |
|---------|------|------|
| `/api/admin/styles/categories` | GET/POST | 风格分类列表/创建 |
| `/api/admin/styles/subcategories` | GET/POST | 风格子分类 |

---

### 2.4 订单管理接口

**文件位置：** `app/routes/admin_orders_*.py`

| 接口路径 | 方法 | 说明 |
|---------|------|------|
| `/admin/orders` | GET | 订单列表页面 |
| `/admin/orders/export` | GET | 导出订单 |
| `/admin/order/<order_id>` | GET/POST | 订单详情页面 |
| `/admin/orders/batch-update-status` | POST | 批量更新状态 |

---

### 2.5 用户管理接口

**文件位置：** `app/routes/admin_profile.py`、`admin_users_api.py`

| 接口路径 | 方法 | 说明 |
|---------|------|------|
| `/api/admin/users` | GET/POST | 用户列表/新增 |
| `/api/admin/users/<user_id>` | GET/PUT/DELETE | 用户详情/更新/删除 |
| `/api/admin/profile` | GET/POST | 当前账户信息 |

---

### 2.6 其他管理接口（详细）

#### 优惠券管理 `admin_coupon_api.py` → `/api/admin/coupons`

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/admin/coupons/create` | POST | 创建优惠券 |
| `/api/admin/coupons/<id>` | GET | 获取优惠券详情 |
| `/api/admin/coupons/<id>/update` | PUT | 更新优惠券 |
| `/api/admin/coupons/<id>/delete` | DELETE | 删除优惠券 |

#### 仪表盘 `admin_dashboard_api.py` → `/api/admin/dashboard`

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/admin/dashboard/revenue` | GET | 营收统计 |
| `/api/admin/dashboard/processing-orders` | GET | 处理中订单 |
| `/api/admin/dashboard/completed-orders` | GET | 已完成订单 |
| `/api/admin/dashboard/error-orders` | GET | 异常订单 |

#### 首页管理 `admin_homepage_api.py` → `/api/admin/homepage`

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/admin/homepage/banners` | GET/POST | 轮播图列表/创建 |
| `/api/admin/homepage/banners/<id>` | PUT/DELETE | 更新/删除轮播图 |
| `/api/admin/homepage/config` | GET/PUT | 首页配置 |
| `/api/admin/homepage/category-navs` | GET/POST | 分类导航 |
| `/api/admin/homepage/product-sections` | GET/POST | 产品区块 |

#### 系统配置 `admin_system_api.py` → `/api/admin/system-config`

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/admin/system-config` | GET | 获取系统配置 |
| `/api/admin/system-config/comfyui` | POST | ComfyUI 配置 |
| `/api/admin/system-config/concurrency` | POST | 并发与队列配置 |
| `/api/admin/system-config/image-paths` | POST | 图片路径配置 |

#### 订单操作（页面表单）`admin_orders_*`

| 路径 | 方法 | 说明 |
|------|------|------|
| `/admin/orders/batch-update-status` | POST | 批量更新订单状态 |
| `/admin/orders/get-customer-info` | GET | 获取客户信息 |
| `/admin/order/<id>/send-to-printer` | POST | 发送到冲印 |
| `/admin/order/<id>/manual-logistics` | POST | 录入快递单号 |

#### 推广管理 `admin_promotion_api.py` → `/admin/api/promotion`

| 路径 | 方法 | 说明 |
|------|------|------|
| `/admin/api/promotion/commissions` | GET | 分佣记录列表 |
| `/admin/api/promotion/users` | GET | 推广用户列表 |
| `/admin/api/promotion/user/own-orders` | GET | 推广用户自有订单 |
| `/admin/api/promotion/visits` | GET | 访问记录 |
| `/admin/api/promotion/visits/detail` | GET | 访问详情 |
| `/admin/api/promotion/commission/<id>` | GET | 分佣详情 |
| `/admin/api/promotion/commission/<id>` | DELETE | 删除分佣 |
| `/admin/api/promotion/user/<user_id>` | DELETE | 删除推广用户 |

#### 团购管理 `admin_groupon_api.py` → `/api/admin/groupon`

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/admin/groupon/verify` | POST | 团购订单核销（生成随机码免拍券） |
| `/api/admin/groupon/verify/list` | GET | 核销记录列表 |

#### 退款审核 `admin_refund_api.py` → `/api/admin/refund`

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/admin/refund/list` | GET | 退款申请列表 |
| `/api/admin/refund/approve/<order_id>` | POST | 批准退款 |
| `/api/admin/refund/reject/<order_id>` | POST | 拒绝退款 |

#### 其他

| 文件 | 前缀 | 说明 |
|------|------|------|
| `admin_shop_api.py` | `/admin/shop` | 商城产品/订单 |
| `admin_profile.py` | `/api/admin/profile` | 账户与用户管理 |

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

## 四、加盟商/选片/AI/美图接口

> **详细文档**：  
> - 加盟商与选片：`docs/api/加盟商与选片API说明.md`  
> - AI 任务与美图：`docs/api/AI任务与美图API说明.md`

### 4.1 加盟商 API

| 路径 | 方法 | 说明 |
|------|------|------|
| `/franchisee/api/check-quota` | POST | 检查额度 |
| `/franchisee/api/deduct-quota` | POST | 扣除额度 |
| `/franchisee/api/account-info/<qr_code>` | GET | 账户信息（扫码） |
| `/franchisee/api/cancel-order/<order_id>` | POST | 取消订单 |

### 4.2 选片 API

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/photo-selection/search-orders` | POST | 通过手机号/订单号查询订单 |
| `/api/photo-selection/verify-token` | POST | 验证选片 Token |

### 4.3 AI 任务 API

| 路径 | 方法 | 说明 |
|------|------|------|
| `/admin/ai/api/tasks` | GET | 获取 AI 任务列表 |
| `/admin/ai/api/tasks/<task_id>` | GET | 获取任务详情 |

### 4.4 美图 API

| 路径 | 方法 | 说明 |
|------|------|------|
| `/admin/meitu/api/config` | GET/POST | 美图 API 配置 |
| `/admin/meitu/api/presets` | GET/POST | 预设列表/创建 |
| `/admin/meitu/api/tasks` | GET | 美颜任务列表 |
| `/admin/meitu/api/tasks/<id>/recheck` | POST | 重新查询任务结果 |

---

## 五、接口调用说明

### 5.1 小程序调用方式

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

### 5.2 接口认证

**小程序接口：**
- 使用 `openid` 或 `userId` 进行用户认证
- 通过 `wx.request` 的 `header` 传递认证信息

**管理后台接口：**
- 使用Session认证
- 需要管理员登录

### 5.3 错误处理

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

## 六、接口文件位置汇总

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

## 七、接口调用示例

### 7.1 小程序获取产品列表

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

### 7.2 创建订单

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

### 7.3 生成核销二维码

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

---

## 八、相关文档

- **docs/api/API文档索引与复用说明.md** - 文档索引与路径说明
- **docs/api/API错误码说明.md** - 错误码与处理建议
- **docs/api/API请求响应示例.md** - 请求/响应示例与 curl
- **小程序API接口说明文档.md** - 小程序 66 个接口清单

---

**最后更新：** 2026-02-06
