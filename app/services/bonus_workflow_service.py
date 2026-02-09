# -*- coding: utf-8 -*-
"""
产品额外赠送工作流服务
用于在订单创建后自动创建赠送的工作流任务
"""

import logging

logger = logging.getLogger(__name__)
import os
import sys
from datetime import datetime


def create_bonus_workflows_for_order(
    order_id,
    db=None,
    Order=None,
    Product=None,
    ProductBonusWorkflow=None,
    APITemplate=None,
    StyleImage=None,
    AITask=None,
    OrderImage=None,
):
    """
    为订单创建产品的额外赠送工作流任务

    Args:
        order_id: 订单ID
        db: 数据库实例
        Order: Order模型类
        Product: Product模型类
        ProductBonusWorkflow: ProductBonusWorkflow模型类
        APITemplate: APITemplate模型类
        StyleImage: StyleImage模型类
        AITask: AITask模型类
        OrderImage: OrderImage模型类

    Returns:
        tuple: (success: bool, created_count: int, error_message: str)
    """
    try:
        # 获取数据库模型
        if not all([db, Order, Product, ProductBonusWorkflow]):
            # 尝试从test_server获取
            if "test_server" in sys.modules:
                test_server_module = sys.modules["test_server"]
                db = db or test_server_module.db
                Order = Order or test_server_module.Order
                Product = Product or test_server_module.Product
                ProductBonusWorkflow = ProductBonusWorkflow or (
                    test_server_module.ProductBonusWorkflow
                    if hasattr(test_server_module, "ProductBonusWorkflow")
                    else None
                )
                APITemplate = APITemplate or (
                    test_server_module.APITemplate
                    if hasattr(test_server_module, "APITemplate")
                    else None
                )
                StyleImage = StyleImage or test_server_module.StyleImage
                AITask = AITask or test_server_module.AITask
                OrderImage = OrderImage or test_server_module.OrderImage

        if not all([db, Order, Product]):
            return False, 0, "数据库模型未初始化"

        if not ProductBonusWorkflow:
            # 如果ProductBonusWorkflow模型不存在，说明功能未启用
            return True, 0, "产品赠送工作流功能未启用"

        # 获取订单
        order = Order.query.get(order_id)
        if not order:
            return False, 0, "订单不存在"

        # 从订单中获取产品信息
        # 尝试从product_name中提取产品代码，或从product_type获取
        product_code = None
        if hasattr(order, "product_type") and order.product_type:
            product_code = order.product_type
        elif order.product_name:
            # 从产品名称中提取代码（假设格式为"产品名称 - 尺寸"）
            product_name_parts = order.product_name.split(" - ")
            if product_name_parts:
                # 尝试通过产品名称查找
                product = Product.query.filter(
                    Product.name.like(f"%{product_name_parts[0]}%")
                ).first()
                if product:
                    product_code = product.code

        if not product_code:
            logger.warning("订单 {order.order_number} 无法确定产品代码，跳过赠送工作流")
            return True, 0, "无法确定产品代码"

        # 查找产品
        product = Product.query.filter_by(code=product_code, is_active=True).first()
        if not product:
            logger.warning("订单 {order.order_number} 的产品 {product_code} 不存在，跳过赠送工作流")
            return True, 0, "产品不存在"

        # 查找产品的赠送工作流配置
        bonus_workflows = (
            ProductBonusWorkflow.query.filter_by(product_id=product.id, is_active=True)
            .order_by(ProductBonusWorkflow.sort_order)
            .all()
        )

        if not bonus_workflows:
            logger.info(f"ℹ️  产品 {product.name} 没有配置赠送工作流")
            return True, 0, "产品没有配置赠送工作流"

        logger.info(f"🎁 为订单 {order.order_number} 创建 {len(bonus_workflows)} 个赠送工作流任务")

        # 获取订单的输入图片
        app = None
        if "test_server" in sys.modules:
            test_server_module = sys.modules["test_server"]
            app = test_server_module.app

        if not app:
            return False, 0, "应用实例未初始化"

        # 获取订单图片（优先使用主图）
        order_images = OrderImage.query.filter_by(order_id=order.id).all()
        if not order_images:
            return False, 0, "订单没有上传的图片"

        # 优先使用主图，如果没有主图则使用第一张
        main_image = next((img for img in order_images if img.is_main), order_images[0])
        input_image_path = os.path.join(app.config["UPLOAD_FOLDER"], main_image.path)

        if not os.path.exists(input_image_path):
            return False, 0, "订单图片文件不存在"

        created_count = 0

        # 遍历每个赠送工作流配置
        for bonus_workflow in bonus_workflows:
            try:
                if bonus_workflow.workflow_type == "api_template":
                    # API模板类型
                    if not APITemplate or not bonus_workflow.api_template_id:
                        logger.warning("赠送工作流 {bonus_workflow.id} 配置的API模板不存在，跳过")
                        continue

                    api_template = APITemplate.query.get(bonus_workflow.api_template_id)
                    if not api_template or not api_template.is_active:
                        logger.warning("赠送工作流 {bonus_workflow.id} 的API模板未启用，跳过")
                        continue

                    # 创建API任务
                    from app.services.ai_provider_service import create_api_task

                    # 获取默认提示词
                    prompt = api_template.default_prompt or "AI写真"

                    # 如果有批量提示词，使用第一个
                    if api_template.prompts_json:
                        try:
                            import json

                            prompts = json.loads(api_template.prompts_json)
                            if prompts and len(prompts) > 0:
                                prompt = prompts[0]
                        except Exception:
                            pass

                    # 获取上传图片配置
                    upload_config = None
                    if api_template.upload_config:
                        try:
                            import json

                            upload_config = json.loads(api_template.upload_config)
                        except Exception:
                            pass

                    # 构建上传图片列表
                    uploaded_images = []
                    if upload_config and "uploads" in upload_config:
                        # 根据配置上传图片
                        for upload_item in upload_config["uploads"]:
                            if (
                                upload_item.get("key") == "reference"
                                or upload_item.get("name") == "参考图"
                            ):
                                # 上传参考图
                                uploaded_images.append(
                                    {
                                        "url": f"file://{input_image_path}",
                                        "key": upload_item.get("key", "reference"),
                                    }
                                )

                    # 如果没有配置上传，默认上传参考图
                    if not uploaded_images:
                        uploaded_images = [
                            {"url": f"file://{input_image_path}", "key": "reference"}
                        ]

                    # 创建API任务
                    success, api_task, error_message = create_api_task(
                        style_image_id=api_template.style_image_id
                        or (api_template.style_category_id and None),
                        prompt=prompt,
                        image_size=api_template.default_size or "1K",
                        aspect_ratio=api_template.default_aspect_ratio or "auto",
                        uploaded_images=uploaded_images,
                        upload_config=api_template.upload_config,
                        api_config_id=api_template.api_config_id,
                        db=db,
                        AITask=AITask,
                        APITemplate=APITemplate,
                        StyleImage=StyleImage,
                    )

                    if success and api_task:
                        # 关联到订单（如果AITask支持order_id）
                        if hasattr(api_task, "order_id"):
                            api_task.order_id = order.id
                            api_task.order_number = order.order_number
                            db.session.commit()

                        logger.info(
                            f"✅ 创建赠送API任务成功: {bonus_workflow.workflow_name or '未命名'}"
                        )
                        created_count += 1
                    else:
                        logger.error("创建赠送API任务失败: {error_message}")

                elif bonus_workflow.workflow_type == "style_image":
                    # 风格图片类型（使用ComfyUI工作流）
                    if not StyleImage or not bonus_workflow.style_image_id:
                        logger.warning("赠送工作流 {bonus_workflow.id} 配置的风格图片不存在，跳过")
                        continue

                    style_image = StyleImage.query.get(bonus_workflow.style_image_id)
                    if not style_image or not style_image.is_active:
                        logger.warning("赠送工作流 {bonus_workflow.id} 的风格图片未启用，跳过")
                        continue

                    # 创建ComfyUI工作流任务
                    from app.services.workflow_service import create_ai_task

                    success, ai_task, error_message = create_ai_task(
                        order_id=order.id,
                        style_category_id=style_image.category_id,
                        style_image_id=style_image.id,
                        db=db,
                        Order=Order,
                        AITask=AITask,
                        StyleCategory=None,  # 从style_image中获取
                        StyleImage=StyleImage,
                        OrderImage=OrderImage,
                    )

                    if success and ai_task:
                        logger.info(
                            f"✅ 创建赠送ComfyUI任务成功: {bonus_workflow.workflow_name or style_image.name}"
                        )
                        created_count += 1
                    else:
                        logger.error("创建赠送ComfyUI任务失败: {error_message}")

            except Exception as e:
                logger.error("创建赠送工作流任务异常: {str(e)}")
                import traceback

                traceback.print_exc()
                continue

        logger.info(
            f"🎁 订单 {order.order_number} 共创建 {created_count}/{len(bonus_workflows)} 个赠送工作流任务"
        )
        return True, created_count, None

    except Exception as e:
        logger.error("创建赠送工作流任务失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False, 0, f"创建失败: {str(e)}"
