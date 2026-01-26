# 从 bk-photo 导入 API 服务商配置

## 说明

这个脚本可以从 `bk-photo` 项目中自动导入已有的 API 服务商配置到 `AI-studio` 项目，避免手动重新添加配置。

## 使用方法

### 方法一：使用批处理脚本（推荐）

1. 确保 `bk-photo` 项目的数据库文件存在（通常在 `bk-photo/instance/pet_painting.db` 或 `bk-photo/pet_painting.db`）
2. 双击运行 `batch/import_api_configs.bat`
3. 脚本会自动查找并导入配置

### 方法二：使用 Python 脚本

```bash
# 自动查找 bk-photo 数据库
python scripts/database/import_api_provider_configs_from_bkphoto.py

# 手动指定 bk-photo 数据库路径
python scripts/database/import_api_provider_configs_from_bkphoto.py --bkphoto-db "E:\AI-管理系统相关\AI-自拍机项目\bk-photo\instance\pet_painting.db"

# 同时指定目标数据库路径
python scripts/database/import_api_provider_configs_from_bkphoto.py --bkphoto-db "路径1" --target-db "路径2"
```

## 导入规则

- **新增配置**：如果配置名称在目标数据库中不存在，将创建新配置
- **更新配置**：如果配置名称已存在，将更新现有配置的字段
- **保留字段**：`priority` 字段默认为 0（可在导入后手动调整）

## 注意事项

1. **数据库文件路径**：脚本会自动查找以下路径：
   - `../bk-photo/pet_painting.db`
   - `../bk-photo/instance/pet_painting.db`
   - `../bk-photo/instance/database.db`

2. **表名检查**：脚本会检查 `bk-photo` 数据库中是否存在 `api_configs` 表

3. **字段映射**：
   - `bk-photo.api_configs` → `AI-studio.api_provider_configs`
   - 字段名称基本一致，`priority` 字段默认为 0

4. **导入前备份**：建议在导入前备份 `AI-studio` 的数据库文件

## 导入的字段

- `name` - 配置名称
- `api_type` - API类型（nano-banana, gemini-native, veo-video等）
- `host_overseas` - 海外Host
- `host_domestic` - 国内直连Host
- `api_key` - API密钥
- `draw_endpoint` - 绘画接口路径
- `result_endpoint` - 获取结果接口路径
- `file_upload_endpoint` - 文件上传接口路径
- `model_name` - 模型名称
- `is_active` - 是否启用
- `is_default` - 是否默认配置
- `enable_retry` - 是否启用重试
- `created_at` / `updated_at` - 时间戳

## 常见问题

### Q: 提示找不到数据库文件
A: 请手动指定数据库路径：
```bash
python scripts/database/import_api_provider_configs_from_bkphoto.py --bkphoto-db "完整路径\pet_painting.db"
```

### Q: 提示表不存在
A: 确认 `bk-photo` 数据库中的表名是否为 `api_configs`，如果不是，需要修改脚本中的表名。

### Q: 导入后配置不显示
A: 检查 `AI-studio` 数据库中的 `api_provider_configs` 表是否有数据，确认导入是否成功。
