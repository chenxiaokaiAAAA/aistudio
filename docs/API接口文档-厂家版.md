# AI拍照机系统 API接口文档（厂家版）

## 📋 文档说明

本文档提供给厂家，详细说明小程序和Android App调用的所有API接口。

**生产环境地址**：`https://moeart.cc`  
**API基础路径**：`/api/miniprogram`  
**请求格式**：JSON  
**响应格式**：JSON

---

## 目录

1. [小程序API接口](#小程序api接口)
2. [Android App API接口](#android-app-api接口)
3. [订单状态说明](#订单状态说明)
4. [错误处理](#错误处理)
5. [接口测试](#接口测试)

---

## 小程序API接口

### 1. 获取用户OpenID

**接口**：`GET /api/user/openid`

**说明**：小程序登录后获取用户唯一标识

**请求参数**：
```json
{
  "code": "微信登录code（从wx.login获取）"
}
```

**响应示例**：
```json
{
  "success": true,
  "openid": "oUpF8uMuAJO_M2pxb1Q9zNjWeS6o"
}
```

**错误响应**：
```json
{
  "success": false,
  "message": "获取OpenID失败"
}
```

---

### 2. 获取产品列表

**接口**：`GET /api/miniprogram/products`

**说明**：获取所有可用产品配置，包括尺寸、颜色等选项

**请求参数**：无

**响应示例**：
```json
{
  "status": "success",
  "products": [
    {
      "id": 1,
      "name": "证件照",
      "productType": "idphoto",
      "price": 60.0,
      "sizes": [
        {
          "id": 1,
          "name": "1寸",
          "price": 60.0
        },
        {
          "id": 2,
          "name": "2寸",
          "price": 60.0
        }
      ],
      "color_options": ["红底", "蓝底", "白底"],
      "bound_style_category_codes": ["style1", "style2"]
    }
  ]
}
```

---

### 3. 获取风格列表

**接口**：`GET /api/miniprogram/styles`

**说明**：获取风格分类和图片列表，支持按产品ID过滤

**请求参数**：
- `productId`（可选）：产品ID，如果提供则只返回该产品绑定的风格

**响应示例**：
```json
{
  "status": "success",
  "categories": [
    {
      "code": "style1",
      "name": "经典风格",
      "cover_image": "https://moeart.cc/static/images/style1.jpg",
      "images": [
        {
          "code": "img1",
          "url": "https://moeart.cc/static/images/img1.jpg"
        }
      ]
    }
  ]
}
```

---

### 4. 提交订单

**接口**：`POST /api/miniprogram/orders`

**说明**：创建新订单

**请求体**：
```json
{
  "openid": "用户OpenID",
  "productName": "证件照",
  "productType": "idphoto",
  "selectedSpec": "1寸-红底",
  "styleName": "经典风格",
  "quantity": 1,
  "totalPrice": 60.0,
  "customerName": "张三",
  "customerPhone": "13800138000",
  "receiver": "",
  "phone": "",
  "fullAddress": "",
  "remark": ""
}
```

**响应示例**：
```json
{
  "status": "success",
  "orderId": "PET20250114123456ABCD",
  "message": "订单创建成功"
}
```

**错误响应**：
```json
{
  "status": "error",
  "message": "订单创建失败：参数错误"
}
```

---

### 5. 创建支付订单

**接口**：`POST /api/payment/create`

**说明**：创建微信支付订单，返回支付参数

**请求体**：
```json
{
  "orderId": "PET20250114123456ABCD",
  "totalPrice": 60.0,
  "openid": "用户OpenID",
  "skipPayment": false
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "orderId": "PET20250114123456ABCD",
    "payment": {
      "timeStamp": "1609459200",
      "nonceStr": "5K8264ILTKCH16CQ2502SI8ZNMTM67VS",
      "package": "prepay_id=wx2016121016420242444321ca0631331346",
      "signType": "MD5",
      "paySign": "C380BEC2BFD727A4B6845133519F3AD6"
    }
  }
}
```

**开发模式**：
- 如果 `skipPayment: true`，则跳过真实支付，直接返回成功

---

### 6. 获取订单列表

**接口**：`GET /api/miniprogram/orders`

**说明**：获取用户的订单列表

**请求参数**：
- `openid`：用户OpenID（必填）

**响应示例**：
```json
{
  "status": "success",
  "orders": [
    {
      "orderId": "PET20250114123456ABCD",
      "orderId_db": 123,
      "productName": "证件照",
      "styleName": "经典风格",
      "quantity": 1,
      "totalPrice": 60.0,
      "status": "processing",
      "statusText": "处理中",
      "createTime": "2026-01-14 12:34:56",
      "completeTime": null,
      "hdImage": "https://moeart.cc/public/hd/PET20250114123456ABCD_effect_001.png"
    }
  ]
}
```

---

### 7. 获取订单详情

**接口**：`GET /api/miniprogram/order/<order_number>`

**说明**：获取单个订单的详细信息

**路径参数**：
- `order_number`：订单号

**响应示例**：
```json
{
  "status": "success",
  "order": {
    "orderId": "PET20250114123456ABCD",
    "productName": "证件照",
    "styleName": "经典风格",
    "status": "completed",
    "statusText": "已完成",
    "totalPrice": 60.0,
    "createTime": "2026-01-14 12:34:56",
    "shootingCompletedAt": "2026-01-14 13:00:00",
    "completedAt": "2026-01-14 14:00:00",
    "hdImage": "https://moeart.cc/public/hd/PET20250114123456ABCD_effect_001.png",
    "hdImageNoWatermark": "https://moeart.cc/public/hd/clean_PET20250114123456ABCD_effect_001.png"
  }
}
```

---

### 8. 生成订单二维码

**接口**：`GET /api/miniprogram/order/qrcode`

**说明**：生成订单核销二维码（用于Android App扫描）

**请求参数**：
- `orderId`：订单号

**响应示例**：
```json
{
  "success": true,
  "orderId": "PET20250114123456ABCD",
  "qrImage": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "qrContent": "order:PET20250114123456ABCD"
}
```

**二维码内容格式**：`order:订单号`

---

## Android App API接口

### 1. 检查订单状态（核销）

**接口**：`GET /api/miniprogram/order/check`

**说明**：Android App扫描二维码后检查订单是否可核销

**请求参数**：
- `orderId`：订单号（必填）
- `machineSerialNumber`：自拍机序列号（必填）

**请求示例**：
```
GET /api/miniprogram/order/check?orderId=PET20250114123456ABCD&machineSerialNumber=XMSM_001
```

**成功响应**：
```json
{
  "success": true,
  "order": {
    "orderId": "PET20250114123456ABCD",
    "order_number": "PET20250114123456ABCD",
    "is_paid": true,
    "has_photos": false,
    "product_name": "证件照",
    "productType": "idphoto",
    "status": "paid",
    "price": 60.0
  }
}
```

**错误响应（订单已拍摄）**：
```json
{
  "success": false,
  "message": "该订单已经拍摄过，不能重复拍摄",
  "has_photos": true
}
```

**错误响应（订单未支付）**：
```json
{
  "success": false,
  "message": "订单未支付或状态不正确: unpaid"
}
```

**业务逻辑**：
1. 检查订单是否存在
2. 检查订单是否已支付（`is_paid: true`）
3. 检查订单是否已拍摄（`has_photos: false`）
4. 如果订单未关联加盟商，通过 `machineSerialNumber` 自动关联

---

### 2. 上传照片

**接口**：`POST /api/miniprogram/order/upload`

**说明**：Android App拍摄后上传照片到服务器

**请求格式**：`multipart/form-data`

**请求参数**：
- `orderId`：订单号（必填）
- `machineSerialNumber`：自拍机序列号（必填）
- `photos`：照片文件（必填，可多个）

**请求示例**（使用OkHttp）：
```java
MultipartBody.Builder builder = new MultipartBody.Builder()
    .setType(MultipartBody.FORM)
    .addFormDataPart("orderId", "PET20250114123456ABCD")
    .addFormDataPart("machineSerialNumber", "XMSM_001");

for (File file : photoFiles) {
    RequestBody fileBody = RequestBody.create(
        MediaType.parse("image/jpeg"),
        file
    );
    builder.addFormDataPart("photos", file.getName(), fileBody);
}

RequestBody requestBody = builder.build();
```

**成功响应**：
```json
{
  "success": true,
  "message": "照片上传成功",
  "orderId": "PET20250114123456ABCD",
  "uploaded_count": 3
}
```

**错误响应**：
```json
{
  "success": false,
  "message": "上传失败：订单不存在"
}
```

**业务逻辑**：
1. 验证订单是否存在
2. 验证订单是否已支付
3. 验证订单是否已拍摄（防止重复拍摄）
4. 保存照片文件到服务器
5. 更新订单状态为 `processing`（处理中）
6. 记录 `shooting_completed_at`（拍摄完成时间）
7. 通过 `machineSerialNumber` 关联订单到加盟商和门店

**状态变更**：
- 上传前：`paid`（已支付）
- 上传后：`processing`（处理中）

---

## 订单状态说明

### 状态流转图

```
unpaid（待支付）
    ↓ [支付成功]
paid（已支付）
    ↓ [Android App上传照片]
processing（处理中）
    ↓ [后台上传效果图]
completed（已完成）
```

### 状态详细说明

| 状态值 | 中文显示 | 说明 | 触发条件 |
|--------|---------|------|---------|
| `unpaid` | 待支付 | 订单已创建，等待用户支付 | 订单创建时 |
| `paid` | 已支付 | 用户已支付，等待拍摄 | 支付成功后 |
| `processing` | 处理中 | 自拍机已拍摄，等待后台制作效果图 | Android App上传照片后 |
| `completed` | 已完成 | 效果图已制作完成 | 后台上传效果图后 |

### 时间字段说明

| 字段名 | 说明 | 记录时机 |
|--------|------|---------|
| `created_at` | 下单时间 | 订单创建时 |
| `shooting_completed_at` | 拍摄完成时间 | Android App上传照片时 |
| `retouch_completed_at` | 精修美颜完成时间 | 后台上传精修图时 |
| `completed_at` | 制作完成时间 | 后台上传效果图时 |

---

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "message": "错误描述信息"
}
```

### 常见错误码

| HTTP状态码 | 说明 | 处理建议 |
|-----------|------|---------|
| 200 | 请求成功 | 检查响应中的 `success` 字段 |
| 400 | 请求参数错误 | 检查请求参数是否完整、格式是否正确 |
| 404 | 资源不存在 | 检查订单号、资源ID是否正确 |
| 500 | 服务器内部错误 | 联系技术支持 |

### 错误处理示例

**小程序错误处理**：
```javascript
wx.request({
  url: `${config.getApiBaseUrl()}/orders`,
  method: 'GET',
  data: { openid: openid },
  success: function(res) {
    if (res.data.status === 'success') {
      // 处理成功
    } else {
      wx.showToast({
        title: res.data.message || '请求失败',
        icon: 'none'
      });
    }
  },
  fail: function(err) {
    wx.showToast({
      title: '网络异常',
      icon: 'none'
    });
  }
});
```

**Android App错误处理**：
```java
ApiService.getInstance().checkOrder(context, orderId, new ApiService.ApiCallback() {
    @Override
    public void onSuccess(Object data) {
        // 处理成功
    }
    
    @Override
    public void onError(String error) {
        Toast.makeText(context, error, Toast.LENGTH_SHORT).show();
    }
});
```

---

## 接口测试

### 测试工具

1. **Postman**：用于测试API接口
2. **curl**：命令行测试工具
3. **小程序开发者工具**：测试小程序接口
4. **Android Studio**：测试Android App接口

### 测试示例

#### 1. 测试获取产品列表（curl）

```bash
curl -X GET "https://moeart.cc/api/miniprogram/products"
```

#### 2. 测试检查订单状态（curl）

```bash
curl -X GET "https://moeart.cc/api/miniprogram/order/check?orderId=PET20250114123456ABCD&machineSerialNumber=XMSM_001"
```

#### 3. 测试上传照片（curl）

```bash
curl -X POST "https://moeart.cc/api/miniprogram/order/upload" \
  -F "orderId=PET20250114123456ABCD" \
  -F "machineSerialNumber=XMSM_001" \
  -F "photos=@/path/to/photo1.jpg" \
  -F "photos=@/path/to/photo2.jpg"
```

### 测试检查清单

- [ ] 所有接口返回正确的JSON格式
- [ ] 错误处理正确返回错误信息
- [ ] 订单状态流转正确
- [ ] 照片上传功能正常
- [ ] 二维码生成功能正常
- [ ] 订单关联加盟商功能正常

---

## 附录

### 自拍机序列号配置

Android App需要在 `MachineConfig.java` 中配置自拍机序列号：

```java
public class MachineConfig {
    private static final String DEFAULT_SERIAL_NUMBER = "XMSM_001"; // 修改为实际序列号
    
    public static String getSerialNumber(Context context) {
        // 优先使用保存的配置
        // 其次使用设备硬件序列号
        // 最后使用默认值
    }
}
```

### 服务器地址配置

**生产环境**：
- 后端：`https://moeart.cc`
- API：`https://moeart.cc/api/miniprogram`
- 静态资源：`https://moeart.cc/static`
- 媒体文件：`https://moeart.cc/media`

**开发环境**（仅用于测试）：
- 后端：`http://192.168.2.54:8000`
- API：`http://192.168.2.54:8000/api/miniprogram`

---

**文档版本**：v1.0  
**最后更新**：2026-01-14  
**维护者**：开发团队  
**联系方式**：技术支持
