#!/bin/bash
# 使用GitHub Token克隆仓库的脚本
# 在服务器上执行

set -e

# GitHub Token
GITHUB_TOKEN="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"
GITHUB_REPO="chenxiaokaiAAAA/aistudio"
PROJECT_DIR="/root/project_code"

echo "=========================================="
echo "使用GitHub Token克隆仓库"
echo "=========================================="
echo ""

# 创建项目目录
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 如果目录已存在且是git仓库，先检查
if [ -d ".git" ]; then
    echo "检测到已有Git仓库，更新代码..."
    git pull origin master
else
    echo "克隆仓库..."
    # 使用Token克隆
    git clone https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git .
fi

echo ""
echo "✓ 代码克隆/更新完成"
echo ""

# 配置Git凭据（避免后续需要输入token）
echo "配置Git凭据..."
git config --global credential.helper store
echo "https://${GITHUB_TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

echo "✓ Git凭据配置完成"
echo ""
echo "现在可以执行部署脚本了："
echo "  /root/deploy_aliyun.sh"
