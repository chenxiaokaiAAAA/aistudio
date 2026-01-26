#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音小店后台爬虫抓取（不推荐，仅作了解）
"""

import requests
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class DouyinShopScraper:
    """抖音小店爬虫（仅作技术了解，不推荐使用）"""
    
    def __init__(self):
        self.session = requests.Session()
        self.driver = None
        
    def login_to_douyin_shop(self, username, password):
        """登录抖音小店后台"""
        try:
            # 使用Selenium登录（需要安装ChromeDriver）
            self.driver = webdriver.Chrome()
            self.driver.get("https://fxg.jinritemai.com/login")
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 10)
            
            # 输入用户名
            username_input = wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_input.send_keys(username)
            
            # 输入密码
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(password)
            
            # 点击登录
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # 等待登录完成
            time.sleep(3)
            
            print("登录成功")
            return True
            
        except Exception as e:
            print(f"登录失败: {e}")
            return False
    
    def get_orders_from_page(self):
        """从页面获取订单数据"""
        try:
            if not self.driver:
                print("请先登录")
                return []
            
            # 导航到订单页面
            self.driver.get("https://fxg.jinritemai.com/order/list")
            time.sleep(2)
            
            # 等待订单表格加载
            wait = WebDriverWait(self.driver, 10)
            order_table = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.order-table"))
            )
            
            # 解析订单数据
            orders = []
            rows = order_table.find_elements(By.CSS_SELECTOR, "tbody tr")
            
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 6:
                        order_data = {
                            'order_id': cells[0].text.strip(),
                            'customer_name': cells[1].text.strip(),
                            'customer_phone': cells[2].text.strip(),
                            'product_name': cells[3].text.strip(),
                            'total_amount': float(cells[4].text.strip().replace('¥', '')),
                            'status': cells[5].text.strip(),
                            'create_time': cells[6].text.strip() if len(cells) > 6 else ''
                        }
                        orders.append(order_data)
                except Exception as e:
                    print(f"解析订单行失败: {e}")
                    continue
            
            print(f"从页面获取到 {len(orders)} 个订单")
            return orders
            
        except Exception as e:
            print(f"获取订单数据失败: {e}")
            return []
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            self.driver = None

# 使用示例（仅作技术了解）
def scrape_douyin_orders():
    """爬取抖音订单（不推荐使用）"""
    scraper = DouyinShopScraper()
    
    try:
        # 登录（需要真实的用户名密码）
        if scraper.login_to_douyin_shop("your_username", "your_password"):
            # 获取订单数据
            orders = scraper.get_orders_from_page()
            return orders
        else:
            return []
    finally:
        scraper.close()

if __name__ == "__main__":
    print("⚠️ 警告：爬虫方式存在风险，不推荐使用")
    print("1. 可能违反平台服务条款")
    print("2. 可能被检测和封禁")
    print("3. 数据不稳定")
    print("4. 建议使用官方API或文件导入方式")




