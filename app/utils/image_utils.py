# -*- coding: utf-8 -*-
"""
图片处理工具函数
从 test_server.py 迁移图片处理相关函数
"""

import logging

logger = logging.getLogger(__name__)
import os

from PIL import Image


def add_watermark_to_image(
    image_path, watermark_path, output_path=None, opacity=1.0, position="tiled"
):
    """
    为图片添加水印

    Args:
        image_path: 原图片路径
        watermark_path: 水印图片路径
        output_path: 输出路径，如果为None则覆盖原图
        opacity: 水印透明度 (0-1)
        position: 水印位置 ('tiled', 'center', 'bottom_right', 'bottom_left', 'top_right', 'top_left')

    Returns:
        bool: 是否成功添加水印
    """
    try:
        # 验证输入文件
        if not os.path.exists(image_path):
            logger.error("原图文件不存在: {image_path}")
            return False

        if not os.path.exists(watermark_path):
            logger.error("水印文件不存在: {watermark_path}")
            return False

        # 检查文件大小
        if os.path.getsize(image_path) == 0:
            logger.error("原图文件为空: {image_path}")
            return False

        if os.path.getsize(watermark_path) == 0:
            logger.error("水印文件为空: {watermark_path}")
            return False

        # 打开原图和水印图
        with Image.open(image_path) as base_image:
            with Image.open(watermark_path) as watermark:
                # 确保水印图片有alpha通道
                if watermark.mode != "RGBA":
                    watermark = watermark.convert("RGBA")

                # 调整水印透明度
                if opacity < 1.0:
                    # 创建透明水印
                    transparent_watermark = Image.new("RGBA", watermark.size, (0, 0, 0, 0))
                    for x in range(watermark.width):
                        for y in range(watermark.height):
                            r, g, b, a = watermark.getpixel((x, y))
                            transparent_watermark.putpixel((x, y), (r, g, b, int(a * opacity)))
                    watermark = transparent_watermark

                base_width, base_height = base_image.size
                wm_width, wm_height = watermark.size

                # 确保原图有alpha通道
                if base_image.mode != "RGBA":
                    base_image = base_image.convert("RGBA")

                # 创建副本
                watermarked_image = base_image.copy()

                if position == "tiled":
                    # 单层水印自适应放大覆盖整个画面
                    # 计算缩放比例，使水印覆盖整个画面
                    scale_x = base_width / wm_width
                    scale_y = base_height / wm_height

                    # 使用较大的缩放比例，确保完全覆盖
                    scale = max(scale_x, scale_y) * 1.1  # 稍微放大一点确保完全覆盖

                    # 缩放水印
                    new_size = (int(wm_width * scale), int(wm_height * scale))
                    scaled_watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)

                    logger.info(f"水印缩放: {wm_width}x{wm_height} -> {new_size[0]}x{new_size[1]}")

                    # 计算居中位置
                    x = (base_width - new_size[0]) // 2
                    y = (base_height - new_size[1]) // 2

                    # 如果水印超出边界，裁剪到图片大小
                    if new_size[0] > base_width or new_size[1] > base_height:
                        # 计算裁剪区域
                        left = max(0, -x)
                        top = max(0, -y)
                        right = min(new_size[0], base_width - x)
                        bottom = min(new_size[1], base_height - y)

                        # 裁剪水印
                        scaled_watermark = scaled_watermark.crop((left, top, right, bottom))

                        # 调整粘贴位置
                        x = max(0, x)
                        y = max(0, y)

                    # 粘贴水印
                    watermarked_image.paste(scaled_watermark, (x, y), scaled_watermark)

                elif position == "center":
                    # 单个水印居中
                    # 计算水印应该占图片的比例
                    target_ratio = 0.3
                    target_width = int(base_width * target_ratio)
                    target_height = int(base_height * target_ratio)

                    # 按比例缩放水印，保持宽高比
                    scale = min(target_width / wm_width, target_height / wm_height)
                    new_size = (int(wm_width * scale), int(wm_height * scale))
                    scaled_watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)

                    # 计算居中位置
                    x = (base_width - new_size[0]) // 2
                    y = (base_height - new_size[1]) // 2

                    # 粘贴水印
                    watermarked_image.paste(scaled_watermark, (x, y), scaled_watermark)

                else:
                    # 其他位置（保持原有逻辑）
                    # 如果水印太大，按比例缩小
                    if wm_width > base_width * 0.3 or wm_height > base_height * 0.3:
                        scale = min(base_width * 0.3 / wm_width, base_height * 0.3 / wm_height)
                        new_size = (int(wm_width * scale), int(wm_height * scale))
                        watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)
                        wm_width, wm_height = new_size

                    # 根据位置计算坐标
                    if position == "bottom_right":
                        x = base_width - wm_width - 20
                        y = base_height - wm_height - 20
                    elif position == "bottom_left":
                        x = 20
                        y = base_height - wm_height - 20
                    elif position == "top_right":
                        x = base_width - wm_width - 20
                        y = 20
                    elif position == "top_left":
                        x = 20
                        y = 20
                    else:
                        x = base_width - wm_width - 20
                        y = base_height - wm_height - 20

                    # 确保坐标不为负数
                    x = max(0, x)
                    y = max(0, y)

                    # 粘贴水印
                    watermarked_image.paste(watermark, (x, y), watermark)

                # 保存图片
                if output_path is None:
                    output_path = image_path

                # 如果原图是JPEG，需要转换回RGB
                if output_path.lower().endswith((".jpg", ".jpeg")):
                    watermarked_image = watermarked_image.convert("RGB")

                # 保存到临时文件，然后重命名，确保原子性
                temp_path = output_path + ".tmp"
                # 根据原图格式保存临时文件
                if output_path.lower().endswith((".jpg", ".jpeg")):
                    watermarked_image.save(temp_path, format="JPEG", quality=95)
                elif output_path.lower().endswith(".png"):
                    watermarked_image.save(temp_path, format="PNG")
                else:
                    watermarked_image.save(temp_path, quality=95)

                # 验证临时文件
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    # 验证图片格式
                    try:
                        with Image.open(temp_path) as test_img:
                            test_img.verify()
                        # 验证通过，重命名
                        if os.path.exists(output_path):
                            os.remove(output_path)
                        os.rename(temp_path, output_path)
                        logger.info(f"✅ 水印添加成功: {output_path}")
                        return True
                    except Exception as verify_error:
                        logger.error("水印图片验证失败: {str(verify_error)}")
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        return False
                else:
                    logger.error("临时文件保存失败: {temp_path}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return False

    except Exception as e:
        logger.error("添加水印失败: {str(e)}")
        # 清理临时文件
        temp_path = (output_path or image_path) + ".tmp"
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False
