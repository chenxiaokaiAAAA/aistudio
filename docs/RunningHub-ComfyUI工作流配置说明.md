# RunningHub ComfyUI 工作流 API 配置说明

## 📋 API 概述

RunningHub ComfyUI 工作流 API 是一个基于 ComfyUI 工作流的图像处理服务，支持自定义工作流节点参数映射。

**参考文档**: [RunningHub ComfyUI 工作流 API 文档](https://www.runninghub.cn/call-api/api-detail/2004375142916210689?apiType=3)

## 🔍 与其他 API 的区别

### 与标准 API 的区别

| 项目 | 标准 API | RunningHub ComfyUI 工作流 |
|------|---------|---------------------------|
| **请求参数** | prompt, size, aspectRatio | nodeInfoList（节点参数映射） |
| **工作流ID** | 不需要 | 必需（在路径中：/run/workflow/{workflow_id}） |
| **尺寸/比例** | 有标准字段 | 无标准字段，通过节点参数映射 |
| **配置位置** | API配置 + 模板配置 | API配置 + 模板配置（request_body_template） |

### 主要特点

1. **工作流ID**: 每个工作流有唯一的ID，在接口路径中：`/run/workflow/{workflow_id}`
2. **节点参数映射**: 使用 `nodeInfoList` 数组动态修改工作流节点参数
3. **无标准参数**: 没有 prompt, size, aspectRatio 等标准参数
4. **异步API**: 返回 `taskId`，需要轮询查询结果

## 🔧 添加配置

### 方法1：使用脚本添加（推荐）

在项目根目录运行：

```bash
python scripts/add_runninghub_comfyui_config.py
```

### 方法2：通过管理后台添加

1. 登录管理后台
2. 访问 API 配置管理页面
3. 点击"添加配置"
4. 填写以下信息：

```
配置名称: RunningHub-ComfyUI工作流
API类型: runninghub-comfyui-workflow
国内Host: https://www.runninghub.cn
海外Host: https://www.runninghub.cn
API Key: [您的API Key]
绘画接口: /run/workflow/{workflow_id} (占位符，实际ID在模板中配置)
结果接口: /openapi/v2/task/outputs
```

## 📝 在风格分类/图片中配置工作流

### 配置步骤

1. **选择 API 配置**：
   - 在风格分类或风格图片的编辑页面
   - 启用"API模板"
   - 选择 `RunningHub-ComfyUI工作流` 类型的 API 配置

2. **填写工作流配置**（选择 RunningHub ComfyUI 工作流后会自动显示）：
   - **工作流ID**: 从 RunningHub 工作流页面获取，例如：`2004148282525949953`
   - **输入图片节点ID**: 图片节点ID，例如：`7` 或 `["7"]`（支持多个节点，用逗号分隔）
   - **输出节点ID**: 输出节点ID（可选，用于调试）
   - **提示词节点ID**: 提示词节点ID（可选），用户输入的提示词将自动映射到此节点
   - **参考图节点ID**: 参考图节点ID（可选），如果有多个上传入口，第二个图片将映射到此节点
   - **自定义提示词节点ID**: 自定义提示词节点ID（可选），用于固定提示词
   - **自定义提示词内容**: 自定义提示词内容（可选），将映射到自定义提示词节点

### 配置示例

**工作流ID**: `2004148282525949953`

**节点配置**:
- **输入图片节点ID**: `7`
- **提示词节点ID**: `6`
- **输出节点ID**: `4`（可选）
- **参考图节点ID**: `20`（可选）
- **自定义提示词节点ID**: `84`（可选）
- **自定义提示词内容**: `passport photo, white background`（可选）

**说明**:
- 配置格式与原本的 ComfyUI 工作流配置类似，更容易理解和操作
- 系统会自动将配置转换为 RunningHub 所需的 `nodeInfoList` 格式
- 图片会自动映射到输入图片节点的 `image` 参数
- 用户输入的提示词会自动映射到提示词节点的 `text` 参数
- 如果有多个上传入口，第二个图片会自动映射到参考图节点

## 🔄 请求格式

### 请求体示例

```json
{
  "nodeInfoList": [
    {
      "nodeId": "6",
      "inputs": {
        "text": "基于原图风格，将老奶奶替换为一只年迈慈祥的猴子奶奶..."
      }
    },
    {
      "nodeId": "7",
      "inputs": {
        "image": "https://example.com/image1.jpg"
      }
    }
  ],
  "addMetadata": false,
  "instanceType": "default",
  "usePersonalQueue": false
}
```

### 请求参数说明

- **nodeInfoList**: 节点参数映射列表（必填，由系统自动生成）
  - `nodeId`: 节点ID（从配置中获取）
  - `inputs`: 节点的输入参数对象
    - `image`: 图片URL（自动映射，占位符 `{{image_url}}` 会被替换为实际上传的图片）
    - `text`: 提示词（自动映射，占位符 `{{prompt}}` 会被替换为用户输入的提示词）
- **addMetadata**: 是否在输出图片中添加工作流元数据（可选，可在 `request_body_template` 中配置）
- **instanceType**: 运行实例类型，`default` (24G显存) 或 `plus` (48G显存)（可选，可在 `request_body_template` 中配置）
- **usePersonalQueue**: 是否使用个人独占队列（可选，可在 `request_body_template` 中配置）

**注意**: `nodeInfoList` 由系统根据配置的节点ID自动生成，无需手动编写JSON格式。

## 📥 响应格式

### 成功响应示例

```json
{
  "taskId": "2013508786110730241",
  "status": "RUNNING",
  "errorCode": "",
  "errorMessage": "",
  "results": null,
  "clientId": "f828b9af25161bc066ef152db7b29ccc",
  "promptTips": "{\"result\": true, \"error\": null, \"outputs_to_execute\": [\"4\"], \"node_errors\": {}}"
}
```

### 响应字段说明

- **taskId**: 任务ID，用于查询结果
- **status**: 任务状态（QUEUED, RUNNING, SUCCESS, FAILED）
- **errorCode**: 错误码（如果有）
- **errorMessage**: 错误信息（如果有）
- **results**: 结果（初始为 null，完成后包含图片URL）
- **promptTips**: ComfyUI 后端的校验信息（JSON字符串）

## 🔄 异步轮询

RunningHub ComfyUI 工作流 API 是异步API，返回 `taskId` 后需要轮询查询结果：

1. **提交任务**: 调用 `/run/workflow/{workflow_id}`，返回 `taskId`
2. **查询结果**: 使用 `taskId` 调用 `/openapi/v2/task/outputs` 查询结果
3. **状态检查**: 检查 `status` 字段，直到状态为 `SUCCESS` 或 `FAILED`

### 查询结果响应示例

```json
{
  "taskId": "2013508786110730241",
  "status": "SUCCESS",
  "errorCode": "",
  "errorMessage": "",
  "results": [
    {
      "url": "https://rh-images-1252422369.cos.ap-beijing.myqcloud.com/.../ComfyUI_00001_plhjr_1768892915.png",
      "outputType": "png",
      "text": null
    }
  ],
  "clientId": "",
  "promptTips": ""
}
```

## ⚠️ 注意事项

1. **工作流ID**: 每个工作流都有唯一的ID，需要在模板中配置
2. **节点参数映射**: 必须正确配置 `nodeInfoList`，否则工作流无法正常运行
3. **图片参数**: 图片URL需要映射到工作流中的图片节点（通常是 `image` 或 `imageUrls` 字段）
4. **提示词参数**: 提示词需要映射到工作流中的文本节点（通常是 `text` 字段）
5. **异步API**: RunningHub ComfyUI 工作流总是返回 `taskId`，需要轮询查询结果

## 🎯 界面配置说明

当在风格分类/图片的 API 模板配置中选择 `RunningHub-ComfyUI工作流` 类型的 API 配置时：

1. **标准配置项会自动隐藏**：
   - 默认提示词
   - 默认尺寸
   - 默认比例
   - 尺寸/比例可编辑选项

2. **工作流配置项会自动显示**（格式与原本的 ComfyUI 工作流配置类似）：
   - **工作流ID**: 输入框
   - **输入图片节点ID**: 输入框（必填）
   - **输出节点ID**: 输入框（可选）
   - **提示词节点ID**: 输入框（可选）
   - **参考图节点ID**: 输入框（可选）
   - **自定义提示词节点ID**: 输入框（可选）
   - **自定义提示词内容**: 文本域（可选）

3. **配置保存**：
   - 所有工作流配置会保存到 `request_body_template` 字段（JSON格式）
   - 系统会自动将分离字段转换为 RunningHub 所需的 `nodeInfoList` 格式
   - 图片和提示词会自动映射到对应的节点参数

## 📚 相关文档

- [RunningHub ComfyUI 工作流 API 文档](https://www.runninghub.cn/call-api/api-detail/2004375142916210689?apiType=3)
- [RunningHub 全能图片PRO 配置说明](./RunningHub配置说明.md)
- [API服务商集成说明](../API服务商集成说明.md)
