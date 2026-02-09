# 完善API文档

## 📋 现有API文档

### 主要文档
- **管理后台API接口说明文档.md** - 管理后台API接口文档（根目录）
- **小程序API接口说明文档.md** - 小程序API接口文档（根目录）
- **小程序-安卓APP-后台管理系统-接口文档.md** - 统一接口文档（根目录）
- **docs/API接口文档.md** - 主要API文档（如果存在）
- **docs/API接口文档-厂家版.md** - 厂家版API文档
- **docs/小程序API接口清单.md** - 小程序API清单（66个接口）

### 专项文档
- **docs/api/** - API专项文档目录
  - 物流回调接口文档
  - 厂家物流接口文档
  - 商家物流回调接口文档
  - **API错误码说明.md** ✅ 新增
  - **API请求响应示例.md** ✅ 新增

---

## ✅ 已完成

1. **基础API文档** - 主要接口已有文档说明
2. **接口清单** - 小程序API接口清单（66个接口）
3. **分类文档** - 按模块分类的接口文档
4. **错误码说明** ✅ - `docs/api/API错误码说明.md`（HTTP状态码、业务错误码、错误处理建议）
5. **请求响应示例** ✅ - `docs/api/API请求响应示例.md`（订单、产品、支付、选片等接口的 JSON 示例和 curl 命令）

---

## ⏳ 需要完善的内容

### 1. 添加更多接口详细说明

**已完成**（2026-02-06）：
- [x] 管理后台API接口详细说明 - 更新 `管理后台API接口说明文档.md`（2.6 补充、路径修正、新增加盟商/选片/AI/美图）
- [x] 加盟商/AI/选片/美图接口 - 已并入管理后台文档第四节
- [x] 文档索引 - `docs/api/API文档索引与复用说明.md`

**待补充**：
- [x] 核心接口详细说明（见 `docs/api/API接口详细说明.md`）
- [ ] 其余接口按模板逐接口补充（可选）

**完善内容**：
- 请求方法（GET/POST/PUT/DELETE）
- 请求路径
- 请求参数（必填/可选、类型、说明）
- 响应格式（成功/失败）
- 状态码说明

### 2. 完善请求/响应示例

**已完成**：
- [x] JSON请求示例（主要接口）
- [x] JSON响应示例（主要接口）
- [x] curl命令示例

**待补充**：
- [ ] Python请求示例（批量接口）
- [ ] JavaScript请求示例（更多接口）

**示例格式**：
```markdown
### 创建订单

**请求示例**：
```json
POST /api/miniprogram/orders
{
  "product_id": 1,
  "style_id": 2,
  "images": ["url1", "url2"],
  "total_amount": 99.0
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "order_id": 123,
    "order_number": "MP20260101001",
    "total_amount": 99.0
  }
}
```
```

### 3. 添加错误码说明 ✅

**已完成**（见 `docs/api/API错误码说明.md`）：
- [x] 统一错误码定义
- [x] 错误码说明表（HTTP状态码、业务错误码）
- [x] 错误处理建议（前端、Python、curl）

**错误码分类**：
- 1xx - 信息类
- 2xx - 成功类
- 3xx - 重定向类
- 4xx - 客户端错误
- 5xx - 服务器错误

### 4. 添加接口测试用例 ✅

**已完成**（2026-02-06）：
- [x] 正常流程测试用例 - `tests/test_api.py`（小程序、选片、响应格式）
- [x] 自动化测试脚本 - `scripts/tools/api_test_requests.py`、`api_test_curl.sh`、`api_test_curl.bat`
- [x] Postman 集合 - `docs/api/Postman_Collection.json`

**测试工具**：
- `python scripts/tools/api_test_requests.py` - 集成测试（推荐，需先启动服务）
- `pytest tests/test_api.py -v -m api` - 单元测试（依赖 conftest 的 app 初始化）
- Postman 导入 `docs/api/Postman_Collection.json`

### 5. 添加接口版本管理 ✅

**已完成**（见 `docs/api/API版本管理说明.md`）：
- [x] API版本号说明
- [x] 版本兼容性说明
- [x] 废弃接口说明
- [x] API变更日志 - `docs/api/API变更日志.md`

---

## 📝 文档规范

### 接口文档模板

```markdown
## 接口名称

**接口路径**: `/api/endpoint`

**请求方法**: `POST`

**功能说明**: 接口功能描述

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| param1 | string | 是 | 参数说明 |
| param2 | int | 否 | 参数说明 |

**请求示例**:
```json
{
  "param1": "value1",
  "param2": 123
}
```

**响应格式**:

成功响应:
```json
{
  "status": "success",
  "data": {
    "result": "success"
  }
}
```

失败响应:
```json
{
  "status": "error",
  "message": "错误信息",
  "code": 400
}
```

**错误码**:

| 错误码 | 说明 |
|--------|------|
| 400 | 参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |

**测试用例**:

1. 正常流程: ...
2. 异常流程: ...
```

---

## 🔄 后续计划

1. **第一阶段**（已完成）
   - ✅ 创建基础API文档
   - ✅ 整理接口清单

2. **第二阶段**（已完成 2026-02-09）
   - ✅ 完善主要接口详细说明（管理后台、加盟商、AI任务）
   - ✅ 添加请求/响应示例（`docs/api/API请求响应示例.md`）
   - ✅ 添加错误码说明（`docs/api/API错误码说明.md`）

3. **第三阶段**（已完成 2026-02-06）
   - ✅ 添加接口测试用例 - `tests/test_api.py`（pytest，标记 @api）
   - ✅ 创建Postman集合 - `docs/api/Postman_Collection.json`
   - ✅ 添加自动化测试脚本 - `api_test_requests.py`、`api_test_curl.sh`、`api_test_curl.bat`

4. **第四阶段**（已完成 2026-02-09）
   - ✅ API版本管理 - `docs/api/API版本管理说明.md`（版本规则、兼容性、废弃流程）
   - ✅ 接口文档自动化生成 - `scripts/tools/generate_openapi_spec.py`（从路由生成 openapi_spec.json）
   - ✅ Swagger/OpenAPI集成 - Flasgger 提供 `/apidocs` 交互式文档、`/apispec.json` 规范
   - ✅ **文档自动更新** - 启动时从 `app.url_map` 扫描 `/api/`、`/franchisee/api/`、`/admin/api/` 下所有路由，新增接口自动出现在文档中

---

## 📚 相关文档

- **所有API接口-自动化测试脚本-curl.md** - API测试脚本说明
- **管理后台API接口说明文档.md** - 管理后台API文档
- **小程序API接口说明文档.md** - 小程序API文档
- **docs/api/** - API专项文档目录
  - **docs/api/API错误码说明.md** - 错误码与错误处理
  - **docs/api/API请求响应示例.md** - 请求/响应示例与 curl
  - **docs/api/API版本管理说明.md** - 版本规则、兼容性、废弃流程
  - **docs/api/API变更日志.md** - API 变更记录
  - **docs/api/加盟商与选片API说明.md** - 加盟商额度/账户、选片流程
  - **docs/api/AI任务与美图API说明.md** - AI 任务、美图配置/预设
  - **docs/api/API接口详细说明.md** - 核心接口请求参数、类型、响应格式
  - **docs/api/Postman_Collection.json** - Postman 接口集合
  - **docs/api/openapi_spec.json** - 自动生成的 OpenAPI 规范（运行 `python scripts/tools/generate_openapi_spec.py` 生成）
- **Swagger 交互式文档** - 启动服务后访问 `/docs`（横向标签筛选）或 `/apidocs`

---

**最后更新**: 2026-02-09  
**文档版本**: v2.2
