#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云OSS配置指南
"""

def aliyun_oss_setup_guide():
    """阿里云OSS配置指南"""
    
    print("=== 阿里云OSS配置指南 ===")
    print()
    
    print("📋 第一步：注册阿里云账号")
    print("1. 访问: https://www.aliyun.com/")
    print("2. 注册/登录阿里云账号")
    print("3. 完成实名认证")
    print()
    
    print("📋 第二步：开通OSS服务")
    print("1. 进入阿里云控制台")
    print("2. 搜索'对象存储OSS'")
    print("3. 开通OSS服务")
    print("4. 选择按量付费（测试阶段）")
    print()
    
    print("📋 第三步：创建存储桶")
    print("1. 进入OSS控制台")
    print("2. 点击'创建Bucket'")
    print("3. 配置信息:")
    print("   - Bucket名称: pet-painting-images (自定义)")
    print("   - 地域: 选择离您最近的区域")
    print("   - 存储类型: 标准存储")
    print("   - 读写权限: 公共读 (重要!)")
    print("   - 服务端加密: 无")
    print("4. 点击'确定'创建")
    print()
    
    print("📋 第四步：获取访问密钥")
    print("1. 点击右上角头像 → AccessKey管理")
    print("2. 创建AccessKey")
    print("3. 记录以下信息:")
    print("   - AccessKey ID")
    print("   - AccessKey Secret")
    print("4. 妥善保存，不要泄露")
    print()
    
    print("📋 第五步：配置存储桶域名")
    print("1. 进入创建的Bucket")
    print("2. 点击'概览'")
    print("3. 记录'Bucket域名':")
    print("   格式: https://bucket-name.oss-region.aliyuncs.com")
    print("   例如: https://pet-painting-images.oss-cn-shenzhen.aliyuncs.com")
    print()

def create_oss_config():
    """创建OSS配置文件"""
    
    config_content = '''# 阿里云OSS配置
import oss2
import os
from datetime import datetime

# OSS配置信息
OSS_CONFIG = {
    'access_key_id': 'YOUR_ACCESS_KEY_ID',  # 替换为您的AccessKey ID
    'access_key_secret': 'YOUR_ACCESS_KEY_SECRET',  # 替换为您的AccessKey Secret
    'bucket_name': 'pet-painting-images',  # 替换为您的Bucket名称
    'endpoint': 'https://oss-cn-shenzhen.aliyuncs.com',  # 替换为您的区域endpoint
    'bucket_domain': 'https://pet-painting-images.oss-cn-shenzhen.aliyuncs.com',  # 替换为您的Bucket域名
}

class OSSUploader:
    """阿里云OSS上传器"""
    
    def __init__(self):
        self.config = OSS_CONFIG
        self.auth = oss2.Auth(self.config['access_key_id'], self.config['access_key_secret'])
        self.bucket = oss2.Bucket(self.auth, self.config['endpoint'], self.config['bucket_name'])
    
    def upload_file(self, local_file_path, oss_file_path):
        """上传文件到OSS"""
        try:
            result = self.bucket.put_object_from_file(oss_file_path, local_file_path)
            if result.status == 200:
                file_url = f"{self.config['bucket_domain']}/{oss_file_path}"
                return {
                    'success': True,
                    'url': file_url,
                    'message': '上传成功'
                }
            else:
                return {
                    'success': False,
                    'message': f'上传失败，状态码: {result.status}'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'上传异常: {str(e)}'
            }
    
    def upload_hd_image(self, local_file_path, order_number):
        """上传高清图片"""
        # 生成OSS文件路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.basename(local_file_path)
        oss_path = f"hd_images/{order_number}_{timestamp}_{filename}"
        
        return self.upload_file(local_file_path, oss_path)
    
    def upload_final_image(self, local_file_path, order_number):
        """上传成品图片"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.basename(local_file_path)
        oss_path = f"final_images/{order_number}_{timestamp}_{filename}"
        
        return self.upload_file(local_file_path, oss_path)

# 测试函数
def test_oss_connection():
    """测试OSS连接"""
    try:
        uploader = OSSUploader()
        print("✅ OSS连接测试成功")
        return True
    except Exception as e:
        print(f"❌ OSS连接测试失败: {e}")
        return False

if __name__ == '__main__':
    test_oss_connection()
'''
    
    with open('oss_config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("✅ OSS配置文件已创建: oss_config.py")
    print("请编辑此文件，填入您的OSS配置信息")

def create_oss_integration():
    """创建OSS集成代码"""
    
    integration_content = '''# OSS集成到冲印系统
import os
from oss_config import OSSUploader

def upload_to_oss_and_send_to_printer(order, hd_image_path):
    """上传到OSS并发送到冲印系统"""
    
    try:
        # 1. 上传高清图片到OSS
        uploader = OSSUploader()
        upload_result = uploader.upload_hd_image(hd_image_path, order.order_number)
        
        if not upload_result['success']:
            return {
                'success': False,
                'message': f'OSS上传失败: {upload_result["message"]}'
            }
        
        # 2. 更新订单记录，保存OSS URL
        order.oss_hd_image_url = upload_result['url']
        
        # 3. 发送到冲印系统（使用OSS URL）
        from printer_client import PrinterSystemClient
        from printer_config import PRINTER_SYSTEM_CONFIG
        
        printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        
        # 修改订单数据，使用OSS URL
        order_data = printer_client._build_order_data(order, hd_image_path)
        
        # 更新文件URL为OSS URL
        for sub_order in order_data['sub_orders']:
            for photo in sub_order['photos']:
                photo['file_url'] = upload_result['url']
        
        # 发送到冲印系统
        result = printer_client._send_request(order_data)
        
        return {
            'success': True,
            'message': '上传并发送成功',
            'oss_url': upload_result['url'],
            'printer_response': result
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'处理失败: {str(e)}'
        }

# 测试函数
def test_oss_integration():
    """测试OSS集成"""
    print("=== OSS集成测试 ===")
    
    # 创建测试文件
    test_file = 'test_hd_image.jpg'
    with open(test_file, 'w') as f:
        f.write('test image content')
    
    # 创建测试订单对象
    class TestOrder:
        def __init__(self):
            self.order_number = 'TEST_OSS_001'
            self.customer_name = '测试客户'
            self.customer_phone = '13800138000'
            self.size = 'medium'
            self.created_at = '2025-09-15 12:00:00'
    
    order = TestOrder()
    
    # 测试上传和发送
    result = upload_to_oss_and_send_to_printer(order, test_file)
    
    print(f"测试结果: {result}")
    
    # 清理测试文件
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == '__main__':
    test_oss_integration()
'''
    
    with open('oss_integration.py', 'w', encoding='utf-8') as f:
        f.write(integration_content)
    
    print("✅ OSS集成代码已创建: oss_integration.py")

def install_requirements():
    """安装依赖包"""
    
    requirements = '''# 阿里云OSS Python SDK
oss2>=2.18.0

# 其他依赖
requests>=2.25.0
Pillow>=8.0.0
'''
    
    with open('requirements_oss.txt', 'w', encoding='utf-8') as f:
        f.write(requirements)
    
    print("✅ 依赖文件已创建: requirements_oss.txt")
    print("请运行: pip install -r requirements_oss.txt")

def main():
    """主函数"""
    
    aliyun_oss_setup_guide()
    print()
    
    print("=== 配置文件创建 ===")
    create_oss_config()
    create_oss_integration()
    install_requirements()
    print()
    
    print("=== 下一步操作 ===")
    print("1. 按照指南注册阿里云账号并创建OSS")
    print("2. 编辑 oss_config.py 填入您的配置信息")
    print("3. 安装依赖: pip install -r requirements_oss.txt")
    print("4. 测试连接: python oss_config.py")
    print("5. 测试集成: python oss_integration.py")
    print()
    
    print("=== 费用说明 ===")
    print("阿里云OSS按量付费:")
    print("- 存储费用: 约0.12元/GB/月")
    print("- 流量费用: 约0.5元/GB")
    print("- 请求费用: 约0.01元/万次")
    print("- 测试阶段费用很低，通常几元钱")

if __name__ == '__main__':
    main()

