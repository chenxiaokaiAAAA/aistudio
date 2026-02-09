# RunningHub API 服务商配置填写指南

## 📋 配置步骤

### 1. 进入配置页面

访问管理后台：`http://127.0.0.1:8000/admin/ai-provider/config`

点击 **"添加服务商"** 按钮

### 2. 填写配置信息

#### 必填字段

| 字段 | 填写值 | 说明 |
|------|--------|------|
| **配置名称** | `RunningHub-全能图片PRO` | 自定义名称，用于识别此配置 |
| **API类型** | `runninghub-rhart-edit (RunningHub 全能图片PRO)` | 从下拉菜单选择 |
| **API Key** | `您的RunningHub API Key` | 从 RunningHub 控制台获取 |

#### Host 配置

| 字段 | 填写值 | 说明 |
|------|--------|------|
| **国内直连Host** | `https://www.runninghub.cn` | RunningHub 的国内访问地址 |
| **海外Host** | `https://www.runninghub.cn` | RunningHub 的海外访问地址（通常与国内相同） |

#### 接口配置

| 字段 | 填写值 | 说明 |
|------|--------|------|
| **绘画接口** | `/openapi/v2/rhart-image-n-pro/edit` | 提交图片编辑任务的接口 |
| **结果接口** | `/openapi/v2/query` | 查询任务结果的接口（新格式） |
| **文件上传接口** | `/v1/file/upload` | 文件上传接口（可选，如果不需要可以留空） |

#### 其他配置

| 字段 | 填写值 | 说明 |
|------|--------|------|
| **模型名称** | `rhart-image-n-pro` | 可选，可在模板中覆盖 |
| **优先级** | `0` | 数字越大优先级越高（用于重试时选择顺序） |
| **启用** | ✅ **勾选** | 启用此配置 |
| **默认配置** | ❌ **不勾选** | 是否设为默认配置（根据需要） |
| **同步API** | ❌ **不勾选** | RunningHub 是异步API，返回 taskId 后需要轮询 |
| **启用重试** | ✅ **勾选** | 参与自动重试机制 |
| **配置描述** | `RunningHub 全能图片PRO-图生图 API 配置，支持4K超清画质输出，专业级图像编辑` | 可选，用于说明此配置的用途 |

## 📝 完整配置示例

```
配置名称: RunningHub-全能图片PRO
API类型: runninghub-rhart-edit (RunningHub 全能图片PRO)
国内直连Host: https://www.runninghub.cn
海外Host: https://www.runninghub.cn
API Key: 14014c51362d40f3b7794b50f0a67551 (示例，请使用您的真实API Key)
绘画接口: /openapi/v2/rhart-image-n-pro/edit
结果接口: /openapi/v2/query
文件上传接口: /v1/file/upload
模型名称: rhart-image-n-pro
优先级: 0
启用: ✅
默认配置: ❌
同步API: ❌ (重要：必须不勾选)
启用重试: ✅
配置描述: RunningHub 全能图片PRO-图生图 API 配置，支持4K超清画质输出，专业级图像编辑
```

## ⚠️ 重要注意事项

### 1. 同步API 设置

**必须不勾选** "同步API" 选项！

- RunningHub API 是异步API，提交任务后返回 `taskId`
- 系统会自动轮询 `/openapi/v2/query` 接口查询结果
- 如果错误地勾选了"同步API"，系统会认为任务已完成，不会进行轮询

### 2. 结果接口格式

使用新格式 `/openapi/v2/query`：
- 请求体只需要 `{"taskId": "..."}`
- 响应格式：`{"status": "SUCCESS", "results": [{"url": "..."}], "errorMessage": "..."}`

系统会自动识别并使用正确的请求格式。

### 3. API Key 获取

1. 登录 RunningHub 控制台
2. 进入 API 管理页面
3. 创建或查看 API Key
4. 复制 API Key 并粘贴到配置中

### 4. 测试配置

配置保存后，建议：
1. 在"风格管理"中创建一个测试任务
2. 选择此 RunningHub 配置
3. 查看任务执行日志，确认 API 调用正常
4. 确认 `taskId` 已正确保存，系统正在轮询查询结果

## 🔄 请求流程

1. **提交任务**: 调用 `/openapi/v2/rhart-image-n-pro/edit`
   - 请求体：`{"prompt": "...", "resolution": "1K", "aspectRatio": "3:4", "imageUrls": [...]}`
   - 响应：`{"taskId": "...", "status": "QUEUED", ...}`

2. **轮询查询**: 系统自动调用 `/openapi/v2/query`
   - 请求体：`{"taskId": "..."}`
   - 响应：`{"status": "SUCCESS/RUNNING/QUEUED/FAILED", "results": [...], "errorMessage": "..."}`

3. **完成处理**: 当 `status` 为 `SUCCESS` 时，从 `results[0].url` 提取图片URL并下载

## 📚 参考文档

- [RunningHub API 文档](https://www.runninghub.cn/call-api/api-detail/2004543527918551041?apiType=1)
- [RunningHub 配置说明](./RunningHub配置说明.md)

## 🆘 常见问题

### Q: 任务一直显示"处理中"，没有结果？

A: 检查以下几点：
1. 确认"同步API"选项**没有勾选**
2. 检查 API Key 是否正确
3. 查看任务日志，确认 `taskId` 已正确保存
4. 检查轮询服务是否正常运行

### Q: 查询接口应该填什么？

A: 使用 `/openapi/v2/query`（新格式），系统会自动使用正确的请求格式。

### Q: 可以同时配置多个 RunningHub 配置吗？

A: 可以，但需要不同的配置名称，可以设置不同的优先级用于重试机制。
