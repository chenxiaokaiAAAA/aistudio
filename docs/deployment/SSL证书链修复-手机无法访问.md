# SSL 证书链修复 - 解决手机无法访问

> 现象：电脑能打开 https://photogooo.com，手机 Safari 提示「无法建立安全连接」  
> 原因：证书链不完整，缺少中间证书（iOS/手机对证书链要求更严格）

---

## 一、证书位置（不要改）

- **正确路径**：`/etc/nginx/ssl/photogooo.pem` 和 `photogooo.key`
- **根目录的 ssl 空文件夹**：可忽略，阿里云部署可能创建了但未使用，不影响
- **Nginx 配置**：已指向 `/etc/nginx/ssl/`，无需改位置

---

## 二、从阿里云下载完整证书

1. 登录 [阿里云数字证书管理服务](https://yundun.console.aliyun.com/)
2. 找到 `photogooo.com` 证书 → **下载**
3. 选择 **Nginx** 格式（pem/key）→ 下载
4. 解压后通常得到：
   - `xxx.pem` - 域名证书
   - `xxx.key` - 私钥
   - `xxx_chain.pem` 或 `chain.pem` - **中间证书**（重要）

---

## 三、合并完整证书链

Nginx 的 `ssl_certificate` 需要包含：**域名证书 + 中间证书**（顺序不能错）。

```bash
# 在服务器上，假设已上传到 /tmp/ 目录
cd /tmp
# 解压下载的证书包
unzip 23379374_photogooo.com_nginx.zip   # 文件名以实际为准

# 合并证书（域名证书在前，中间证书在后）
cat xxx.pem xxx_chain.pem > fullchain.pem
# 若没有 _chain 文件，可能证书包内是 fullchain.pem，直接使用即可

# 复制到 Nginx 目录并设置权限
sudo cp fullchain.pem /etc/nginx/ssl/photogooo.pem
sudo cp xxx.key /etc/nginx/ssl/photogooo.key
sudo chmod 644 /etc/nginx/ssl/photogooo.pem
sudo chmod 600 /etc/nginx/ssl/photogooo.key

# 验证证书链（应显示 2 或 3 个证书）
grep -c "BEGIN CERTIFICATE" /etc/nginx/ssl/photogooo.pem

# 重新加载 Nginx
sudo nginx -t
sudo systemctl reload nginx
```

---

## 四、若阿里云包内无 chain 文件

部分证书包只有一个 `.pem`，可能已包含完整链。检查：

```bash
grep -c "BEGIN CERTIFICATE" /etc/nginx/ssl/photogooo.pem
```

- **结果为 1**：只有域名证书，需手动添加中间证书
- **结果为 2 或 3**：链完整，若手机仍不行，可能是其他原因

手动添加中间证书：在 [阿里云证书下载页](https://yundun.console.aliyun.com/) 的「根证书下载」区域，下载中间证书（如 DigiCert、Let's Encrypt 等），将内容追加到 `photogooo.pem` 末尾。

---

## 五、验证

```bash
# 服务器本机测试
openssl s_client -connect photogooo.com:443 -servername photogooo.com </dev/null 2>/dev/null | openssl x509 -noout -dates -subject
```

手机 Safari 访问 https://photogooo.com，应能正常打开。

---

## 六、电脑能开、手机不能开（换设备/换网络仍如此）

若证书链完整、端口正常，但手机仍「无法建立安全连接」，可能是：

### 6.1 IPv6 解析问题

手机网络可能优先用 IPv6。若域名有 AAAA 记录但服务器未配置 IPv6，手机连接会失败。

**检查**：在电脑执行 `nslookup photogooo.com`，看是否有 AAAA 记录。

**处理**：若服务器无 IPv6，到域名 DNS 控制台删除 AAAA 记录，只保留 A 记录。

### 6.2 Nginx SSL 兼容性

已更新 `config/nginx_linux_site_no_limit.conf`，增加手机端兼容的加密套件。部署后执行：

```bash
sudo cp /root/project_code/config/nginx_linux_site_no_limit.conf /etc/nginx/sites-available/aistudio
sudo nginx -t
sudo systemctl reload nginx
```

### 6.3 临时关闭 HTTP/2 测试

若仍不行，可尝试关闭 HTTP/2：将 `listen 443 ssl http2` 改为 `listen 443 ssl`，重载 Nginx 后再用手机测试。

---

## 七、IP 直连不跳转（备案期间）

若访问 http://121.43.143.59 仍跳转到 photogooo.com，多半是 Nginx 的 default 站点覆盖了 IP 配置。需**禁用 default 站点**：

```bash
# 备份并禁用 default
sudo mv /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.bak

# 确认 aistudio 配置已部署
sudo cp /root/project_code/config/nginx_linux_site_no_limit.conf /etc/nginx/sites-available/aistudio
sudo ln -sf /etc/nginx/sites-available/aistudio /etc/nginx/sites-enabled/

# 测试并重载
sudo nginx -t
sudo systemctl reload nginx
```

再用 `curl -I http://121.43.143.59` 测试，应返回 200 而非 301。
