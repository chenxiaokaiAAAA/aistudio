# 安卓APP集成指南

本文档说明如何将**订单二维码生成**、**安卓APP扫码确认订单**和**照片回传**功能集成到现有项目中。

---

## 📋 目录

1. [后端API接口](#后端api接口)
2. [小程序代码](#小程序代码)
3. [安卓APP代码](#安卓app代码)
4. [集成步骤](#集成步骤)

---

## 🔌 后端API接口

### 1. 检查订单状态（用于安卓APP扫码）

**接口：** `GET /api/order/check`

**说明：** 安卓APP扫描二维码后，调用此接口检查订单是否存在且已支付。

**请求参数：**
```
orderId: 订单ID（从二维码中解析）
```

**请求示例：**
```javascript
GET /api/order/check?orderId=ORDER1234567890
```

**响应示例：**
```json
{
  "success": true,
  "order": {
    "order_id": "ORDER1234567890",
    "user_openid": "test_openid_xxx",
    "product_type": "idphoto",
    "status": "paid",
    "amount": 29.9,
    "photos": []
  }
}
```

**后端代码（添加到你的 order.js 路由文件）：**

```javascript
// 检查订单状态（用于机器扫码）
router.get('/check', async (req, res) => {
  try {
    const { orderId } = req.query;
    
    // 从数据库获取订单（根据你的数据库实现调整）
    const order = await OrderModel.getByOrderId(orderId);
    
    if (!order) {
      return res.status(404).json({
        success: false,
        message: '订单不存在'
      });
    }
    
    res.json({
      success: true,
      order: order
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
});
```

---

### 2. 上传照片（用于安卓APP回传照片）

**接口：** `POST /api/order/upload`

**说明：** 安卓APP拍摄完成后，调用此接口上传照片。

**请求格式：** `multipart/form-data`

**请求参数：**
```
orderId: 订单ID（字符串）
photos: 照片文件（可多张，字段名：photos）
```

**响应示例：**
```json
{
  "success": true,
  "message": "上传成功",
  "files": [
    {
      "filename": "photo-1234567890-123456789.jpg",
      "originalname": "photo1.jpg",
      "path": "/uploads/photo-1234567890-123456789.jpg",
      "size": 1024000,
      "uploadTime": "2024-01-13T10:00:00.000Z"
    }
  ],
  "orderId": "ORDER1234567890",
  "order": { ... }
}
```

**后端代码（需要安装 multer）：**

```javascript
const multer = require('multer');
const path = require('path');
const fs = require('fs');

// 配置multer用于文件上传
const uploadDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, 'photo-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({
  storage: storage,
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);
    
    if (mimetype && extname) {
      return cb(null, true);
    } else {
      cb(new Error('只支持图片格式: jpeg, jpg, png'));
    }
  }
});

// 上传照片（用于安卓APP）
router.post('/upload', upload.array('photos', 10), async (req, res) => {
  try {
    const { orderId } = req.body;
    
    if (!orderId) {
      return res.status(400).json({
        success: false,
        message: '订单ID不能为空'
      });
    }
    
    const order = await OrderModel.getByOrderId(orderId);
    if (!order) {
      return res.status(404).json({
        success: false,
        message: '订单不存在'
      });
    }
    
    if (!req.files || req.files.length === 0) {
      return res.status(400).json({
        success: false,
        message: '没有上传文件'
      });
    }
    
    // 保存上传的文件信息到订单
    const uploadedFiles = req.files.map(file => ({
      filename: file.filename,
      originalname: file.originalname,
      path: `/uploads/${file.filename}`,
      size: file.size,
      uploadTime: new Date().toISOString()
    }));
    
    // 更新订单照片列表并更新状态为已完成
    await OrderModel.addPhotos(orderId, uploadedFiles);
    await OrderModel.updateStatus(orderId, 'completed', {
      shootingTime: new Date().toISOString(),
      completeTime: new Date().toISOString()
    });
    
    const updatedOrder = await OrderModel.getByOrderId(orderId);
    
    res.json({
      success: true,
      message: '上传成功',
      files: uploadedFiles,
      orderId: orderId,
      order: updatedOrder
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
});
```

**安装依赖：**
```bash
npm install multer
```

**在 server.js 中添加静态文件服务：**
```javascript
const path = require('path');
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));
```

---

## 📱 小程序代码

### 1. 订单列表页面 - 显示二维码按钮

**文件：** `pages/order/order.wxml`

在订单项中添加"显示二维码"按钮：

```xml
<view class="order-actions">
  <button 
    class="action-btn" 
    wx:if="{{item.status === 'paid'}}"
    catchtap="showQRCode"
    data-id="{{item.order_id || item.id}}">
    显示二维码
  </button>
</view>
```

**文件：** `pages/order/order.js`

添加显示二维码的方法：

```javascript
// 查看二维码（用于机器扫码）
showQRCode(e) {
  const orderId = e.currentTarget.dataset.id
  // 跳转到二维码页面
  wx.navigateTo({
    url: `/pages/order/qrcode?id=${orderId}`
  })
}
```

---

### 2. 二维码页面

**创建文件：** `pages/order/qrcode.js`

```javascript
Page({
  data: {
    orderId: '',
    qrCodeText: ''
  },

  onLoad(options) {
    const orderId = options.id
    if (!orderId) {
      wx.showToast({
        title: '订单ID不存在',
        icon: 'none'
      })
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
      return
    }

    // 生成二维码内容：格式为 order:订单ID
    const qrCodeText = `order:${orderId}`
    
    this.setData({
      orderId: orderId,
      qrCodeText: qrCodeText
    })

    // 如果需要生成二维码图片，可以使用 weapp-qrcode 库
    // 或使用微信小程序的 canvas API
  },

  // 复制订单ID
  copyOrderId() {
    wx.setClipboardData({
      data: this.data.orderId,
      success: () => {
        wx.showToast({
          title: '订单ID已复制',
          icon: 'success'
        })
      }
    })
  },

  // 复制二维码内容
  copyQRCodeText() {
    wx.setClipboardData({
      data: this.data.qrCodeText,
      success: () => {
        wx.showToast({
          title: '二维码内容已复制',
          icon: 'success'
        })
      }
    })
  }
})
```

**创建文件：** `pages/order/qrcode.wxml`

```xml
<view class="container">
  <view class="qrcode-section">
    <view class="title">订单二维码</view>
    <view class="order-info">
      <text class="label">订单号：</text>
      <text class="value">{{orderId}}</text>
    </view>
    
    <view class="qrcode-content">
      <!-- 这里可以显示二维码图片，或使用 weapp-qrcode 库生成 -->
      <view class="qrcode-text">{{qrCodeText}}</view>
      <view class="tip">请使用安卓APP扫描此二维码</view>
    </view>

    <!-- 手动输入方式（测试用） -->
    <view class="manual-input">
      <view class="manual-title">手动输入方式（测试用）</view>
      <view class="manual-content">
        <text>如果无法扫描，可以在安卓APP中手动输入：</text>
        <text class="manual-code">{{qrCodeText}}</text>
      </view>
    </view>
  </view>

  <view class="action-buttons">
    <button class="btn" bindtap="copyOrderId">复制订单ID</button>
    <button class="btn" bindtap="copyQRCodeText">复制二维码内容</button>
  </view>
</view>
```

**在 app.json 中添加页面路由：**

```json
{
  "pages": [
    "pages/order/qrcode"
  ]
}
```

---

## 🤖 安卓APP代码

### 1. API服务类

**创建文件：** `app/src/main/java/com/yourpackage/ApiService.java`

```java
package com.yourpackage;

import android.os.Handler;
import android.os.Looper;
import com.google.gson.Gson;
import java.io.File;
import java.io.IOException;
import java.util.List;
import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class ApiService {
    
    private static ApiService instance;
    private OkHttpClient client;
    private Gson gson;
    // ⚠️ 重要：使用电脑的IP地址，不能用localhost
    private String baseUrl = "http://192.168.2.54:3000/api"; // 修改为你的实际IP地址
    
    private ApiService() {
        client = new OkHttpClient();
        gson = new Gson();
    }
    
    public static ApiService getInstance() {
        if (instance == null) {
            instance = new ApiService();
        }
        return instance;
    }
    
    public interface ApiCallback {
        void onSuccess(Object data);
        void onError(String error);
    }
    
    // 检查订单状态
    public void checkOrder(String orderId, ApiCallback callback) {
        Request request = new Request.Builder()
            .url(baseUrl + "/order/check?orderId=" + orderId)
            .get()
            .build();
        
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                runOnUiThread(() -> callback.onError(e.getMessage()));
            }
            
            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    String responseBody = response.body().string();
                    runOnUiThread(() -> callback.onSuccess(responseBody));
                } else {
                    runOnUiThread(() -> callback.onError("订单不存在或未支付"));
                }
            }
        });
    }
    
    // 上传照片
    public void uploadPhotos(String orderId, List<String> imagePaths, ApiCallback callback) {
        MultipartBody.Builder builder = new MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("orderId", orderId);
        
        for (int i = 0; i < imagePaths.size(); i++) {
            File file = new File(imagePaths.get(i));
            if (file.exists()) {
                RequestBody fileBody = RequestBody.create(
                    MediaType.parse("image/jpeg"), file);
                builder.addFormDataPart("photos", "photo" + i + ".jpg", fileBody);
            }
        }
        
        RequestBody requestBody = builder.build();
        Request request = new Request.Builder()
            .url(baseUrl + "/order/upload")
            .post(requestBody)
            .build();
        
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                runOnUiThread(() -> callback.onError(e.getMessage()));
            }
            
            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    String responseBody = response.body().string();
                    runOnUiThread(() -> callback.onSuccess(responseBody));
                } else {
                    runOnUiThread(() -> callback.onError("上传失败"));
                }
            }
        });
    }
    
    private void runOnUiThread(Runnable runnable) {
        new Handler(Looper.getMainLooper()).post(runnable);
    }
}
```

**在 build.gradle 中添加依赖：**

```gradle
dependencies {
    implementation 'com.squareup.okhttp3:okhttp:4.9.3'
    implementation 'com.google.code.gson:gson:2.8.9'
}
```

---

### 2. 扫码页面

**在扫码成功后解析二维码内容：**

```java
private void handleScanResult(String qrCodeContent) {
    // 解析二维码内容，获取订单ID
    // 格式示例: order:ORDER1234567890
    if (qrCodeContent.startsWith("order:")) {
        String orderId = qrCodeContent.substring(6); // 去掉 "order:" 前缀
        checkOrderStatus(orderId);
    } else {
        Toast.makeText(this, "无效的订单二维码", Toast.LENGTH_SHORT).show();
    }
}

private void checkOrderStatus(String orderId) {
    // 调用API检查订单状态
    ApiService.getInstance().checkOrder(orderId, new ApiService.ApiCallback() {
        @Override
        public void onSuccess(Object data) {
            // 解析订单数据
            try {
                JSONObject jsonObject = new JSONObject((String) data);
                JSONObject orderObj = jsonObject.getJSONObject("order");
                String status = orderObj.getString("status");
                
                if ("paid".equals(status)) {
                    // 订单已支付，跳转到拍摄页面
                    Intent intent = new Intent(ScanActivity.this, CameraActivity.class);
                    intent.putExtra("orderId", orderId);
                    intent.putExtra("orderData", (String) data);
                    startActivity(intent);
                    finish();
                } else {
                    Toast.makeText(ScanActivity.this, "订单未支付，无法开始拍摄", Toast.LENGTH_SHORT).show();
                }
            } catch (JSONException e) {
                Toast.makeText(ScanActivity.this, "解析订单数据失败", Toast.LENGTH_SHORT).show();
            }
        }
        
        @Override
        public void onError(String error) {
            Toast.makeText(ScanActivity.this, error, Toast.LENGTH_SHORT).show();
        }
    });
}
```

---

### 3. 照片上传页面

**在拍摄完成后，选择照片并上传：**

```java
private void uploadPhotos() {
    if (selectedImages.isEmpty()) {
        Toast.makeText(this, "请至少选择一张照片", Toast.LENGTH_SHORT).show();
        return;
    }
    
    // 显示上传进度
    Toast.makeText(this, "正在上传...", Toast.LENGTH_SHORT).show();
    
    // 上传照片到服务器
    ApiService.getInstance().uploadPhotos(orderId, selectedImages, new ApiService.ApiCallback() {
        @Override
        public void onSuccess(Object data) {
            Toast.makeText(PhotoSelectActivity.this, "上传成功", Toast.LENGTH_SHORT).show();
            // 返回主页面
            Intent intent = new Intent(PhotoSelectActivity.this, MainActivity.class);
            intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivity(intent);
            finish();
        }
        
        @Override
        public void onError(String error) {
            Toast.makeText(PhotoSelectActivity.this, "上传失败: " + error, Toast.LENGTH_SHORT).show();
        }
    });
}
```

---

## 🔧 集成步骤

### 后端集成

1. **安装依赖：**
   ```bash
   npm install multer
   ```

2. **添加路由：**
   - 在 `server.js` 中确保已引入 `multer`
   - 添加 `/api/order/check` 路由（GET）
   - 添加 `/api/order/upload` 路由（POST，使用 multer 中间件）
   - 添加静态文件服务：`app.use('/uploads', express.static(path.join(__dirname, 'uploads')))`

3. **创建 uploads 目录：**
   ```bash
   mkdir uploads
   ```

### 小程序集成

1. **创建二维码页面：**
   - 创建 `pages/order/qrcode.js`
   - 创建 `pages/order/qrcode.wxml`
   - 创建 `pages/order/qrcode.wxss`（样式文件）

2. **在订单列表页面添加按钮：**
   - 在 `pages/order/order.wxml` 中添加"显示二维码"按钮
   - 在 `pages/order/order.js` 中添加 `showQRCode` 方法

3. **在 app.json 中注册页面：**
   ```json
   {
     "pages": [
       "pages/order/qrcode"
     ]
   }
   ```

### 安卓APP集成

1. **添加依赖：**
   - 在 `build.gradle` 中添加 `okhttp3` 和 `gson`

2. **创建 ApiService 类：**
   - 复制 `ApiService.java` 到你的项目中
   - 修改 `baseUrl` 为你的后端IP地址

3. **实现扫码功能：**
   - 在扫码成功后调用 `handleScanResult` 方法
   - 解析二维码内容（格式：`order:订单ID`）
   - 调用 `checkOrderStatus` 检查订单状态

4. **实现照片上传：**
   - 在拍摄/选择照片后，调用 `uploadPhotos` 方法
   - 上传成功后返回主页面

---

## 📝 注意事项

1. **IP地址配置：**
   - 小程序和安卓APP都需要使用电脑的IP地址，不能用 `localhost`
   - 获取IP方法：命令行输入 `ipconfig`（Windows）或 `ifconfig`（Mac/Linux）

2. **二维码格式：**
   - 统一使用格式：`order:订单ID`
   - 例如：`order:ORDER1234567890`

3. **订单状态：**
   - `unpaid`: 未支付
   - `paid`: 已支付（可以开始拍摄）
   - `shooting`: 拍摄中
   - `completed`: 已完成（照片已上传）

4. **文件上传限制：**
   - 单张照片最大 10MB
   - 支持格式：jpeg, jpg, png
   - 一次最多上传 10 张照片

5. **网络权限：**
   - 安卓APP需要在 `AndroidManifest.xml` 中添加网络权限
   - 如果使用 HTTP（非HTTPS），需要配置网络安全策略

---

## 🎯 测试流程

1. **小程序端：**
   - 创建订单并支付
   - 在订单列表点击"显示二维码"
   - 复制订单ID或二维码内容

2. **安卓APP端：**
   - 打开APP，点击"扫描二维码"
   - 扫描小程序显示的二维码（或手动输入）
   - 如果订单已支付，进入拍摄页面
   - 拍摄完成后选择照片并上传
   - 上传成功后返回主页面

3. **验证：**
   - 在小程序订单列表中查看订单状态是否变为"已完成"
   - 查看订单照片是否显示

---

## 📞 常见问题

**Q: 安卓APP无法连接到服务器？**
A: 检查IP地址是否正确，确保手机和电脑在同一网络，检查防火墙设置。

**Q: 上传照片失败？**
A: 检查文件大小是否超过10MB，检查文件格式是否支持，检查服务器 uploads 目录权限。

**Q: 订单状态检查失败？**
A: 检查订单ID是否正确，检查订单是否已支付，检查后端数据库连接。

---

## 📚 相关文件

- 后端API：`backend/api/order.js`
- 小程序二维码页面：`miniprogram/pages/order/qrcode.js`
- 安卓API服务：`android-app/app/src/main/java/com/aphoto/camera/ApiService.java`

---

**文档版本：** v1.0  
**最后更新：** 2024-01-13
