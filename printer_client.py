# 冲印系统API客户端
import requests
import json
import os
import base64
from datetime import datetime
from urllib.parse import urljoin
import logging

# 尝试导入新的尺寸配置，如果不存在则使用旧的配置
try:
    from size_config import (
        SIZE_MAPPING, 
        VALIDATION_CONFIG, 
        SEND_FORMAT_CONFIG, 
        SIZE_ALIAS_MAPPING
    )
    USE_NEW_CONFIG = True
except ImportError:
    # 如果新配置不存在，使用旧的配置
    from printer_config import SIZE_MAPPING
    USE_NEW_CONFIG = False
    VALIDATION_CONFIG = {
        'enabled': True,
        'default_dpi': 300,
        'tolerance_percent': 5,
        'strict_mode': False,
    }
    SEND_FORMAT_CONFIG = {
        'width_decimals': 2,
        'height_decimals': 2,
        'size_format': 'cm',
        'include_pixel_size': True,
        'include_dpi': True,
    }
    SIZE_ALIAS_MAPPING = {}

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrinterSystemClient:
    """冲印系统API客户端"""
    
    def __init__(self, config):
        self.config = config
        self.api_url = config['api_url']
        self.source_app_id = config['source_app_id']
        self.shop_id = config['shop_id']
        self.shop_name = config['shop_name']
        self.timeout = config.get('timeout', 30)
        self.retry_times = config.get('retry_times', 3)
    
    def _find_size_info(self, size_key):
        """查找尺寸配置信息（支持别名映射）"""
        # 1. 检查别名映射
        if size_key in SIZE_ALIAS_MAPPING:
            size_key = SIZE_ALIAS_MAPPING[size_key]
        
        # 2. 直接匹配
        if size_key in SIZE_MAPPING:
            return SIZE_MAPPING[size_key]
        
        # 3. 通过产品名称反向查找
        for key, value in SIZE_MAPPING.items():
            if value.get('product_name') == size_key:
                return value
            # 4. 部分匹配查找
            elif size_key in value.get('product_name', '') or value.get('product_name', '') in size_key:
                return value
        
        return None
    
    def _validate_image_size(self, image_path, order):
        """验证图片尺寸是否符合要求（使用新的配置系统）"""
        # 检查是否启用验证
        if not VALIDATION_CONFIG.get('enabled', True):
            logger.info("尺寸验证已禁用")
            return {
                'valid': True,
                'message': '尺寸验证已禁用',
                'required': None,
                'actual': None
            }
        
        try:
            from PIL import Image
            
            with Image.open(image_path) as img:
                width, height = img.size
                
                # 查找尺寸配置
                size_key = order.size
                size_info = self._find_size_info(size_key)
                
                if not size_info:
                    return {
                        'valid': False,
                        'message': f'订单尺寸 "{size_key}" 未在配置中找到',
                        'required': None,
                        'actual': {'width': width, 'height': height}
                    }
                
                # 获取要求的尺寸
                required_width_cm = size_info['width_cm']
                required_height_cm = size_info['height_cm']
                
                # 获取DPI（优先使用产品配置，否则使用全局配置）
                required_dpi = size_info.get('dpi', VALIDATION_CONFIG.get('default_dpi', 300))
                
                # 获取误差范围（优先使用产品配置，否则使用全局配置）
                tolerance_percent = size_info.get('tolerance_percent', VALIDATION_CONFIG.get('tolerance_percent', 5))
                
                # 计算要求的像素尺寸
                required_width_px = int(required_width_cm * required_dpi / 2.54)
                required_height_px = int(required_height_cm * required_dpi / 2.54)
                
                # 严格模式：尺寸必须完全匹配
                if VALIDATION_CONFIG.get('strict_mode', False):
                    width_valid = width == required_width_px
                    height_valid = height == required_height_px
                    tolerance_info = "严格模式：尺寸必须完全匹配"
                else:
                    # 计算误差范围
                    tolerance_min = 1 - tolerance_percent / 100
                    tolerance_max = 1 + tolerance_percent / 100
                    
                    width_ratio = width / required_width_px
                    height_ratio = height / required_height_px
                    
                    width_valid = tolerance_min <= width_ratio <= tolerance_max
                    height_valid = tolerance_min <= height_ratio <= tolerance_max
                    tolerance_info = f"允许误差: ±{tolerance_percent}%"
                
                if width_valid and height_valid:
                    return {
                        'valid': True,
                        'message': '图片尺寸符合要求',
                        'required': {
                            'width_cm': required_width_cm,
                            'height_cm': required_height_cm,
                            'width_px': required_width_px,
                            'height_px': required_height_px,
                            'dpi': required_dpi,
                            'tolerance_percent': tolerance_percent,
                            'tolerance_info': tolerance_info
                        },
                        'actual': {
                            'width': width,
                            'height': height,
                            'width_cm': round(width * 2.54 / required_dpi, 2),
                            'height_cm': round(height * 2.54 / required_dpi, 2)
                        }
                    }
                else:
                    actual_width_cm = round(width * 2.54 / required_dpi, 2)
                    actual_height_cm = round(height * 2.54 / required_dpi, 2)
                    return {
                        'valid': False,
                        'message': f'图片尺寸不符合要求。需要: {required_width_cm}cm x {required_height_cm}cm ({required_width_px}x{required_height_px}px @ {required_dpi}DPI)，实际: {actual_width_cm}cm x {actual_height_cm}cm ({width}x{height}px)。{tolerance_info}',
                        'required': {
                            'width_cm': required_width_cm,
                            'height_cm': required_height_cm,
                            'width_px': required_width_px,
                            'height_px': required_height_px,
                            'dpi': required_dpi,
                            'tolerance_percent': tolerance_percent,
                            'tolerance_info': tolerance_info
                        },
                        'actual': {
                            'width': width,
                            'height': height,
                            'width_cm': actual_width_cm,
                            'height_cm': actual_height_cm
                        }
                    }
                    
        except Exception as e:
            return {
                'valid': False,
                'message': f'验证图片尺寸时发生错误: {str(e)}',
                'required': None,
                'actual': None
            }
    
    def send_order_to_printer(self, order, image_path, order_obj=None):
        """
        发送订单到冲印系统
        
        Args:
            order: 订单对象
            image_path: 图片路径
            order_obj: 数据库订单对象（用于更新状态）
            
        Returns:
            dict: 响应结果
        """
        try:
            # 更新发送状态为"发送中"
            if order_obj:
                order_obj.printer_send_status = 'sending'
                order_obj.printer_send_time = datetime.now()
                order_obj.printer_error_message = None
                order_obj.printer_response_data = None
            
            logger.info(f"开始发送订单 {order.order_number} 到冲印系统")
            logger.info(f"图片路径: {image_path}")
            
            # 检查图片文件是否存在
            # 尝试多个可能的路径
            possible_paths = [
                image_path,  # 原始路径
                os.path.join('hd_images', image_path),  # hd_images目录
                os.path.join('uploads', image_path),  # uploads目录
                os.path.join('final_works', image_path),  # final_works目录
            ]
            
            actual_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    actual_path = path
                    break
            
            if not actual_path:
                error_msg = f"图片文件不存在，尝试的路径: {possible_paths}"
                logger.error(error_msg)
                if order_obj:
                    order_obj.printer_send_status = 'sent_failed'
                    order_obj.printer_error_message = error_msg
                return {
                    'success': False,
                    'message': error_msg,
                    'error_type': 'file_not_found'
                }
            
            logger.info(f"找到图片文件: {actual_path}")
            
            # 验证图片尺寸
            validation_result = self._validate_image_size(actual_path, order)
            logger.info(f"图片尺寸验证结果: {validation_result}")
            
            if not validation_result['valid']:
                error_msg = f"图片尺寸验证失败: {validation_result['message']}"
                logger.error(error_msg)
                if order_obj:
                    order_obj.printer_send_status = 'sent_failed'
                    order_obj.printer_error_message = error_msg
                return {
                    'success': False,
                    'message': error_msg,
                    'error_type': 'size_validation_failed',
                    'validation_result': validation_result
                }
            
            logger.info("✅ 图片尺寸验证通过")
            
            # 构建订单数据
            order_data = self._build_order_data(order, actual_path)
            
            # 显示发送的数据包内容（调试用）
            logger.info(f"发送数据包预览:")
            logger.info(f"  订单号: {order_data.get('order_number', 'N/A')}")
            logger.info(f"  产品ID: {order_data.get('product_id', 'N/A')}")
            logger.info(f"  产品名称: {order_data.get('product_name', 'N/A')}")
            if 'sub_orders' in order_data and order_data['sub_orders']:
                sub_order = order_data['sub_orders'][0]
                logger.info(f"  图片信息:")
                logger.info(f"    文件名: {sub_order.get('file_name', 'N/A')}")
                logger.info(f"    像素尺寸: {sub_order.get('pix_width', 'N/A')} x {sub_order.get('pix_height', 'N/A')}")
                logger.info(f"    DPI: {sub_order.get('dpi', 'N/A')}")
                logger.info(f"    物理尺寸: {sub_order.get('width', 'N/A')} x {sub_order.get('height', 'N/A')}")
            
            # 发送请求
            response = self._send_request(order_data)
            
            # 更新发送状态为"发送成功"
            if order_obj:
                order_obj.printer_send_status = 'sent_success'
                order_obj.printer_response_data = json.dumps(response, ensure_ascii=False)
            
            logger.info(f"订单 {order.order_number} 发送到冲印系统成功")
            logger.info(f"冲印系统响应: {response}")
            
            return {
                'success': True,
                'message': '订单发送成功',
                'response': response,
                'send_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            error_msg = f'发送失败: {str(e)}'
            logger.error(f"发送订单到冲印系统失败: {error_msg}")
            
            # 更新发送状态为"发送失败"
            if order_obj:
                order_obj.printer_send_status = 'sent_failed'
                order_obj.printer_error_message = error_msg
            
            return {
                'success': False,
                'message': error_msg,
                'error_type': 'api_error',
                'send_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _build_order_data(self, order, final_image_path):
        """构建订单数据"""
        
        # 获取图片信息
        image_info = self._get_image_info(final_image_path, order)
        
        # 构建收件人信息
        shipping_receiver = {
            'name': order.customer_name,
            'mobile': order.customer_phone,
            'province': '广东省',  # 默认值
            'city': '深圳市',
            'city_part': '南山区',
            'street': '详细地址',
            'corp_name': ''
        }
        
        # 尝试从地址中解析信息
        if order.shipping_info:
            try:
                import json
                # 解析JSON格式的地址信息
                shipping_data = json.loads(order.shipping_info)
                
                # 提取地址信息
                receiver = shipping_data.get('receiver', '')
                phone = shipping_data.get('phone', '')
                full_address = shipping_data.get('fullAddress', '')
                remark = shipping_data.get('remark', '')
                
                # 更新收件人信息
                if receiver:
                    shipping_receiver['name'] = receiver
                if phone:
                    shipping_receiver['mobile'] = phone
                if full_address:
                    # 直接使用完整地址作为街道地址
                    shipping_receiver['street'] = full_address
                    
            except (json.JSONDecodeError, AttributeError):
                # 如果JSON解析失败，直接使用原始地址
                shipping_receiver['street'] = str(order.shipping_info)
        
        # 构建照片信息（根据发送格式配置）
        photo_data = {
            'page_type': 0,  # 0=内页
            'index': 1,
            'num': 1,
            'file_name': os.path.basename(final_image_path),
            'width': image_info['width_cm'],  # 厂家要求的宽度（已格式化）
            'height': image_info['height_cm'],  # 厂家要求的高度（已格式化）
            'size': f"{image_info['width_cm']}x{image_info['height_cm']}",  # 尺寸字符串
            'size_width': image_info['width_cm'],  # 单独的宽度字段
            'size_height': image_info['height_cm'],  # 单独的高度字段
            'file_url': self._get_file_url(final_image_path)
        }
        
        # 根据配置决定是否包含像素尺寸和DPI
        if SEND_FORMAT_CONFIG.get('include_pixel_size', True):
            photo_data['pix_width'] = image_info['width']
            photo_data['pix_height'] = image_info['height']
        
        if SEND_FORMAT_CONFIG.get('include_dpi', True):
            photo_data['dpi'] = image_info['dpi']
        
        photos = [photo_data]
        
        # 根据尺寸获取产品ID（使用新的查找方法）
        product_id = 'P001'  # 默认产品ID
        product_name = f"定制油画 {order.size}"
        
        # 如果订单有尺寸信息，尝试从SIZE_MAPPING获取
        if hasattr(order, 'size') and order.size:
            size_info = self._find_size_info(order.size)
            
            if size_info:
                product_id = size_info['product_id']
                product_name = size_info['product_name']
        
        # 构建子订单信息
        sub_orders = [{
            'sub_order_id': f"{order.order_number}_1",
            'complex_product': None,
            'customer_name': order.customer_name,
            'props': [],
            'product_id': product_id,  # 使用正确的产品ID
            'product_name': product_name,
            'shop_product_sn': order.order_number,
            'remark': "",
            'num': 1,
            'photos': photos
        }]
        
        # 根据订单的加盟商信息动态获取 shop_id 和 shop_name
        shop_id = self.shop_id  # 默认使用配置中的值
        shop_name = self.shop_name  # 默认使用配置中的值
        
        # 检查订单是否有加盟商，且加盟商是否配置了专属的厂家ID
        if hasattr(order, 'franchisee_id') and order.franchisee_id:
            try:
                from test_server import FranchiseeAccount
                franchisee = FranchiseeAccount.query.get(order.franchisee_id)
                if franchisee:
                    # 如果加盟商配置了专属的厂家ID，则使用加盟商的配置
                    if franchisee.printer_shop_id:
                        shop_id = franchisee.printer_shop_id
                        logger.info(f"使用加盟商专属 shop_id: {shop_id} (加盟商: {franchisee.company_name})")
                    if franchisee.printer_shop_name:
                        shop_name = franchisee.printer_shop_name
                        logger.info(f"使用加盟商专属 shop_name: {shop_name} (加盟商: {franchisee.company_name})")
            except Exception as e:
                logger.warning(f"获取加盟商配置失败，使用默认配置: {str(e)}")
        
        # 构建完整订单数据
        order_data = {
            'source_app_id': self.source_app_id,
            'order_id': f"YT_{order.id}",  # 主订单标识号
            'order_no': order.order_number,  # 来源系统订单号
            'order_time': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'push_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'remark': "",
            'shop_id': shop_id,  # 使用动态获取的 shop_id
            'shop_name': shop_name,  # 使用动态获取的 shop_name
            'shipping_receiver': shipping_receiver,
            'sub_orders': sub_orders
        }
        
        return order_data
    
    def _get_image_info(self, image_path, order):
        """获取图片信息（使用厂家要求的尺寸）"""
        try:
            from PIL import Image
            
            with Image.open(image_path) as img:
                width, height = img.size
                
                # 查找尺寸配置
                size_key = order.size
                size_info = self._find_size_info(size_key)
                
                if size_info:
                    # 优先使用厂家要求的尺寸（manufacturer_width_cm/manufacturer_height_cm）
                    # 如果没有配置，则使用标准尺寸（width_cm/height_cm）
                    manufacturer_width_cm = size_info.get('manufacturer_width_cm', size_info.get('width_cm'))
                    manufacturer_height_cm = size_info.get('manufacturer_height_cm', size_info.get('height_cm'))
                    
                    # 获取DPI
                    dpi = size_info.get('dpi', VALIDATION_CONFIG.get('default_dpi', 300))
                    
                    logger.info(f"找到尺寸配置: {manufacturer_width_cm}cm x {manufacturer_height_cm}cm")
                    logger.info(f"使用厂家要求的尺寸: {manufacturer_width_cm}cm x {manufacturer_height_cm}cm")
                else:
                    # 如果找不到配置，使用默认A4尺寸
                    manufacturer_width_cm = 21.0
                    manufacturer_height_cm = 29.7
                    dpi = VALIDATION_CONFIG.get('default_dpi', 300)
                    logger.warning(f"未找到尺寸配置，使用默认A4尺寸: {manufacturer_width_cm}cm x {manufacturer_height_cm}cm")
                
                # 根据发送格式配置格式化尺寸
                width_decimals = SEND_FORMAT_CONFIG.get('width_decimals', 2)
                height_decimals = SEND_FORMAT_CONFIG.get('height_decimals', 2)
                
                result = {
                    'width': width,
                    'height': height,
                    'dpi': dpi,
                    'width_cm': round(manufacturer_width_cm, width_decimals),
                    'height_cm': round(manufacturer_height_cm, height_decimals)
                }
                
                logger.info(f"返回图片信息: {result}")
                return result
                
        except Exception as e:
            logger.error(f"获取图片信息失败: {str(e)}")
            # 返回默认值
            return {
                'width': 2480,
                'height': 3508,
                'dpi': 300,
                'width_cm': 21.0,
                'height_cm': 29.7
            }
    
    def _get_file_url(self, image_path):
        """获取文件访问URL"""
        filename = os.path.basename(image_path)
        base_url = self.config.get('file_access_base_url', "http://photogooo")
        
        # 对文件名进行URL编码，避免厂家系统自动编码导致的问题
        from urllib.parse import quote
        encoded_filename = quote(filename)
        
        # 根据图片类型选择不同的路径
        if 'hd_' in filename:
            return f"{base_url}/public/hd/{encoded_filename}"  # 使用URL编码的文件名
        elif 'final_' in filename:
            return f"{base_url}/media/final/{encoded_filename}"
        else:
            return f"{base_url}/media/original/{encoded_filename}"
    
    def _send_request(self, order_data):
        """发送请求到冲印系统"""
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        for attempt in range(self.retry_times):
            try:
                logger.info(f"发送订单数据到冲印系统 (尝试 {attempt + 1}/{self.retry_times})")
                logger.info(f"请求URL: {self.api_url}")
                logger.info(f"订单数据: {json.dumps(order_data, ensure_ascii=False, indent=2)}")
                
                response = requests.post(
                    self.api_url,
                    json=order_data,
                    headers=headers,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"冲印系统响应: {result}")
                
                return result
                
            except requests.exceptions.RequestException as e:
                logger.error(f"请求失败 (尝试 {attempt + 1}): {str(e)}")
                if attempt == self.retry_times - 1:
                    raise e
                
                # 等待后重试
                import time
                time.sleep(2 ** attempt)  # 指数退避
        
        raise Exception("所有重试尝试都失败了")
