# API 错误码说明

> 本文档定义项目 API 的统一错误响应格式和错误码说明。

---

## 一、响应格式

### 成功响应

```json
{
  "status": "success",
  "data": { ... },
  "message": "操作成功"
}
```

部分接口使用 `success: true` 格式：

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 失败响应

```json
{
  "status": "error",
  "message": "错误描述信息",
  "error_code": "ERROR_CODE"
}
```

---

## 二、HTTP 状态码

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 | 成功 | 请求成功处理 |
| 302 | 重定向 | 登录跳转等 |
| 400 | 请求错误 | 参数错误、验证失败 |
| 401 | 未授权 | 未登录或 token 失效 |
| 403 | 禁止访问 | 权限不足 |
| 404 | 未找到 | 资源不存在 |
| 500 | 服务器错误 | 内部异常 |

---

## 三、业务错误码

### 3.1 通用错误码

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| 无 | 401 | 未登录 |
| 无 | 403 | 权限不足 |
| VALIDATION_ERROR | 400 | 参数验证失败 |
| PERMISSION_ERROR | 403 | 权限不足 |
| AUTH_ERROR | 401 | 认证失败 |
| NOT_FOUND | 404 | 资源未找到 |
| SERVER_ERROR | 500 | 服务器内部错误 |

### 3.2 订单相关

| 错误信息 | 说明 |
|----------|------|
| 订单不存在 | 订单号无效或已删除 |
| 订单未完成支付或状态异常 | 订单状态不允许当前操作 |
| 订单用户身份验证失败 | openid/phone 与订单不匹配 |

### 3.3 用户相关

| 错误信息 | 说明 |
|----------|------|
| 用户ID或OpenID不能为空 | 必填参数缺失 |
| 用户不存在 | 用户未注册或未找到 |
| 会话ID不能为空 | 访问统计参数缺失 |

### 3.4 系统相关

| 错误信息 | 说明 |
|----------|------|
| 系统未初始化 | 数据库或配置未就绪 |
| 保存失败 | 数据库写入失败 |

---

## 四、错误处理建议

### 4.1 前端处理

```javascript
// 小程序/前端示例
wx.request({
  url: apiUrl,
  success: (res) => {
    if (res.statusCode === 200) {
      const data = res.data;
      if (data.status === 'success' || data.success) {
        // 成功处理
      } else {
        // 业务错误
        wx.showToast({ title: data.message || '操作失败', icon: 'none' });
      }
    } else if (res.statusCode === 401) {
      // 未登录，跳转登录
    } else if (res.statusCode === 403) {
      // 权限不足
    } else {
      // 其他错误
      wx.showToast({ title: res.data?.message || '网络错误', icon: 'none' });
    }
  }
});
```

### 4.2 Python 请求示例

```python
import requests

response = requests.post(url, json=data)
if response.status_code == 200:
    result = response.json()
    if result.get('status') == 'success' or result.get('success'):
        # 成功
        pass
    else:
        # 业务错误
        print(result.get('message', '操作失败'))
else:
    # HTTP 错误
    print(response.json().get('message', '请求失败'))
```

### 4.3 curl 错误处理

```bash
# 检查 HTTP 状态码
HTTP_CODE=$(curl -s -o /tmp/response.json -w "%{http_code}" -X POST "$URL" -d '{}')
if [ "$HTTP_CODE" = "200" ]; then
  # 检查业务状态
  STATUS=$(jq -r '.status' /tmp/response.json)
  if [ "$STATUS" = "success" ]; then
    echo "成功"
  else
    echo "业务错误: $(jq -r '.message' /tmp/response.json)"
  fi
else
  echo "HTTP错误: $HTTP_CODE"
fi
```

---

## 五、相关文档

- **管理后台API接口说明文档.md** - 管理后台接口
- **小程序API接口说明文档.md** - 小程序接口
- **docs/api/API请求响应示例.md** - 请求/响应示例

---

**最后更新**: 2026-02-06
