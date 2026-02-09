# 在 test_server.py 中添加抖音同步功能

# 1. 导入抖音同步模块
from douyin_sync import create_douyin_sync_routes, start_douyin_sync_scheduler
from douyin_webhook import register_douyin_webhook_routes
from douyin_db_sync import create_douyin_db_sync_routes

# 2. 注册路由
create_douyin_sync_routes(app)
register_douyin_webhook_routes(app)
create_douyin_db_sync_routes(app)

# 3. 启动定时同步（可选）
# start_douyin_sync_scheduler()

# 4. 在后台管理页面添加同步按钮
# 在 templates/admin/dashboard.html 中添加：
# <a href="/api/douyin/sync/orders" class="btn btn-info">同步抖音订单</a>




