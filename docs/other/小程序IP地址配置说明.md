# 小程序IP地址配置说明

## 📋 需要修改的位置

### ✅ 只需要修改 1 个文件

**文件路径**：`aistudio-小程序/config.js`

---

## 🔧 修改方法

### 方法1：切换到生产环境（推荐）

在 `config.js` 中，将第 7 行改为：

```javascript
const ENV = 'production';  // 改为 'production'
```

这样会自动使用 `production` 配置中的 `121.43.143.59`。

---

### 方法2：直接修改生产环境IP（如果需要调试）

如果 `121.43.143.59` 需要改为其他IP，修改 `config.js` 第 23-28 行：

```javascript
production: {
  baseUrl: 'http://121.43.143.59',  // 改为你的服务器IP
  apiBaseUrl: 'http://121.43.143.59/api/miniprogram',
  apiUrl: 'http://121.43.143.59/api',
  staticUrl: 'http://121.43.143.59/static',
  mediaUrl: 'http://121.43.143.59/media'
}
```

---

## 📊 配置说明

### 当前配置（config.js）

```javascript
// 当前环境：'local' 或 'production'
const ENV = 'local';  // ← 这里改为 'production' 即可

// 本地开发配置
const SERVER_CONFIG = {
  local: {
    baseUrl: `http://${LOCAL_IP}:8000`,
    apiBaseUrl: `http://${LOCAL_IP}:8000/api/miniprogram`,
    apiUrl: `http://${LOCAL_IP}:8000/api`,
    staticUrl: `http://${LOCAL_IP}:8000/static`,
    mediaUrl: `http://${LOCAL_IP}:8000/media`
  },
  production: {
    baseUrl: 'http://121.43.143.59',  // ← 生产环境IP
    apiBaseUrl: 'http://121.43.143.59/api/miniprogram',
    apiUrl: 'http://121.43.143.59/api',
    staticUrl: 'http://121.43.143.59/static',
    mediaUrl: 'http://121.43.143.59/media'
  }
};
```

---

## ✅ 其他文件说明

### 不需要修改的文件

小程序中**所有其他文件**都通过 `config.js` 来获取服务器地址，包括：

- `app.js` - 使用 `config.getApiUrl()`
- `pages/index/index.js` - 使用 `config.getApiUrl()`
- `pages/orders/orders.js` - 使用 `config.getApiBaseUrl()`
- `pages/product/product.js` - 使用 `config.getApiBaseUrl()`
- `pages/style/style.js` - 使用 `config.getBaseUrl()`
- `utils/image-helper.js` - 使用 `config.getBaseUrl()`

**结论**：只需要修改 `config.js` 一个文件即可！

---

## 🚀 快速切换

### 切换到生产环境（调试服务器）

```javascript
// config.js 第 7 行
const ENV = 'production';  // 改为 'production'
```

### 切换回本地开发

```javascript
// config.js 第 7 行
const ENV = 'local';  // 改为 'local'
```

---

## 📝 注意事项

1. **端口号**：如果服务器不是8000端口，需要修改 `production` 配置中的URL
2. **HTTPS**：如果后续使用HTTPS，将 `http://` 改为 `https://`
3. **域名**：域名申请后，将IP地址替换为域名即可

---

## 🔍 验证配置

修改后，在小程序开发者工具中：

1. 重新编译小程序
2. 打开控制台，查看网络请求
3. 确认请求地址是否为 `http://121.43.143.59`

---

## 📋 配置项说明

| 配置项 | 用途 | 示例 |
|--------|------|------|
| `baseUrl` | 服务器基础地址 | `http://121.43.143.59` |
| `apiBaseUrl` | 小程序API基础地址 | `http://121.43.143.59/api/miniprogram` |
| `apiUrl` | 通用API地址 | `http://121.43.143.59/api` |
| `staticUrl` | 静态资源地址 | `http://121.43.143.59/static` |
| `mediaUrl` | 媒体文件地址 | `http://121.43.143.59/media` |
