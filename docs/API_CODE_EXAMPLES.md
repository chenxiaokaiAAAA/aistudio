# API代码示例 - 可直接复制使用

本文档提供可直接复制到现有项目的代码示例。

---

## 🔌 后端代码

### 1. 检查订单状态接口

**文件：** `backend/api/order.js`（添加到现有路由文件）

```javascript
// 检查订单状态（用于机器扫码）
// 注意：此接口不需要token验证，因为安卓APP扫码时没有用户token
router.get('/check', async (req, res) => {
  try {
    const { orderId } = req.query;
    
    if (!orderId) {
      return res.status(400).json({
        success: false,
        message: '订单ID不能为空'
      });
    }
    
    // 根据你的数据库实现调整
    // 示例：使用 Sequelize 或 Mongoose
    const order = await OrderModel.findOne({ 
      where: { order_id: orderId } 
    });
    
    // 或者使用原生SQL
    // const order = await db.query('SELECT * FROM orders WHERE order_id = ?', [orderId]);
    
    if (!order) {
      return res.status(404).json({
        success: false,
        message: '订单不存在'
      });
    }
    
    // 返回订单信息
    res.json({
      success: true,
      order: {
        order_id: order.order_id,
        user_openid: order.user_openid,
        product_type: order.product_type,
        status: order.status,
        amount: order.amount,
        photos: order.photos || []
      }
    });
  } catch (error) {
    console.error('检查订单状态失败:', error);
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
});
```

---

### 2. 照片上传接口

**文件：** `backend/api/order.js`（添加到现有路由文件）

**首先安装依赖：**
```bash
npm install multer
```

**然后添加以下代码：**

```javascript
const multer = require('multer');
const path = require('path');
const fs = require('fs');

// 配置上传目录
const uploadDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// 配置multer存储
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, 'photo-' + uniqueSuffix + path.extname(file.originalname));
  }
});

// 配置multer
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

// 上传照片接口（用于安卓APP）
router.post('/upload', upload.array('photos', 10), async (req, res) => {
  try {
    const { orderId } = req.body;
    
    if (!orderId) {
      return res.status(400).json({
        success: false,
        message: '订单ID不能为空'
      });
    }
    
    // 检查订单是否存在
    const order = await OrderModel.findOne({ 
      where: { order_id: orderId } 
    });
    
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
    
    // 处理上传的文件
    const uploadedFiles = req.files.map(file => ({
      filename: file.filename,
      originalname: file.originalname,
      path: `/uploads/${file.filename}`,
      size: file.size,
      uploadTime: new Date().toISOString()
    }));
    
    // 更新订单照片列表
    // 根据你的数据库实现调整
    const currentPhotos = order.photos || [];
    const updatedPhotos = [...currentPhotos, ...uploadedFiles];
    
    await OrderModel.update(
      { 
        photos: updatedPhotos,
        status: 'completed',
        shooting_time: new Date(),
        complete_time: new Date()
      },
      { where: { order_id: orderId } }
    );
    
    // 获取更新后的订单
    const updatedOrder = await OrderModel.findOne({ 
      where: { order_id: orderId } 
    });
    
    res.json({
      success: true,
      message: '上传成功',
      files: uploadedFiles,
      orderId: orderId,
      order: updatedOrder
    });
  } catch (error) {
    console.error('上传照片失败:', error);
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
});
```

**在 server.js 中添加静态文件服务：**

```javascript
const path = require('path');

// 静态文件服务（用于访问上传的照片）
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));
```

---

## 📱 小程序代码

### 1. 订单列表页面 - 添加二维码按钮

**文件：** `pages/order/order.wxml`

在订单项中添加按钮（找到订单操作区域）：

```xml
<view class="order-actions">
  <!-- 其他按钮... -->
  
  <!-- 显示二维码按钮（仅已支付订单显示） -->
  <button 
    class="action-btn" 
    wx:if="{{item.status === 'paid' || item.status === '已支付'}}"
    catchtap="showQRCode"
    data-id="{{item.order_id || item.id}}">
    显示二维码
  </button>
</view>
```

**文件：** `pages/order/order.js`

添加方法：

```javascript
Page({
  // ... 现有代码 ...

  // 显示订单二维码
  showQRCode(e) {
    const orderId = e.currentTarget.dataset.id;
    if (!orderId) {
      wx.showToast({
        title: '订单ID不存在',
        icon: 'none'
      });
      return;
    }
    
    // 跳转到二维码页面
    wx.navigateTo({
      url: `/pages/order/qrcode?id=${orderId}`
    });
  }
});
```

---

### 2. 二维码页面

**创建文件：** `pages/order/qrcode.js`

```javascript
Page({
  data: {
    orderId: '',
    qrCodeText: '',
    qrCodeImage: '' // 如果使用二维码图片库，存储图片路径
  },

  onLoad(options) {
    const orderId = options.id;
    if (!orderId) {
      wx.showToast({
        title: '订单ID不存在',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
      return;
    }

    // 生成二维码内容：格式为 order:订单ID
    const qrCodeText = `order:${orderId}`;
    
    this.setData({
      orderId: orderId,
      qrCodeText: qrCodeText
    });

    // 如果需要生成二维码图片，可以使用 weapp-qrcode 库
    // 安装：npm install weapp-qrcode
    // 然后在这里调用生成二维码的方法
  },

  // 复制订单ID
  copyOrderId() {
    wx.setClipboardData({
      data: this.data.orderId,
      success: () => {
        wx.showToast({
          title: '订单ID已复制',
          icon: 'success'
        });
      }
    });
  },

  // 复制二维码内容
  copyQRCodeText() {
    wx.setClipboardData({
      data: this.data.qrCodeText,
      success: () => {
        wx.showToast({
          title: '二维码内容已复制',
          icon: 'success'
        });
      }
    });
  }
});
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
      <!-- 二维码图片显示区域 -->
      <!-- 如果使用 weapp-qrcode 库，在这里显示生成的二维码图片 -->
      <image wx:if="{{qrCodeImage}}" src="{{qrCodeImage}}" class="qrcode-image" />
      
      <!-- 临时方案：显示文本格式的二维码内容 -->
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

  <view class="help-section">
    <view class="help-title">使用说明</view>
    <view class="help-content">
      <text>1. 打开安卓拍摄APP</text>
      <text>2. 点击"扫描二维码确认订单"</text>
      <text>3. 扫描此页面显示的二维码</text>
      <text>4. 或手动输入二维码内容</text>
    </view>
  </view>
</view>
```

**创建文件：** `pages/order/qrcode.wxss`（样式文件）

```css
.container {
  padding: 40rpx;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.qrcode-section {
  background-color: #fff;
  border-radius: 20rpx;
  padding: 40rpx;
  margin-bottom: 30rpx;
}

.title {
  font-size: 36rpx;
  font-weight: bold;
  text-align: center;
  margin-bottom: 40rpx;
}

.order-info {
  display: flex;
  justify-content: center;
  margin-bottom: 40rpx;
}

.label {
  font-size: 28rpx;
  color: #666;
}

.value {
  font-size: 28rpx;
  color: #333;
  font-weight: bold;
  margin-left: 10rpx;
}

.qrcode-content {
  text-align: center;
  margin-bottom: 40rpx;
}

.qrcode-image {
  width: 400rpx;
  height: 400rpx;
  margin: 0 auto 20rpx;
}

.qrcode-text {
  font-size: 32rpx;
  color: #333;
  font-weight: bold;
  margin-bottom: 20rpx;
  word-break: break-all;
}

.tip {
  font-size: 24rpx;
  color: #999;
}

.manual-input {
  margin-top: 40rpx;
  padding: 30rpx;
  background-color: #f9f9f9;
  border-radius: 10rpx;
}

.manual-title {
  font-size: 28rpx;
  font-weight: bold;
  margin-bottom: 20rpx;
}

.manual-content {
  font-size: 24rpx;
  color: #666;
}

.manual-code {
  display: block;
  margin-top: 10rpx;
  font-size: 26rpx;
  color: #333;
  font-weight: bold;
  word-break: break-all;
}

.action-buttons {
  display: flex;
  gap: 20rpx;
  margin-bottom: 30rpx;
}

.btn {
  flex: 1;
  background-color: #007aff;
  color: #fff;
  border-radius: 10rpx;
  font-size: 28rpx;
}

.help-section {
  background-color: #fff;
  border-radius: 20rpx;
  padding: 40rpx;
}

.help-title {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 20rpx;
}

.help-content {
  font-size: 26rpx;
  color: #666;
  line-height: 1.8;
}

.help-content text {
  display: block;
  margin-bottom: 10rpx;
}
```

**在 app.json 中注册页面：**

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
    // 获取IP方法：命令行输入 ipconfig，找到"IPv4 地址"
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

### 2. 扫码功能集成

**在扫码Activity中：**

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
    // 显示加载提示
    Toast.makeText(this, "正在检查订单...", Toast.LENGTH_SHORT).show();
    
    // 调用API检查订单状态
    ApiService.getInstance().checkOrder(orderId, new ApiService.ApiCallback() {
        @Override
        public void onSuccess(Object data) {
            // 解析订单数据
            try {
                JSONObject jsonObject = new JSONObject((String) data);
                if (jsonObject.getBoolean("success")) {
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
                } else {
                    Toast.makeText(ScanActivity.this, jsonObject.getString("message"), Toast.LENGTH_SHORT).show();
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

### 3. 照片上传功能集成

**在照片选择Activity中：**

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

## 📝 配置说明

### 1. 网络权限（Android）

**在 AndroidManifest.xml 中添加：**

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

### 2. 网络安全配置（如果使用HTTP）

**创建文件：** `app/src/main/res/xml/network_security_config.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">192.168.2.54</domain>
        <domain includeSubdomains="true">localhost</domain>
    </domain-config>
</network-security-config>
```

**在 AndroidManifest.xml 中引用：**

```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ...>
</application>
```

---

## ✅ 测试清单

- [ ] 后端 `/api/order/check` 接口可以正常访问
- [ ] 后端 `/api/order/upload` 接口可以正常上传文件
- [ ] 小程序可以显示订单二维码
- [ ] 安卓APP可以扫描二维码并解析订单ID
- [ ] 安卓APP可以检查订单状态
- [ ] 安卓APP可以上传照片
- [ ] 上传后订单状态自动更新为"已完成"

---

**文档版本：** v1.0  
**最后更新：** 2024-01-13
