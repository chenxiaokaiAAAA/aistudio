# 小程序拍摄二维码和安卓APP接口文档

> 本文档详细说明了小程序拍摄二维码和安卓APP需要对接的接口，以及厂家APP对接所需的接口。

---

## 一、小程序拍摄二维码相关接口

### 1.1 生成订单核销二维码
- **接口**: `GET /api/miniprogram/order/qrcode`
- **功能**: 生成订单核销二维码（小程序端调用）
- **请求参数**:
  - `orderId` 或 `order_id`: 订单号（如：`MP20260101XXX`）
- **返回数据**:
  ```json
  {
    "success": true,
    "orderId": "MP20260101XXX",
    "qrContent": "order:MP20260101XXX",
    "qrImage": "data:image/png;base64,..."
  }
  ```
- **二维码格式**: `order:订单号`
- **使用场景**: 小程序用户在"我的订单"页面点击"核销"按钮时调用

### 1.2 生成拍摄核销二维码（立即拍摄订单）
- **接口**: `POST /api/miniprogram/orders/<order_id>/generate-qrcode`
- **功能**: 为立即拍摄订单生成核销二维码
- **请求参数**:
  ```json
  {
    "action": "shooting"  // 可选，默认为"shooting"
  }
  ```
- **返回数据**:
  ```json
  {
    "success": true,
    "orderId": "MP20260101XXX",
    "qrContent": "order:MP20260101XXX",
    "qrImage": "data:image/png;base64,...",
    "message": "拍摄核销二维码生成成功"
  }
  ```

---

## 二、安卓APP核销和上传接口

### 2.1 检查订单状态（核销接口）
- **接口**: `GET /api/miniprogram/order/check`
- **功能**: 安卓APP扫码后检查订单状态，用于核销验证
- **请求参数**:
  - `orderId` 或 `order_id`: 订单号（从二维码中解析）
  - `machineSerialNumber` 或 `machine_serial_number` 或 `selfie_machine_id`: **设备序列号（必填）**
- **返回数据**:
  ```json
  {
    "status": "success",
    "order": {
      "order_number": "MP20260101XXX",
      "status": "paid",
      "customer_name": "张三",
      "customer_phone": "13800138000",
      "order_mode": "shooting",
      "franchisee_id": 1,
      "store_name": "厦门SM商城"
    },
    "can_shoot": true,
    "message": "订单验证成功，可以拍摄"
  }
  ```
- **错误返回**:
  ```json
  {
    "status": "error",
    "message": "订单不存在"  // 或 "订单已拍摄过" 等
  }
  ```
- **关键功能**:
  - 如果订单未关联加盟商，且提供了设备序列号，会自动关联到对应的加盟商
  - 通过设备序列号查找 `SelfieMachine` 表，找到对应的加盟商并更新订单

### 2.2 上传订单照片（拍摄后回传）
- **接口**: `POST /api/miniprogram/order/upload`
- **功能**: 安卓APP拍摄完成后上传照片
- **请求方式**: `multipart/form-data`
- **请求参数**:
  - `orderId` 或 `order_id`: 订单号（必填）
  - `machineSerialNumber` 或 `machine_serial_number` 或 `selfie_machine_id`: **设备序列号（必填）**
  - `photos`: 图片文件数组（必填，字段名必须是 `photos`）
- **返回数据**:
  ```json
  {
    "success": true,
    "orderId": "MP20260101XXX",
    "uploadedFiles": [
      {
        "filename": "android_abc123_photo0.jpg",
        "path": "/uploads/android_abc123_photo0.jpg",
        "uploadTime": "2026-02-03T19:00:00"
      }
    ],
    "message": "照片上传成功"
  }
  ```
- **关键功能**:
  - 自动保存上传的照片到 `uploads` 目录
  - 创建 `OrderImage` 记录关联到订单
  - 如果订单未关联加盟商，通过设备序列号自动关联
  - 更新订单状态：
    - 立即拍摄订单：如果启用美图API，更新为"美颜中"，否则更新为"AI任务处理中"
    - 其他订单：更新为"正在拍摄"
  - 自动触发图片处理流程（美图API + AI工作流）

---

## 三、设备序列号绑定机制

### 3.1 设备管理（后台管理）

#### 设备表结构 (`SelfieMachine`)
```python
{
  "id": 1,
  "franchisee_id": 1,  # 关联的加盟商ID
  "machine_name": "SM商城-1号机",  # 设备名称
  "machine_serial_number": "XMSM_001",  # 设备序列号（全局唯一）
  "location": "厦门SM商城1楼",  # 设备位置
  "status": "active",  # 状态：active, inactive, maintenance
  "notes": "备注信息",
  "created_at": "2026-01-01T00:00:00"
}
```

#### 设备管理接口（后台管理，厂家APP不需要调用）
- **添加设备**: `POST /franchisee/admin/accounts/<account_id>/machines/add`
- **编辑设备**: `POST /franchisee/admin/accounts/<account_id>/machines/<machine_id>/edit`
- **删除设备**: `POST /franchisee/admin/accounts/<account_id>/machines/<machine_id>/delete`

### 3.2 设备序列号关联订单逻辑

**核心逻辑**：
1. 安卓APP在调用核销和上传接口时，必须传递设备序列号
2. 后端通过设备序列号查找 `SelfieMachine` 表
3. 找到对应的设备后，获取关联的加盟商信息
4. 如果订单未关联加盟商，自动更新订单的以下字段：
   - `franchisee_id`: 加盟商ID
   - `store_name`: 门店名称
   - `selfie_machine_id`: 设备序列号
   - `external_platform`: 设备名称或平台标识
   - `external_order_number`: 设备序列号

**代码示例**（后端逻辑）：
```python
# 如果订单还没有关联加盟商，且提供了自拍机序列号
if not order.franchisee_id and machine_serial_number:
    # 通过自拍机序列号查找对应的设备
    machine = SelfieMachine.query.filter_by(
        machine_serial_number=machine_serial_number,
        status='active'
    ).first()
    
    if machine and machine.franchisee:
        franchisee = machine.franchisee
        # 更新订单的加盟商信息
        order.franchisee_id = franchisee.id
        order.store_name = franchisee.store_name or order.store_name
        order.selfie_machine_id = machine_serial_number
        order.external_platform = machine.machine_name or 'miniprogram'
        order.external_order_number = machine_serial_number
        db.session.commit()
```

---

## 四、厂家APP对接接口清单

如果厂家要使用自己的APP对接系统，需要提供以下接口：

### 4.1 核心接口（必接）

#### 1. 检查订单状态（核销）
- **接口**: `GET /api/miniprogram/order/check`
- **必填参数**:
  - `orderId`: 订单号
  - `machineSerialNumber`: 设备序列号
- **说明**: 扫码后调用此接口验证订单，系统会自动通过设备序列号关联订单到对应的加盟商

#### 2. 上传订单照片
- **接口**: `POST /api/miniprogram/order/upload`
- **请求方式**: `multipart/form-data`
- **必填参数**:
  - `orderId`: 订单号
  - `machineSerialNumber`: 设备序列号
  - `photos`: 图片文件数组（字段名必须是 `photos`）
- **说明**: 拍摄完成后上传照片，系统会自动处理并触发后续流程

### 4.2 可选接口（根据需求）

#### 3. 获取订单详情
- **接口**: `GET /api/miniprogram/order/<order_number>`
- **功能**: 获取订单详细信息
- **请求参数**:
  - `order_number`: 订单号
- **返回**: 订单完整信息

#### 4. 获取订单二维码
- **接口**: `GET /api/miniprogram/order/qrcode`
- **功能**: 获取订单二维码（如果厂家APP需要显示二维码）
- **请求参数**:
  - `orderId`: 订单号
- **返回**: 二维码图片（base64格式）

---

## 五、厂家APP对接步骤

### 步骤1：设备序列号配置

1. **在管理后台添加设备**：
   - 登录管理后台
   - 进入"加盟商管理" → 选择加盟商 → "自拍机设备"标签页
   - 点击"添加设备"
   - 填写设备信息：
     - **设备名称**: 如 `SM商城-1号机`
     - **设备序列号**: 如 `XMSM_001`（**必须与APP配置的序列号完全一致**）
     - **设备位置**: 如 `厦门SM商城1楼`
     - **状态**: 选择 `正常`

2. **在厂家APP中配置序列号**：
   - APP需要有一个配置项存储设备序列号
   - 序列号必须与管理后台填写的完全一致（区分大小写、空格等）

### 步骤2：实现扫码功能

1. **解析二维码**：
   - 二维码格式：`order:订单号`
   - 解析后提取订单号（去掉 `order:` 前缀）

2. **调用核销接口**：
   ```java
   // Java示例
   String orderId = "MP20260101XXX";  // 从二维码解析
   String machineSerialNumber = getMachineSerialNumber();  // 从APP配置获取
   
   String url = baseUrl + "/api/miniprogram/order/check" 
              + "?orderId=" + orderId
              + "&machineSerialNumber=" + machineSerialNumber;
   
   // 发送GET请求
   ```

### 步骤3：实现拍摄和上传功能

1. **拍摄照片**：
   - 使用相机API拍摄照片
   - 保存到临时目录

2. **上传照片**：
   ```java
   // Java示例
   String orderId = "MP20260101XXX";
   String machineSerialNumber = getMachineSerialNumber();
   List<File> photoFiles = getPhotoFiles();  // 拍摄的照片文件
   
   // 构建multipart/form-data请求
   MultipartBody.Builder builder = new MultipartBody.Builder()
       .setType(MultipartBody.FORM)
       .addFormDataPart("orderId", orderId)
       .addFormDataPart("machineSerialNumber", machineSerialNumber);  // ⭐ 关键
   
   // 添加照片文件（字段名必须是 "photos"）
   for (File file : photoFiles) {
       RequestBody fileBody = RequestBody.create(
           MediaType.parse("image/jpeg"), 
           file
       );
       builder.addFormDataPart("photos", file.getName(), fileBody);
   }
   
   RequestBody requestBody = builder.build();
   
   // 发送POST请求到 /api/miniprogram/order/upload
   ```

### 步骤4：处理响应

1. **核销接口响应**：
   - 成功：返回订单信息，可以开始拍摄
   - 失败：返回错误信息（订单不存在、已拍摄过等）

2. **上传接口响应**：
   - 成功：返回上传的文件信息
   - 失败：返回错误信息

---

## 六、接口调用示例

### 6.1 完整流程示例

```java
// 1. 扫码获取订单号
String qrContent = scanQRCode();  // "order:MP20260101XXX"
String orderId = qrContent.replace("order:", "");

// 2. 获取设备序列号（从APP配置）
String machineSerialNumber = getMachineSerialNumber();  // "XMSM_001"

// 3. 调用核销接口验证订单
String checkUrl = baseUrl + "/api/miniprogram/order/check" 
                + "?orderId=" + orderId
                + "&machineSerialNumber=" + machineSerialNumber;
                
Response checkResponse = httpClient.get(checkUrl);
if (checkResponse.isSuccess()) {
    // 4. 开始拍摄
    List<File> photos = takePhotos();
    
    // 5. 上传照片
    MultipartBody.Builder builder = new MultipartBody.Builder()
        .setType(MultipartBody.FORM)
        .addFormDataPart("orderId", orderId)
        .addFormDataPart("machineSerialNumber", machineSerialNumber);
    
    for (File photo : photos) {
        RequestBody fileBody = RequestBody.create(
            MediaType.parse("image/jpeg"), 
            photo
        );
        builder.addFormDataPart("photos", photo.getName(), fileBody);
    }
    
    RequestBody requestBody = builder.build();
    String uploadUrl = baseUrl + "/api/miniprogram/order/upload";
    Response uploadResponse = httpClient.post(uploadUrl, requestBody);
    
    if (uploadResponse.isSuccess()) {
        // 上传成功，提示用户
        showMessage("照片上传成功！");
    }
}
```

### 6.2 错误处理

```java
// 核销接口错误处理
if (!checkResponse.isSuccess()) {
    String errorMessage = checkResponse.getErrorMessage();
    if (errorMessage.contains("订单不存在")) {
        showError("订单不存在，请检查二维码是否正确");
    } else if (errorMessage.contains("已拍摄过")) {
        showError("该订单已经拍摄过，无法重复拍摄");
    } else {
        showError("订单验证失败：" + errorMessage);
    }
    return;
}

// 上传接口错误处理
if (!uploadResponse.isSuccess()) {
    String errorMessage = uploadResponse.getErrorMessage();
    if (errorMessage.contains("订单不存在")) {
        showError("订单不存在");
    } else if (errorMessage.contains("没有上传文件")) {
        showError("请选择要上传的照片");
    } else {
        showError("照片上传失败：" + errorMessage);
    }
    return;
}
```

---

## 七、重要注意事项

### 7.1 设备序列号要求

1. **唯一性**: 设备序列号必须全局唯一，不能与其他设备重复
2. **一致性**: APP配置的序列号必须与管理后台填写的完全一致
3. **格式建议**: 建议使用 `门店代码_设备编号` 格式，如：
   - `XMSM_001` (厦门SM商城-1号机)
   - `BJ_CY_002` (北京朝阳店-2号机)
   - `SH_PD_003` (上海浦东店-3号机)

### 7.2 接口调用要求

1. **必填参数**: 
   - 核销接口：`orderId`、`machineSerialNumber`
   - 上传接口：`orderId`、`machineSerialNumber`、`photos`

2. **字段名要求**:
   - 设备序列号支持多种字段名：`machineSerialNumber`、`machine_serial_number`、`selfie_machine_id`
   - 上传文件的字段名必须是 `photos`（复数形式）

3. **请求格式**:
   - 核销接口：`GET` 请求，参数在URL中
   - 上传接口：`POST` 请求，`multipart/form-data` 格式

### 7.3 订单关联逻辑

1. **自动关联**: 如果订单未关联加盟商，系统会自动通过设备序列号关联
2. **关联时机**: 在核销和上传时都会尝试关联
3. **关联字段**: 关联后会更新订单的加盟商、门店、设备等信息

### 7.4 订单状态流转

**立即拍摄订单**：
1. 用户下单 → `paid` (已支付)
2. 生成二维码 → 用户扫码
3. 核销验证 → 可以拍摄
4. 上传照片 → `retouching` (美颜中) 或 `ai_processing` (AI任务处理中)
5. AI处理完成 → `pending_selection` (待选片)

**其他订单**：
1. 用户下单 → `paid` (已支付)
2. 上传照片 → `shooting` (正在拍摄)

---

## 八、接口测试

### 8.1 测试工具

可以使用以下工具测试接口：

1. **Postman**: 
   - 核销接口：GET请求，参数在Query Params
   - 上传接口：POST请求，Body选择form-data，添加文件

2. **curl命令**:
   ```bash
   # 测试核销接口
   curl "http://your-server.com/api/miniprogram/order/check?orderId=MP20260101XXX&machineSerialNumber=XMSM_001"
   
   # 测试上传接口
   curl -X POST "http://your-server.com/api/miniprogram/order/upload" \
     -F "orderId=MP20260101XXX" \
     -F "machineSerialNumber=XMSM_001" \
     -F "photos=@photo1.jpg" \
     -F "photos=@photo2.jpg"
   ```

### 8.2 测试步骤

1. **准备测试数据**:
   - 创建一个测试订单（订单号：`MP20260101XXX`）
   - 在管理后台添加测试设备（序列号：`TEST_001`）

2. **测试核销接口**:
   - 调用核销接口，验证返回订单信息
   - 检查订单是否自动关联到加盟商

3. **测试上传接口**:
   - 准备测试图片文件
   - 调用上传接口，验证照片上传成功
   - 检查订单状态是否更新
   - 检查订单图片是否保存

---

## 九、接口总结

### 厂家APP必须对接的接口（2个）：

1. ✅ **GET /api/miniprogram/order/check** - 检查订单状态（核销）
2. ✅ **POST /api/miniprogram/order/upload** - 上传订单照片

### 可选接口（根据需求）：

3. ⚪ **GET /api/miniprogram/order/<order_number>** - 获取订单详情
4. ⚪ **GET /api/miniprogram/order/qrcode** - 获取订单二维码

### 关键参数：

- **设备序列号** (`machineSerialNumber`): 必填，用于关联订单到加盟商
- **订单号** (`orderId`): 必填，从二维码解析
- **照片文件** (`photos`): 必填，上传接口需要

---

**最后更新**: 2026-02-03
**维护者**: AI Assistant
