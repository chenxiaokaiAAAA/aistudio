# UI组件快速替换索引

## 🎯 快速查找表

### 按钮组件

| 按钮类型 | 类名 | 修改位置 | 常用属性 |
|---------|------|---------|---------|
| **提交订单** | `.btn-primary` | `styles/common.wxss` | `background-color`, `color`, `border-radius`, `font-size` |
| **加入购物车** | `.btn-secondary` | `styles/common.wxss` | `background-color`, `color`, `border-radius`, `font-size` |
| **查看详情** | `.btn-text-link` | `styles/common.wxss` | `color`, `font-size` |
| **核销按钮** | `.btn-qrcode` | `styles/common.wxss` | `background-color`, `color`, `border-radius` |
| **切换状态** | `.btn-switch-status` | `styles/common.wxss` | `background-color`, `color`, `border-radius` |
| **关闭/确定** | `.btn-close` | `styles/common.wxss` | `background-color`, `color`, `border-radius` |

### 导航组件

| 组件类型 | 类名 | 修改位置 | 常用属性 |
|---------|------|---------|---------|
| **返回按钮** | `.nav-back-icon` | `styles/common.wxss` | `font-size`, `color`, `font-weight` |
| **首页按钮** | `.nav-home-icon` | `styles/common.wxss` | `font-size`, `color`, `font-weight` |

### 图片容器组件

| 组件类型 | 类名 | 修改位置 | 常用属性 |
|---------|------|---------|---------|
| **风格图片** | `.style-image-wrapper` | `styles/common.wxss` | `padding-bottom` (控制比例) |
| **尺寸效果图** | `.size-effect-image-wrapper` | `styles/common.wxss` | `padding-bottom` (控制比例) |

### 布局组件

| 组件类型 | 类名 | 修改位置 | 常用属性 |
|---------|------|---------|---------|
| **底部操作栏** | `.bottom-action-bar` | `styles/common.wxss` | `background-color`, `padding`, `border-top` |

---

## 📝 常用修改场景

### 场景1：修改所有按钮的颜色主题

**文件：** `styles/common.wxss`

```css
/* 主要按钮 - 改为红色主题 */
.btn-primary {
  background-color: #FF6B6B; /* 修改这里 */
  color: #fff;
}

/* 次要按钮 - 改为橙色主题 */
.btn-secondary {
  background-color: #FF9500; /* 修改这里 */
  color: #fff;
}
```

---

### 场景2：修改按钮大小

**文件：** `styles/common.wxss`

```css
.btn-primary {
  height: 100rpx; /* 从 88rpx 改为 100rpx */
  line-height: 100rpx;
  font-size: 36rpx; /* 从 32rpx 改为 36rpx */
}
```

---

### 场景3：修改产品图片比例

**文件：** `styles/common.wxss`

```css
/* 改为1:1正方形 */
.style-image-wrapper {
  padding-bottom: 100%; /* 从 133.33% 改为 100% */
}

.size-effect-image-wrapper {
  padding-bottom: 100%; /* 从 133.33% 改为 100% */
}
```

---

### 场景4：修改返回按钮图标

**方式1：修改字符（文本图标）**

**文件：** 各页面的 `.wxml` 文件

```xml
<!-- 从 ‹ 改为 ← -->
<text class="nav-back-icon">←</text>
```

**方式2：使用图片图标**

**文件：** `styles/common.wxss`

```css
.nav-back-icon {
  /* 改为图片 */
  width: 48rpx;
  height: 48rpx;
  font-size: 0; /* 隐藏文本 */
}
```

然后在 `.wxml` 中：
```xml
<image class="nav-back-icon" src="/images/back.png" mode="aspectFit"></image>
```

---

## 🔍 组件使用位置查找

### 查找使用某个组件的所有页面

使用以下命令查找：

```bash
# 查找使用 .btn-primary 的所有文件
grep -r "btn-primary" aistudio-小程序/pages/

# 查找使用 .btn-secondary 的所有文件
grep -r "btn-secondary" aistudio-小程序/pages/

# 查找使用 .nav-back-icon 的所有文件
grep -r "nav-back-icon" aistudio-小程序/pages/
```

---

## ⚠️ 重要提醒

1. **修改前备份**：修改公共样式前，建议先备份 `styles/common.wxss`
2. **测试所有页面**：修改后需要在所有使用该组件的页面上测试
3. **保持一致性**：不要在不同页面使用不同的样式变体
4. **iOS兼容性**：修改时间相关功能时，注意iOS日期格式兼容性

---

## 📚 相关文档

- [UI组件替换指南](./UI组件替换指南.md) - 详细的使用说明
- [重构完成总结](./重构完成总结.md) - 项目重构总结

---

**最后更新：** 2026-01-31
