# 加盟商厂家ID配置功能说明

## 📋 功能概述

本功能允许为不同的加盟商配置专属的厂家ID（shop_id）和厂家名称（shop_name）。当加盟商的订单发送到厂家系统时，将使用其专属配置，而不是系统默认配置。

## 🎯 使用场景

- **默认情况**: 所有订单使用 `printer_config.py` 中的默认配置
- **加盟商专属**: 如果某个加盟商在厂家系统中有专属的影楼编号和名称，可以为其单独配置

## 🔧 配置步骤

### 第一步：添加数据库字段

运行数据库迁移脚本：

```bash
python add_franchisee_printer_fields.py
```

这将为 `franchisee_accounts` 表添加以下字段：
- `printer_shop_id`: 厂家影楼编号
- `printer_shop_name`: 厂家影楼名称

### 第二步：在管理后台配置

1. 登录管理后台
2. 进入 **加盟商管理** → **选择要配置的加盟商** → **编辑**
3. 在 **厂家ID配置** 部分填写：
   - **厂家影楼编号**: 该加盟商在厂家系统中的编号（如：CS001）
   - **厂家影楼名称**: 该加盟商在厂家系统中的名称（如：加盟商A影楼）
4. 点击 **保存修改**

### 第三步：验证配置

- 如果配置了专属ID，该加盟商的订单将使用专属配置
- 如果未配置，将使用默认配置（`printer_config.py` 中的配置）

## 📊 配置优先级

```
订单发送时的 shop_id 和 shop_name 选择逻辑：

1. 检查订单是否有加盟商 (order.franchisee_id)
   ├─ 有加盟商
   │  ├─ 检查加盟商是否配置了 printer_shop_id
   │  │  ├─ 已配置 → 使用加盟商专属配置 ✅
   │  │  └─ 未配置 → 使用默认配置 ⚠️
   │  └─ 无加盟商 → 使用默认配置 ⚠️
   └─ 无加盟商 → 使用默认配置 ⚠️
```

## 💡 使用示例

### 示例1: 默认配置

**printer_config.py**:
```python
PRINTER_SYSTEM_CONFIG = {
    'shop_id': 'CS',      # 默认影楼编号
    'shop_name': '测试',   # 默认影楼名称
    # ...
}
```

**结果**: 所有普通订单和未配置专属ID的加盟商订单都使用 `CS` / `测试`

### 示例2: 加盟商专属配置

**加盟商A**:
- 厂家影楼编号: `CS001`
- 厂家影楼名称: `加盟商A影楼`

**结果**: 加盟商A的所有订单使用 `CS001` / `加盟商A影楼`

**加盟商B**:
- 厂家影楼编号: (未配置)
- 厂家影楼名称: (未配置)

**结果**: 加盟商B的订单使用默认配置 `CS` / `测试`

## 🔍 测试功能

运行测试脚本查看配置情况：

```bash
python test_franchisee_printer_config.py
```

测试脚本将显示：
- 默认配置信息
- 所有加盟商的配置情况
- 不同订单的配置使用情况

## ⚙️ 技术实现

### 数据库字段

```sql
ALTER TABLE franchisee_accounts 
ADD COLUMN printer_shop_id VARCHAR(50);

ALTER TABLE franchisee_accounts 
ADD COLUMN printer_shop_name VARCHAR(100);
```

### 代码修改

1. **printer_client.py**: 
   - 修改 `_build_order_data` 方法
   - 根据订单的加盟商信息动态获取 `shop_id` 和 `shop_name`

2. **franchisee_routes.py**: 
   - 在编辑加盟商时保存厂家ID配置

3. **templates/admin/franchisee_edit.html**: 
   - 添加厂家ID配置输入框

## 📝 注意事项

1. **可选配置**: 厂家ID配置是可选的，如果留空，将使用默认配置
2. **配置生效**: 配置保存后立即生效，新订单将使用新配置
3. **历史订单**: 已发送的订单不受影响，只有新发送的订单会使用新配置
4. **配置验证**: 建议在配置后测试发送一个订单，确认厂家ID正确

## 🐛 故障排除

### 问题1: 配置后订单仍使用默认ID

**可能原因**:
- 订单没有关联到加盟商 (`order.franchisee_id` 为空)
- 加盟商的 `printer_shop_id` 字段为空

**解决方法**:
- 检查订单的 `franchisee_id` 是否正确
- 确认加盟商已正确配置 `printer_shop_id`

### 问题2: 无法保存配置

**可能原因**:
- 数据库字段未添加
- 权限不足

**解决方法**:
- 运行 `add_franchisee_printer_fields.py` 添加字段
- 确认当前用户有管理员权限

## 📞 相关文件

- `add_franchisee_printer_fields.py`: 数据库迁移脚本
- `printer_client.py`: 冲印系统客户端（包含动态获取逻辑）
- `franchisee_routes.py`: 加盟商管理路由
- `templates/admin/franchisee_edit.html`: 加盟商编辑页面
- `printer_config.py`: 默认配置（第10-11行）

---

**最后更新**: 2025-01-XX  
**版本**: v1.0

