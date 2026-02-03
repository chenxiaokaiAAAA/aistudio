# 冲印系统配置指南

## 🎉 连接测试结果

✅ **冲印系统连接成功！**
- API地址: `http://xmdmsm.xicp.cn:5995/api/ODSGate/NewOrder`
- 响应状态: 200 OK
- 系统代号: ZPG

## 📋 需要向厂家获取的信息

### 1. 影楼信息
- **shop_id**: 您的影楼编号（用于订单标识）
- **shop_name**: 您的影楼名称（用于订单显示）

### 2. 认证信息（可选）
- **auth_token**: API认证Token（如果厂家要求认证）

## 🔧 配置步骤

### 第一步：获取厂家信息
联系厂家获取以下信息：
```
影楼编号: [厂家提供]
影楼名称: [厂家提供]
认证Token: [如果需要]
```

### 第二步：更新配置文件
编辑 `printer_config.py` 文件，将以下内容替换为实际值：

```python
PRINTER_SYSTEM_CONFIG = {
    'enabled': True,
    'api_base_url': 'http://xmdmsm.xicp.cn:5995/api/ODSGate',
    'api_url': 'http://xmdmsm.xicp.cn:5995/api/ODSGate/NewOrder',
    'source_app_id': 'ZPG',  # ✅ 已配置
    'shop_id': 'YOUR_SHOP_ID',  # ❌ 需要厂家提供
    'shop_name': 'YOUR_SHOP_NAME',  # ❌ 需要厂家提供
    'auth_token': 'YOUR_AUTH_TOKEN',  # ❌ 如果需要认证
    'callback_url': 'https://dev-camera-api.photogo520.com/open/xmdm/express/notify',
    'file_access_base_url': 'http://photogooo',  # ✅ 已配置
    'timeout': 30,
    'retry_times': 3,
}
```

### 第三步：测试完整流程
1. 更新配置后运行测试：
   ```bash
   python test_printer_connection.py
   ```

2. 在管理后台测试订单发送：
   - 上传高清图片
   - 状态变为"高清放大"
   - 系统自动发送到冲印系统

## 📡 回调接口配置

厂家提供的回调接口：
```
https://dev-camera-api.photogo520.com/open/xmdm/express/notify
```

这个接口用于接收快递信息更新，系统会自动处理。

## 🔍 故障排查

### 如果发送失败，检查：
1. **网络连接**: 确保服务器能访问 `xmdmsm.xicp.cn:5995`
2. **配置信息**: 确保 `shop_id` 和 `shop_name` 正确
3. **文件访问**: 确保高清图片文件存在且可访问
4. **日志信息**: 查看服务器日志了解具体错误

### 常见错误：
- `订单时间栏位的数据不正确`: 这是正常的测试响应
- `网络连接失败`: 检查网络或API地址
- `认证失败`: 检查 `auth_token` 配置

## 🚀 下一步

1. **联系厂家**获取 `shop_id` 和 `shop_name`
2. **更新配置文件**
3. **测试完整流程**
4. **开始正常使用**

配置完成后，当订单状态变为"高清放大"时，系统会自动将高清图片发送给厂家！

