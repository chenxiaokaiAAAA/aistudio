# -*- coding: utf-8 -*-
"""
类型提示定义模块
为项目提供统一的类型提示和类型别名
"""

from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

from flask import Request, Response
from werkzeug.datastructures import FileStorage

# 类型别名
T = TypeVar("T")
JsonDict = Dict[str, Any]
JsonList = List[JsonDict]
OrderDict = Dict[str, Any]
UserDict = Dict[str, Any]
ImagePath = str
FilePath = str

# Flask相关类型
FlaskResponse = Union[Response, Tuple[str, int], Tuple[Response, int]]
FlaskRequest = Request
FileUpload = FileStorage

# 数据库相关类型
ModelId = Union[int, str]
OrderId = ModelId
UserId = ModelId
ProductId = ModelId

# 图片处理相关类型
ImageSize = Tuple[int, int]  # (width, height)
ImageFormat = str  # 'JPEG', 'PNG', 'WEBP', etc.
CompressResult = Tuple[bool, int, int]  # (success, original_size, new_size)

# API响应类型
ApiResponse = Dict[str, Any]
ApiSuccessResponse = Dict[str, Union[bool, str, Any]]
ApiErrorResponse = Dict[str, Union[str, int]]

# 配置类型
ConfigDict = Dict[str, Any]
PathConfig = Dict[str, str]

# 函数类型
RouteHandler = Callable[..., FlaskResponse]
Middleware = Callable[[Request], Optional[Response]]
Validator = Callable[[Any], bool]

# 导出常用类型
__all__ = [
    "T",
    "JsonDict",
    "JsonList",
    "OrderDict",
    "UserDict",
    "ImagePath",
    "FilePath",
    "FlaskResponse",
    "FlaskRequest",
    "FileUpload",
    "ModelId",
    "OrderId",
    "UserId",
    "ProductId",
    "ImageSize",
    "ImageFormat",
    "CompressResult",
    "ApiResponse",
    "ApiSuccessResponse",
    "ApiErrorResponse",
    "ConfigDict",
    "PathConfig",
    "RouteHandler",
    "Middleware",
    "Validator",
]
