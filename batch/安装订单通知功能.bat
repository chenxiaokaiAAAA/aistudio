@echo off
chcp 65001 >nul
echo ============================================
echo 订单通知系统 - 依赖安装脚本
echo ============================================
echo.

echo 正在安装所需的Python库...
echo.

pip install plyer==2.1.0
pip install pyttsx3==2.90

echo.
echo ============================================
echo 安装完成！
echo ============================================
echo.
echo 已安装：
echo   - plyer (桌面通知)
echo   - pyttsx3 (语音播报)
echo.
echo 系统将在下次启动时自动启用订单通知功能。
echo.
echo 你可以通过编辑 "order_notification_config.py" 文件
echo 来自定义通知行为。
echo.
echo 详细信息请查看: 订单通知配置说明.md
echo.
pause


