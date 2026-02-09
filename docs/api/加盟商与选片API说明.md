# 加盟商与选片 API 说明

> **文档索引**：详见 `docs/api/API文档索引与复用说明.md`  
> **错误码**：`docs/api/API错误码说明.md` | **请求示例**：`docs/api/API请求响应示例.md`

## 一、加盟商 API

**路径前缀**：`/franchisee/api`  
**认证**：Session 登录（加盟商账户）  
**文件位置**：`app/routes/franchisee/api.py`

### 1.1 额度与账户

| 路径 | 方法 | 说明 |
|------|------|------|
| `/franchisee/api/check-quota` | POST | 检查额度是否充足 |
| `/franchisee/api/deduct-quota` | POST | 扣除额度（下单时） |
| `/franchisee/api/account-info/<qr_code>` | GET | 根据二维码获取账户信息（扫码关联） |
| `/franchisee/api/cancel-order/<order_id>` | POST | 取消订单 |

### 1.2 加盟商管理（厂家后台）

**路径前缀**：`/franchisee/admin`  
**文件位置**：`app/routes/franchisee/admin.py`

| 路径 | 方法 | 说明 |
|------|------|------|
| `/franchisee/admin/accounts` | GET | 加盟商账户列表 |
| `/franchisee/admin/accounts/export` | GET | 导出账户 |
| `/franchisee/admin/accounts/add` | GET/POST | 新增加盟商 |
| `/franchisee/admin/accounts/<id>/recharge` | GET/POST | 充值 |
| `/franchisee/admin/accounts/<id>` | GET | 账户详情 |
| `/franchisee/admin/accounts/<id>/edit` | GET/POST | 编辑账户 |
| `/franchisee/admin/accounts/<id>/delete` | POST | 删除账户 |
| `/franchisee/admin/accounts/<id>/machines/add` | POST | 添加自拍机 |
| `/franchisee/admin/accounts/<id>/machines/<mid>/edit` | POST | 编辑自拍机 |
| `/franchisee/admin/accounts/<id>/machines/<mid>/delete` | POST | 删除自拍机 |
| `/franchisee/admin/accounts/<id>/qrcode-preview` | GET | 加盟商二维码预览 |

### 1.3 加盟商前端（自用）

**路径前缀**：`/franchisee`  
**文件位置**：`app/routes/franchisee/frontend.py`

| 路径 | 方法 | 说明 |
|------|------|------|
| `/franchisee/login` | GET/POST | 加盟商登录 |
| `/franchisee/dashboard` | GET | 仪表盘 |
| `/franchisee/orders` | GET | 订单列表 |
| `/franchisee/order/<id>` | GET | 订单详情 |
| `/franchisee/groupon/verify` | GET/POST | 团购核销 |
| `/franchisee/groupon/records` | GET | 团购核销记录 |
| `/franchisee/coupons` | GET | 优惠券 |
| `/franchisee/api/qrcode-preview` | GET | 二维码预览 |

---

## 二、选片 API

**路径前缀**：`/api/photo-selection`（API）、`/admin/photo-selection`（页面）  
**认证**：选片 Token 或管理员 Session  
**文件位置**：`app/routes/photo_selection/`

### 2.1 查询与验证

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/photo-selection/search-orders` | POST | 通过手机号/订单号查询订单 |
| `/api/photo-selection/verify-token` | POST | 验证选片 Token |

### 2.2 选片流程（页面）

| 路径 | 方法 | 说明 |
|------|------|------|
| `/admin/photo-selection` | GET | 选片订单列表 |
| `/admin/photo-selection/<order_id>` | GET | 选片详情 |
| `/admin/photo-selection/<order_id>/confirm` | GET | 确认选片 |
| `/admin/photo-selection/<order_id>/review` | GET | 审核 |
| `/admin/photo-selection/<order_id>/check-payment` | GET | 检查支付 |
| `/admin/photo-selection/<order_id>/skip-payment` | POST | 跳过支付 |
| `/admin/photo-selection/<order_id>/submit` | POST | 提交选片 |
| `/admin/photo-selection/<order_id>/start-print` | POST | 发起打印 |
| `/admin/photo-selection/generate-qrcode` | POST | 生成选片二维码 |

---

## 三、请求示例

### 3.1 加盟商检查额度

```bash
curl -X POST "https://your-server/franchisee/api/check-quota" \
  -H "Content-Type: application/json" \
  -d '{"amount": 29.9, "franchisee_id": 1}'
```

### 3.2 选片查询订单

```bash
curl -X POST "https://your-server/api/photo-selection/search-orders" \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000"}' 
# 或
  -d '{"order_number": "PET20260101XXX"}'
```

---

## 四、相关文档

- **管理后台API接口说明文档.md** - 管理后台完整接口
- **小程序API接口说明文档.md** - 小程序接口
- **docs/api/API文档索引与复用说明.md** - 文档索引
- **Swagger** - 启动服务后访问 `/docs`，选择「加盟商」标签

---

**最后更新**：2026-02-09
