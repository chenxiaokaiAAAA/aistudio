#!/bin/bash
# 使用GitHub Token克隆仓库
GITHUB_TOKEN="YOUR_GITHUB_TOKEN"
GITHUB_REPO="chenxiaokaiAAAA/aistudio"
PROJECT_DIR="/root/project_code"

mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

if [ -d ".git" ]; then
    echo "更新代码..."
    git pull origin master
else
    echo "克隆仓库..."
    git clone https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git .
fi

git config --global credential.helper store
echo "https://${GITHUB_TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
