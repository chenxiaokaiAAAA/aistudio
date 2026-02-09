# 阿里云 OSS 存储配置说明

## 一、阿里云控制台准备

### 1. 创建存储桶（Bucket）

1. 登录 [阿里云控制台](https://www.aliyun.com/) → 对象存储 OSS
2. 创建 Bucket
   - **Bucket 名称**：如 `photogooo-images`（需唯一）
   - **地域**：选择离用户最近的区域（如华东1-杭州）
   - **存储类型**：标准存储
   - **读写权限**：**公共读**（图片需公网访问）
3. 创建完成后，在 Bucket 概览中记录：
   - **Bucket 域名**：如 `https://photogooo-images.oss-cn-hangzhou.aliyuncs.com`
   - **Endpoint**：如 `oss-cn-hangzhou.aliyuncs.com`

### 2. 获取 AccessKey

1. 右上角头像 → AccessKey 管理
2. 创建 AccessKey，记录 **AccessKey ID** 和 **AccessKey Secret**
3. 妥善保存，勿泄露

---

## 二、项目内配置

### 方式一：管理后台配置（推荐）

1. 登录管理后台 → **系统配置** → **图片路径配置**
2. **存储类型** 选择「阿里云 OSS」
3. 填写 OSS 配置：
   - **OSS 存储桶名称**：如 `photogooo-images`
   - **OSS 端点地址**：如 `oss-cn-hangzhou.aliyuncs.com`
   - **OSS 自定义域名**（可选）：若配置了 CDN 或自定义域名
   - **OSS AccessKey ID**
   - **OSS AccessKey Secret**
4. 点击「保存图片路径配置」
5. **重启应用**：`sudo systemctl restart aistudio`

### 方式二：scripts/oss_config.py（美图 API 等模块）

若使用美图 API 测试等需要直接上传到 OSS 的功能，需配置：

```python
# scripts/oss_config.py
OSS_CONFIG = {
    'access_key_id': '你的AccessKey ID',
    'access_key_secret': '你的AccessKey Secret',
    'bucket_name': 'photogooo-images',
    'endpoint': 'https://oss-cn-hangzhou.aliyuncs.com',
    'bucket_domain': 'https://photogooo-images.oss-cn-hangzhou.aliyuncs.com',
}
```

---

## 三、安装依赖

```bash
pip install oss2
```

或加入 `requirements.txt`：`oss2>=2.18.0`

---

## 四、验证

1. 管理后台保存配置后，检查是否生效
2. 上传一张图片，确认能正常访问
3. 若使用美图 API，可运行 `python scripts/oss_config.py` 测试连接

---

## 五、注意事项

- **AccessKey 安全**：不要提交到 Git，建议使用 RAM 子账号并限制 OSS 权限
- **Bucket 权限**：图片需公网访问时，Bucket 需设为「公共读」
- **费用**：OSS 按量计费，存储约 0.12 元/GB/月，流量约 0.5 元/GB
