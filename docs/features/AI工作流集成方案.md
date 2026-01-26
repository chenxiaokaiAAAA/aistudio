# AI工作流集成方案

## 📋 概述

本文档说明如何将AI模板功能（ComfyUI工作流调用）集成到现有的风格分类管理系统中，实现小程序用户选择AI写真产品后，自动调用对应的工作流进行AI处理。

---

## 🔄 现有系统架构

### 1. 数据模型关系

```
Product (产品)
  └── ProductStyleCategory (产品-风格分类绑定)
        └── StyleCategory (风格分类)
              └── StyleImage (风格图片)
```

**当前流程**：
1. 小程序用户选择产品（如"AI写真"）
2. 系统根据 `ProductStyleCategory` 获取该产品绑定的风格分类
3. 用户选择风格分类（如"拟人风格"）
4. 用户选择风格图片（如"威廉国王"）
5. 用户上传照片
6. 提交订单（目前只是保存订单，没有AI处理）

### 2. 现有数据模型

**StyleCategory（风格分类）**：
```python
- id
- name              # 分类名称，如"拟人风格"
- code              # 分类代码，如"anthropomorphic"
- description       # 分类描述
- icon              # 图标
- cover_image       # 封面图片URL
- sort_order        # 排序
- is_active         # 是否启用
- created_at
```

**StyleImage（风格图片）**：
```python
- id
- category_id        # 所属分类ID
- name              # 风格名称，如"威廉国王"
- code              # 风格代码，如"william"
- description       # 风格描述
- image_url         # 图片URL
- sort_order        # 排序
- is_active         # 是否启用
- created_at
```

---

## 🎯 AI模板功能核心逻辑

### 1. AI模板数据结构（参考项目）

```javascript
{
    "photoId": "1752637962943",              // 模板唯一ID
    "name": "吉卜力风格",                      // 模板名称
    "templateImage": "1752637962880-xxx.png", // 模板预览图
    "workflow": "1752739818841-xxx",          // 工作流名称（不含.json）
    "workflowFile": "1752739818841-xxx.json", // 工作流文件名
    "inputIds": ["199"],                      // 输入图片节点ID数组
    "outputId": "136",                        // 输出节点ID
    "refId": "20",                            // 参考图节点ID（可选）
    "refImage": "1752222086833-xxx.jpg",      // 参考图文件名（可选）
    "userPresetPromptId": "178",              // 用户预设提示词节点ID（可选）
    "customPrompt": {                         // 自定义提示词（可选）
        "content": "passport photo, white background",
        "id": "84"
    }
}
```

### 2. 工作流调用流程

```
1. 用户上传图片
   ↓
2. 上传图片到服务器，获取文件名
   ↓
3. 加载工作流JSON文件（prompt配置）
   ↓
4. 替换工作流中的参数：
   - 替换输入图片节点（inputIds）
   - 替换参考图节点（refId，如果有）
   - 设置提示词节点（customPrompt，如果有）
   ↓
5. 加载工作流配置（workflow结构）
   ↓
6. 组装ComfyUI API请求体
   ↓
7. 提交到ComfyUI服务器（/api/prompt）
   ↓
8. 获取prompt_id，等待处理结果
```

---

## 🔗 集成方案设计

### 方案一：在StyleCategory级别绑定工作流（推荐）

**设计思路**：
- 每个风格分类（StyleCategory）可以绑定一个AI工作流
- 当用户选择该风格分类下的任意风格图片时，都使用同一个工作流
- 工作流配置存储在 `StyleCategory` 模型中

**优点**：
- 简单直接，一个分类对应一个工作流
- 配置集中，易于管理
- 适合风格分类下所有图片使用相同处理逻辑的场景

**缺点**：
- 如果同一分类下不同图片需要不同工作流，无法支持

---

### 方案二：在StyleImage级别绑定工作流

**设计思路**：
- 每个风格图片（StyleImage）可以绑定一个独立的AI工作流
- 更灵活，可以为每个风格图片配置不同的处理逻辑

**优点**：
- 灵活性高，每个风格图片可以有不同的处理逻辑
- 适合不同风格图片需要不同工作流的场景

**缺点**：
- 配置分散，管理复杂
- 如果同一分类下多个图片使用相同工作流，需要重复配置

---

### 方案三：混合方案（推荐用于复杂场景）

**设计思路**：
- `StyleCategory` 可以配置默认工作流
- `StyleImage` 可以覆盖父分类的工作流配置
- 优先级：`StyleImage.workflow` > `StyleCategory.workflow`

**优点**：
- 兼顾灵活性和便利性
- 支持分类级别和图片级别的配置

**缺点**：
- 实现复杂度较高

---

## 💡 采用方案：方案三（混合方案）

基于业务需求，采用**方案三（混合方案）**：
- `StyleCategory` 可以配置默认工作流（分类级别）
- `StyleImage` 可以覆盖父分类的工作流配置（图片级别）
- 优先级：`StyleImage.workflow` > `StyleCategory.workflow`
- 兼顾灵活性和便利性，支持不同场景的需求

**图片来源说明**：
- 优先使用美颜API处理后的图片（`retouch_completed_at` 不为空时）
- 如果美颜API未配置或未处理，使用自拍机拍摄的原图
- 图片来源自动判断，无需用户选择

**工作流预览图**：
- 使用风格模板的图片（`StyleImage.image_url` 或 `StyleCategory.cover_image`）
- 不需要单独存储工作流预览图，避免重复

---

## 📊 数据库设计

### 1. 扩展 StyleCategory 模型（分类级别工作流配置）

在 `app/models.py` 中为 `StyleCategory` 添加工作流相关字段：

```python
class StyleCategory(db.Model):
    # ... 现有字段 ...
    
    # ⭐ AI工作流相关字段（新增）- 分类级别默认配置
    workflow_name = db.Column(db.String(200))          # 工作流名称（不含.json）
    workflow_file = db.Column(db.String(200))          # 工作流文件名（含.json）
    workflow_input_ids = db.Column(db.Text)            # 输入图片节点ID（JSON数组字符串，如["199"]）
    workflow_output_id = db.Column(db.String(50))      # 输出节点ID
    workflow_ref_id = db.Column(db.String(50))         # 参考图节点ID（可选）
    workflow_ref_image = db.Column(db.String(500))     # 参考图文件名（可选）
    workflow_user_prompt_id = db.Column(db.String(50)) # 用户预设提示词节点ID（可选）
    workflow_custom_prompt_id = db.Column(db.String(50)) # 自定义提示词节点ID（可选）
    workflow_custom_prompt_content = db.Column(db.Text) # 自定义提示词内容（可选）
    is_ai_enabled = db.Column(db.Boolean, default=False) # 是否启用AI工作流处理（分类级别）
```

### 2. 扩展 StyleImage 模型（图片级别工作流配置）

在 `app/models.py` 中为 `StyleImage` 添加工作流相关字段：

```python
class StyleImage(db.Model):
    # ... 现有字段 ...
    
    # ⭐ AI工作流相关字段（新增）- 图片级别配置（覆盖分类配置）
    workflow_name = db.Column(db.String(200))          # 工作流名称（不含.json），如果为空则使用分类配置
    workflow_file = db.Column(db.String(200))          # 工作流文件名（含.json）
    workflow_input_ids = db.Column(db.Text)            # 输入图片节点ID（JSON数组字符串）
    workflow_output_id = db.Column(db.String(50))      # 输出节点ID
    workflow_ref_id = db.Column(db.String(50))         # 参考图节点ID（可选）
    workflow_ref_image = db.Column(db.String(500))     # 参考图文件名（可选）
    workflow_user_prompt_id = db.Column(db.String(50)) # 用户预设提示词节点ID（可选）
    workflow_custom_prompt_id = db.Column(db.String(50)) # 自定义提示词节点ID（可选）
    workflow_custom_prompt_content = db.Column(db.Text) # 自定义提示词内容（可选）
    is_ai_enabled = db.Column(db.Boolean)              # 是否启用AI工作流（如果为None，继承分类配置）
```

### 3. 创建 AITask 模型（AI任务管理）

在 `app/models.py` 中创建新的 `AITask` 模型：

```python
class AITask(db.Model):
    """AI工作流任务"""
    __tablename__ = 'ai_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    order = db.relationship('Order', backref=db.backref('ai_tasks', lazy=True))
    order_number = db.Column(db.String(50), nullable=False)  # 订单号（冗余字段，便于查询）
    
    # 工作流配置信息（保存任务创建时的配置）
    workflow_name = db.Column(db.String(200))          # 工作流名称
    workflow_file = db.Column(db.String(200))          # 工作流文件名
    style_category_id = db.Column(db.Integer, db.ForeignKey('style_category.id'))  # 风格分类ID
    style_image_id = db.Column(db.Integer, db.ForeignKey('style_image.id'))      # 风格图片ID
    
    # 输入图片信息
    input_image_path = db.Column(db.String(500))       # 输入图片路径（原图或美颜后的图）
    input_image_type = db.Column(db.String(20), default='original')  # original/retouched
    
    # ComfyUI任务信息
    comfyui_prompt_id = db.Column(db.String(100))      # ComfyUI返回的prompt_id
    comfyui_node_id = db.Column(db.String(50))         # 输出节点ID
    
    # 任务状态
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed, cancelled
    # pending: 待处理
    # processing: 处理中
    # completed: 已完成
    # failed: 失败
    # cancelled: 已取消
    
    # 输出结果
    output_image_path = db.Column(db.String(500))       # 输出图片路径（效果图）
    
    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.now)  # 任务创建时间
    started_at = db.Column(db.DateTime)                # 任务开始处理时间
    completed_at = db.Column(db.DateTime)              # 任务完成时间
    estimated_completion_time = db.Column(db.DateTime) # 预计完成时间
    
    # 错误信息
    error_message = db.Column(db.Text)                  # 错误信息
    error_code = db.Column(db.String(50))               # 错误代码
    retry_count = db.Column(db.Integer, default=0)     # 重试次数
    
    # 处理信息
    processing_log = db.Column(db.Text)                 # 处理日志（JSON格式）
    comfyui_response = db.Column(db.Text)               # ComfyUI响应数据（JSON格式）
    
    # 备注
    notes = db.Column(db.Text)                         # 备注信息
```

### 4. 创建 AIConfig 模型（AI配置管理）

在 `app/models.py` 中创建新的 `AIConfig` 模型：

```python
class AIConfig(db.Model):
    """AI工作流系统配置"""
    __tablename__ = 'ai_config'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(50), unique=True, nullable=False)  # 配置键
    config_value = db.Column(db.Text)                                   # 配置值
    description = db.Column(db.String(200))                             # 配置说明
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 常用配置键：
    # 'comfyui_base_url' - ComfyUI服务器地址，如 'http://sm003:8188'
    # 'comfyui_api_endpoint' - API端点，如 '/api/prompt'
    # 'comfyui_timeout' - 超时时间（秒）
    # 'prefer_retouched_image' - 是否优先使用美颜后的图片（true/false）
    # 'auto_retry_on_failure' - 失败后是否自动重试（true/false）
    # 'max_retry_count' - 最大重试次数
```

### 5. 工作流文件存储

创建目录结构：
```
AI-studio/
├── workflows/                    # 工作流JSON文件存储目录（新增）
│   └── *.json                   # ComfyUI工作流文件
└── static/
    └── images/                   # 风格模板图片（已存在，用作工作流预览图）
        └── ...
```

---

## 🔧 实现步骤

### 阶段1：数据库扩展

1. **创建数据库迁移脚本**：
   - 为 `style_category` 表添加工作流相关字段
   - 创建 `workflows/` 目录

2. **更新模型定义**：
   - 在 `app/models.py` 中扩展 `StyleCategory` 模型

### 阶段2：管理后台功能

1. **扩展风格分类管理页面**：
   - 在 `/admin/styles` 页面添加"AI工作流配置"区域
   - 支持上传工作流JSON文件
   - 支持配置工作流参数（inputIds、outputId等）

2. **添加API接口**：
   - `POST /api/admin/styles/workflow/upload` - 上传工作流文件
   - `GET /api/admin/styles/workflow/<filename>` - 获取工作流文件
   - `PUT /api/admin/styles/categories/<id>/workflow` - 更新工作流配置

### 阶段3：工作流调用服务

1. **创建工作流服务**：
   - `app/services/workflow_service.py` - 封装工作流调用逻辑

2. **主要功能**：
   - `get_workflow_config()` - 获取工作流配置（支持分类级别和图片级别）
   - `get_input_image()` - 获取输入图片（优先使用美颜后的图片，否则使用原图）
   - `load_workflow_file()` - 加载工作流JSON文件
   - `replace_workflow_params()` - 替换工作流参数
   - `submit_to_comfyui()` - 提交到ComfyUI
   - `check_workflow_status()` - 检查处理状态
   - `get_workflow_result()` - 获取处理结果
   - `create_ai_task()` - 创建AI任务记录
   - `retry_ai_task()` - 重新处理任务
   - `get_comfyui_config()` - 获取ComfyUI配置（从数据库读取）

### 阶段4：订单处理集成

1. **修改订单创建逻辑**：
   - 在 `app/services/order_service.py` 中，订单创建后检查是否启用AI工作流
   - 如果启用，自动创建AI任务并调用工作流处理
   - 图片来源自动判断：优先使用美颜后的图片（`retouch_completed_at` 不为空），否则使用原图

2. **订单状态扩展**：
   - 保持现有订单状态不变
   - AI处理状态由 `AITask` 模型管理，不直接修改订单状态
   - 订单的 `final_image` 字段在AI任务完成后自动更新

3. **结果保存**：
   - 工作流处理完成后，将结果图片保存到订单的 `final_image` 字段
   - 同时保存到 `AITask.output_image_path` 字段
   - 更新 `AITask.status` 为 `completed`
   - 更新 `AITask.completed_at` 时间

### 阶段5：小程序集成

1. **无需修改小程序代码**：
   - 小程序流程保持不变：选择产品 -> 选择风格 -> 上传照片 -> 提交订单
   - 后端自动处理AI工作流，用户无需感知

2. **订单详情页优化**（可选）：
   - 显示AI处理进度（预计完成时间、当前状态）
   - 显示处理日志（如果有错误）
   - 不提供"重新处理"功能（由管理后台处理）

---

## 📝 详细实现逻辑

### 1. 工作流配置数据结构

```python
# StyleCategory 中的工作流配置
{
    "workflow_name": "anthropomorphic_workflow",
    "workflow_file": "anthropomorphic_workflow.json",
    "workflow_input_ids": ["199"],           # JSON字符串，存储为 ["199"]
    "workflow_output_id": "136",
    "workflow_ref_id": "20",                 # 可选
    "workflow_ref_image": "ref_image.jpg",   # 可选
    "workflow_user_prompt_id": "178",        # 可选
    "workflow_custom_prompt_id": "84",       # 可选
    "workflow_custom_prompt_content": "passport photo, white background",  # 可选
    "is_ai_enabled": True
}
```

### 2. 工作流调用流程（Python实现）

```python
# app/services/workflow_service.py

def process_order_with_workflow(order_id, style_category_id, user_image_path):
    """
    使用工作流处理订单
    
    Args:
        order_id: 订单ID
        style_category_id: 风格分类ID
        user_image_path: 用户上传的图片路径
    
    Returns:
        tuple: (success: bool, prompt_id: str, error_message: str)
    """
    # 1. 获取风格分类的工作流配置
    category = StyleCategory.query.get(style_category_id)
    if not category or not category.is_ai_enabled:
        return False, None, "风格分类未启用AI工作流"
    
    # 2. 上传用户图片到ComfyUI服务器（如果需要）
    # 或者直接使用本地路径
    
    # 3. 加载工作流JSON文件
    workflow_file_path = os.path.join('workflows', category.workflow_file)
    with open(workflow_file_path, 'r', encoding='utf-8') as f:
        workflow_data = json.load(f)
    
    # 4. 解析工作流配置
    input_ids = json.loads(category.workflow_input_ids) if category.workflow_input_ids else []
    output_id = category.workflow_output_id
    
    # 5. 替换工作流参数
    # 5.1 替换输入图片
    if input_ids and len(input_ids) > 0:
        workflow_data[input_ids[0]]['inputs']['image'] = user_image_path
    
    # 5.2 替换参考图（如果有）
    if category.workflow_ref_id and category.workflow_ref_image:
        workflow_data[category.workflow_ref_id]['inputs']['image'] = category.workflow_ref_image
    
    # 5.3 设置自定义提示词（如果有）
    if category.workflow_custom_prompt_id and category.workflow_custom_prompt_content:
        workflow_data[category.workflow_custom_prompt_id]['inputs']['text'] = category.workflow_custom_prompt_content
    
    # 6. 加载工作流结构（从workflow字段获取）
    workflow_structure = workflow_data.get('workflow', {})
    
    # 7. 组装ComfyUI API请求
    request_body = {
        "prompt": workflow_data,
        "client_id": f"order_{order_id}_{int(time.time())}"
    }
    
    # 8. 提交到ComfyUI
    comfyui_url = "http://your-comfyui-server:8188/api/prompt"
    response = requests.post(comfyui_url, json=request_body)
    
    if response.status_code == 200:
        result = response.json()
        prompt_id = result.get('prompt_id')
        return True, prompt_id, None
    else:
        return False, None, f"提交失败: {response.text}"
```

### 3. 订单创建后自动处理

```python
# app/services/order_service.py

def create_miniprogram_order(data, ...):
    """创建小程序订单"""
    # ... 现有订单创建逻辑 ...
    
    # 订单创建成功后，检查是否需要AI处理
    if order.style_category_id:
        category = StyleCategory.query.get(order.style_category_id)
        if category and category.is_ai_enabled:
            # 异步调用工作流处理
            from app.services.workflow_service import process_order_with_workflow
            
            # 获取用户上传的图片路径
            user_image_path = order.original_image  # 或从OrderImage获取
            
            # 调用工作流处理
            success, prompt_id, error = process_order_with_workflow(
                order.id,
                order.style_category_id,
                user_image_path
            )
            
            if success:
                # 更新订单状态为AI处理中
                order.status = 'ai_processing'
                order.ai_prompt_id = prompt_id  # 需要添加此字段
                db.session.commit()
            else:
                # 记录错误，但不影响订单创建
                print(f"AI工作流处理失败: {error}")
    
    return result
```

---

## 🔄 完整业务流程

### 小程序端流程（无需修改）

```
1. 用户选择产品（如"AI写真"）
   ↓
2. 系统返回该产品绑定的风格分类列表
   ↓
3. 用户选择风格分类（如"拟人风格"）
   ↓
4. 系统返回该分类下的风格图片列表
   ↓
5. 用户选择风格图片（如"威廉国王"）
   ↓
6. 用户上传照片
   ↓
7. 提交订单
```

### 后端处理流程（新增）

```
1. 接收订单创建请求
   ↓
2. 创建订单记录
   ↓
3. 检查订单关联的风格分类是否启用AI工作流
   ↓
4. 如果启用：
   a. 获取工作流配置
   b. 加载工作流JSON文件
   c. 替换工作流参数（用户图片、参考图、提示词等）
   d. 提交到ComfyUI服务器
   e. 获取prompt_id，更新订单状态为"AI处理中"
   f. 异步轮询ComfyUI，获取处理结果
   g. 处理完成后，保存结果图片，更新订单状态为"AI处理完成"
   ↓
5. 返回订单创建成功
```

---

## 📁 文件结构

### 新增文件

```
AI-studio/
├── app/
│   ├── models.py                    # 扩展：添加AITask、AIConfig模型
│   ├── services/
│   │   └── workflow_service.py     # 工作流服务（新增）
│   └── routes/
│       ├── admin.py                 # 扩展：添加工作流管理路由
│       └── ai.py                    # AI任务管理路由（新增）
│
├── workflows/                       # 工作流文件目录（新增）
│   └── *.json
│
└── templates/
    └── admin/
        ├── styles.html              # 扩展：添加工作流配置UI
        ├── ai_tasks.html            # AI任务管理页面（新增）
        ├── ai_config.html           # AI配置管理页面（新增）
        └── order_detail.html        # 扩展：添加AI处理进度显示
```

---

## 🔌 ComfyUI集成配置

### 1. ComfyUI服务器配置

需要在配置文件中添加ComfyUI服务器地址：

```python
# config/config.yml 或 server_config.py

COMFYUI_CONFIG = {
    'base_url': 'http://your-comfyui-server:8188',
    'api_endpoint': '/api/prompt',
    'status_endpoint': '/api/history',
    'result_endpoint': '/api/view',
    'timeout': 300  # 超时时间（秒）
}
```

### 2. 工作流文件格式

工作流文件必须是ComfyUI兼容的JSON格式，包含：
- 节点配置（`prompt`）
- 工作流结构（`workflow`，可选）

---

## ⚠️ 注意事项

1. **工作流文件管理**：
   - 工作流JSON文件需要存储在服务器可访问的目录
   - 确保文件路径正确，支持相对路径和绝对路径

2. **节点ID配置**：
   - `inputIds`、`outputId` 等节点ID必须与工作流JSON中的节点ID对应
   - 建议在管理后台添加节点ID验证功能

3. **异步处理**：
   - ComfyUI处理是异步的，需要轮询或使用WebSocket获取结果
   - 建议使用后台任务队列（如Celery）处理长时间任务

4. **错误处理**：
   - 工作流调用失败不应影响订单创建
   - 需要完善的错误日志和用户提示

5. **性能优化**：
   - 工作流文件可以缓存，避免重复读取
   - 考虑使用Redis缓存工作流配置

6. **安全性**：
   - 工作流文件上传需要验证JSON格式
   - 限制文件大小和上传频率

---

## 📋 开发检查清单

### 数据库
- [ ] 创建数据库迁移脚本，添加工作流相关字段到 `StyleCategory` 和 `StyleImage`
- [ ] 创建 `AITask` 模型表
- [ ] 创建 `AIConfig` 模型表
- [ ] 初始化 `AIConfig` 默认配置（ComfyUI地址等）
- [ ] 创建 `workflows/` 目录

### 后端服务
- [ ] 创建 `app/services/workflow_service.py`
- [ ] 实现 `get_workflow_config()` - 支持混合方案（图片级别 > 分类级别）
- [ ] 实现 `get_input_image()` - 优先使用美颜后的图片
- [ ] 实现 `create_ai_task()` - 创建AI任务并提交到ComfyUI
- [ ] 实现 `retry_ai_task()` - 重新处理任务
- [ ] 实现 `get_comfyui_config()` - 从数据库读取配置
- [ ] 实现工作流文件上传接口
- [ ] 实现工作流配置更新接口（分类级别和图片级别）
- [ ] 实现ComfyUI调用逻辑
- [ ] 实现结果获取和保存逻辑（轮询或WebSocket）

### 管理后台
- [ ] 扩展风格分类管理页面，添加工作流配置UI（分类级别）
- [ ] 扩展风格图片管理，添加工作流配置UI（图片级别）
- [ ] 添加工作流文件上传功能
- [ ] 添加工作流参数配置表单
- [ ] 创建AI任务管理页面（`/admin/ai/tasks`）
  - [ ] 显示任务列表（订单号、输入图片、输出图片、状态、预计完成时间、错误信息）
  - [ ] 支持筛选和搜索
  - [ ] 支持手动上传原图
  - [ ] 支持重新处理功能
  - [ ] 显示处理日志和错误详情
- [ ] 创建AI配置管理页面（`/admin/ai/config`）
  - [ ] 显示和修改ComfyUI服务器地址
  - [ ] 配置图片来源优先级
  - [ ] 配置超时时间、重试次数等
- [ ] 扩展订单详情页面
  - [ ] 显示AI处理进度（预计完成时间、是否收到图片、是否有报错）
  - [ ] 显示AI任务列表
  - [ ] 支持重新处理功能
  - [ ] 显示处理日志

### 订单处理
- [ ] 修改订单创建逻辑，集成工作流调用
- [ ] 实现图片来源自动判断（优先美颜后的图片）
- [ ] 实现异步结果获取机制（轮询ComfyUI状态）
- [ ] 结果保存到订单的 `final_image` 字段

### 测试
- [ ] 测试工作流文件上传
- [ ] 测试工作流配置保存（分类级别和图片级别）
- [ ] 测试混合方案：图片级别配置覆盖分类级别配置
- [ ] 测试图片来源优先级：优先使用美颜后的图片
- [ ] 测试ComfyUI调用
- [ ] 测试AI任务创建和管理
- [ ] 测试重新处理功能
- [ ] 测试完整流程：订单创建 -> AI处理 -> 结果保存
- [ ] 测试配置管理：动态修改ComfyUI地址

---

## 🎯 后续优化方向

1. **工作流模板库**：
   - 创建常用工作流模板库
   - 支持一键应用模板

2. **批量处理**：
   - 支持批量订单的AI处理
   - 优化处理队列

3. **结果预览**：
   - 在管理后台预览AI处理结果
   - 支持重新处理

4. **性能监控**：
   - 监控ComfyUI处理时间
   - 统计处理成功率

5. **多ComfyUI服务器**：
   - 支持配置多个ComfyUI服务器
   - 实现负载均衡

---

**文档版本**：v1.0  
**创建时间**：2026-01-14  
**最后更新**：2026-01-14
