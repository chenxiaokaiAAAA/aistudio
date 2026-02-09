# 阿里云服务器-打印FRP与redis启动命令说明

## FRP启动命令

### 服务端（frps）
```bash
./frps -c frps.toml
```

### 客户端（frpc）
```bash
./frpc -c frpc.toml
```

## Redis启动命令

### Linux
```bash
# 启动Redis服务
sudo systemctl start redis
# 或
redis-server

# 检查状态
redis-cli ping
```

### Windows
```bash
redis-server.exe
```

详细说明请参考：
- `docs/deployment/多门店frp配置方案.md`
- `docs/deployment/Redis安装和配置指南.md`
