# AI调用模块集成方案

## 需求概述

将 bk-photo 项目中的云端API服务商调用功能集成到 AI-studio 项目中，与现有的 ComfyUI 工作流调用、美图API调用形成统一的AI调用体系。

## 功能需求

### 1. 风格分类管理页面扩展
在编辑风格模板图片时，现有3个标签页：
- ✅ 基本信息
- ✅ AI工作流配置（ComfyUI）
- ✅ 测试工作流

**新增2个标签页**：
- 📝 **API调用模板**：配置云端API服务商调用参数
  - 服务商选择
  - 模型名称
  - 尺寸配置
  - 默认提示词
  - 上传图片入口
  - 积分扣除配置
  - 请求体配置等

- 🧪 **API出图测试**：测试云端API调用
  - 上传测试图片
  - 选择服务商
  - 提交任务
  - 查看结果

### 2. 管理后台新增入口
- **API服务商配置**：管理所有API服务商配置
  - 服务商信息
  - API密钥
  - 重试配置
  - 任务失败切换服务商逻辑

## 代码组织方案

### 目录结构

```
AI-studio/
├── app/
│   ├── services/              # 服务层（业务逻辑）
│   │   ├── __init__.py
│   │   ├── workflow_service.py        # ComfyUI工作流调用（已有）
│   │   ├── meitu_api_service.py        # 美图API调用（已有）
│   │   ├── ai_provider_service.py      # 云端API服务商调用（新增）
│   │   └── ai_call_unified.py          # 统一AI调用接口（新增）
│   │
│   ├── routes/                # 路由层（API端点）
│   │   ├── ai.py              # AI任务管理（已有）
│   │   ├── meitu.py            # 美图API管理（已有）
│   │   └── ai_provider.py     # API服务商管理（新增）
│   │
│   ├── models.py               # 数据模型
│   │   ├── StyleCategory       # 风格分类（已有）
│   │   ├── StyleImage          # 风格图片（已有）
│   │   ├── AITask              # AI任务（已有）
│   │   ├── AIConfig            # AI配置（已有）
│   │   ├── MeituAPIConfig      # 美图API配置（已有）
│   │   ├── APIProviderConfig   # API服务商配置（新增）
│   │   └── APITemplate         # API调用模板（新增）
│   │
│   └── utils/                  # 工具函数
│       └── ai_call_utils.py    # AI调用通用工具（新增）
│
└── templates/
    └── admin/
        ├── styles.html         # 风格管理页面（需扩展）
        ├── ai_provider_config.html  # API服务商配置页面（新增）
        └── api_template_test.html   # API出图测试页面（新增）
```

### 模块职责划分

#### 1. 服务层（services/）

**`ai_provider_service.py`** - 云端API服务商调用服务
- 调用不同服务商的API（OpenAI、Gemini、豆包等）
- 处理请求体构建
- 处理响应解析
- 错误处理和重试逻辑

**`ai_call_unified.py`** - 统一AI调用接口
- 根据配置选择调用方式（ComfyUI / 美图API / 云端API）
- 统一的任务创建接口
- 统一的结果处理接口

#### 2. 路由层（routes/）

**`ai_provider.py`** - API服务商管理路由
- API服务商配置CRUD
- 服务商测试接口
- 重试配置管理

#### 3. 数据模型

**`APIProviderConfig`** - API服务商配置
- 服务商名称
- API密钥
- 模型列表
- 重试配置
- 优先级等

**`APITemplate`** - API调用模板
- 关联到 StyleImage
- 服务商选择
- 模型名称
- 尺寸配置
- 提示词模板
- 请求体模板
- 积分扣除等

## 实现步骤

### 阶段1：代码组织（基础架构）
1. ✅ 创建 `app/services/ai_provider_service.py`
2. ✅ 创建 `app/services/ai_call_unified.py`
3. ✅ 创建 `app/routes/ai_provider.py`
4. ✅ 在 `app/models.py` 中添加新模型

### 阶段2：API服务商配置管理
1. ✅ 创建 API服务商配置页面
2. ✅ 实现服务商CRUD功能
3. ✅ 实现重试配置管理

### 阶段3：API调用模板配置
1. ✅ 在风格管理页面添加"API调用模板"标签页
2. ✅ 实现模板配置表单
3. ✅ 实现模板保存和加载

### 阶段4：API出图测试
1. ✅ 在风格管理页面添加"API出图测试"标签页
2. ✅ 实现测试图片上传
3. ✅ 实现任务提交和结果展示

### 阶段5：任务失败重试逻辑
1. ✅ 实现服务商切换逻辑
2. ✅ 实现自动重试机制
3. ✅ 实现重试记录和日志

## 关键设计决策

### 1. 统一调用接口
所有AI调用都通过 `ai_call_unified.py` 的统一接口，内部根据配置选择具体实现：
- ComfyUI → `workflow_service.py`
- 美图API → `meitu_api_service.py`
- 云端API → `ai_provider_service.py`

### 2. 模板配置优先级
- 图片级别 > 分类级别（与ComfyUI工作流一致）
- 支持图片级别覆盖分类级别的默认配置

### 3. 重试策略
- 任务失败时，自动切换到下一个可用的服务商
- 记录已尝试的服务商，避免重复尝试
- 支持全局重试开关

### 4. 数据模型关系
```
StyleCategory (风格分类)
  └── StyleImage (风格图片)
      ├── ComfyUI工作流配置（已有）
      ├── 美图API预设配置（已有）
      └── API调用模板（新增）
          └── APIProviderConfig (服务商配置)
```

## 注意事项

1. **代码复用**：尽量复用 bk-photo 项目中已验证的逻辑
2. **向后兼容**：确保不影响现有的 ComfyUI 和美图API功能
3. **模块化**：每个调用方式独立，便于维护和扩展
4. **统一接口**：对外提供统一的调用接口，内部实现可替换
