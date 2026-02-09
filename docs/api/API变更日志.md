# API 变更日志

> 记录 API 重要的新增、变更和废弃，便于客户端迁移。格式参见 [API版本管理说明](./API版本管理说明.md)。

---

## [1.0.0] - 2026-02-09

### 新增
- Swagger/OpenAPI 交互式文档 - `/apidocs`
- OpenAPI 规范端点 - `/apispec.json`
- API 版本管理说明文档 - `docs/api/API版本管理说明.md`
- 接口文档自动化生成脚本 - `scripts/tools/generate_openapi_spec.py`

### 说明
- 当前所有接口默认版本为 v1
- 无破坏性变更

---

## 变更记录模板

```markdown
## [x.y.z] - YYYY-MM-DD

### 新增
- 接口路径 - 说明

### 变更
- 接口路径 - 变更说明

### 废弃
- 接口路径 - 废弃说明，替代方案
```
