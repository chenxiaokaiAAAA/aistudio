# API服务商集成说明

## 已完成的工作

### 1. 数据库模型更新 ✅
- 在 `APIProviderConfig` 模型中添加了 `is_sync_api` 字段
- 字段类型：`BOOLEAN`，默认值：`False`
- 用途：区分同步API和异步API
  - `True` = 同步API（如 gemini-native）
  - `False` = 异步API（如 nano-banana）

### 2. 数据库迁移脚本 ✅
- 创建了 `scripts/database/add_is_sync_api_field.py` 迁移脚本
- 在 `test_server.py` 的 `migrate_database()` 函数中添加了自动迁移逻辑
- 启动项目时会自动检查并添加字段
- 会根据 `api_type` 自动设置 `is_sync_api` 的值（gemini-native 设为同步API）

### 3. 风格图片编辑页面结构 ✅
- 已在风格图片编辑模态框中添加了两个新的标签页链接：
  - "API编辑" 标签页
  - "API测试" 标签页

## 待完成的工作

### 1. 完善 API 编辑标签页内容
需要在 `AI-studio/templates/admin/styles.html` 的 `imageApiEdit` tab-pane 中添加完整的表单字段。

参考 `bk-photo-v3/templates/admin/ai_works_edit.html` 中的字段：
- API配置选择
- 模型名称选择
- 默认提示词
- 提示词是否可编辑
- 默认尺寸和比例
- 尺寸和比例是否可编辑
- 积分扣除
- 提示词优化（VEO模型）

### 2. 完善 API 测试标签页内容
需要在 `AI-studio/templates/admin/styles.html` 的 `imageApiTest` tab-pane 中添加测试功能。

参考 `bk-photo-v3/templates/ai_work.html` 中的测试逻辑：
- 图片上传
- 提示词输入（可选）
- 测试按钮
- 结果显示
- 轮询逻辑（区分同步/异步API）

### 3. 添加 JavaScript 函数
需要在 `AI-studio/templates/admin/styles.html` 的 JavaScript 部分添加以下函数：

#### API编辑相关：
- `loadApiConfigs()` - 加载API配置列表
- `toggleApiTemplateConfig()` - 切换API模板配置显示
- `loadApiTemplateData(imageId)` - 加载API模板数据
- `saveApiTemplate()` - 保存API模板配置

#### API测试相关：
- `handleApiTestImageUpload(file)` - 处理测试图片上传
- `testApiTemplate()` - 测试API模板
- `pollApiTestResult(taskId, isSyncApi)` - 轮询测试结果（区分同步/异步）

### 4. 创建后端API路由
需要在 `AI-studio/app/routes/admin_styles_api.py` 或创建新的路由文件添加以下接口：

#### API模板管理：
- `GET /api/admin/styles/images/<image_id>/api-template` - 获取API模板配置
- `POST /api/admin/styles/images/<image_id>/api-template` - 创建/更新API模板配置
- `DELETE /api/admin/styles/images/<image_id>/api-template` - 删除API模板配置

#### API测试：
- `POST /api/admin/styles/images/<image_id>/test-api` - 测试API模板
- `GET /api/admin/styles/images/test-api/task/<task_id>` - 获取测试任务状态

### 5. 集成到保存逻辑
需要在 `saveImage()` 函数中添加API模板的保存逻辑，将API模板数据保存到 `APITemplate` 表中。

## 实现步骤

### 步骤1：完善前端页面
1. 在 `imageApiEdit` tab-pane 中添加完整的表单字段（参考已添加的结构）
2. 在 `imageApiTest` tab-pane 中添加测试功能
3. 添加相应的 JavaScript 函数

### 步骤2：创建后端API
1. 在 `app/routes/admin_styles_api.py` 中添加API模板管理接口
2. 实现API测试接口（参考 bk-photo-v3 的 `ai_routes.py`）

### 步骤3：集成保存逻辑
1. 修改 `saveImage()` 函数，添加API模板数据的保存
2. 修改 `loadImageData()` 函数，加载API模板数据

### 步骤4：测试
1. 测试API模板的创建和编辑
2. 测试API模板的测试功能（同步和异步API）

## 参考文件

### bk-photo-v3 项目：
- `templates/admin/ai_works_edit.html` - AI模板编辑页面
- `templates/ai_work.html` - AI测试页面
- `ai_routes.py` - AI相关路由和API接口

### AI-studio 项目：
- `app/models.py` - 数据库模型（已更新）
- `templates/admin/styles.html` - 风格管理页面（部分更新）
- `app/routes/admin_styles_api.py` - 风格管理API路由

## 注意事项

1. **同步/异步API区分**：
   - 同步API（`is_sync_api=True`）：不需要轮询，直接返回结果
   - 异步API（`is_sync_api=False`）：需要轮询获取结果

2. **API模板优先级**：
   - 如果风格图片配置了API模板，优先使用API模板
   - 如果没有配置API模板，使用AI工作流配置

3. **数据存储**：
   - API模板数据存储在 `api_templates` 表中
   - 通过 `style_image_id` 关联到风格图片

4. **测试功能**：
   - 测试时需要使用真实的API配置
   - 需要处理API调用失败的情况
   - 需要区分同步和异步API的轮询逻辑

