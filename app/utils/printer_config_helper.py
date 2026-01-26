# -*- coding: utf-8 -*-
"""
打印机配置辅助函数
用于根据订单关联的门店/自拍机获取对应的打印机配置
"""
import logging

logger = logging.getLogger(__name__)

def get_printer_config_for_order(order, models):
    """
    根据订单获取对应的打印机配置
    
    Args:
        order: Order对象，包含selfie_machine_id和store_name
        models: 数据库模型字典
    
    Returns:
        dict: {
            'local_printer_path': str,  # 本地打印机路径（本地部署）
            'local_printer_proxy_url': str,  # 打印代理服务地址（远程部署）
            'local_printer_proxy_api_key': str,  # 打印代理服务API密钥
            'machine_id': str,  # 使用的自拍机ID
            'store_name': str  # 门店名称
        }
    """
    try:
        AIConfig = models.get('AIConfig')
        if not AIConfig:
            logger.warning("AIConfig模型不存在，使用默认配置")
            return _get_default_printer_config(models)
        
        # 优先使用订单的selfie_machine_id查找配置
        machine_id = None
        store_name = None
        
        if order:
            machine_id = getattr(order, 'selfie_machine_id', None)
            store_name = getattr(order, 'store_name', None)
            
            # 如果没有selfie_machine_id，尝试通过门店名称查找
            if not machine_id and store_name:
                # 尝试通过门店名称查找自拍机
                try:
                    SelfieMachine = models.get('SelfieMachine')
                    if SelfieMachine:
                        # 查找该门店的第一个活跃自拍机
                        machine = SelfieMachine.query.filter_by(
                            status='active'
                        ).join(
                            models.get('FranchiseeAccount')
                        ).filter(
                            models.get('FranchiseeAccount').store_name == store_name
                        ).first()
                        
                        if machine:
                            machine_id = machine.machine_serial_number
                            logger.info(f"通过门店名称 {store_name} 找到自拍机: {machine_id}")
                except Exception as e:
                    logger.warning(f"通过门店名称查找自拍机失败: {e}")
        
        # 如果有自拍机ID，尝试获取该自拍机的打印机配置
        if machine_id:
            config_key_path = f'local_printer_path_{machine_id}'
            config_key_proxy_url = f'local_printer_proxy_url_{machine_id}'
            config_key_api_key = f'local_printer_proxy_api_key_{machine_id}'
            
            printer_path_config = AIConfig.query.filter_by(config_key=config_key_path).first()
            proxy_url_config = AIConfig.query.filter_by(config_key=config_key_proxy_url).first()
            api_key_config = AIConfig.query.filter_by(config_key=config_key_api_key).first()
            
            if printer_path_config and printer_path_config.config_value:
                logger.info(f"找到自拍机 {machine_id} 的打印机配置")
                return {
                    'local_printer_path': printer_path_config.config_value,
                    'local_printer_proxy_url': proxy_url_config.config_value if proxy_url_config else '',
                    'local_printer_proxy_api_key': api_key_config.config_value if api_key_config else '',
                    'machine_id': machine_id,
                    'store_name': store_name
                }
            elif proxy_url_config and proxy_url_config.config_value:
                logger.info(f"找到自拍机 {machine_id} 的打印代理配置")
                return {
                    'local_printer_path': '',
                    'local_printer_proxy_url': proxy_url_config.config_value,
                    'local_printer_proxy_api_key': api_key_config.config_value if api_key_config else '',
                    'machine_id': machine_id,
                    'store_name': store_name
                }
            else:
                logger.info(f"自拍机 {machine_id} 没有配置打印机，使用默认配置")
        
        # 如果没有找到门店配置，使用默认配置
        return _get_default_printer_config(models)
        
    except Exception as e:
        logger.error(f"获取打印机配置失败: {e}")
        import traceback
        traceback.print_exc()
        return _get_default_printer_config(models)

def _get_default_printer_config(models):
    """获取默认打印机配置"""
    try:
        AIConfig = models.get('AIConfig')
        if not AIConfig:
            return {
                'local_printer_path': '',
                'local_printer_proxy_url': '',
                'local_printer_proxy_api_key': '',
                'machine_id': None,
                'store_name': None
            }
        
        local_printer_config = AIConfig.query.filter_by(config_key='local_printer_path').first()
        proxy_url_config = AIConfig.query.filter_by(config_key='local_printer_proxy_url').first()
        api_key_config = AIConfig.query.filter_by(config_key='local_printer_proxy_api_key').first()
        
        return {
            'local_printer_path': local_printer_config.config_value if local_printer_config else '',
            'local_printer_proxy_url': proxy_url_config.config_value if proxy_url_config else '',
            'local_printer_proxy_api_key': api_key_config.config_value if api_key_config else '',
            'machine_id': None,
            'store_name': None
        }
    except Exception as e:
        logger.error(f"获取默认打印机配置失败: {e}")
        return {
            'local_printer_path': '',
            'local_printer_proxy_url': '',
            'local_printer_proxy_api_key': '',
            'machine_id': None,
            'store_name': None
        }

def save_printer_config_for_machine(machine_id, printer_path=None, proxy_url=None, api_key=None, models=None):
    """
    保存指定自拍机的打印机配置
    
    Args:
        machine_id: 自拍机序列号
        printer_path: 本地打印机路径（可选）
        proxy_url: 打印代理服务地址（可选）
        api_key: 打印代理服务API密钥（可选）
        models: 数据库模型字典
    
    Returns:
        bool: 是否保存成功
    """
    try:
        if not models:
            return False
        
        db = models.get('db')
        AIConfig = models.get('AIConfig')
        
        if not db or not AIConfig:
            return False
        
        configs_to_save = []
        
        if printer_path is not None:
            configs_to_save.append((
                f'local_printer_path_{machine_id}',
                printer_path,
                f'自拍机 {machine_id} 的本地打印机路径'
            ))
        
        if proxy_url is not None:
            configs_to_save.append((
                f'local_printer_proxy_url_{machine_id}',
                proxy_url,
                f'自拍机 {machine_id} 的打印代理服务地址'
            ))
        
        if api_key is not None:
            configs_to_save.append((
                f'local_printer_proxy_api_key_{machine_id}',
                api_key,
                f'自拍机 {machine_id} 的打印代理服务API密钥'
            ))
        
        for config_key, config_value, description in configs_to_save:
            config = AIConfig.query.filter_by(config_key=config_key).first()
            if config:
                config.config_value = config_value
                config.description = description
            else:
                config = AIConfig(config_key=config_key, config_value=config_value, description=description)
                db.session.add(config)
        
        db.session.commit()
        logger.info(f"已保存自拍机 {machine_id} 的打印机配置")
        return True
        
    except Exception as e:
        logger.error(f"保存自拍机 {machine_id} 的打印机配置失败: {e}")
        if 'db' in locals():
            db.session.rollback()
        return False

def get_all_machine_printer_configs(models):
    """
    获取所有自拍机的打印机配置
    
    Returns:
        list: [
            {
                'machine_id': str,
                'machine_name': str,
                'store_name': str,
                'local_printer_path': str,
                'local_printer_proxy_url': str,
                'local_printer_proxy_api_key': str
            },
            ...
        ]
    """
    try:
        AIConfig = models.get('AIConfig')
        SelfieMachine = models.get('SelfieMachine')
        FranchiseeAccount = models.get('FranchiseeAccount')
        
        if not AIConfig or not SelfieMachine:
            logger.warning("AIConfig或SelfieMachine模型未找到")
            return []
        
        # 获取所有自拍机（不限制状态，因为可能有些自拍机暂时停用但需要配置打印机）
        machines = SelfieMachine.query.all()
        logger.info(f"找到 {len(machines)} 台自拍机")
        
        result = []
        for machine in machines:
            machine_id = machine.machine_serial_number
            machine_name = machine.machine_name
            
            # 获取门店名称
            store_name = ''
            if FranchiseeAccount and machine.franchisee_id:
                try:
                    # 尝试通过关系属性访问
                    if hasattr(machine, 'franchisee') and machine.franchisee:
                        store_name = machine.franchisee.store_name or ''
                    else:
                        # 如果关系未定义，直接查询
                        franchisee = FranchiseeAccount.query.get(machine.franchisee_id)
                        if franchisee:
                            store_name = franchisee.store_name or ''
                except Exception as e:
                    logger.warning(f"获取自拍机 {machine_id} 的门店名称失败: {e}")
            
            # 获取打印机配置
            config_key_path = f'local_printer_path_{machine_id}'
            config_key_proxy_url = f'local_printer_proxy_url_{machine_id}'
            config_key_api_key = f'local_printer_proxy_api_key_{machine_id}'
            
            printer_path_config = AIConfig.query.filter_by(config_key=config_key_path).first()
            proxy_url_config = AIConfig.query.filter_by(config_key=config_key_proxy_url).first()
            api_key_config = AIConfig.query.filter_by(config_key=config_key_api_key).first()
            
            result.append({
                'machine_id': machine_id,
                'machine_name': machine_name,
                'store_name': store_name,
                'local_printer_path': printer_path_config.config_value if printer_path_config else '',
                'local_printer_proxy_url': proxy_url_config.config_value if proxy_url_config else '',
                'local_printer_proxy_api_key': api_key_config.config_value if api_key_config else ''
            })
        
        return result
        
    except Exception as e:
        logger.error(f"获取所有自拍机打印机配置失败: {e}")
        import traceback
        traceback.print_exc()
        return []
