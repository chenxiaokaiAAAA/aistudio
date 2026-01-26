# -*- coding: utf-8 -*-
"""
本地打印机模块（Windows网络打印机）
用于打印电子照片
"""
import os
import sys
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LocalPrinter:
    """本地打印机客户端（Windows网络打印机）"""
    
    def __init__(self, printer_path):
        """
        初始化本地打印机
        
        Args:
            printer_path: 打印机路径，如 '\\\\sm003\\HP OfficeJet Pro 7730 series'
        """
        self.printer_path = printer_path
        self.is_windows = sys.platform == 'win32'
        
        if not self.is_windows:
            logger.warning("本地打印功能仅支持Windows系统")
    
    def print_image(self, image_path, copies=1, paper_size='A4'):
        """
        打印图片到本地打印机
        
        Args:
            image_path: 图片文件路径
            copies: 打印份数（默认1份）
            paper_size: 纸张大小（默认A4）
            
        Returns:
            dict: 打印结果
        """
        if not self.is_windows:
            return {
                'success': False,
                'message': '本地打印功能仅支持Windows系统',
                'error_type': 'platform_not_supported'
            }
        
        if not os.path.exists(image_path):
            return {
                'success': False,
                'message': f'图片文件不存在: {image_path}',
                'error_type': 'file_not_found'
            }
        
        try:
            # 方法1: 使用Windows命令直接打印
            result = self._print_via_command(image_path, copies)
            
            if result['success']:
                logger.info(f"✅ 图片打印成功: {image_path}")
                return result
            else:
                # 如果命令方式失败，尝试使用Python库
                logger.warning(f"命令打印失败，尝试使用Python库: {result.get('message')}")
                return self._print_via_python_lib(image_path, copies, paper_size)
                
        except Exception as e:
            error_msg = f'打印失败: {str(e)}'
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'error_type': 'print_error'
            }
    
    def _print_via_command(self, image_path, copies):
        """使用Windows命令打印（推荐方法）"""
        try:
            import subprocess
            
            # 使用Windows的print命令或PowerShell
            # 方法1: 使用PowerShell的Start-Process命令
            printer_name = self._extract_printer_name()
            
            # 构建PowerShell命令
            ps_command = f'''
            $printer = "{printer_name}"
            $file = "{image_path.replace(chr(92), chr(92)+chr(92))}"
            Start-Process -FilePath $file -Verb Print -WindowStyle Hidden
            '''
            
            # 或者使用更简单的方法：直接调用默认打印
            # 使用rundll32或直接调用图片查看器的打印功能
            cmd = f'rundll32.exe printui.dll,PrintUIEntry /in /n "{printer_name}"'
            
            # 更简单的方法：使用mspaint或图片查看器打印
            # 但这种方法需要用户交互，不适合自动化
            
            # 最佳方法：使用Python的win32print库（如果可用）
            try:
                import win32print
                import win32api
                
                # 获取打印机句柄
                printer_handle = win32print.OpenPrinter(printer_name)
                
                # 打印文件
                win32api.ShellExecute(
                    0,
                    "print",
                    image_path,
                    f'/d:"{printer_name}"',
                    ".",
                    0
                )
                
                win32print.ClosePrinter(printer_handle)
                
                return {
                    'success': True,
                    'message': '打印任务已发送',
                    'printer': printer_name,
                    'file': image_path,
                    'copies': copies
                }
            except ImportError:
                # 如果没有win32print，使用subprocess调用系统打印
                logger.warning("win32print库未安装，使用备用方法")
                
                # 使用Windows的默认打印方式
                import subprocess
                result = subprocess.run(
                    ['powershell', '-Command', 
                     f'Start-Process -FilePath "{image_path}" -Verb Print'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return {
                        'success': True,
                        'message': '打印任务已发送（使用默认打印机）',
                        'file': image_path,
                        'copies': copies
                    }
                else:
                    return {
                        'success': False,
                        'message': f'打印命令执行失败: {result.stderr}',
                        'error_type': 'command_failed'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'message': f'命令打印失败: {str(e)}',
                'error_type': 'command_error'
            }
    
    def _print_via_python_lib(self, image_path, copies, paper_size):
        """使用Python库打印（备用方法）"""
        try:
            from PIL import Image
            
            # 打开图片
            img = Image.open(image_path)
            
            # 这里可以添加图片处理逻辑（如调整大小、DPI等）
            
            # 使用PIL的打印功能（需要系统支持）
            # 注意：PIL本身不直接支持打印，需要配合其他库
            
            # 保存为临时文件，然后使用系统命令打印
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            img.save(temp_file.name, 'PNG', dpi=(300, 300))
            temp_file.close()
            
            # 使用命令打印临时文件
            result = self._print_via_command(temp_file.name, copies)
            
            # 清理临时文件
            try:
                os.unlink(temp_file.name)
            except:
                pass
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Python库打印失败: {str(e)}',
                'error_type': 'python_lib_error'
            }
    
    def _extract_printer_name(self):
        """从打印机路径中提取打印机名称"""
        # 如果路径是 \\sm003\打印机名，提取打印机名
        if self.printer_path.startswith('\\\\'):
            # 格式: \\sm003\HP OfficeJet Pro 7730 series
            parts = self.printer_path.split('\\')
            if len(parts) >= 4:
                # 返回完整路径或只返回打印机名
                return self.printer_path  # 返回完整路径
            else:
                return parts[-1] if parts else self.printer_path
        else:
            # 如果已经是打印机名，直接返回
            return self.printer_path
    
    def test_connection(self):
        """测试打印机连接"""
        if not self.is_windows:
            return {
                'success': False,
                'message': '本地打印功能仅支持Windows系统'
            }
        
        try:
            import win32print
            
            printer_name = self._extract_printer_name()
            printer_handle = win32print.OpenPrinter(printer_name)
            
            if printer_handle:
                win32print.ClosePrinter(printer_handle)
                return {
                    'success': True,
                    'message': f'打印机连接正常: {printer_name}'
                }
            else:
                return {
                    'success': False,
                    'message': f'无法连接到打印机: {printer_name}'
                }
                
        except ImportError:
            return {
                'success': False,
                'message': '需要安装pywin32库才能使用本地打印功能。请运行: pip install pywin32'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'测试连接失败: {str(e)}'
            }
    
    def print_via_proxy(self, proxy_url, image_url, copies=1, api_key=None):
        """
        通过打印代理服务打印（用于远程服务器）
        
        Args:
            proxy_url: 打印代理服务地址
            image_url: 图片URL
            copies: 打印份数
            api_key: API密钥（可选）
        """
        try:
            from local_printer_client import LocalPrinterClient
            client = LocalPrinterClient(proxy_url, api_key)
            return client.print_image(image_url=image_url, copies=copies)
        except ImportError:
            return {
                'success': False,
                'message': '打印代理客户端模块未找到'
            }
