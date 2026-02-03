# UI组件替换指南

## 📋 目录

1. [概述](#概述)
2. [公共样式文件](#公共样式文件)
3. [通用按钮组件](#通用按钮组件)
4. [导航栏组件](#导航栏组件)
5. [产品详情页组件](#产品详情页组件)
6. [订单相关组件](#订单相关组件)
7. [如何替换UI组件](#如何替换ui组件)
8. [常见问题](#常见问题)

---

## 概述

本文档说明如何统一管理和替换小程序中的UI组件。所有通用组件样式都集中在 `styles/common.wxss` 文件中，便于后续UI更新时只需修改一个文件即可。

### 核心原则

1. **统一管理**：所有通用组件样式集中在 `styles/common.wxss`
2. **标准化类名**：使用统一的CSS类名，避免每个页面重复定义
3. **易于替换**：修改公共样式文件即可更新所有页面的UI
4. **保持兼容**：保留旧样式类名作为兼容，逐步迁移

---

## 公共样式文件

### 文件位置
```
aistudio-小程序/styles/common.wxss
```

### 引入方式

在每个页面的 `.wxss` 文件顶部引入：

```css
@import '../../styles/common.wxss';
```

或者在 `app.wxss` 中全局引入（推荐）：

```css
@import './styles/common.wxss';
```

---

## 通用按钮组件

### 1. 主要按钮（提交订单、确认等）

**类名：** `.btn-primary`

**使用场景：**
- 提交订单
- 确认操作
- 主要操作按钮

**HTML结构：**
```xml
<button class="btn-primary" bindtap="handleSubmit">提交订单</button>
```

**样式特点：**
- 绿色背景 (#07c160)
- 白色文字
- 圆角 12rpx
- 高度 88rpx
- 全宽按钮

**自定义样式：**
如需修改样式，只需编辑 `styles/common.wxss` 中的 `.btn-primary` 类。

---

### 2. 次要按钮（加入购物车、取消等）

**类名：** `.btn-secondary`

**使用场景：**
- 加入购物车
- 取消操作
- 次要操作按钮

**HTML结构：**
```xml
<button class="btn-secondary" bindtap="addToCart">加入购物车</button>
```

**样式特点：**
- 浅灰背景 (#f5f5f5)
- 深色文字 (#333)
- 圆角 12rpx
- 高度 88rpx
- 全宽按钮

---

### 3. 文本链接按钮（查看详情等）

**类名：** `.btn-text-link`

**使用场景：**
- 查看详情
- 更多操作
- 文本链接

**HTML结构：**
```xml
<button class="btn-text-link" bindtap="viewDetail">查看详情</button>
```

**样式特点：**
- 透明背景
- 蓝色文字 (#1890ff)
- 无边框
- 最小高度 44rpx

---

### 4. 核销按钮

**类名：** `.btn-qrcode`

**使用场景：**
- 订单核销
- 二维码相关操作

**HTML结构：**
```xml
<button class="btn-qrcode" bindtap="showQRCode">核销</button>
```

**样式特点：**
- 绿色背景 (#4CAF50)
- 白色文字
- 圆角 25rpx
- 内联按钮（非全宽）

---

### 5. 关闭按钮

**类名：** `.btn-close`

**使用场景：**
- 模态框关闭
- 弹窗确认

**HTML结构：**
```xml
<button class="btn-close" bindtap="closeModal">确定</button>
```

---

## 导航栏组件

### 返回按钮

**类名：** `.nav-left` + `.nav-back-icon`

**HTML结构：**
```xml
<view class="nav-left" bindtap="navigateBack">
  <text class="nav-back-icon">‹</text>
</view>
```

**样式特点：**
- 字体大小：48rpx
- 字体粗细：300
- 颜色：#333
- 容器：60rpx × 60rpx

**替换方法：**
如需更换返回图标，只需修改 `styles/common.wxss` 中的 `.nav-back-icon` 样式，或替换字符 `‹` 为其他图标。

---

### 首页按钮

**类名：** `.nav-left` + `.nav-home-icon`

**HTML结构：**
```xml
<view class="nav-left" bindtap="navigateToHome">
  <text class="nav-home-icon">⌂</text>
</view>
```

---

## 产品详情页组件

### 风格选择图片

**类名：** `.style-image-wrapper`

**HTML结构：**
```xml
<view class="style-image-wrapper">
  <image src="{{item.image_url}}" mode="aspectFill"></image>
</view>
```

**图片比例：** 3:4 竖版（133.33% padding-bottom）

**替换方法：**
如需修改图片比例，编辑 `styles/common.wxss` 中的 `.style-image-wrapper` 的 `padding-bottom` 值：
- 1:1 正方形：`padding-bottom: 100%`
- 3:4 竖版：`padding-bottom: 133.33%`
- 4:3 横版：`padding-bottom: 75%`
- 16:9 横版：`padding-bottom: 56.25%`

---

### 尺寸效果图

**类名：** `.size-effect-image-wrapper`

**HTML结构：**
```xml
<view class="size-effect-image-wrapper">
  <image src="{{size.effect_image_url}}" mode="aspectFill"></image>
</view>
```

**图片比例：** 3:4 竖版（与风格图片一致）

---

### 底部操作栏

**类名：** `.bottom-action-bar`

**HTML结构：**
```xml
<view class="bottom-action-bar">
  <button class="btn-secondary" bindtap="addToCart">加入购物车</button>
  <button class="btn-primary" bindtap="submitOrder">提交订单</button>
</view>
```

**样式特点：**
- 固定在页面底部
- 白色背景
- 顶部边框
- 阴影效果
- 两个按钮并排显示

---

## 订单相关组件

### 查看详情按钮

**类名：** `.btn-view-detail`

**使用位置：**
- 订单列表页
- 订单详情页

**HTML结构：**
```xml
<button class="btn-view-detail" bindtap="viewDetail">查看详情</button>
```

---

### 核销按钮

**类名：** `.btn-qrcode`

**使用位置：**
- 订单列表页（待拍摄订单）
- 订单详情页

**HTML结构：**
```xml
<button class="btn-qrcode" bindtap="showQRCode">核销</button>
```

---

### 切换订单状态按钮

**类名：** `.btn-switch-status`

**使用位置：**
- 订单详情页

**HTML结构：**
```xml
<button class="btn-switch-status" bindtap="switchOrderStatus">切换订单状态</button>
```

---

## 如何替换UI组件

### 步骤1：确定要替换的组件

查看当前页面使用的类名，例如：
- `.btn-primary` - 主要按钮
- `.btn-secondary` - 次要按钮
- `.nav-back-icon` - 返回按钮

### 步骤2：修改公共样式文件

编辑 `aistudio-小程序/styles/common.wxss` 文件，找到对应的样式类，修改以下属性：

```css
/* 示例：修改主要按钮样式 */
.btn-primary {
  background-color: #你的新颜色;  /* 修改背景色 */
  color: #你的文字颜色;           /* 修改文字颜色 */
  border-radius: 你的圆角值;      /* 修改圆角 */
  font-size: 你的字体大小;        /* 修改字体大小 */
  /* ... 其他属性 */
}
```

### 步骤3：检查所有使用该组件的页面

使用搜索功能查找所有使用该类的页面：
```bash
# 搜索使用 .btn-primary 的所有文件
grep -r "btn-primary" aistudio-小程序/pages/
```

### 步骤4：测试所有相关页面

确保修改后所有页面的按钮样式都正确显示。

---

## 常见问题

### Q1: 为什么订单时间每次都要更新？

**A:** 这是因为时间格式化函数 `OrderStatusHelper.formatTime()` 需要兼容iOS系统。iOS只支持特定的日期格式，如果后端返回的时间格式不符合，需要转换。

**解决方案：**
已在 `utils/order-status-helper.js` 中修复，现在会自动将 "YYYY-MM-DD HH:mm" 格式转换为iOS兼容的ISO格式。

**如果仍有问题：**
1. 检查后端返回的时间格式
2. 确保使用 `OrderStatusHelper.formatTime()` 格式化时间
3. 避免直接使用 `new Date("2026-01-30 01:56")` 这种格式

---

### Q2: 如何修改按钮的图标？

**A:** 有两种方式：

**方式1：使用文本图标（当前方式）**
```xml
<text class="nav-back-icon">‹</text>
```
修改 `styles/common.wxss` 中的字体大小和字符即可。

**方式2：使用图片图标**
```xml
<image class="nav-back-icon" src="/images/back.png" mode="aspectFit"></image>
```
修改 `styles/common.wxss` 中的 `.nav-back-icon` 样式，将 `font-size` 改为 `width` 和 `height`。

---

### Q3: 如何统一修改所有按钮的颜色？

**A:** 只需修改 `styles/common.wxss` 文件：

```css
/* 修改主要按钮颜色 */
.btn-primary {
  background-color: #你的新颜色;
}

/* 修改次要按钮颜色 */
.btn-secondary {
  background-color: #你的新颜色;
}
```

---

### Q4: 产品详情页的规格图片比例在哪里设置？

**A:** 在 `styles/common.wxss` 文件中：

```css
/* 风格选择图片 - 3:4 比例 */
.style-image-wrapper {
  padding-bottom: 133.33%; /* 修改这个值即可改变比例 */
}

/* 尺寸效果图 - 3:4 比例 */
.size-effect-image-wrapper {
  padding-bottom: 133.33%; /* 修改这个值即可改变比例 */
}
```

**常用比例：**
- 1:1 正方形：`100%`
- 3:4 竖版：`133.33%`
- 4:3 横版：`75%`
- 16:9 横版：`56.25%`

---

### Q5: 如何添加新的按钮样式？

**A:** 在 `styles/common.wxss` 中添加新的样式类：

```css
/* 新增按钮样式 */
.btn-custom {
  background-color: #你的颜色;
  color: #你的文字颜色;
  border-radius: 12rpx;
  font-size: 32rpx;
  /* ... 其他属性 */
}
```

然后在页面中使用：
```xml
<button class="btn-custom" bindtap="handleAction">自定义按钮</button>
```

---

## 组件清单

### 已统一的组件

✅ **导航栏组件**
- 返回按钮 (`.nav-back-icon`)
- 首页按钮 (`.nav-home-icon`)

✅ **通用按钮**
- 主要按钮 (`.btn-primary`)
- 次要按钮 (`.btn-secondary`)
- 文本链接按钮 (`.btn-text-link`)
- 核销按钮 (`.btn-qrcode`)
- 关闭按钮 (`.btn-close`)

✅ **产品详情页组件**
- 风格选择图片容器 (`.style-image-wrapper`)
- 尺寸效果图容器 (`.size-effect-image-wrapper`)
- 底部操作栏 (`.bottom-action-bar`)

✅ **卡片组件（风格库、产品馆等）**
- 卡片网格容器 (`.card-grid`)
- 卡片容器 (`.card-item`)
- 卡片图片容器 (`.card-image-container`)
- 卡片名称 (`.card-name`)

✅ **订单相关组件**
- 查看详情按钮 (`.btn-view-detail`)
- 切换订单状态按钮 (`.btn-switch-status`)

---

## 快速替换示例

### 示例1：修改所有主要按钮的颜色

编辑 `styles/common.wxss`：
```css
.btn-primary {
  background-color: #FF6B6B; /* 从绿色改为红色 */
}
```

保存后，所有使用 `.btn-primary` 的按钮都会变成红色。

---

### 示例2：修改返回按钮的图标

编辑 `styles/common.wxss`：
```css
.nav-back-icon {
  font-size: 40rpx; /* 从 48rpx 改为 40rpx */
}
```

或者在 WXML 中替换字符：
```xml
<text class="nav-back-icon">←</text> <!-- 从 ‹ 改为 ← -->
```

---

### 示例3：修改产品图片比例

编辑 `styles/common.wxss`：
```css
.style-image-wrapper {
  padding-bottom: 100%; /* 从 133.33% 改为 100%，变成1:1正方形 */
}
```

---

## 注意事项

1. **不要在每个页面重复定义样式**：所有通用样式都应该在 `styles/common.wxss` 中定义
2. **保持类名一致性**：使用统一的类名，不要创建类似的变体
3. **测试兼容性**：修改样式后，需要在不同设备上测试
4. **保留旧样式**：如果页面中有特殊需求，可以保留页面特定的样式，但优先使用公共样式

---

## 更新日志

- **2026-01-31**: 创建公共样式文件和UI组件替换指南
- **2026-01-31**: 统一返回按钮样式
- **2026-01-31**: 修复订单时间iOS兼容性问题
- **2026-01-31**: 统一产品详情页图片比例

---

**最后更新：** 2026-01-31
