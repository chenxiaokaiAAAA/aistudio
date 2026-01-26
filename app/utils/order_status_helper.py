# -*- coding: utf-8 -*-
"""
订单状态辅助函数
提供订单状态的映射、验证和显示功能
"""

# 订单状态定义
ORDER_STATUSES = {
    'paid': '已支付',
    'shooting': '正在拍摄',
    'retouching': '美颜处理中',
    'ai_processing': 'AI任务处理中',
    'pending_selection': '待选片',
    'selection_completed': '已选片',
    'printing': '打印中',
    'pending_shipment': '待发货',
    'shipped': '已发货',
    # 向后兼容的旧状态
    'unpaid': '未支付',
    'pending': '待处理',
    'processing': '处理中',
    'manufacturing': '制作中',
    'completed': '已完成',
    'hd_ready': '高清图就绪',
    'cancelled': '已取消',
    'refunded': '已退款',
}

# 状态流转顺序（用于验证状态是否可以更新）
STATUS_FLOW = [
    'unpaid',           # 0. 未支付
    'paid',             # 1. 已支付
    'shooting',         # 2. 正在拍摄
    'retouching',       # 3. 美颜处理中
    'ai_processing',    # 4. AI任务处理中
    'pending_selection', # 5. 待选片
    'selection_completed', # 6. 已选片
    'printing',         # 7. 打印中
    'pending_shipment', # 8. 待发货
    'shipped',          # 9. 已发货
]

# 旧状态到新状态的映射
OLD_STATUS_MAPPING = {
    'pending': 'paid',
    'processing': 'ai_processing',
    'manufacturing': 'printing',
    'completed': 'selection_completed',
    'hd_ready': 'pending_selection',
    'shipped': 'shipped',  # 保持不变
}

def get_status_display_name(status):
    """获取状态的显示名称"""
    return ORDER_STATUSES.get(status, status)

def can_update_status(current_status, new_status):
    """
    检查是否可以更新状态
    
    Args:
        current_status: 当前状态
        new_status: 新状态
    
    Returns:
        bool: 是否可以更新
    """
    # 如果状态相同，允许更新（用于刷新）
    if current_status == new_status:
        return True
    
    # 获取状态在流程中的位置
    try:
        current_index = STATUS_FLOW.index(current_status) if current_status in STATUS_FLOW else -1
        new_index = STATUS_FLOW.index(new_status) if new_status in STATUS_FLOW else -1
    except ValueError:
        # 如果状态不在流程中，允许更新（可能是特殊状态如cancelled）
        return True
    
    # 如果当前状态或新状态不在流程中，允许更新
    if current_index == -1 or new_index == -1:
        return True
    
    # 只能向前流转（新状态的位置应该大于等于当前状态的位置）
    return new_index >= current_index

def normalize_status(status):
    """
    规范化状态（将旧状态映射到新状态）
    
    Args:
        status: 状态值
    
    Returns:
        str: 规范化后的状态
    """
    return OLD_STATUS_MAPPING.get(status, status)

def get_next_status(current_status):
    """
    获取下一个状态（如果存在）
    
    Args:
        current_status: 当前状态
    
    Returns:
        str or None: 下一个状态，如果不存在则返回None
    """
    try:
        current_index = STATUS_FLOW.index(current_status) if current_status in STATUS_FLOW else -1
        if current_index >= 0 and current_index < len(STATUS_FLOW) - 1:
            return STATUS_FLOW[current_index + 1]
    except ValueError:
        pass
    return None

def get_all_statuses():
    """获取所有状态列表"""
    return list(ORDER_STATUSES.keys())

def get_status_options():
    """获取状态选项（用于下拉框）"""
    return [(status, get_status_display_name(status)) for status in STATUS_FLOW if status in ORDER_STATUSES]
