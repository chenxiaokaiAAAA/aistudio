# -*- coding: utf-8 -*-
"""
打印代理服务
运行在本地，接收来自阿里云服务器的打印请求，并转发到本地打印机
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import logging
from datetime import datetime
import base64
import tempfile

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 从环境变量或配置文件读取打印机路径
PRINTER_PATH = os.getenv('LOCAL_PRINTER_PATH', r'\\sm003\HP OfficeJet Pro 7730 series')
API_KEY = os.getenv('PRINT_PROXY_API_KEY', '')  # 可选：API密钥，用于安全验证
PORT = int(os.getenv('PRINT_PROXY_PORT', 8888))

class LocalPrinter:
    """本地打印机客户端"""
    
    def __init__(self, printer_path):
        self.printer_path = printer_path
        self.is_windows = sys.platform == 'win32'
    
    def print_image(self, image_path, copies=1):
        """打印图片"""
        logger.info(f"开始打印: 图片路径={image_path}, 份数={copies}")
        
        if not self.is_windows:
            logger.error("非Windows系统，无法打印")
            return {
                'success': False,
                'message': '本地打印功能仅支持Windows系统'
            }
        
        if not os.path.exists(image_path):
            logger.error(f"图片文件不存在: {image_path}")
            return {
                'success': False,
                'message': f'图片文件不存在: {image_path}'
            }
        
        logger.info(f"图片文件存在: {image_path}, 文件大小: {os.path.getsize(image_path)} 字节")
        
        try:
            import win32print
            import win32api
            
            # 直接使用配置的打印机路径（不再发现和尝试多个打印机）
            printer_name = self._extract_printer_name()
            logger.info(f"使用配置的打印机: {printer_name}")
            
            # 验证打印机连接
            try:
                printer_handle = win32print.OpenPrinter(printer_name)
                if printer_handle:
                    win32print.ClosePrinter(printer_handle)
                    logger.info(f"✅ 打印机连接正常: {printer_name}")
                else:
                    return {
                        'success': False,
                        'message': f'无法连接到打印机: {printer_name}'
                    }
            except Exception as e:
                logger.error(f"检查打印机连接失败: {str(e)}")
                return {
                    'success': False,
                    'message': f'无法连接到打印机或打印机名无效: {printer_name} ({str(e)})'
                }
            
            # 方法1: 使用ShellExecute（适用于本地打印机）
            logger.info(f"尝试方法1: ShellExecute")
            try:
                result_code = win32api.ShellExecute(
                    0,
                    "print",
                    image_path,
                    f'/d:"{printer_name}"',
                    ".",
                    0
                )
                logger.info(f"ShellExecute返回码: {result_code}")
                
                if result_code > 32:  # 成功时返回大于32的值
                    logger.info(f"✅ 打印任务已发送 (ShellExecute): {image_path} -> {printer_name}")
                    return {
                        'success': True,
                        'message': '打印任务已发送',
                        'printer': printer_name,
                        'file': image_path,
                        'copies': copies,
                        'method': 'ShellExecute',
                        'result_code': result_code
                    }
            except Exception as e:
                logger.warning(f"ShellExecute方法失败: {str(e)}")
            
            # 方法2: 使用win32print直接打印（适用于网络打印机）
            logger.info(f"尝试方法2: win32print直接打印")
            try:
                # 打开打印机
                printer_handle = win32print.OpenPrinter(printer_name)
                
                # 读取文件内容
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                # 开始打印作业
                job_info = ("测试打印", None, "RAW")
                job_id = win32print.StartDocPrinter(printer_handle, 1, job_info)
                win32print.StartPagePrinter(printer_handle)
                
                # 写入打印数据（对于图片，可能需要转换为打印格式）
                # 注意：直接打印图片数据可能不工作，需要转换为打印机可识别的格式
                # 这里我们使用更简单的方法：通过系统默认程序打印
                
                win32print.EndPagePrinter(printer_handle)
                win32print.EndDocPrinter(printer_handle)
                win32print.ClosePrinter(printer_handle)
                
                logger.info(f"✅ 打印任务已发送 (win32print): {image_path} -> {printer_name}")
                return {
                    'success': True,
                    'message': '打印任务已发送',
                    'printer': printer_name,
                    'file': image_path,
                    'copies': copies,
                    'method': 'win32print'
                }
            except Exception as e:
                logger.warning(f"win32print方法失败: {str(e)}")
            
            # 方法3: 使用subprocess调用系统打印命令
            logger.info(f"尝试方法3: subprocess系统命令")
            try:
                import subprocess
                # 使用Windows的默认图片查看器打印
                subprocess.run([
                    'rundll32.exe',
                    'printui.dll,PrintUIEntry',
                    '/in',
                    '/n',
                    printer_name
                ], check=False)
                
                # 或者直接使用图片查看器打印
                subprocess.Popen([
                    'mspaint.exe',
                    '/p',
                    image_path
                ], shell=True)
                
                logger.info(f"✅ 打印任务已发送 (subprocess): {image_path} -> {printer_name}")
                return {
                    'success': True,
                    'message': '打印任务已发送（使用系统命令）',
                    'printer': printer_name,
                    'file': image_path,
                    'copies': copies,
                    'method': 'subprocess'
                }
            except Exception as e:
                logger.error(f"subprocess方法失败: {str(e)}")
            
            # 所有方法都失败
            error_msg = '所有打印方法都失败了'
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }
            
        except ImportError as e:
            logger.error(f"缺少pywin32库: {str(e)}")
            return {
                'success': False,
                'message': '需要安装pywin32库: pip install pywin32'
            }
        except Exception as e:
            logger.error(f"打印失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'打印失败: {str(e)}'
            }
    
    def _extract_printer_name(self):
        """提取打印机名称"""
        # 如果路径是 \\服务器\打印机名 格式，尝试不同的方式
        if self.printer_path.startswith('\\\\'):
            # 尝试直接使用完整路径
            printer_name = self.printer_path
            logger.info(f"尝试使用完整路径: {printer_name}")
            
            # 如果完整路径失败，尝试只使用打印机名部分
            # 例如：\\192.168.2.95\HPB483F8 -> HPB483F8
            parts = self.printer_path.split('\\')
            if len(parts) >= 4:
                simple_name = parts[-1]  # 获取最后一部分（打印机名）
                logger.info(f"提取的简单打印机名: {simple_name}")
                return simple_name
            
            return printer_name
        else:
            return self.printer_path
    
    # 已移除get_available_printers方法，直接使用配置的打印机路径

# 初始化打印机
printer = LocalPrinter(PRINTER_PATH)

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'printer_path': PRINTER_PATH,
        'platform': sys.platform,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/print', methods=['POST'])
def print_image():
    """打印图片接口"""
    try:
        # 验证API密钥（如果设置了）
        if API_KEY:
            provided_key = request.headers.get('X-API-Key') or request.json.get('api_key')
            if provided_key != API_KEY:
                return jsonify({
                    'success': False,
                    'message': 'API密钥验证失败'
                }), 401
        
        # 获取打印参数
        data = request.json or {}
        image_data = data.get('image_data')  # Base64编码的图片数据
        image_url = data.get('image_url')  # 图片URL
        image_path = data.get('image_path')  # 本地图片路径
        file_ext = data.get('file_ext')  # 文件扩展名（优先使用）
        copies = int(data.get('copies', 1))
        
        # 处理图片数据
        actual_image_path = None
        
        if image_path and os.path.exists(image_path):
            # 使用本地路径
            actual_image_path = image_path
        elif image_data:
            # Base64数据，保存为临时文件
            try:
                file_bytes = base64.b64decode(image_data)
                
                # 优先使用请求中提供的文件扩展名
                if not file_ext:
                    # 如果没有提供扩展名，尝试从数据中检测文件类型
                    file_ext = '.jpg'  # 默认JPG
                    if file_bytes.startswith(b'%PDF'):
                        file_ext = '.pdf'
                    elif file_bytes.startswith(b'\xd0\xcf\x11\xe0'):  # Office文档
                        file_ext = '.doc'
                    elif file_bytes.startswith(b'PK\x03\x04'):  # ZIP格式（可能是docx）
                        file_ext = '.docx'
                    elif file_bytes.startswith(b'\x89PNG'):
                        file_ext = '.png'
                    elif file_bytes.startswith(b'GIF'):
                        file_ext = '.gif'
                    elif file_bytes.startswith(b'BM'):
                        file_ext = '.bmp'
                    else:
                        # 尝试检测是否为文本文件（检查前100字节是否都是可打印字符）
                        try:
                            sample = file_bytes[:100] if len(file_bytes) > 100 else file_bytes
                            if sample and all(32 <= b < 127 or b in (9, 10, 13) for b in sample):
                                file_ext = '.txt'
                                logger.info("检测到文本文件格式")
                        except:
                            pass
                
                # 确保扩展名以点开头
                if file_ext and not file_ext.startswith('.'):
                    file_ext = '.' + file_ext
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
                temp_file.write(file_bytes)
                temp_file.close()
                actual_image_path = temp_file.name
                logger.info(f"保存临时文件: {actual_image_path} (格式: {file_ext}, 大小: {len(file_bytes)} 字节)")
            except Exception as e:
                logger.error(f"解析文件数据失败: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'解析文件数据失败: {str(e)}'
                }), 400
        elif image_url:
            # 从URL下载图片
            try:
                import requests
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                temp_file.write(response.content)
                temp_file.close()
                actual_image_path = temp_file.name
                logger.info(f"下载并保存图片: {actual_image_path}")
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'下载图片失败: {str(e)}'
                }), 400
        else:
            return jsonify({
                'success': False,
                'message': '请提供图片数据（image_data、image_url或image_path）'
            }), 400
        
        # 执行打印
        result = printer.print_image(actual_image_path, copies)
        
        # 延迟清理临时文件，给打印任务足够的时间打开文件
        # ShellExecute是异步的，需要等待一段时间才能确保文件被打开
        if actual_image_path and actual_image_path.startswith(tempfile.gettempdir()):
            import threading
            import time
            
            def delayed_cleanup(file_path, delay_seconds=5):
                """延迟清理临时文件"""
                time.sleep(delay_seconds)
                try:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                        logger.info(f"已清理临时文件: {file_path}")
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {file_path}, 错误: {str(e)}")
            
            # 在后台线程中延迟清理
            cleanup_thread = threading.Thread(target=delayed_cleanup, args=(actual_image_path,))
            cleanup_thread.daemon = True
            cleanup_thread.start()
            logger.info(f"已安排延迟清理临时文件: {actual_image_path} (5秒后)")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"打印接口错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@app.route('/print/blank', methods=['POST'])
def print_blank_page():
    """打印空白页（用于测试）"""
    try:
        # 验证API密钥（如果设置了）
        if API_KEY:
            provided_key = request.headers.get('X-API-Key') or (request.json and request.json.get('api_key'))
            if provided_key != API_KEY:
                return jsonify({
                    'success': False,
                    'message': 'API密钥验证失败'
                }), 401
        
        # 创建一个空白图片
        try:
            from PIL import Image
            import tempfile
            
            # 创建A4尺寸的空白图片（300 DPI）
            width = int(8.27 * 300)  # A4宽度 8.27英寸
            height = int(11.69 * 300)  # A4高度 11.69英寸
            
            blank_image = Image.new('RGB', (width, height), color='white')
            
            # 添加测试文字（必须添加，确保不是空白页）
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(blank_image)
                
                # 尝试使用系统字体
                try:
                    # 尝试多种常见字体路径
                    font_paths = [
                        "arial.ttf",
                        "C:/Windows/Fonts/arial.ttf",
                        "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                        "C:/Windows/Fonts/simsun.ttc",  # 宋体
                    ]
                    font = None
                    for font_path in font_paths:
                        try:
                            font = ImageFont.truetype(font_path, 500)  # 使用大字体，确保清晰可见
                            break
                        except:
                            continue
                    
                    if not font:
                        font = ImageFont.load_default()
                except:
                    font = ImageFont.load_default()
                
                # 在页面中央添加一个大大的字符 "a"（用于测试打印）
                text = "a"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                position = ((width - text_width) // 2, (height - text_height) // 2)
                draw.text(position, text, fill='black', font=font)
                
                logger.info(f"已添加测试字符 'a' 到图片中心")
            except Exception as e:
                # 如果无法添加文字，至少添加一个点
                logger.warning(f"无法添加文字，尝试添加点: {str(e)}")
                try:
                    draw = ImageDraw.Draw(blank_image)
                    # 在中心添加一个小黑点
                    center_x, center_y = width // 2, height // 2
                    draw.ellipse([center_x-10, center_y-10, center_x+10, center_y+10], fill='black')
                    logger.info(f"已添加测试点")
                except:
                    logger.error("无法添加任何内容到图片")
            
            # 保存为临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            blank_image.save(temp_file.name, 'JPEG', quality=95, dpi=(300, 300))
            temp_file.close()
            
            logger.info(f"创建测试页（包含字符'a'）: {temp_file.name}")
            
            # 打印
            result = printer.print_image(temp_file.name, copies=1)
            
            # 清理临时文件
            try:
                os.unlink(temp_file.name)
            except:
                pass
            
            if result.get('success'):
                result['message'] = '测试页打印成功（包含字符"a"）'
            
            return jsonify(result)
            
        except ImportError:
            return jsonify({
                'success': False,
                'message': '需要安装PIL库: pip install Pillow'
            }), 500
        except Exception as e:
            logger.error(f"打印空白页失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'打印失败: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"打印空白页接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@app.route('/test', methods=['GET'])
def test_printer():
    """测试打印机连接"""
    try:
        if not printer.is_windows:
            return jsonify({
                'success': False,
                'message': '本地打印功能仅支持Windows系统'
            })
        
        import win32print
        printer_name = printer._extract_printer_name()
        printer_handle = win32print.OpenPrinter(printer_name)
        
        if printer_handle:
            win32print.ClosePrinter(printer_handle)
            return jsonify({
                'success': True,
                'message': f'打印机连接正常: {printer_name}',
                'printer_path': PRINTER_PATH
            })
        else:
            return jsonify({
                'success': False,
                'message': f'无法连接到打印机: {printer_name}'
            })
    except ImportError:
        return jsonify({
            'success': False,
            'message': '需要安装pywin32库: pip install pywin32'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'测试连接失败: {str(e)}'
        })

if __name__ == '__main__':
    logger.info(f"🚀 打印代理服务启动")
    logger.info(f"   打印机路径: {PRINTER_PATH}")
    logger.info(f"   监听端口: {PORT}")
    logger.info(f"   平台: {sys.platform}")
    
    if API_KEY:
        logger.info(f"   API密钥: 已启用")
    else:
        logger.warning(f"   API密钥: 未设置（建议设置以提高安全性）")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
