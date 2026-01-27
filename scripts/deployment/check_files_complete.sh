#!/bin/bash
# 检查服务器端文件是否完整

echo "========================================"
echo "    检查服务器端文件完整性"
echo "========================================"
echo

PROJECT_DIR="/root/project_code"
MISSING_FILES=()
WARNING_FILES=()

# 检查核心文件
check_file() {
    local file=$1
    local required=$2
    
    if [ ! -f "$PROJECT_DIR/$file" ]; then
        if [ "$required" = "required" ]; then
            MISSING_FILES+=("$file")
            echo "❌ [缺失] $file (必需)"
        else
            WARNING_FILES+=("$file")
            echo "⚠️  [缺失] $file (可选)"
        fi
    else
        echo "✅ [存在] $file"
    fi
}

echo "[检查] 核心应用文件"
echo
check_file "test_server.py" "required"
check_file "start_production.py" "required"
check_file "gunicorn.conf.py" "required"
check_file "requirements.txt" "required"
echo

echo "[检查] 配置文件"
echo
check_file "config/nginx_linux.conf" "required"
check_file "config/nginx_linux_site.conf" "optional"
echo

echo "[检查] 应用目录"
echo
[ -d "$PROJECT_DIR/app" ] && echo "✅ [存在] app/" || MISSING_FILES+=("app/")
[ -d "$PROJECT_DIR/app/routes" ] && echo "✅ [存在] app/routes/" || MISSING_FILES+=("app/routes/")
[ -d "$PROJECT_DIR/app/services" ] && echo "✅ [存在] app/services/" || MISSING_FILES+=("app/services/")
[ -d "$PROJECT_DIR/app/utils" ] && echo "✅ [存在] app/utils/" || MISSING_FILES+=("app/utils/")
check_file "app/models.py" "required"
echo

echo "[检查] 模板和静态文件"
echo
[ -d "$PROJECT_DIR/templates" ] && echo "✅ [存在] templates/" || MISSING_FILES+=("templates/")
[ -d "$PROJECT_DIR/static" ] && echo "✅ [存在] static/" || MISSING_FILES+=("static/")
[ -d "$PROJECT_DIR/static/css" ] && echo "✅ [存在] static/css/" || WARNING_FILES+=("static/css/")
[ -d "$PROJECT_DIR/static/js" ] && echo "✅ [存在] static/js/" || WARNING_FILES+=("static/js/")
echo

echo "[检查] 脚本和文档"
echo
[ -d "$PROJECT_DIR/scripts" ] && echo "✅ [存在] scripts/" || WARNING_FILES+=("scripts/")
[ -d "$PROJECT_DIR/docs" ] && echo "✅ [存在] docs/" || WARNING_FILES+=("docs/")
echo

echo "[检查] 虚拟环境"
echo
if [ -d "$PROJECT_DIR/venv" ]; then
    echo "✅ [存在] venv/"
    if [ -f "$PROJECT_DIR/venv/bin/python" ]; then
        echo "✅ [存在] venv/bin/python"
    else
        echo "⚠️  [警告] venv/bin/python 不存在，虚拟环境可能不完整"
    fi
else
    echo "⚠️  [缺失] venv/ (需要运行: python3 -m venv venv)"
fi
echo

echo "[检查] 数据库文件"
echo
if [ -f "$PROJECT_DIR/instance/pet_painting.db" ]; then
    echo "✅ [存在] instance/pet_painting.db"
    DB_SIZE=$(du -h "$PROJECT_DIR/instance/pet_painting.db" | cut -f1)
    echo "   大小: $DB_SIZE"
else
    echo "⚠️  [缺失] instance/pet_painting.db (数据库文件不会被 Git 同步)"
    echo "   提示：需要单独备份和恢复数据库文件"
fi
echo

echo "[检查] Git 状态"
echo
cd "$PROJECT_DIR"
if [ -d ".git" ]; then
    echo "✅ Git 仓库已初始化"
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
    echo "   当前分支: $CURRENT_BRANCH"
    LAST_COMMIT=$(git log -1 --format="%h - %s" 2>/dev/null || echo "无提交记录")
    echo "   最新提交: $LAST_COMMIT"
    
    # 检查是否有未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️  [警告] 有未提交的更改"
        git status --short
    else
        echo "✅ 工作区干净"
    fi
else
    echo "❌ [错误] 不是 Git 仓库"
fi
echo

echo "========================================"
echo "    检查结果汇总"
echo "========================================"
echo

if [ ${#MISSING_FILES[@]} -eq 0 ]; then
    echo "✅ 所有必需文件都存在"
else
    echo "❌ 以下必需文件缺失："
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    echo
    echo "建议：运行以下命令同步代码"
    echo "  cd $PROJECT_DIR"
    echo "  git pull origin main"
fi

if [ ${#WARNING_FILES[@]} -gt 0 ]; then
    echo
    echo "⚠️  以下可选文件缺失（不影响运行）："
    for file in "${WARNING_FILES[@]}"; do
        echo "   - $file"
    done
fi

echo
