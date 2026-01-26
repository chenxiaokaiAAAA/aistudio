# server_config.py
# 服务器地址配置
# 开发环境：使用本地地址
# 生产环境：使用云端地址

import os

# 当前环境：'local' 或 'production'
# 优先使用环境变量 SERVER_ENV，如果没有则使用文件中的默认值
# 直接修改下面的 'local' 为 'production' 即可切换环境
ENV = os.environ.get('SERVER_ENV', 'local')  # 修改这里的 'local' 为 'production' 即可切换

# 服务器地址配置
SERVER_CONFIG = {
    'local': {
        'base_url': 'http://192.168.2.54:8000',
        'api_base_url': 'http://192.168.2.54:8000/api',
        'static_url': 'http://192.168.2.54:8000/static',
        'media_url': 'http://192.168.2.54:8000/media',
        'notify_url': 'http://192.168.2.54:8000/api/payment/notify'
    },
    'production': {
        'base_url': 'https://moeart.cc',
        'api_base_url': 'https://moeart.cc/api',
        'static_url': 'https://moeart.cc/static',
        'media_url': 'https://moeart.cc/media',
        'notify_url': 'https://moeart.cc/api/payment/notify'
    }
}

# 获取当前环境的配置
def get_config():
    return SERVER_CONFIG.get(ENV, SERVER_CONFIG['production'])

# 便捷方法
def get_base_url():
    return get_config()['base_url']

def get_api_base_url():
    return get_config()['api_base_url']

def get_static_url():
    return get_config()['static_url']

def get_media_url():
    return get_config()['media_url']

def get_notify_url():
    return get_config()['notify_url']
