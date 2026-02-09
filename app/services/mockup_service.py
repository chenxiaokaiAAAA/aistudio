# -*- coding: utf-8 -*-
"""
样机套图服务
基于 psd-tools 实现 PSD 智能对象替换，生成样机效果图
"""

import logging
import os
import uuid
from urllib.parse import unquote

from PIL import Image

logger = logging.getLogger(__name__)

# 延迟导入 psd-tools（可选依赖）
try:
    from psd_tools import PSDImage
    from psd_tools.api.layers import SmartObjectLayer
    from psd_tools.constants import ChannelID

    PSD_TOOLS_AVAILABLE = True
except ImportError:
    PSD_TOOLS_AVAILABLE = False
    PSDImage = None
    SmartObjectLayer = None
    ChannelID = None


def replace_psd_smart_object(psd_path, smart_layer_name, new_image_path, output_path, output_format="jpg"):
    """
    替换 PSD 智能对象内容，生成套图

    :param psd_path: PSD 文件路径
    :param smart_layer_name: 智能对象图层名
    :param new_image_path: 用户原图路径
    :param output_path: 输出文件路径
    :param output_format: "psd" 保留图层，"jpg" 扁平图片
    :return: True 成功
    """
    if not PSD_TOOLS_AVAILABLE:
        raise RuntimeError("psd-tools 未安装，请执行: pip install psd-tools")

    psd = PSDImage.open(psd_path)
    target_smart_layer = None

    for layer in psd.descendants():
        if isinstance(layer, SmartObjectLayer) and layer.name == smart_layer_name:
            target_smart_layer = layer
            break

    if not target_smart_layer:
        raise ValueError(f"未找到智能对象图层：{smart_layer_name}")

    # 处理用户原图：等比例缩放 + 中心裁剪，适配智能对象尺寸（无拉伸）
    new_img = Image.open(new_image_path).convert("RGB")
    so_w, so_h = target_smart_layer.size
    scale = max(so_w / new_img.width, so_h / new_img.height)
    new_w = int(new_img.width * scale)
    new_h = int(new_img.height * scale)
    scaled = new_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    crop_left = (scaled.width - so_w) // 2
    crop_top = (scaled.height - so_h) // 2
    crop_img = scaled.crop((crop_left, crop_top, crop_left + so_w, crop_top + so_h))

    w, h = target_smart_layer.width, target_smart_layer.height
    crop_img = crop_img.resize((w, h), Image.Resampling.LANCZOS)
    rgb = crop_img.convert("RGB")

    r_data = rgb.getchannel("R").tobytes()
    g_data = rgb.getchannel("G").tobytes()
    b_data = rgb.getchannel("B").tobytes()
    alpha_data = b"\xff" * (w * h)

    depth = psd.depth
    version = psd.version
    for ci, cd in zip(target_smart_layer._record.channel_info, target_smart_layer._channels):
        if ci.id == ChannelID.TRANSPARENCY_MASK:
            cd.set_data(alpha_data, w, h, depth, version)
        elif ci.id == ChannelID.CHANNEL_0:
            cd.set_data(r_data, w, h, depth, version)
        elif ci.id == ChannelID.CHANNEL_1:
            cd.set_data(g_data, w, h, depth, version)
        elif ci.id == ChannelID.CHANNEL_2:
            cd.set_data(b_data, w, h, depth, version)

    psd._mark_updated()

    if output_format == "psd":
        psd.save(output_path)
    else:
        final_img = psd.composite()
        final_img.save(output_path, quality=95, optimize=True)
    return True


def resolve_image_path_from_url(image_url, app):
    """
    从 /public/hd/{filename} 格式的 URL 解析出本地文件路径

    :param image_url: 图片 URL，如 /public/hd/xxx.jpg 或 /public/hd/xxx_thumb.jpg
    :param app: Flask 应用实例
    :return: 本地文件绝对路径，若不存在返回 None
    """
    if not image_url or not app:
        return None

    # 提取 filename
    prefix = "/public/hd/"
    if prefix not in image_url:
        # 可能是完整 URL，尝试提取路径部分
        if "public/hd/" in image_url:
            image_url = image_url.split("public/hd/")[-1]
        else:
            return None
    else:
        image_url = image_url.split(prefix)[-1]

    filename = unquote(image_url.split("?")[0].strip())

    hd_folder = app.config.get("HD_FOLDER", "hd_images")
    final_folder = app.config.get("FINAL_FOLDER", "final_works")
    if not os.path.isabs(hd_folder):
        hd_folder = os.path.join(app.root_path, hd_folder)
    if not os.path.isabs(final_folder):
        final_folder = os.path.join(app.root_path, final_folder)

    for folder in [hd_folder, final_folder]:
        filepath = os.path.join(folder, filename)
        if os.path.exists(filepath):
            return filepath

        # 若是缩略图，尝试找原图
        if filename.endswith("_thumb.jpg"):
            base = filename.replace("_thumb.jpg", "")
            for ext in [".png", ".jpg", ".jpeg", ".webp"]:
                orig_path = os.path.join(folder, base + ext)
                if os.path.exists(orig_path):
                    return orig_path

    return None


def resolve_psd_path(psd_path, app):
    """
    解析 PSD 文件路径（支持相对路径）

    :param psd_path: 配置的 PSD 路径（相对或绝对）
    :param app: Flask 应用实例
    :return: 绝对路径
    """
    if not psd_path:
        return None
    if os.path.isabs(psd_path) and os.path.exists(psd_path):
        return psd_path
    # 相对路径：相对于项目根目录或 data/mockup_templates
    root = app.root_path if app else os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    for base in [root, os.path.join(root, "data", "mockup_templates")]:
        full = os.path.join(base, psd_path) if not os.path.isabs(psd_path) else psd_path
        if os.path.exists(full):
            return full
    return psd_path if os.path.exists(psd_path) else None


def generate_mockup(template, image_url, app, output_format="jpg"):
    """
    生成样机套图

    :param template: MockupTemplate 模型实例
    :param image_url: 选片图片 URL（如 /public/hd/xxx.jpg）
    :param app: Flask 应用实例
    :param output_format: jpg 或 psd
    :return: (success, result_dict) result_dict 含 preview_url, filepath, filename
    """
    if not PSD_TOOLS_AVAILABLE:
        return False, {"error": "psd-tools 未安装"}

    image_path = resolve_image_path_from_url(image_url, app)
    if not image_path or not os.path.exists(image_path):
        return False, {"error": "无法解析或找到原图文件"}

    psd_path = resolve_psd_path(template.psd_path, app)
    if not psd_path or not os.path.exists(psd_path):
        return False, {"error": "PSD 模板文件不存在"}

    # 输出目录：data/mockup_output 或 MOCKUP_OUTPUT_FOLDER
    output_dir = app.config.get("MOCKUP_OUTPUT_FOLDER")
    if not output_dir:
        output_dir = os.path.join(app.root_path, "data", "mockup_output")
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(app.root_path, output_dir)

    os.makedirs(output_dir, exist_ok=True)

    ext = "psd" if output_format == "psd" else "jpg"
    filename = f"mockup_{uuid.uuid4().hex[:12]}.{ext}"
    output_path = os.path.join(output_dir, filename)

    try:
        replace_psd_smart_object(
            psd_path,
            template.smart_layer_name or "photogo",
            image_path,
            output_path,
            output_format=output_format,
        )
        # 生成可访问的 URL
        preview_url = f"/public/mockup/{filename}"
        return True, {
            "preview_url": preview_url,
            "filepath": output_path,
            "filename": filename,
        }
    except Exception as e:
        logger.exception("样机生成失败: %s", e)
        return False, {"error": str(e)}


def generate_mockup_from_path(template, image_path, app, output_format="jpg"):
    """
    从本地文件路径生成样机套图（用于测试上传）

    :param template: MockupTemplate 模型实例
    :param image_path: 本地图片文件绝对路径
    :param app: Flask 应用实例
    :param output_format: jpg 或 psd
    :return: (success, result_dict)
    """
    if not PSD_TOOLS_AVAILABLE:
        return False, {"error": "psd-tools 未安装"}

    if not image_path or not os.path.exists(image_path):
        return False, {"error": "图片文件不存在"}

    psd_path = resolve_psd_path(template.psd_path, app)
    if not psd_path or not os.path.exists(psd_path):
        return False, {"error": "PSD 模板文件不存在"}

    output_dir = app.config.get("MOCKUP_OUTPUT_FOLDER")
    if not output_dir:
        output_dir = os.path.join(app.root_path, "data", "mockup_output")
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(app.root_path, output_dir)

    os.makedirs(output_dir, exist_ok=True)

    ext = "psd" if output_format == "psd" else "jpg"
    filename = f"mockup_{uuid.uuid4().hex[:12]}.{ext}"
    output_path = os.path.join(output_dir, filename)

    try:
        replace_psd_smart_object(
            psd_path,
            template.smart_layer_name or "photogo",
            image_path,
            output_path,
            output_format=output_format,
        )
        return True, {
            "preview_url": f"/public/mockup/{filename}",
            "filepath": output_path,
            "filename": filename,
        }
    except Exception as e:
        logger.exception("样机生成失败: %s", e)
        return False, {"error": str(e)}


def scan_psd_templates(directory):
    """
    扫描目录下所有 PSD 文件，检测智能对象图层

    :param directory: 目录路径
    :return: [{"name", "path", "smart_layer_name", "all_smart_layers"}, ...]
    """
    if not PSD_TOOLS_AVAILABLE or not os.path.isdir(directory):
        return []

    templates = []
    for f in os.listdir(directory):
        if f.lower().endswith(".psd"):
            psd_path = os.path.join(directory, f)
            try:
                psd = PSDImage.open(psd_path)
                smart_layers = [
                    layer for layer in psd.descendants() if isinstance(layer, SmartObjectLayer)
                ]
                if smart_layers:
                    target = next(
                        (l for l in smart_layers if l.name == "photogo"), smart_layers[0]
                    )
                    templates.append({
                        "name": f,
                        "path": psd_path,
                        "smart_layer_name": target.name,
                        "all_smart_layers": [l.name for l in smart_layers],
                    })
            except Exception:
                pass
    return templates
