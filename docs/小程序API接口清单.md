# 小程序API接口清单

> 本文档列出了小程序需要对接的所有后端API接口，用于UI重新设计时的接口对接参考。

## 基础配置

- **API基础路径**: `/api/miniprogram` (小程序专用接口)
- **用户API路径**: `/api/user` (用户相关接口)
- **支付API路径**: `/api/payment` (支付相关接口)
- **选片API路径**: `/api/photo-selection` (选片相关接口)

---

## 一、用户认证与注册 (User API)

### 1.1 获取OpenID
- **接口**: `POST /api/user/openid`
- **功能**: 通过微信登录code获取用户openid
- **请求参数**:
  ```json
  {
    "code": "微信登录code"
  }
  ```
- **返回**: `{success: true, openid: "xxx"}`

### 1.2 用户注册
- **接口**: `POST /api/user/register`
- **功能**: 注册新用户
- **请求参数**:
  ```json
  {
    "openid": "用户openid",
    "phone": "手机号（可选）",
    "nickname": "昵称（可选）"
  }
  ```
- **返回**: `{success: true, userId: "xxx"}`

### 1.3 检查用户是否存在
- **接口**: `POST /api/user/check`
- **功能**: 检查用户是否已注册
- **请求参数**:
  ```json
  {
    "openid": "用户openid"
  }
  ```
- **返回**: `{exists: true/false}`

### 1.4 更新用户信息
- **接口**: `POST /api/user/update-info`
- **功能**: 更新用户个人信息
- **请求参数**:
  ```json
  {
    "openid": "用户openid",
    "nickname": "昵称",
    "avatar": "头像URL"
  }
  ```

### 1.5 绑定/更新手机号
- **接口**: `POST /api/user/phone`
- **功能**: 绑定或更新手机号
- **请求参数**:
  ```json
  {
    "openid": "用户openid",
    "phone": "手机号"
  }
  ```

### 1.6 发送短信验证码
- **接口**: `POST /api/user/sendSmsCode`
- **功能**: 发送短信验证码
- **请求参数**:
  ```json
  {
    "phone": "手机号"
  }
  ```

### 1.7 验证短信验证码
- **接口**: `POST /api/user/verifySmsCode`
- **功能**: 验证短信验证码
- **请求参数**:
  ```json
  {
    "phone": "手机号",
    "code": "验证码"
  }
  ```

### 1.8 更新手机号
- **接口**: `POST /api/user/update-phone`
- **功能**: 更新用户手机号
- **请求参数**:
  ```json
  {
    "openid": "用户openid",
    "phone": "新手机号"
  }
  ```

---

## 二、订单管理 (Orders API)

### 2.1 提交订单
- **接口**: `POST /api/miniprogram/orders`
- **功能**: 创建新订单
- **请求参数**:
  ```json
  {
    "openid": "用户openid",
    "items": [
      {
        "product_id": 1,
        "size_id": 1,
        "style_id": 1,
        "quantity": 1,
        "price": 99.00
      }
    ],
    "customer_name": "客户姓名",
    "customer_phone": "客户电话",
    "order_mode": "shooting|making",
    "franchisee_id": 1
  }
  ```
- **返回**: `{status: "success", order_number: "MP20260101XXX"}`

### 2.2 获取订单列表
- **接口**: `GET /api/miniprogram/orders`
- **功能**: 获取用户订单列表
- **请求参数**:
  - `openid`: 用户openid
  - `phone`: 手机号（可选）
  - `userId`: 用户ID（可选）
- **返回**: `{status: "success", orders: [...]}`

### 2.3 获取订单详情
- **接口**: `GET /api/miniprogram/order/<order_number>`
- **功能**: 获取单个订单详情
- **返回**: `{status: "success", order: {...}}`

### 2.4 检查订单状态
- **接口**: `GET /api/miniprogram/order/check`
- **功能**: 检查订单状态
- **请求参数**:
  - `order_number`: 订单号
  - `phone`: 手机号

### 2.5 上传订单图片（Android APP）
- **接口**: `POST /api/miniprogram/order/upload`
- **功能**: 上传订单原图（用于立即拍摄订单）
- **请求参数**: FormData
  - `order_number`: 订单号
  - `images`: 图片文件数组

### 2.6 更新订单图片
- **接口**: `PUT /api/miniprogram/orders/<order_id>/images`
- **功能**: 更新订单图片
- **请求参数**:
  ```json
  {
    "images": ["url1", "url2"]
  }
  ```

### 2.7 删除订单图片
- **接口**: `DELETE /api/miniprogram/orders/<order_id>/images/delete`
- **功能**: 删除订单图片
- **请求参数**:
  ```json
  {
    "image_url": "图片URL"
  }
  ```

### 2.8 更新订单状态
- **接口**: `PUT /api/miniprogram/orders/<order_id>/status`
- **功能**: 更新订单状态
- **请求参数**:
  ```json
  {
    "status": "pending_selection|selection_completed|..."
  }
  ```

### 2.9 设置订单为手动模式
- **接口**: `POST /api/miniprogram/orders/<order_id>/set-manual`
- **功能**: 将订单设置为手动处理模式

### 2.10 更新订单类型
- **接口**: `POST /api/miniprogram/orders/<order_id>/update-order-mode`
- **功能**: 更新订单类型（立即拍摄/立即制作）
- **请求参数**:
  ```json
  {
    "order_mode": "shooting|making"
  }
  ```

### 2.11 生成订单二维码
- **接口**: `POST /api/miniprogram/orders/<order_id>/generate-qrcode`
- **功能**: 生成订单核销二维码
- **返回**: `{qrcode: "base64图片"}`

### 2.12 获取订单二维码
- **接口**: `GET /api/miniprogram/order/qrcode`
- **功能**: 获取订单二维码
- **请求参数**:
  - `order_id`: 订单ID

---

## 三、商品与风格 (Catalog API)

### 3.1 获取风格列表
- **接口**: `GET /api/miniprogram/styles`
- **功能**: 获取所有风格分类和风格图片
- **返回**: `{status: "success", data: {categories: [...], styles: [...]}}`

### 3.2 刷新风格列表
- **接口**: `GET /api/miniprogram/styles/refresh`
- **功能**: 强制刷新风格列表（清除缓存）

### 3.3 获取产品分类
- **接口**: `GET /api/miniprogram/product-categories`
- **功能**: 获取产品分类列表
- **返回**: `{status: "success", categories: [...]}`

### 3.4 获取产品列表
- **接口**: `GET /api/miniprogram/products`
- **功能**: 获取产品列表
- **请求参数**:
  - `category_id`: 分类ID（可选）
  - `subcategory_id`: 子分类ID（可选）
- **返回**: `{status: "success", data: [...]}`

### 3.5 获取首页轮播图
- **接口**: `GET /api/miniprogram/banners`
- **功能**: 获取首页轮播图
- **返回**: `{status: "success", banners: [...]}`

### 3.6 获取首页配置
- **接口**: `GET /api/miniprogram/homepage-config`
- **功能**: 获取首页配置信息
- **返回**: `{status: "success", config: {...}}`

---

## 四、作品管理 (Works API)

### 4.1 获取作品列表
- **接口**: `GET /api/miniprogram/works`
- **功能**: 获取用户作品列表
- **请求参数**:
  - `openid`: 用户openid
  - `phone`: 手机号（可选）
- **返回**: `{status: "success", works: [...]}`

---

## 五、支付相关 (Payment API)

### 5.1 创建支付订单
- **接口**: `POST /api/payment/create`
- **功能**: 创建微信支付订单
- **请求参数**:
  ```json
  {
    "order_number": "订单号",
    "openid": "用户openid",
    "total_amount": 99.00
  }
  ```
- **返回**: `{success: true, payment_params: {...}}` (微信支付参数)

### 5.2 完成免费订单
- **接口**: `POST /api/payment/complete-free-order`
- **功能**: 完成免费订单（金额为0的订单）
- **请求参数**:
  ```json
  {
    "order_number": "订单号"
  }
  ```

### 5.3 支付回调（内部）
- **接口**: `POST /api/payment/notify`
- **功能**: 微信支付回调（小程序无需调用）

---

## 六、优惠券 (Coupons API)

### 6.1 获取用户优惠券列表
- **接口**: `GET /api/coupons/user/<userId>`
- **功能**: 获取用户可用的优惠券列表
- **返回**: `{status: "success", coupons: [...]}`

### 6.2 获取可用优惠券数量
- **接口**: `GET /api/user/coupons/available-count`
- **功能**: 获取用户可用优惠券数量
- **请求参数**:
  - `openid`: 用户openid
- **返回**: `{count: 5}`

---

## 七、推广相关 (Promotion API)

### 7.1 获取推广码
- **接口**: `GET /api/miniprogram/promotion-code`
- **功能**: 获取用户推广码
- **请求参数**:
  - `phone`: 手机号
- **返回**: `{status: "success", promotion_code: "XXX"}`

### 7.2 检查推广资格
- **接口**: `POST /api/user/check-promotion-eligibility`
- **功能**: 检查用户是否有推广资格
- **请求参数**:
  ```json
  {
    "userId": "用户ID",
    "openId": "用户openid"
  }
  ```

### 7.3 更新推广资格
- **接口**: `POST /api/user/update-promotion-eligibility`
- **功能**: 更新用户推广资格

### 7.4 获取佣金信息
- **接口**: `GET /api/user/commission`
- **功能**: 获取用户佣金信息
- **请求参数**:
  - `openid`: 用户openid
- **返回**: `{total_commission: 100.00, ...}`

### 7.5 获取提现记录
- **接口**: `GET /api/user/withdrawals`
- **功能**: 获取用户提现记录
- **请求参数**:
  - `openid`: 用户openid

---

## 八、消息通知 (Messages API)

### 8.1 获取消息列表
- **接口**: `GET /api/user/messages`
- **功能**: 获取用户消息列表
- **请求参数**:
  - `openid`: 用户openid
- **返回**: `{messages: [...]}`

### 8.2 获取未读消息数
- **接口**: `GET /api/user/messages/unread-count`
- **功能**: 获取未读消息数量
- **请求参数**:
  - `openid`: 用户openid
- **返回**: `{count: 5}`

### 8.3 标记消息已读
- **接口**: `POST /api/user/messages/read`
- **功能**: 标记消息为已读
- **请求参数**:
  ```json
  {
    "message_id": 1,
    "openid": "用户openid"
  }
  ```

### 8.4 检查消息
- **接口**: `GET /api/user/messages/check`
- **功能**: 检查是否有新消息

### 8.5 订阅消息状态更新
- **接口**: `POST /api/user/subscription-status`
- **功能**: 更新用户订阅消息状态
- **请求参数**:
  ```json
  {
    "openId": "用户openid",
    "isSubscribed": true,
    "subscriptionResult": {...}
  }
  ```

---

## 九、选片相关 (Photo Selection API)

### 9.1 验证选片Token
- **接口**: `POST /api/photo-selection/verify-token`
- **功能**: 验证选片登录token
- **请求参数**:
  ```json
  {
    "token": "选片token",
    "openid": "用户openid"
  }
  ```
- **返回**: `{success: true, orders: [...]}`

### 9.2 查询订单（选片用）
- **接口**: `POST /api/photo-selection/search-orders`
- **功能**: 通过手机号或订单号查询订单（用于选片）
- **请求参数**:
  ```json
  {
    "phone": "手机号",
    "order_number": "订单号",
    "franchisee_id": 1
  }
  ```
- **返回**: `{success: true, orders: [...]}`

---

## 十、团购相关 (Groupon API)

### 10.1 团购核销
- **接口**: `POST /api/miniprogram/groupon/verify`
- **功能**: 核销团购券
- **请求参数**:
  ```json
  {
    "code": "团购码",
    "staff_id": "员工ID"
  }
  ```

### 10.2 检查员工权限
- **接口**: `GET /api/miniprogram/groupon/check-staff`
- **功能**: 检查员工是否有核销权限
- **请求参数**:
  - `staff_id`: 员工ID

### 10.3 获取团购套餐
- **接口**: `GET /api/miniprogram/groupon/packages`
- **功能**: 获取团购套餐列表

### 10.4 第三方团购查询
- **接口**: `POST /api/miniprogram/third-party-groupon/query`
- **功能**: 查询第三方团购信息

### 10.5 第三方团购核销
- **接口**: `POST /api/miniprogram/third-party-groupon/verify`
- **功能**: 核销第三方团购

### 10.6 第三方团购兑换
- **接口**: `POST /api/miniprogram/third-party-groupon/redeem`
- **功能**: 兑换第三方团购

---

## 十一、门店相关 (Shop API)

### 11.1 获取门店产品列表
- **接口**: `GET /api/miniprogram/shop/products`
- **功能**: 获取门店产品列表
- **请求参数**:
  - `franchisee_id`: 门店ID（可选）

### 11.2 获取门店产品详情
- **接口**: `GET /api/miniprogram/shop/products/<product_id>`
- **功能**: 获取门店产品详情

### 11.3 创建门店订单
- **接口**: `POST /api/miniprogram/shop/orders`
- **功能**: 创建门店订单

### 11.4 获取门店订单列表
- **接口**: `GET /api/miniprogram/shop/orders`
- **功能**: 获取门店订单列表

---

## 十二、数字头像 (Digital Avatar API)

### 12.1 获取数字头像列表
- **接口**: `GET /api/miniprogram/digital-avatar/list`
- **功能**: 获取数字头像列表

---

## 十三、分享奖励 (Share Reward API)

### 13.1 记录分享
- **接口**: `POST /api/miniprogram/share/record`
- **功能**: 记录用户分享行为

### 13.2 领取分享奖励
- **接口**: `POST /api/miniprogram/share/reward`
- **功能**: 领取分享奖励

---

## 十四、媒体文件 (Media API)

### 14.1 获取原图
- **接口**: `GET /api/miniprogram/media/original/<filename>`
- **功能**: 获取订单原图

### 14.2 获取效果图
- **接口**: `GET /api/miniprogram/media/final/<filename>`
- **功能**: 获取订单效果图

### 14.3 获取静态图片
- **接口**: `GET /api/miniprogram/static/images/<path:filename>`
- **功能**: 获取静态资源图片

### 14.4 上传文件
- **接口**: `POST /api/miniprogram/upload`
- **功能**: 上传文件
- **请求参数**: FormData
  - `file`: 文件

---

## 十五、访问统计 (Visit API)

### 15.1 记录访问
- **接口**: `POST /api/user/visit`
- **功能**: 记录用户访问行为
- **请求参数**:
  ```json
  {
    "openid": "用户openid",
    "page": "页面路径",
    "referrer": "来源"
  }
  ```

### 15.2 获取访问统计
- **接口**: `GET /api/user/visit/stats`
- **功能**: 获取访问统计数据（管理员）

---

## 十六、退款相关 (Refund API)

### 16.1 申请退款
- **接口**: `POST /api/miniprogram/refund/request`
- **功能**: 申请退款
- **请求参数**:
  ```json
  {
    "order_number": "订单号",
    "phone": "手机号",
    "reason": "退款原因"
  }
  ```

### 16.2 检查订单（退款用）
- **接口**: `GET /api/miniprogram/refund/check-order`
- **功能**: 检查订单是否可以退款
- **请求参数**:
  - `order_number`: 订单号
  - `phone`: 手机号

### 16.3 检查退款权限
- **接口**: `GET /api/miniprogram/refund/check-permission`
- **功能**: 检查用户是否有退款权限

---

## 接口统计

### 按模块分类统计：

1. **用户认证与注册**: 8个接口
2. **订单管理**: 12个接口
3. **商品与风格**: 6个接口
4. **作品管理**: 1个接口
5. **支付相关**: 3个接口
6. **优惠券**: 2个接口
7. **推广相关**: 5个接口
8. **消息通知**: 5个接口
9. **选片相关**: 2个接口
10. **团购相关**: 6个接口
11. **门店相关**: 4个接口
12. **数字头像**: 1个接口
13. **分享奖励**: 2个接口
14. **媒体文件**: 4个接口
15. **访问统计**: 2个接口
16. **退款相关**: 3个接口

**总计**: 约 **66个API接口**

---

## 注意事项

1. **认证方式**: 大部分接口需要 `openid` 参数，部分接口支持 `phone` 或 `userId`
2. **错误处理**: 所有接口返回格式统一，包含 `status: "success"` 或 `success: true`
3. **图片URL**: 图片URL使用 `config.getStaticUrl()` 或 `config.getMediaUrl()` 拼接
4. **环境配置**: 开发环境使用 `config.getApiBaseUrl()`，生产环境自动切换
5. **支付回调**: 支付回调接口由微信服务器调用，小程序无需处理

---

## 接口调用示例

```javascript
// 使用 config.js 中的配置
const config = require('../../config');

// 调用接口
wx.request({
  url: `${config.getApiBaseUrl()}/orders`,
  method: 'GET',
  data: {
    openid: wx.getStorageSync('openid')
  },
  success: function(res) {
    if (res.data.status === 'success') {
      // 处理成功响应
    }
  }
});
```

---

**最后更新**: 2026-02-03
**维护者**: AI Assistant
