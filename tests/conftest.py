# -*- coding: utf-8 -*-
"""
pytest配置文件
提供测试用的fixtures和配置
"""

import os
import sys
from pathlib import Path

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ["FLASK_ENV"] = "testing"
os.environ["TESTING"] = "1"


@pytest.fixture(scope="session")
def app():
    """创建测试用的Flask应用"""
    # 设置测试环境变量
    os.environ["TESTING"] = "1"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["FLASK_ENV"] = "testing"

    # 先创建app和db
    from app import create_app, db

    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False

    # 在app context中设置db，这样models.py可以正常使用
    with app.app_context():
        # 直接设置models.py中的db实例（在导入models之前设置）
        # 这样可以避免在导入models时db尚未初始化的问题
        import app.models as models_module

        # 直接设置_db_instance和db，避免通过set_db函数（因为set_db在models.py中）
        models_module._db_instance = db
        models_module.db = db

        yield app


@pytest.fixture(scope="function")
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """创建测试数据库"""
    from app import db

    # 创建所有表
    db.create_all()

    yield db

    # 清理
    db.session.remove()
    db.drop_all()
