# -*- coding: utf-8 -*-
"""
根据Excel文档列表整理项目文档
将需要保留在根目录的文档移动到根目录，其他文档整理到docs目录
"""

import os
import shutil
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent
DOCS_DIR = ROOT_DIR / "docs"

# 文档映射关系：源文件路径 -> 目标文件名
DOC_MAPPING = {
    # 管理后台相关
    "docs/项目结构说明文档.md": "管理后台各页面说明文档.md",
    "docs/项目结构说明文档.md": "管理后台目录结构.md",  # 同一个文件，复制两次
    "docs/API接口文档.md": "管理后台API接口说明文档.md",
    "docs/deployment/冲印系统配置指南.md": "冲印系统配置文档及API接口说明.md",
    "docs/deployment/微信支付配置说明.md": "管理后台选片页面支付配置说明.md",
    
    # 小程序相关
    "docs/小程序目录结构说明.md": "小程序目录结构.md",
    "docs/小程序API接口清单.md": "小程序API接口说明文档.md",
    "docs/小程序拍摄二维码和安卓APP接口文档.md": "小程序-安卓APP-后台管理系统-接口文档.md",
    "docs/deployment/微信支付配置说明.md": "小程序微信支付配置说明.md",
    "docs/第三方团购核销功能说明.md": "第三方团购核销功能说明.md",
    "docs/优惠券类型系统设计.md": "小程序分享领优惠券的机制.md",  # 包含分享领券机制
    
    # 部署相关
    "docs/deployment/多门店frp配置方案.md": "打印机配置文档-多门店FRP配置方案.md",
    "docs/deployment/Redis安装和配置指南.md": "云端服务器-linux-SQL数据库更换部署与安装Redis安装.md",
    "docs/deployment/Linux服务器常用命令.md": "linux云端服务器常用命令说明.md",
    "docs/deployment/PostgreSQL迁移指南.md": "阿里云服务器迁移说明文档.md",
    "docs/deployment/PostgreSQL备份快速参考.md": "阿里云服务器备份脚本-数据库自动备份配置方案.md",
    "docs/项目全面评估和优化建议.md": "当前项目整体性能评估.md",
}

# 需要创建的文档（从现有文档合并或创建）
DOCS_TO_CREATE = {
    "小程序页面说明文档.md": {
        "source_dir": "docs/小程序页面文档",
        "merge": True
    },
    "小程序操作手册.md": {
        "content": """# 小程序操作手册

## 一、新增首页分类

### 步骤
1. 进入管理后台 -> 首页配置
2. 点击"添加分类"
3. 填写分类信息（名称、图标、链接等）
4. 保存

## 二、修改UI样式

### 修改全局样式
- 文件位置：`aistudio-小程序/styles/common.wxss`
- 修改公共组件样式

### 修改页面样式
- 文件位置：`aistudio-小程序/pages/页面名/页面名.wxss`
- 修改对应页面的样式

## 三、修改某个公共组件的样式

### 步骤
1. 找到组件对应的样式文件
2. 在 `styles/common.wxss` 中修改对应样式类
3. 或创建新的样式类覆盖

## 四、新增产品

### 步骤
1. 进入管理后台 -> 产品管理
2. 点击"添加产品"
3. 填写产品信息（名称、价格、尺寸、风格等）
4. 上传产品图片
5. 保存

详细说明请参考：`docs/features/` 目录下的相关文档
"""
    },
    "github同步脚本.md": {
        "content": """# GitHub同步脚本

## 使用方法

### 本地同步到GitHub
```bash
# 使用批处理脚本
完整同步到GitHub并部署.bat

# 或使用Git命令
git add .
git commit -m "更新说明"
git push origin main
```

### 服务器从GitHub同步
```bash
# 使用部署脚本
scripts/deployment/sync_from_github.sh
```

详细说明请参考：`docs/deployment/代码同步完整指南.md`
"""
    },
    "本地数据库同步到阿里云服务器的脚本.md": {
        "content": """# 本地数据库同步到阿里云服务器的脚本

## 使用方法

### 方法1：使用迁移脚本
```bash
python migrate_data_auto.py
```

### 方法2：使用数据库备份恢复
```bash
# 1. 备份本地数据库
python scripts/database/backup_database.py

# 2. 上传备份文件到服务器
# 3. 在服务器上恢复
python scripts/database/restore_database.py
```

详细说明请参考：
- `docs/deployment/PostgreSQL迁移指南.md`
- `docs/deployment/数据迁移断点续传说明.md`
"""
    },
    "阿里云-配置OSS存储桶说明.md": {
        "content": """# 阿里云-配置OSS存储桶说明

## 配置步骤

1. 登录阿里云控制台
2. 进入OSS服务
3. 创建存储桶（Bucket）
4. 配置访问权限
5. 获取AccessKey和SecretKey
6. 在项目配置文件中设置OSS相关参数

详细说明请参考：`docs/deployment/` 目录下的相关文档
"""
    },
    "阿里云服务器-域名证书部署.md": {
        "content": """# 阿里云服务器-域名证书部署

## 部署步骤

1. 申请SSL证书（阿里云SSL证书服务或Let's Encrypt）
2. 下载证书文件
3. 配置Nginx使用SSL证书
4. 重启Nginx服务

详细说明请参考：`docs/deployment/HTTPS自动启动配置说明.md`
"""
    },
    "阿里云服务器-最完整版本部署流程.md": {
        "content": """# 阿里云服务器-最完整版本部署流程

## 需要安装的依赖

### 系统依赖
- Python 3.x
- PostgreSQL
- Redis
- Nginx

### Python依赖
```bash
pip install -r requirements.txt
```

## 需要运行的脚本

1. 数据库初始化：`python scripts/database/setup_postgresql.py`
2. 数据迁移：`python migrate_data_auto.py`
3. 启动服务：`python start_production.py`

详细说明请参考：`docs/deployment/生产环境部署指南.md`
"""
    },
    "阿里云服务器-打印FRP与redis启动命令说明.md": {
        "content": """# 阿里云服务器-打印FRP与redis启动命令说明

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
"""
    },
    "统一部署文档.md": {
        "content": """# 统一部署文档

## 部署流程

1. 环境准备
2. 数据库配置
3. 代码部署
4. 服务启动
5. 验证测试

详细说明请参考：`docs/deployment/生产环境部署指南.md`
"""
    },
    "所有API接口-自动化测试脚本-curl.md": {
        "content": """# 所有API接口-自动化测试脚本-curl

## 测试脚本位置

- `scripts/tools/` 目录下的测试脚本
- `docs/api/` 目录下的API文档

## 使用方法

```bash
# 运行测试脚本
bash scripts/tools/test_api.sh

# 或使用curl直接测试
curl -X POST http://localhost:8000/api/endpoint
```

详细说明请参考：`docs/API接口文档.md`
"""
    },
    "完善API文档.md": {
        "content": """# 完善API文档

## 现有API文档

- `docs/API接口文档.md` - 主要API文档
- `docs/API接口文档-厂家版.md` - 厂家版API文档
- `docs/小程序API接口清单.md` - 小程序API清单

## 需要完善的内容

1. 添加更多接口说明
2. 完善请求/响应示例
3. 添加错误码说明
4. 添加接口测试用例

详细说明请参考：`docs/api/` 目录
"""
    },
    "添加单元测试.md": {
        "content": """# 添加单元测试

## 测试框架

建议使用：
- pytest
- unittest

## 测试目录结构

```
tests/
├── test_models.py
├── test_routes.py
└── test_services.py
```

## 运行测试

```bash
pytest tests/
```

## 注意事项

1. 测试数据库使用独立的测试数据库
2. 测试后清理测试数据
3. 保持测试用例的独立性

详细说明请参考：`docs/` 目录下的测试相关文档
"""
    },
}

def copy_doc(source_path, target_name):
    """复制文档到根目录"""
    source = ROOT_DIR / source_path
    target = ROOT_DIR / target_name
    
    if not source.exists():
        print(f"  [SKIP] 源文件不存在: {source_path}")
        return False
    
    try:
        # 如果目标文件已存在，先备份
        if target.exists():
            backup = ROOT_DIR / f"{target_name}.bak"
            if backup.exists():
                backup.unlink()
            target.rename(backup)
            print(f"  [WARN] 备份已存在文件: {target_name}")
        
        # 复制文件
        shutil.copy2(source, target)
        print(f"  [OK] 已复制: {source_path} -> {target_name}")
        return True
    except Exception as e:
        print(f"  [ERROR] 错误: 无法复制 {source_path}: {e}")
        return False

def create_doc(target_name, content=None, source_dir=None, merge=False):
    """创建文档"""
    target = ROOT_DIR / target_name
    
    if target.exists():
        print(f"  [SKIP] 文件已存在: {target_name}")
        return False
    
    try:
        if content:
            # 直接写入内容
            target.write_text(content, encoding='utf-8')
            print(f"  [OK] 已创建: {target_name}")
            return True
        elif source_dir and merge:
            # 合并多个文件
            source = ROOT_DIR / source_dir
            if source.exists() and source.is_dir():
                # 读取目录下所有md文件并合并
                merged_content = f"# {target_name.replace('.md', '')}\n\n"
                for md_file in sorted(source.glob("*.md")):
                    merged_content += f"## {md_file.stem}\n\n"
                    merged_content += md_file.read_text(encoding='utf-8')
                    merged_content += "\n\n---\n\n"
                target.write_text(merged_content, encoding='utf-8')
                print(f"  [OK] 已合并创建: {target_name}")
                return True
        return False
    except Exception as e:
        print(f"  [ERROR] 错误: 无法创建 {target_name}: {e}")
        return False

def organize_docs():
    """整理文档"""
    print("=" * 80)
    print("开始整理文档...")
    print("=" * 80)
    
    # 统计
    copied_count = 0
    created_count = 0
    skipped_count = 0
    
    # 1. 复制现有文档
    print("\n【第一步】复制现有文档到根目录:")
    print("-" * 80)
    for source_path, target_name in DOC_MAPPING.items():
        if copy_doc(source_path, target_name):
            copied_count += 1
        else:
            skipped_count += 1
    
    # 2. 创建新文档
    print("\n【第二步】创建新文档:")
    print("-" * 80)
    for target_name, config in DOCS_TO_CREATE.items():
        if create_doc(target_name, **config):
            created_count += 1
        else:
            skipped_count += 1
    
    # 3. 处理特殊文档（需要从项目结构说明文档提取）
    print("\n【第三步】处理特殊文档:")
    print("-" * 80)
    
    # 管理后台目录结构（从项目结构说明文档提取管理后台部分）
    project_structure = ROOT_DIR / "docs/项目结构说明文档.md"
    if project_structure.exists():
        content = project_structure.read_text(encoding='utf-8')
        # 提取管理后台相关部分
        admin_section = []
        lines = content.split('\n')
        in_admin_section = False
        for line in lines:
            if '管理后台' in line and '#' in line:
                in_admin_section = True
            if in_admin_section:
                admin_section.append(line)
                if line.startswith('##') and '管理后台' not in line and '小程序' in line:
                    break
        
        if admin_section:
            admin_dir_doc = ROOT_DIR / "管理后台目录结构.md"
            if not admin_dir_doc.exists():
                admin_dir_doc.write_text('\n'.join(admin_section), encoding='utf-8')
                print(f"  [OK] 已创建: 管理后台目录结构.md")
                created_count += 1
    
    # 4. 总结
    print("\n" + "=" * 80)
    print("整理完成!")
    print("=" * 80)
    print(f"已复制文档: {copied_count} 个")
    print(f"已创建文档: {created_count} 个")
    print(f"跳过/失败: {skipped_count} 个")
    print("\n所有文档已整理到根目录，请检查并完善内容。")

if __name__ == "__main__":
    organize_docs()
