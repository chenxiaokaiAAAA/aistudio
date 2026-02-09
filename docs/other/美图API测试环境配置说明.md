# 美图API测试环境配置说明

## 问题说明

美图API需要接收**公网可访问的图片URL**，本地 `localhost` 的URL无法被美图API服务器访问。

## 解决方案

### 测试环境
需要先将图片上传到**云端存储服务**（如阿里云OSS、腾讯云COS等），获取公网可访问的URL。

### 生产环境
图片已经有公网URL，直接使用即可。

## 配置步骤

### 1. 配置OSS（阿里云对象存储）

编辑 `AI-studio/scripts/oss_config.py` 文件，填入您的OSS配置信息：

```python
OSS_CONFIG = {
    'access_key_id': '您的AccessKey ID',
    'access_key_secret': '您的AccessKey Secret',
    'bucket_name': '您的Bucket名称',
    'endpoint': 'https://oss-cn-shenzhen.aliyuncs.com',  # 根据您的区域调整
    'bucket_domain': 'https://您的bucket域名.oss-cn-shenzhen.aliyuncs.com',
}
```

### 2. 安装OSS SDK

```bash
pip install oss2
```

### 3. 测试OSS连接

```bash
python scripts/oss_config.py
```

如果看到 "✅ OSS连接测试成功"，说明配置正确。

## 使用说明

### 测试接口自动上传

在美图API配置页面进行测试时，系统会：

1. **自动检测**：如果图片是本地路径，会自动尝试上传到OSS
2. **获取公网URL**：上传成功后获取OSS的公网URL
3. **调用API**：使用公网URL调用美图API

### 如果OSS未配置

如果OSS未配置或上传失败，测试会返回错误提示：
```
无法获取图片的公网URL。请配置OSS（scripts/oss_config.py）或提供公网可访问的图片URL
```

## 生产环境

在生产环境中：

1. **图片已有公网URL**：直接使用，无需上传到OSS
2. **自动判断**：代码会自动检测，如果图片路径已经是 `http://` 或 `https://` 开头，直接使用
3. **无需OSS**：如果所有图片都有公网URL，可以不配置OSS

## 注意事项

1. **OSS费用**：OSS按存储和流量计费，测试时注意控制成本
2. **图片清理**：建议定期清理测试图片，避免占用存储空间
3. **安全性**：OSS的AccessKey请妥善保管，不要提交到代码仓库

## 其他云存储服务

如果需要使用其他云存储服务（如腾讯云COS、七牛云等），可以：

1. 参考 `scripts/oss_config.py` 的实现
2. 创建类似的上传函数
3. 在 `app/services/meitu_api_service.py` 的 `upload_image_to_oss` 函数中添加支持
