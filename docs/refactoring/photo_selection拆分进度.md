# photo_selection.py 拆分进度

**日期**: 2026-02-05  
**状态**: 🚧 进行中

## 拆分方案

将 `photo_selection.py` (2018行) 拆分为以下模块：

1. ✅ `utils.py` - 工具函数和共享代码（token管理等）
2. ✅ `list.py` - 订单列表 (`photo_selection_list`)
3. ⏳ `detail.py` - 订单详情 (`photo_selection_detail`)
4. ⏳ `submit.py` - 提交选片 (`photo_selection_submit`)
5. ⏳ `confirm.py` - 确认选片 (`photo_selection_confirm`, `photo_selection_review`, `check_payment_status`, `skip_payment`)
6. ⏳ `print_module.py` - 打印相关 (`start_print`)
7. ⏳ `qrcode.py` - 二维码相关 (`generate_selection_qrcode`, `verify_selection_token`)
8. ⏳ `search.py` - 搜索相关 (`search_orders_for_selection`)

## 已完成

- ✅ 创建目录结构 `app/routes/photo_selection/`
- ✅ 创建 `utils.py` 工具函数模块
- ✅ 创建 `list.py` 订单列表模块
- ✅ 创建 `__init__.py` 主蓝图注册文件
- ✅ 备份原文件为 `photo_selection_old.py`

## 待完成

- ⏳ 创建并迁移 `detail.py`
- ⏳ 创建并迁移 `submit.py`
- ⏳ 创建并迁移 `confirm.py`
- ⏳ 创建并迁移 `print_module.py`
- ⏳ 创建并迁移 `qrcode.py`
- ⏳ 创建并迁移 `search.py`
- ⏳ 更新 `test_server.py` 中的导入
- ⏳ 测试所有路由功能
- ⏳ 删除原文件 `photo_selection.py`

## 注意事项

- 原文件已备份为 `photo_selection_old.py`
- `__init__.py` 暂时从原文件导入，待所有模块完成后切换
- 所有模块需要保持相同的导入和依赖关系
