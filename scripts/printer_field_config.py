#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冲印系统字段配置管理
用于管理必须字段的映射和验证
"""

import json
import os
from datetime import datetime

class PrinterFieldConfig:
    """冲印系统字段配置管理"""
    
    def __init__(self, config_file="printer_field_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self.get_default_config()
    
    def save_config(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "required_fields": {
                "product_id": {
                    "description": "产品编号",
                    "required": True,
                    "validation": "must_match_manufacturer",
                    "mapping": {
                        "size_1": "001",
                        "size_2": "002", 
                        "size_3": "003",
                        "size_4": "004"
                    }
                },
                "product_name": {
                    "description": "产品名称",
                    "required": True,
                    "validation": "string_not_empty",
                    "mapping": {
                        "size_1": "小型油画 (30x40cm)",
                        "size_2": "中型油画 (40x50cm)",
                        "size_3": "大型油画 (50x70cm)", 
                        "size_4": "超大型油画 (70x100cm)"
                    }
                },
                "order_id": {
                    "description": "订单ID",
                    "required": True,
                    "validation": "string_not_empty",
                    "format": "YT_{order_id}"
                },
                "order_no": {
                    "description": "订单号",
                    "required": True,
                    "validation": "string_not_empty"
                },
                "customer_name": {
                    "description": "客户姓名",
                    "required": True,
                    "validation": "string_not_empty"
                },
                "mobile": {
                    "description": "客户电话",
                    "required": True,
                    "validation": "phone_number"
                },
                "file_url": {
                    "description": "图片URL",
                    "required": True,
                    "validation": "valid_url"
                },
                "file_name": {
                    "description": "文件名",
                    "required": True,
                    "validation": "string_not_empty"
                },
                "pix_width": {
                    "description": "像素宽度",
                    "required": True,
                    "validation": "positive_integer"
                },
                "pix_height": {
                    "description": "像素高度", 
                    "required": True,
                    "validation": "positive_integer"
                },
                "dpi": {
                    "description": "分辨率",
                    "required": True,
                    "validation": "positive_integer",
                    "default": 300
                },
                "width": {
                    "description": "物理宽度(cm)",
                    "required": True,
                    "validation": "positive_float"
                },
                "height": {
                    "description": "物理高度(cm)",
                    "required": True,
                    "validation": "positive_float"
                }
            },
            "optional_fields": {
                "province": {
                    "description": "省份",
                    "required": False,
                    "default": "广东省"
                },
                "city": {
                    "description": "城市",
                    "required": False,
                    "default": "深圳市"
                },
                "city_part": {
                    "description": "区县",
                    "required": False,
                    "default": "南山区"
                },
                "street": {
                    "description": "详细地址",
                    "required": False,
                    "default": "详细地址"
                },
                "remark": {
                    "description": "订单备注",
                    "required": False,
                    "format": "订单备注: {order_number}"
                }
            },
            "manufacturer_products": {
                "description": "厂家系统中的产品列表（需要厂家提供）",
                "products": [
                    {
                        "product_id": "001",
                        "product_name": "小型油画",
                        "size": "30x40cm",
                        "price": 50.0
                    },
                    {
                        "product_id": "002", 
                        "product_name": "中型油画",
                        "size": "40x50cm",
                        "price": 80.0
                    },
                    {
                        "product_id": "003",
                        "product_name": "大型油画", 
                        "size": "50x70cm",
                        "price": 120.0
                    },
                    {
                        "product_id": "004",
                        "product_name": "超大型油画",
                        "size": "70x100cm", 
                        "price": 200.0
                    }
                ]
            },
            "validation_rules": {
                "must_match_manufacturer": "产品ID必须在厂家产品列表中",
                "string_not_empty": "字符串不能为空",
                "phone_number": "必须是有效的手机号码格式",
                "valid_url": "必须是有效的URL格式",
                "positive_integer": "必须是正整数",
                "positive_float": "必须是正数"
            }
        }
    
    def validate_field(self, field_name, value, order_data=None):
        """验证字段值"""
        if field_name not in self.config["required_fields"]:
            return True, "字段不在必填列表中"
        
        field_config = self.config["required_fields"][field_name]
        
        # 检查是否为空
        if field_config["required"] and not value:
            return False, f"{field_config['description']}不能为空"
        
        # 验证规则
        validation = field_config.get("validation")
        if validation == "must_match_manufacturer":
            # 检查产品ID是否在厂家产品列表中
            products = self.config["manufacturer_products"]["products"]
            product_ids = [p["product_id"] for p in products]
            if value not in product_ids:
                return False, f"产品ID {value} 不在厂家产品列表中: {product_ids}"
        
        elif validation == "string_not_empty":
            if not isinstance(value, str) or not value.strip():
                return False, f"{field_config['description']}不能为空"
        
        elif validation == "phone_number":
            if not isinstance(value, str) or len(value) != 11 or not value.isdigit():
                return False, f"{field_config['description']}格式不正确"
        
        elif validation == "valid_url":
            if not isinstance(value, str) or not value.startswith(('http://', 'https://')):
                return False, f"{field_config['description']}格式不正确"
        
        elif validation == "positive_integer":
            try:
                int_val = int(value)
                if int_val <= 0:
                    return False, f"{field_config['description']}必须是正整数"
            except (ValueError, TypeError):
                return False, f"{field_config['description']}必须是整数"
        
        elif validation == "positive_float":
            try:
                float_val = float(value)
                if float_val <= 0:
                    return False, f"{field_config['description']}必须是正数"
            except (ValueError, TypeError):
                return False, f"{field_config['description']}必须是数字"
        
        return True, "验证通过"
    
    def get_field_value(self, field_name, order_data):
        """获取字段值"""
        field_config = self.config["required_fields"].get(field_name, {})
        
        # 如果有映射，使用映射值
        if "mapping" in field_config:
            size_key = order_data.get("size", "").replace("size_", "")
            if size_key in field_config["mapping"]:
                return field_config["mapping"][size_key]
        
        # 如果有格式，使用格式
        if "format" in field_config:
            return field_config["format"].format(**order_data)
        
        # 返回默认值
        return field_config.get("default", "")
    
    def update_manufacturer_products(self, products):
        """更新厂家产品列表"""
        self.config["manufacturer_products"]["products"] = products
        self.save_config()
        print(f"已更新厂家产品列表，共 {len(products)} 个产品")
    
    def print_config_summary(self):
        """打印配置摘要"""
        print("=== 冲印系统字段配置摘要 ===")
        print(f"必填字段数量: {len(self.config['required_fields'])}")
        print(f"可选字段数量: {len(self.config['optional_fields'])}")
        print(f"厂家产品数量: {len(self.config['manufacturer_products']['products'])}")
        
        print("\n必填字段列表:")
        for field, config in self.config["required_fields"].items():
            print(f"  - {field}: {config['description']}")
        
        print("\n厂家产品列表:")
        for product in self.config["manufacturer_products"]["products"]:
            print(f"  - {product['product_id']}: {product['product_name']} ({product['size']})")

def main():
    """主函数"""
    config_manager = PrinterFieldConfig()
    
    print("=== 冲印系统字段配置管理 ===")
    print()
    
    # 打印配置摘要
    config_manager.print_config_summary()
    
    print("\n=== 配置管理选项 ===")
    print("1. 查看当前配置")
    print("2. 更新厂家产品列表")
    print("3. 验证订单数据")
    print("4. 保存配置")
    
    choice = input("\n请选择操作 (1-4): ").strip()
    
    if choice == "1":
        config_manager.print_config_summary()
    elif choice == "2":
        print("\n请输入厂家产品信息（JSON格式）:")
        products_json = input()
        try:
            products = json.loads(products_json)
            config_manager.update_manufacturer_products(products)
        except json.JSONDecodeError:
            print("JSON格式错误")
    elif choice == "3":
        print("\n请输入订单数据（JSON格式）:")
        order_json = input()
        try:
            order_data = json.loads(order_json)
            print("\n字段验证结果:")
            for field, config in config_manager.config["required_fields"].items():
                value = config_manager.get_field_value(field, order_data)
                is_valid, message = config_manager.validate_field(field, value, order_data)
                status = "✅" if is_valid else "❌"
                print(f"  {status} {field}: {message}")
        except json.JSONDecodeError:
            print("JSON格式错误")
    elif choice == "4":
        config_manager.save_config()
        print("配置已保存")

if __name__ == '__main__':
    main()

