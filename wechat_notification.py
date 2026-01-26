#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
微信通知模块
支持企业微信和微信公众号消息推送
"""

import requests
import json
import logging

logger = logging.getLogger(__name__)


class WeChatNotification:
    """微信通知类"""
    
    def __init__(self):
        """初始化微信通知配置"""
        # 尝试加载配置
        try:
            from wechat_notification_config import (
                WECHAT_NOTIFICATION_ENABLED,
                WECHAT_TYPE,  # 'enterprise' 或 'mp'
                ENTERPRISE_WEBHOOK_URL,  # 企业微信机器人webhook
                MP_TOKEN,  # 微信公众号token
                MP_APP_ID,  # 微信公众号AppID
                MP_APP_SECRET,  # 微信公众号AppSecret
                MP_TEMPLATE_ID  # 模板ID
            )
            self.enabled = WECHAT_NOTIFICATION_ENABLED
            self.type = WECHAT_TYPE
            self.enterprise_webhook = ENTERPRISE_WEBHOOK_URL
            self.mp_token = MP_TOKEN
            self.mp_app_id = MP_APP_ID
            self.mp_app_secret = MP_APP_SECRET
            self.mp_template_id = MP_TEMPLATE_ID
        except ImportError:
            # 使用默认配置
            self.enabled = False
            self.type = 'enterprise'
            self.enterprise_webhook = ''
            self.mp_token = ''
            self.mp_app_id = ''
            self.mp_app_secret = ''
            self.mp_template_id = ''
    
    def send_order_notification(self, order_number, customer_name, total_price, source='小程序'):
        """
        发送订单通知
        
        Args:
            order_number: 订单号
            customer_name: 客户姓名
            total_price: 订单金额
            source: 订单来源
        """
        if not self.enabled:
            logger.info("微信通知功能未启用")
            return False
        
        try:
            if self.type == 'enterprise':
                return self._send_enterprise_notification(order_number, customer_name, total_price, source)
            elif self.type == 'mp':
                return self._send_mp_notification(order_number, customer_name, total_price, source)
            else:
                logger.error(f"不支持的微信类型: {self.type}")
                return False
        except Exception as e:
            logger.error(f"发送微信通知失败: {e}")
            return False
    
    def _send_enterprise_notification(self, order_number, customer_name, total_price, source):
        """发送企业微信通知"""
        if not self.enterprise_webhook:
            logger.error("企业微信webhook未配置")
            return False
        
        try:
            # 构建消息内容
            message = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"""## 🛒 新订单提醒
**订单号**: {order_number}
**客户姓名**: {customer_name}
**订单金额**: ¥{total_price}
**订单来源**: {source}
**时间**: {self._get_current_time()}"""
                }
            }
            
            # 发送请求
            response = requests.post(
                self.enterprise_webhook,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info(f"企业微信通知发送成功: {order_number}")
                    return True
                else:
                    logger.error(f"企业微信通知发送失败: {result.get('errmsg')}")
                    return False
            else:
                logger.error(f"企业微信通知请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"发送企业微信通知异常: {e}")
            return False
    
    def _send_mp_notification(self, order_number, customer_name, total_price, source):
        """发送微信公众号通知（需要openid）"""
        # 这里需要订阅者的openid，暂时不实现
        logger.warning("微信公众号通知需要用户openid，暂未实现")
        return False
    
    def _get_current_time(self):
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# 全局实例
_wechat_notification = None


def get_wechat_notification():
    """获取全局微信通知实例"""
    global _wechat_notification
    if _wechat_notification is None:
        _wechat_notification = WeChatNotification()
    return _wechat_notification


def send_order_notification(order_number, customer_name, total_price, source='小程序'):
    """便捷函数：发送订单通知"""
    wechat = get_wechat_notification()
    return wechat.send_order_notification(order_number, customer_name, total_price, source)


if __name__ == '__main__':
    # 测试
    print("测试微信通知功能...")
    result = send_order_notification(
        order_number="PET20250101001",
        customer_name="测试客户",
        total_price=99.0,
        source="小程序"
    )
    print(f"发送结果: {result}")


