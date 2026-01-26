# 阿里云OSS配置
import oss2
import os
from datetime import datetime

# OSS配置信息 - 请填入您的实际信息
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
        """上传高清图片到OSS"""
        try:
            # 生成OSS文件路径
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.basename(local_file_path)
            oss_path = f"hd_images/{order_number}_{timestamp}_{filename}"
            return self.upload_file(local_file_path, oss_path)
        except Exception as e:
            return {
                'success': False,
                'message': f'上传异常: {str(e)}'
            }
    
    def upload_test_image(self, local_file_path, order_number=None):
        """上传测试图片到OSS（用于美图API测试）"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.basename(local_file_path)
            if order_number:
                oss_path = f"meitu_test/{order_number}_{timestamp}_{filename}"
            else:
                oss_path = f"meitu_test/test_{timestamp}_{filename}"
            return self.upload_file(local_file_path, oss_path)
        except Exception as e:
            return {
                'success': False,
                'message': f'上传异常: {str(e)}'
            }

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

