# API模板管理模块说明

## 模块化安排

### ✅ 已确认：API模板管理属于风格管理模块

**API模板管理功能将添加到现有的 `app/routes/admin_styles_api.py` 模块中**，原因：

1. **功能关联性强**：API模板是风格图片的配置项，与风格管理紧密相关
2. **数据模型关联**：`APITemplate` 模型通过 `style_image_id` 关联到 `StyleImage`
3. **管理界面集成**：API编辑和测试标签页已经集成在风格图片编辑模态框中
4. **避免过度拆分**：不需要单独创建新模块，保持代码组织清晰

### 模块结构

```
app/routes/admin_styles_api.py  (现有模块)
├── 风格分类管理API
├── 风格图片管理API
├── AI工作流测试API
└── API模板管理API (新增)
    ├── GET  /api/admin/styles/images/<image_id>/api-template
    ├── POST /api/admin/styles/images/<image_id>/api-template
    ├── POST /api/admin/styles/images/<image_id>/test-api
    └── GET  /api/admin/styles/images/test-api/task/<task_id>
```

### 不需要单独拆分的理由

1. **路由数量适中**：只有4个API接口，不需要单独模块
2. **功能内聚**：都是风格图片相关的配置和管理
3. **维护方便**：相关代码集中在一个文件中，便于维护
4. **符合现有架构**：与项目中其他模块的拆分标准一致

## 需要添加的API接口

### 1. 获取API模板配置
```python
@admin_styles_api_bp.route('/images/<int:image_id>/api-template', methods=['GET'])
@login_required
def get_api_template(image_id):
    """获取风格图片的API模板配置"""
    # 实现逻辑
```

### 2. 保存API模板配置
```python
@admin_styles_api_bp.route('/images/<int:image_id>/api-template', methods=['POST'])
@login_required
def save_api_template(image_id):
    """保存风格图片的API模板配置"""
    # 实现逻辑
```

### 3. 测试API模板
```python
@admin_styles_api_bp.route('/images/<int:image_id>/test-api', methods=['POST'])
@login_required
def test_api_template(image_id):
    """测试API模板"""
    # 实现逻辑
```

### 4. 获取测试任务状态
```python
@admin_styles_api_bp.route('/images/test-api/task/<task_id>', methods=['GET'])
@login_required
def get_api_test_task_status(task_id):
    """获取API测试任务状态"""
    # 实现逻辑
```

## 数据模型

### APITemplate 模型（已存在）
- `style_image_id` - 关联到风格图片
- `api_config_id` - 关联到API配置
- `model_name` - 模型名称
- `default_prompt` - 默认提示词
- `default_size` - 默认尺寸
- `default_aspect_ratio` - 默认比例
- `points_cost` - 积分扣除
- `prompt_editable` - 提示词是否可编辑
- `size_editable` - 尺寸是否可编辑
- `aspect_ratio_editable` - 比例是否可编辑
- `enhance_prompt` - 是否优化提示词

## 参考实现

参考 `bk-photo-v3` 项目中的：
- `ai_routes.py` - AI相关路由和API接口
- `templates/admin/ai_works_edit.html` - AI模板编辑页面
- `templates/ai_work.html` - AI测试页面

## 总结

✅ **API模板管理功能将添加到 `admin_styles_api.py` 模块中**
✅ **不需要单独拆分模块**
✅ **符合项目现有的模块化架构**
✅ **便于维护和扩展**

