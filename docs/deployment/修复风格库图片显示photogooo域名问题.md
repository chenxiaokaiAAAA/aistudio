# 修复风格库图片显示photogooo域名问题

## 🔍 问题现象

小程序风格库的图片地址显示为 `https://photogooo/media/original/...`，而不是配置的 `121.43.143.59`。

## 🔧 问题原因

1. **服务器配置问题**：`server_config.py` 中生产环境配置使用的是 `https://photogooo`
2. **数据库存储问题**：数据库中存储的图片URL包含 `photogooo` 域名
3. **代码替换逻辑不完整**：代码只替换了 `192.168.2.54`，没有替换 `photogooo` 域名

## ✅ 修复方案

### 文件1：`server_config.py`

**位置**：`/root/project_code/server_config.py`

**需要修改**：第 25-30 行

**原代码**：
```python
'production': {
    'base_url': 'https://photogooo',
    'api_base_url': 'https://photogooo/api',
    'static_url': 'https://photogooo/static',
    'media_url': 'https://photogooo/media',
    'notify_url': 'https://photogooo/api/payment/notify'
}
```

**修改为**：
```python
'production': {
    'base_url': 'http://121.43.143.59',  # 临时使用IP地址，域名申请后改为域名
    'api_base_url': 'http://121.43.143.59/api',
    'static_url': 'http://121.43.143.59/static',
    'media_url': 'http://121.43.143.59/media',
    'notify_url': 'http://121.43.143.59/api/payment/notify'
}
```

---

### 文件2：`app/routes/miniprogram/catalog.py`

**位置**：`/root/project_code/app/routes/miniprogram/catalog.py`

**需要修改的地方**（共3处）：

#### 修改1：封面图URL处理（约第105-113行）

**原代码**：
```python
if not cover_image.startswith('http'):
    cover_image = f"{current_base_url}{cover_image}"
elif '192.168.2.54' in cover_image:
    cover_image = cover_image.replace('http://192.168.2.54:8000', current_base_url)
```

**修改为**：
```python
if not cover_image.startswith('http'):
    cover_image = f"{current_base_url}{cover_image}"
elif '192.168.2.54' in cover_image:
    cover_image = cover_image.replace('http://192.168.2.54:8000', current_base_url)
elif 'photogooo' in cover_image:
    # 如果URL包含旧的域名，替换为当前配置的地址
    cover_image = cover_image.replace('https://photogooo', current_base_url)
    cover_image = cover_image.replace('http://photogooo', current_base_url)
```

#### 修改2：风格图片URL处理（约第126-135行）

**原代码**：
```python
if not image_url.startswith('http'):
    image_url = f"{current_base_url}{image_url}"
elif '192.168.2.54' in image_url:
    image_url = image_url.replace('http://192.168.2.54:8000', current_base_url)
```

**修改为**：
```python
if not image_url.startswith('http'):
    image_url = f"{current_base_url}{image_url}"
elif '192.168.2.54' in image_url:
    image_url = image_url.replace('http://192.168.2.54:8000', current_base_url)
elif 'photogooo' in image_url:
    # 如果URL包含旧的域名，替换为当前配置的地址
    image_url = image_url.replace('https://photogooo', current_base_url)
    image_url = image_url.replace('http://photogooo', current_base_url)
```

#### 修改3：子分类封面图URL处理（约第95-99行）

**原代码**：
```python
if not subcategory_data['cover_image'].startswith('http'):
    subcategory_data['cover_image'] = f"{current_base_url}{subcategory_data['cover_image']}"
elif '192.168.2.54' in subcategory_data['cover_image']:
    subcategory_data['cover_image'] = subcategory_data['cover_image'].replace('http://192.168.2.54:8000', current_base_url)
```

**修改为**：
```python
if not subcategory_data['cover_image'].startswith('http'):
    subcategory_data['cover_image'] = f"{current_base_url}{subcategory_data['cover_image']}"
elif '192.168.2.54' in subcategory_data['cover_image']:
    subcategory_data['cover_image'] = subcategory_data['cover_image'].replace('http://192.168.2.54:8000', current_base_url)
elif 'photogooo' in subcategory_data['cover_image']:
    subcategory_data['cover_image'] = subcategory_data['cover_image'].replace('https://photogooo', current_base_url)
    subcategory_data['cover_image'] = subcategory_data['cover_image'].replace('http://photogooo', current_base_url)
```

---

### 文件3：`app/routes/miniprogram/catalog.py`（刷新接口）

**位置**：`/root/project_code/app/routes/miniprogram/catalog.py`

**需要修改**：`/styles/refresh` 接口中的相同逻辑（约第191-220行）

应用相同的修改逻辑。

---

## 🚀 快速修复命令

在服务器上执行：

```bash
cd /root/project_code

# 备份文件
cp server_config.py server_config.py.bak
cp app/routes/miniprogram/catalog.py app/routes/miniprogram/catalog.py.bak

# 然后手动编辑这两个文件，应用上面的修改
# 或者使用同步脚本同步本地已修复的文件
```

---

## 📋 验证修复

修复后：

1. **重启服务**：
   ```bash
   systemctl restart aistudio
   ```

2. **在小程序中测试**：
   - 打开风格库页面
   - 查看图片URL是否已改为 `http://121.43.143.59`
   - 检查图片是否能正常显示

3. **查看日志**：
   ```bash
   journalctl -u aistudio -f
   ```

---

## ⚠️ 注意事项

1. **域名申请后**：将 `server_config.py` 中的IP地址改回域名
2. **数据库清理**：如果数据库中有大量包含 `photogooo` 的URL，可以考虑批量更新
3. **HTTPS**：域名申请后，将 `http://` 改为 `https://`
