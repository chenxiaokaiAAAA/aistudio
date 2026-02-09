# API 接口自动化测试脚本

## 测试脚本

| 脚本 | 说明 | 用法 |
|------|------|------|
| `scripts/tools/api_test_requests.py` | Python 自动化测试（推荐） | `python scripts/tools/api_test_requests.py [BASE_URL]` |
| `scripts/tools/api_test_curl.sh` | Bash curl 测试（Linux/Mac/Git Bash） | `bash scripts/tools/api_test_curl.sh [BASE_URL]` |
| `scripts/tools/api_test_curl.bat` | Windows curl 测试 | `api_test_curl.bat [BASE_URL]` |

## 前置条件

**请先启动服务**：
```bash
python test_server.py
# 或
python start.py
```

默认测试地址：`http://localhost:8000`

## 使用方法

```bash
# Python 测试（跨平台）
python scripts/tools/api_test_requests.py
python scripts/tools/api_test_requests.py http://192.168.1.100:8000

# Bash 测试
bash scripts/tools/api_test_curl.sh

# pytest 单元测试（需项目 conftest 正常）
pytest tests/test_api.py -v -m api
# 若 pytest 因 app 初始化失败，请使用 api_test_requests.py（需先启动服务）
```

## Postman 集合

导入 `docs/api/Postman_Collection.json` 到 Postman 进行手动测试。

## 相关文档

- **管理后台API接口说明文档.md** - 接口说明
- **docs/api/API请求响应示例.md** - 请求/响应示例
