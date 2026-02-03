# 冲印系统集成配置
# 厂家提供的配置信息

# 冲印系统配置
PRINTER_SYSTEM_CONFIG = {
    'enabled': True,  # 是否启用冲印系统集成
    'api_base_url': 'http://xmdmsm.xicp.cn:5995/api/ODSGate',  # 冲印系统API基础地址
    'api_url': 'http://xmdmsm.xicp.cn:5995/api/ODSGate/NewOrder',  # 新订单接口
    'source_app_id': 'ZPG',  # 订单来源系统代号
    'shop_id': 'CS',  # 冲印系统对应的影楼编号（测试环境）
    'shop_name': '测试',  # 影楼名称（测试环境）
    'auth_token': 'YOUR_AUTH_TOKEN',  # 如果API需要认证，这里填写Token
    'callback_url': 'https://dev-camera-api.photogo520.com/open/xmdm/express/notify',  # 快递信息回调地址
    'file_access_base_url': 'http://photogooo',  # 外部可访问的文件基础URL
    'use_oss': True,  # 是否使用阿里云OSS存储
    'oss_bucket_domain': 'https://pet-painting-images.oss-cn-shenzhen.aliyuncs.com',  # OSS存储桶域名
    'timeout': 30,  # 请求超时时间（秒）
    'retry_times': 3,  # 重试次数
}

# 尺寸映射：将系统内部尺寸映射到冲印系统识别的尺寸代码或描述
# 此配置由产品配置管理页面自动生成 - 请勿手动修改
SIZE_MAPPING = {
    '88888': {'product_id': '88888', 'product_name': '证件照证件照-1寸', 'width_cm': 35.6, 'height_cm': 35.6},
    '1': {'product_id': '1', 'product_name': 'AI写真1', 'width_cm': 35.6, 'height_cm': 35.6},
    '12寸-（30x30cm）肌理油画框': {'product_id': '33673', 'product_name': '梵高油画框30x30cm肌理画框', 'width_cm': 35.6, 'height_cm': 35.6},
}
