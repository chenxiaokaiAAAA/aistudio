# miniprogram.py 拆分说明

## 拆分方案

由于文件较大（1826行），建议拆分为以下子模块：

1. **orders.py** - 订单相关路由（约1000行）
   - 提交订单
   - 获取订单列表
   - 订单详情
   - 订单状态更新
   - 订单图片管理
   - 订单核销

2. **media.py** - 媒体文件路由（约100行）
   - 原图访问
   - 效果图访问
   - 静态图片访问
   - 图片上传

3. **catalog.py** - 目录相关路由（约400行）
   - 风格分类
   - 产品配置
   - 轮播图

4. **works.py** - 作品路由（约100行）
   - 获取用户作品

5. **promotion.py** - 推广码路由（约100行）
   - 获取推广码

6. **common.py** - 公共函数（约50行）
   - get_models()
   - get_helper_functions()

## 目录结构

```
app/routes/miniprogram/
├── __init__.py      # 统一注册蓝图
├── common.py        # 公共函数
├── orders.py        # 订单路由
├── media.py         # 媒体路由
├── catalog.py       # 目录路由
├── works.py         # 作品路由
└── promotion.py     # 推广路由
```

## 注意事项

1. 所有子模块使用 `bp = Blueprint(...)` 创建蓝图
2. 在主 `__init__.py` 中统一注册所有子蓝图
3. 更新 `test_server.py` 中的导入，从 `app.routes.miniprogram` 导入 `miniprogram_bp`
