# API 文档索引与复用说明

> 本文档梳理项目中现有 API 文档，说明可复用内容及补充方向。

---

## 一、现有文档清单

| 文档 | 路径 | 内容概要 | 可复用性 |
|------|------|----------|----------|
| **管理后台API接口说明文档** | 根目录 | 小程序+管理后台+自拍机综合接口 | ✅ 主体可复用，需修正路径、补充 2.6 |
| **小程序API接口说明文档** | 根目录 | 66 个接口清单，按模块分类 | ✅ 完整，可直接引用 |
| **小程序API接口清单** | docs/other/ | 与根目录版类似 | ⚠️ 与根目录版重复，建议以根目录为准 |
| **API接口文档** | docs/other/ | 与 管理后台API 内容几乎相同 | ⚠️ 重复，建议统一到根目录 |
| **项目完整功能文档** | docs/other/ | 含 API 列表（/api/admin/ 前缀） | ✅ 可参考路径与模块划分 |
| **API错误码说明** | docs/api/ | 错误码、HTTP 状态、处理建议 | ✅ 已完善 |
| **API请求响应示例** | docs/api/ | 主要接口 JSON 示例、curl | ✅ 已完善 |
| **加盟商与选片API说明** | docs/api/ | 加盟商额度/账户、选片流程 | ✅ 已完善 |
| **AI任务与美图API说明** | docs/api/ | AI 任务、美图配置/预设/任务 | ✅ 已完善 |
| **API接口详细说明** | docs/api/ | 核心接口请求参数、类型、响应格式 | ✅ 已完善 |
| **API版本管理说明** | docs/api/ | 版本规则、兼容性、废弃流程 | ✅ 已完善 |
| **API变更日志** | docs/api/ | API 变更记录 | ✅ 已完善 |
| **Swagger/OpenAPI** | /docs、/apidocs | 交互式文档，/docs 带横向标签筛选（需启动服务） | ✅ 已集成 |
| **小程序-安卓APP-接口文档** | 根目录 | 核销、拍摄相关 | ✅ 专项完整 |
| **物流/厂家接口** | docs/api/ | 物流回调、厂家接口 | ✅ 专项完整 |

---

## 二、路径前缀说明

| 模块 | 前缀 | 示例 |
|------|------|------|
| 小程序 | `/api/miniprogram` | `/api/miniprogram/orders` |
| 用户 | `/api/user` | `/api/user/info` |
| 支付 | `/api/payment` | `/api/payment/create` |
| 管理后台 API | `/api/admin` | `/api/admin/coupons/create` |
| 管理后台页面 | `/admin` | `/admin/orders`（HTML 页面） |
| 选片 | `/api/photo-selection` | `/api/photo-selection/search-orders` |
| 加盟商 | `/franchisee` | `/franchisee/api/check-quota` |
| AI 任务 | `/admin/ai` | `/admin/ai/api/tasks` |
| 美图 | `/admin/meitu` | `/admin/meitu/config` |

**注意**：管理后台存在两类路由：
- **页面路由** `/admin/xxx`：返回 HTML，部分表单提交也走此路径
- **纯 API** `/api/admin/xxx`：返回 JSON，供前端 fetch/axios 调用

---

## 三、复用与补充策略

### 3.1 管理后台API接口说明文档（根目录）

**可复用**：
- 2.1–2.5 产品、分类、风格、订单、用户管理（结构正确）
- 需修正：部分接口实际为 `/api/admin/xxx`，非 `/admin/api/xxx`

**需补充**：
- 2.6 其他管理接口：补充具体路径与说明
- 仪表盘、首页、优惠券、推广、团购、系统配置、退款等

### 3.2 小程序接口

- **小程序API接口说明文档.md** 已较完整，可直接引用
- 与 **API请求响应示例.md** 配合使用

### 3.3 加盟商、选片、AI、美图

- **加盟商与选片**：`docs/api/加盟商与选片API说明.md` - 额度、账户、选片流程
- **AI 任务与美图**：`docs/api/AI任务与美图API说明.md` - 任务列表、美图配置/预设

---

## 四、文档引用关系

```
管理后台API接口说明文档.md（主入口）
├── 小程序API接口说明文档.md
├── docs/api/API错误码说明.md
├── docs/api/API请求响应示例.md
├── docs/api/API版本管理说明.md
├── docs/api/API变更日志.md
├── docs/api/加盟商与选片API说明.md
├── docs/api/AI任务与美图API说明.md
├── /apidocs（Swagger 交互式文档）
└── 小程序-安卓APP-后台管理系统-接口文档.md
```

## 五、Swagger/OpenAPI 使用

1. **安装依赖**：`pip install flasgger`
2. **启动服务**：`python test_server.py`
3. **访问文档**：
   - **推荐** `http://localhost:8000/docs` — 横向标签筛选，按模块快速查找
   - `http://localhost:8000/apidocs` — 完整 Swagger UI
4. **生成规范**：`python scripts/tools/generate_openapi_spec.py` 生成 `docs/api/openapi_spec.json`
5. **中文说明**：接口文档中的 summary 已统一为中文（如「获取风格列表」），支持自动推断

---

**最后更新**: 2026-02-09
