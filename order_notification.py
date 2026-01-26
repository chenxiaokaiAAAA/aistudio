#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
订单通知系统
支持桌面通知、语音播报和音效提醒
"""

import os
import logging
from datetime import datetime

# 尝试导入通知相关库
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("警告: plyer库未安装，桌面通知功能不可用")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("警告: pyttsx3库未安装，语音播报功能不可用")

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrderNotificationService:
    """订单通知服务"""
    
    def __init__(self):
        """初始化通知服务"""
        # 尝试加载配置文件
        try:
            from order_notification_config import (
                ENABLE_NOTIFICATION,
                ENABLE_DESKTOP_NOTIFICATION,
                ENABLE_VOICE_NOTIFICATION,
                ENABLE_SOUND_NOTIFICATION,
                TTS_RATE,
                TTS_VOLUME,
                NOTIFICATION_TIMEOUT
            )
            self.enabled = ENABLE_NOTIFICATION
            self.desktop_notification = ENABLE_DESKTOP_NOTIFICATION
            self.voice_notification = ENABLE_VOICE_NOTIFICATION
            self.sound_notification = ENABLE_SOUND_NOTIFICATION
            self.notification_timeout = NOTIFICATION_TIMEOUT
            self.tts_rate = TTS_RATE
            self.tts_volume = TTS_VOLUME
        except ImportError:
            # 使用默认配置
            self.enabled = True
            self.desktop_notification = True
            self.voice_notification = True
            self.sound_notification = True
            self.notification_timeout = 10
            self.tts_rate = 150
            self.tts_volume = 1.0
        
        self._tts_engine = None
        
        # 初始化TTS引擎
        if TTS_AVAILABLE and self.voice_notification:
            try:
                self._tts_engine = pyttsx3.init()
                # 设置语音参数
                self._tts_engine.setProperty('rate', self.tts_rate)  # 语速
                self._tts_engine.setProperty('volume', self.tts_volume)  # 音量
                # 尝试设置为中文语音
                voices = self._tts_engine.getProperty('voices')
                for voice in voices:
                    if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                        self._tts_engine.setProperty('voice', voice.id)
                        break
            except Exception as e:
                logger.error(f"初始化TTS引擎失败: {e}")
                self._tts_engine = None
                self.voice_notification = False
    
    def notify_new_order(self, order_number, customer_name, total_price, source='小程序'):
        """
        新订单通知
        
        Args:
            order_number: 订单号
            customer_name: 客户姓名
            total_price: 订单金额
            source: 订单来源（默认：小程序）
        """
        if not self.enabled:
            return
        
        try:
            # 记录日志
            logger.info(f"📢 新订单通知: {order_number} - {customer_name} - ¥{total_price}")
            
            # 桌面通知
            if self.desktop_notification and PLYER_AVAILABLE:
                self._send_desktop_notification(order_number, customer_name, total_price, source)
            
            # 语音播报
            if self.voice_notification and self._tts_engine:
                self._send_voice_notification(order_number, customer_name, total_price, source)
            
            # 音效提醒
            if self.sound_notification and WINSOUND_AVAILABLE:
                self._play_notification_sound()
            
        except Exception as e:
            logger.error(f"发送订单通知失败: {e}")
    
    def _send_desktop_notification(self, order_number, customer_name, total_price, source):
        """发送桌面通知"""
        try:
            title = "🛒 新订单提醒"
            message = f"订单号: {order_number}\n客户: {customer_name}\n金额: ¥{total_price}\n来源: {source}"
            
            notification.notify(
                title=title,
                message=message,
                app_name="AI拍照机系统",
                timeout=self.notification_timeout,
                app_icon=None  # 可以设置应用图标
            )
            logger.info("桌面通知已发送")
        except Exception as e:
            logger.error(f"发送桌面通知失败: {e}")
    
    def _send_voice_notification(self, order_number, customer_name, total_price, source):
        """语音播报"""
        try:
            # 构建语音文本
            if 'chinese' in self._tts_engine.getProperty('voice').lower():
                # 中文播报
                text = f"新订单，订单号{order_number}，客户{customer_name}，金额{total_price}元"
            else:
                # 英文播报
                text = f"New order: {order_number}, Customer: {customer_name}, Amount: {total_price} yuan"
            
            # 播报
            self._tts_engine.say(text)
            self._tts_engine.runAndWait()
            logger.info(f"语音播报完成: {text}")
        except Exception as e:
            logger.error(f"语音播报失败: {e}")
    
    def _play_notification_sound(self):
        """播放通知音效"""
        try:
            # Windows系统声音
            # 可以根据需要修改为自定义声音文件
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception as e:
            logger.error(f"播放音效失败: {e}")
    
    def notify_paid_order(self, order_number, customer_name, total_price):
        """已支付订单通知"""
        if not self.enabled:
            return
        
        try:
            logger.info(f"💰 订单支付通知: {order_number} - ¥{total_price}")
            
            if self.desktop_notification and PLYER_AVAILABLE:
                notification.notify(
                    title="💰 订单支付成功",
                    message=f"订单号: {order_number}\n客户: {customer_name}\n金额: ¥{total_price}",
                    app_name="AI拍照机系统",
                    timeout=8
                )
            
            # 播放不同的音效
            if self.sound_notification and WINSOUND_AVAILABLE:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            
        except Exception as e:
            logger.error(f"支付通知失败: {e}")
    
    def set_enabled(self, enabled):
        """设置通知开关"""
        self.enabled = enabled
        logger.info(f"订单通知功能: {'已启用' if enabled else '已禁用'}")
    
    def set_desktop_notification(self, enabled):
        """设置桌面通知开关"""
        self.desktop_notification = enabled
    
    def set_voice_notification(self, enabled):
        """设置语音播报开关"""
        self.voice_notification = enabled
    
    def set_sound_notification(self, enabled):
        """设置音效开关"""
        self.sound_notification = enabled


# 全局通知实例
_order_notification = None


def get_notification_service():
    """获取全局通知服务实例"""
    global _order_notification
    if _order_notification is None:
        _order_notification = OrderNotificationService()
    return _order_notification


# 便捷函数
def notify_new_order(order_number, customer_name, total_price, source='小程序'):
    """便捷函数：通知新订单"""
    service = get_notification_service()
    service.notify_new_order(order_number, customer_name, total_price, source)


def notify_paid_order(order_number, customer_name, total_price):
    """便捷函数：通知已支付订单"""
    service = get_notification_service()
    service.notify_paid_order(order_number, customer_name, total_price)


if __name__ == '__main__':
    # 测试功能
    print("测试订单通知功能...")
    
    service = get_notification_service()
    
    # 测试新订单通知
    print("\n1. 测试新订单通知")
    service.notify_new_order(
        order_number="PET20250101001",
        customer_name="张三",
        total_price=99.0,
        source="小程序"
    )
    
    # 测试已支付订单通知
    print("\n2. 测试支付通知")
    service.notify_paid_order(
        order_number="PET20250101001",
        customer_name="张三",
        total_price=99.0
    )
    
    print("\n测试完成！")

