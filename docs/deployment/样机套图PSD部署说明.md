# 样机套图（PSD）部署说明

## 一、为什么提示「未找到 PSD 文件」

1. **目录未同步**：同步脚本之前**没有包含 `data` 目录**，所以服务器上的 `/root/project_code/data` 里没有 `mockup_templates` 文件夹，应用在 `data/mockup_templates` 下找不到 PSD。
2. **依赖未安装**：样机套图依赖 **psd-tools**（及 Pillow）。若服务器 venv 里未安装，扫描/生成会报错「psd-tools 未安装」。

---

## 二、已做修改（同步脚本）

- **「仅同步代码」**和**「同步全部」**的目录中已加入 **`data`**。
- 同步后，本地的 `data/mockup_templates`（及 `data/mockup_output` 等）会传到服务器 `/root/project_code/data/`，应用即可在 `data/mockup_templates` 下找到 PSD。

---

## 三、你需要做的

### 1. 再执行一次「同步全部」或「仅同步代码」

- 确保本地 `data/mockup_templates` 下已有 PSD 文件（如 `001.psd`）。
- 运行同步后，服务器会出现 `/root/project_code/data/mockup_templates/` 及其中的 PSD，与本地一致。

### 2. 在服务器上安装样机相关依赖

```bash
cd /root/project_code
source venv/bin/activate
pip install psd-tools Pillow
# 或一次性安装全部依赖
pip install -r requirements.txt
sudo systemctl restart aistudio
```

### 3. 验证

- 后台打开「样机套图」/「选择 PSD 文件」，应能扫描到 `data/mockup_templates` 下的 PSD。
- 若仍提示未找到，在服务器上执行：  
  `ls -la /root/project_code/data/mockup_templates/`  
  确认是否有 `.psd` 文件。

---

## 四、目录对应关系

| 位置     | 路径 |
|----------|------|
| 本地     | `项目根目录/data/mockup_templates/`（如 `001.psd`） |
| 服务器   | `/root/project_code/data/mockup_templates/` |
| 应用读取 | `current_app.root_path + "data" + "mockup_templates"` → 即项目下的 `data/mockup_templates` |

同步脚本会把本地 `data` 整体传到服务器 `REMOTE_PROJECT_PATH/data`，因此本地和服务器目录结构一致后，就不会再出现「本地的文件目录跟服务器的对不上」的问题。
