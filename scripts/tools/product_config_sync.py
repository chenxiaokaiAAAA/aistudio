#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
产品配置自动同步模块
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Product, ProductSize

class ProductConfigSync:
    """产品配置自动同步类"""
    
    def __init__(self):
        self.printer_config_file = 'printer_config.py'
        self.size_config_file = 'size_config.py'
    
    def sync_to_printer_config(self):
        """同步产品配置到冲印系统配置文件（同时更新两个配置文件）"""
        
        print("🔄 开始自动同步产品配置到冲印系统...")
        
        with app.app_context():
            # 获取所有产品配置
            products = Product.query.filter_by(is_active=True).all()
            
            # 构建新的SIZE_MAPPING（用于printer_config.py，简单格式）
            printer_size_mapping = {}
            
            # 构建新的SIZE_MAPPING（用于size_config.py，完整格式）
            size_config_mapping = {}
            
            for product in products:
                sizes = ProductSize.query.filter_by(product_id=product.id, is_active=True).all()
                
                for size in sizes:
                    if size.printer_product_id:
                        # 获取尺寸信息
                        width_cm, height_cm = self._get_size_dimensions(size.size_name)
                        
                        # 使用printer_product_id作为key
                        key = size.printer_product_id
                        product_name = f"{product.name}{size.size_name}"
                        
                        # printer_config.py 格式（简单）
                        printer_size_mapping[key] = {
                            'product_id': size.printer_product_id,
                            'product_name': product_name,
                            'width_cm': width_cm,
                            'height_cm': height_cm
                        }
                        
                        # size_config.py 格式（完整，包含更多字段）
                        size_config_mapping[key] = {
                            'product_id': size.printer_product_id,
                            'product_name': product_name,
                            'width_cm': width_cm,
                            'height_cm': height_cm,
                            'manufacturer_width_cm': width_cm,  # 默认与width_cm相同
                            'manufacturer_height_cm': height_cm,  # 默认与height_cm相同
                            'dpi': 300,  # 默认DPI
                            'tolerance_percent': 5,  # 默认误差范围
                        }
            
            # 添加小程序新格式映射（保持兼容性）
            printer_size_mapping['12寸-（30x30cm）肌理油画框'] = {
                'product_id': '33673',
                'product_name': '梵高油画框30x30cm肌理画框',
                'width_cm': 35.6,
                'height_cm': 35.6
            }
            
            size_config_mapping['12寸-（30x30cm）肌理油画框'] = {
                'product_id': '33673',
                'product_name': '梵高油画框30x30cm肌理画框',
                'width_cm': 35.6,
                'height_cm': 35.6,
                'manufacturer_width_cm': 35.6,
                'manufacturer_height_cm': 35.6,
                'dpi': 300,
                'tolerance_percent': 5,
            }
            
            # 生成并写入 printer_config.py
            printer_config_content = self._generate_printer_config_content(printer_size_mapping)
            with open(self.printer_config_file, 'w', encoding='utf-8') as f:
                f.write(printer_config_content)
            
            # 生成并写入 size_config.py（保留原有的配置结构）
            size_config_content = self._generate_size_config_content(size_config_mapping)
            with open(self.size_config_file, 'w', encoding='utf-8') as f:
                f.write(size_config_content)
            
            print(f"✅ 自动同步完成！")
            print(f"   更新了 {len(printer_size_mapping)} 个尺寸映射")
            print(f"   ✅ {self.printer_config_file} 已更新")
            print(f"   ✅ {self.size_config_file} 已更新")
            
            return True
    
    def _get_size_dimensions(self, size_name):
        """根据尺寸名称获取实际尺寸"""
        
        # 默认尺寸
        width_cm = 35.6
        height_cm = 35.6
        
        # 根据尺寸名称推断实际尺寸
        if '30x30' in size_name or '30x30cm' in size_name or '12寸' in size_name:
            width_cm = 35.6
            height_cm = 35.6
        elif '30x40' in size_name or '30x40cm' in size_name or '16寸' in size_name:
            width_cm = 35.6
            height_cm = 45.6
        elif '40x53' in size_name or '40x53.3cm' in size_name or '21寸' in size_name:
            width_cm = 45.6
            height_cm = 58.9
        elif '50x66' in size_name or '50x66.7cm' in size_name or '27寸' in size_name:
            width_cm = 55.6
            height_cm = 72.2
        elif '40x60' in size_name or '40x60cm' in size_name:
            width_cm = 45.6
            height_cm = 65.6
        elif '10寸' in size_name:
            width_cm = 25.0
            height_cm = 25.0
        elif '8寸' in size_name:
            width_cm = 20.0
            height_cm = 25.0
        
        return width_cm, height_cm
    
    def _generate_printer_config_content(self, size_mapping):
        """生成 printer_config.py 配置文件内容"""
        
        config_content = f'''# 冲印系统集成配置
# 厂家提供的配置信息

# 冲印系统配置
PRINTER_SYSTEM_CONFIG = {{
    'enabled': True,  # 是否启用冲印系统集成
    'api_base_url': 'http://xmdmsm.xicp.cn:5995/api/ODSGate',  # 冲印系统API基础地址
    'api_url': 'http://xmdmsm.xicp.cn:5995/api/ODSGate/NewOrder',  # 新订单接口
    'source_app_id': 'ZPG',  # 订单来源系统代号
    'shop_id': 'CS',  # 冲印系统对应的影楼编号（测试环境）
    'shop_name': '测试',  # 影楼名称（测试环境）
    'auth_token': 'YOUR_AUTH_TOKEN',  # 如果API需要认证，这里填写Token
    'callback_url': 'https://dev-camera-api.photogo520.com/open/xmdm/express/notify',  # 快递信息回调地址
    'file_access_base_url': 'http://moeart.cc',  # 外部可访问的文件基础URL
    'use_oss': True,  # 是否使用阿里云OSS存储
    'oss_bucket_domain': 'https://pet-painting-images.oss-cn-shenzhen.aliyuncs.com',  # OSS存储桶域名
    'timeout': 30,  # 请求超时时间（秒）
    'retry_times': 3,  # 重试次数
}}

# 尺寸映射：将系统内部尺寸映射到冲印系统识别的尺寸代码或描述
# 此配置由产品配置管理页面自动生成 - 请勿手动修改
SIZE_MAPPING = {{
'''
        
        # 添加尺寸映射
        for key, value in size_mapping.items():
            config_content += f"    '{key}': {{'product_id': '{value['product_id']}', 'product_name': '{value['product_name']}', 'width_cm': {value['width_cm']}, 'height_cm': {value['height_cm']}}},\n"
        
        config_content += "}\n"
        
        return config_content
    
    def _generate_size_config_content(self, size_mapping):
        """生成 size_config.py 配置文件内容（完整格式）"""
        
        config_content = '''# 尺寸配置表 - 产品尺寸检查标准和发送标准配置
# 此文件用于配置发送给厂家的尺寸标准和验证规则
# 此配置由产品配置管理页面自动生成 - 请勿手动修改

# ==================== 验证规则配置 ====================
VALIDATION_CONFIG = {
    'enabled': True,  # 是否启用尺寸验证
    'default_dpi': 300,  # 默认DPI
    'tolerance_percent': 5,  # 允许的误差百分比（5%表示允许95%-105%的误差）
    'strict_mode': False,  # 严格模式：如果为True，尺寸必须完全匹配，不允许误差
}

# ==================== 尺寸发送格式配置 ====================
SEND_FORMAT_CONFIG = {
    'width_decimals': 2,  # 宽度小数点位数（发送给厂家的格式）
    'height_decimals': 2,  # 高度小数点位数（发送给厂家的格式）
    'size_format': 'cm',  # 尺寸单位：'cm' 或 'mm'
    'include_pixel_size': True,  # 是否包含像素尺寸
    'include_dpi': True,  # 是否包含DPI信息
}

# ==================== 产品尺寸映射表 ====================
# 格式说明：
#   - size_key: 订单中的尺寸标识（可以是产品ID、尺寸名称等）
#   - product_id: 厂家产品ID
#   - product_name: 产品名称
#   - width_cm: 要求的宽度（厘米），精确到小数点后2位
#   - height_cm: 要求的高度（厘米），精确到小数点后2位
#   - manufacturer_width_cm: 厂家要求的宽度（可能不同，用于发送）
#   - manufacturer_height_cm: 厂家要求的高度（可能不同，用于发送）
#   - dpi: 要求的DPI（可选，默认使用VALIDATION_CONFIG中的default_dpi）
#   - tolerance_percent: 该产品的特殊误差范围（可选，默认使用VALIDATION_CONFIG中的tolerance_percent）

SIZE_MAPPING = {
'''
        
        # 添加尺寸映射（完整格式）
        for key, value in size_mapping.items():
            config_content += f"    '{key}': {{\n"
            config_content += f"        'product_id': '{value['product_id']}',\n"
            config_content += f"        'product_name': '{value['product_name']}',\n"
            config_content += f"        'width_cm': {value['width_cm']},\n"
            config_content += f"        'height_cm': {value['height_cm']},\n"
            config_content += f"        'manufacturer_width_cm': {value['manufacturer_width_cm']},  # 厂家要求的宽度（可能与width_cm不同）\n"
            config_content += f"        'manufacturer_height_cm': {value['manufacturer_height_cm']},  # 厂家要求的高度（可能与height_cm不同）\n"
            config_content += f"        'dpi': {value['dpi']},\n"
            config_content += f"        'tolerance_percent': {value['tolerance_percent']},\n"
            config_content += f"    }},\n"
        
        config_content += '''}

# ==================== 尺寸别名映射 ====================
# 用于将订单中的不同尺寸标识映射到同一个产品配置
# 例如：订单中可能使用 "12寸" 或 "30x30cm" 都指向同一个产品
SIZE_ALIAS_MAPPING = {
    # '12寸': '33673',
    # '30x30cm': '33673',
    # '30x30': '33673',
}

# ==================== 使用说明 ====================
"""
1. 添加新产品尺寸：
   在 SIZE_MAPPING 中添加新的配置项，key 为订单中使用的尺寸标识
    
2. 配置厂家要求的精确尺寸：
   如果厂家要求的尺寸与标准尺寸不同，设置 manufacturer_width_cm 和 manufacturer_height_cm
   发送给厂家时会使用这两个值
   
3. 调整验证规则：
   修改 VALIDATION_CONFIG 来调整全局验证规则
   或在产品配置中设置 tolerance_percent 来设置特定产品的误差范围
   
4. 调整发送格式：
   修改 SEND_FORMAT_CONFIG 来调整发送给厂家的尺寸格式
   
5. 添加尺寸别名：
   在 SIZE_ALIAS_MAPPING 中添加别名映射，支持多种尺寸标识指向同一产品
"""
'''
        
        return config_content
    
    def check_sync_status(self):
        """检查同步状态"""
        
        print("\n🔍 检查自动同步状态...")
        
        with app.app_context():
            # 检查数据库中的产品配置
            products = Product.query.filter_by(is_active=True).all()
            total_sizes = 0
            
            print(f"   数据库产品配置:")
            for product in products:
                sizes = ProductSize.query.filter_by(product_id=product.id, is_active=True).all()
                total_sizes += len(sizes)
                print(f"     {product.name}: {len(sizes)} 个尺寸")
            
            print(f"   总计: {len(products)} 个产品, {total_sizes} 个尺寸")
            
            # 检查配置文件（优先检查 size_config.py）
            try:
                # 优先检查 size_config.py（实际使用的配置文件）
                try:
                    from size_config import SIZE_MAPPING as size_config_mapping
                    config_printer_ids = set()
                    for key, value in size_config_mapping.items():
                        config_printer_ids.add(value['product_id'])
                    print(f"   size_config.py: {len(size_config_mapping)} 个尺寸映射")
                except ImportError:
                    # 如果 size_config.py 不存在，检查 printer_config.py
                    from printer_config import SIZE_MAPPING as size_config_mapping
                    config_printer_ids = set()
                    for key, value in size_config_mapping.items():
                        config_printer_ids.add(value['product_id'])
                    print(f"   printer_config.py: {len(size_config_mapping)} 个尺寸映射")
                
                # 检查一致性
                db_printer_ids = set()
                for product in products:
                    sizes = ProductSize.query.filter_by(product_id=product.id, is_active=True).all()
                    for size in sizes:
                        if size.printer_product_id:
                            db_printer_ids.add(size.printer_product_id)
                
                if db_printer_ids == config_printer_ids:
                    print(f"   ✅ 配置一致")
                    return True
                else:
                    print(f"   ❌ 配置不一致")
                    print(f"     数据库: {db_printer_ids}")
                    print(f"     配置文件: {config_printer_ids}")
                    missing = db_printer_ids - config_printer_ids
                    extra = config_printer_ids - db_printer_ids
                    if missing:
                        print(f"     缺失的产品ID: {missing}")
                    if extra:
                        print(f"     多余的产品ID: {extra}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ 配置文件检查失败: {str(e)}")
                return False

# 全局同步实例
product_sync = ProductConfigSync()

def auto_sync_product_config():
    """自动同步产品配置（供外部调用）"""
    return product_sync.sync_to_printer_config()

def check_auto_sync_status():
    """检查自动同步状态（供外部调用）"""
    return product_sync.check_sync_status()

if __name__ == "__main__":
    # 执行自动同步
    auto_sync_product_config()
    check_auto_sync_status()



