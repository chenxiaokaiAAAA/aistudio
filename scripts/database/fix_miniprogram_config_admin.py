#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复小程序配置中被错误保存为 "admin" 的值
（通常由浏览器自动填充导致）
运行: python scripts/database/fix_miniprogram_config_admin.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def fix_config():
    """修复 ai_config 表中错误的 admin 值"""
    from app import create_app, db
    from app.models import AIConfig

    app = create_app()
    with app.app_context():
        fixes = []

        # 获取 pay_appid，用于同步到 miniprogram_appid
        pay_appid_config = AIConfig.query.filter_by(config_key="wechat_pay_appid").first()
        pay_appid_val = (pay_appid_config.config_value or "").strip() if pay_appid_config else ""

        # 修复 miniprogram_appid：有效值应以 wx 开头，否则用 pay_appid 替代或清空
        # 包括 admin、admin2222、admin123 等浏览器自动填充的无效值
        config = AIConfig.query.filter_by(config_key="miniprogram_appid").first()
        if config and config.config_value:
            val = (config.config_value or "").strip()
            if not val.startswith("wx"):  # 无效的 AppID
                if pay_appid_val and pay_appid_val.startswith("wx"):
                    config.config_value = pay_appid_val
                    fixes.append(f"miniprogram_appid: {val[:20]}... -> {pay_appid_val[:15]}... (已从支付AppID同步)")
                else:
                    config.config_value = ""
                    fixes.append(f"miniprogram_appid: {val[:20]}... -> (空，请重新填写)")
            else:
                print(f"  miniprogram_appid 当前值: {val[:15]}... (无需修复)")
        else:
            print(f"  miniprogram_appid: 未配置")

        # 修复 wechat_pay_mch_id：有效值应为数字，admin/admin2222 等无效
        config = AIConfig.query.filter_by(config_key="wechat_pay_mch_id").first()
        if config and config.config_value:
            val = (config.config_value or "").strip()
            if val.lower().startswith("admin"):  # admin、admin2222 等无效值
                config.config_value = ""
                fixes.append(f"wechat_pay_mch_id: {val[:20]}... -> (空，请重新填写)")
            else:
                print(f"  wechat_pay_mch_id 当前值: {val[:15]}... (无需修复)")
        else:
            print(f"  wechat_pay_mch_id: 未配置")

        if fixes:
            db.session.commit()
            print("✅ 已修复以下配置:")
            for f in fixes:
                print(f"   - {f}")
            print("\n请到管理后台「小程序配置」重新填写正确的 AppID 和商户号")
        else:
            print("✅ 未发现需要修复的配置（或已修复）")


if __name__ == "__main__":
    print("=" * 50)
    print("修复小程序配置中的错误 'admin' 值")
    print("=" * 50)
    try:
        fix_config()
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
