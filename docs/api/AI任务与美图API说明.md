# AI 任务与美图 API 说明

> **文档索引**：详见 `docs/api/API文档索引与复用说明.md`  
> **错误码**：`docs/api/API错误码说明.md` | **请求示例**：`docs/api/API请求响应示例.md`

## 一、AI 任务 API

**路径前缀**：`/admin/ai`  
**认证**：Session 登录（管理员/运营）  
**文件位置**：`app/routes/ai_tasks_api.py`、`app/routes/ai.py`

### 1.1 任务列表与详情

| 路径 | 方法 | 说明 |
|------|------|------|
| `/admin/ai/api/tasks` | GET | 获取 AI 任务列表 |
| `/admin/ai/api/tasks/<task_id>` | GET | 获取任务详情 |

### 1.2 查询参数（任务列表）

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认 1 |
| per_page | int | 每页条数，默认 10 |
| status | string | 状态筛选：pending/processing/completed/failed |
| order_number | string | 订单号模糊查询 |
| start_date | string | 开始日期 (ISO) |
| end_date | string | 结束日期 (ISO) |
| image_type | string | 图片类型 |
| playground_only | bool | 仅 Playground 任务 |

### 1.3 页面路由

| 路径 | 方法 | 说明 |
|------|------|------|
| `/admin/ai/tasks` | GET | AI 任务管理页面 |
| `/admin/ai/config` | GET | AI 配置管理页面 |

### 1.4 相关模块

- **API 服务商配置**：`/admin/ai-provider` - API 提供方配置（ComfyUI、RunningHub 等）
- **AI 配置**：`app/routes/ai_config_api.py` - 工作流、轮询等配置
- **AI 调试**：`app/routes/ai_debug_api.py` - 调试接口

---

## 二、美图 API

**路径前缀**：`/admin/meitu`  
**认证**：Session 登录（管理员/运营）  
**文件位置**：`app/routes/meitu/`

### 2.1 配置管理

| 路径 | 方法 | 说明 |
|------|------|------|
| `/admin/meitu/config` | GET | 美图配置页面 |
| `/admin/meitu/api/config` | GET | 获取美图 API 配置 |
| `/admin/meitu/api/config` | POST | 保存美图 API 配置 |

### 2.2 预设管理

| 路径 | 方法 | 说明 |
|------|------|------|
| `/admin/meitu/api/presets` | GET | 预设列表 |
| `/admin/meitu/api/presets` | POST | 创建预设 |
| `/admin/meitu/api/presets/<preset_id>` | GET | 预设详情 |
| `/admin/meitu/api/presets/<preset_id>` | PUT | 更新预设 |
| `/admin/meitu/api/presets/<preset_id>` | DELETE | 删除预设 |
| `/admin/meitu/api/style-categories` | GET | 风格分类列表 |
| `/admin/meitu/api/style-images` | GET | 风格图片列表 |

### 2.3 任务管理

| 路径 | 方法 | 说明 |
|------|------|------|
| `/admin/meitu/tasks` | GET | 美颜任务管理页面 |
| `/admin/meitu/api/tasks` | GET | 美颜任务列表 |
| `/admin/meitu/api/tasks/<task_id>` | GET | 任务详情 |
| `/admin/meitu/api/tasks/<task_id>/recheck` | POST | 重新查询任务结果 |

### 2.4 任务列表查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| per_page | int | 每页条数 |
| order_number | string | 订单号 |

---

## 三、请求示例

### 3.1 AI 任务列表

```bash
curl "https://your-server/admin/ai/api/tasks?page=1&per_page=10&status=processing" \
  -H "Cookie: session=..."
```

### 3.2 美图配置保存

```bash
curl -X POST "https://your-server/admin/meitu/api/config" \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "api_key": "your_key",
    "api_secret": "your_secret",
    "api_base_url": "https://api.yunxiu.meitu.com",
    "enable_in_workflow": true
  }'
```

### 3.3 美图任务重新查询

```bash
curl -X POST "https://your-server/admin/meitu/api/tasks/123/recheck" \
  -H "Cookie: session=..."
```

---

## 四、相关文档

- **管理后台API接口说明文档.md** - 管理后台完整接口
- **docs/features/AI任务管理页面设计.md** - AI 任务页面设计
- **docs/api/API服务商集成说明.md** - API 服务商配置
- **Swagger** - 启动服务后访问 `/docs`，选择「管理后台」标签

---

**最后更新**：2026-02-09
