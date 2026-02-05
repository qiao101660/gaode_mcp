# -*- coding: utf-8 -*-
"""
高德地图 MCP 服务器 - 统一配置模块

提供配置加载、API URL 管理、验证工具和日志配置
"""
import os
import sys
import logging
import colorlog
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# =========================================
# API 配置
# =========================================

# API Key - 优先从环境变量读取，必要时报错
def get_api_key() -> str:
    """
    获取高德地图 API Key
    
    Returns:
        API Key 字符串
        
    Raises:
        ValueError: 当 API Key 未配置时
    """
    api_key = os.getenv("AMAP_API_KEY", "")
    if not api_key:
        raise ValueError(
            "❌ AMAP_API_KEY 未配置！\n"
            "请在 .env 文件中设置 AMAP_API_KEY=\n"
            "或设置环境变量：export AMAP_API_KEY=your_key\n\n"
            "获取地址：https://lbs.amap.com/dev/"
        )
    return api_key


# API URLs (支持环境变量覆盖)
AMAP_GEO_URL = os.getenv("AMAP_GEO_URL", "https://restapi.amap.com/v3/geocode/geo")
AMAP_REGEO_URL = os.getenv("AMAP_REGEO_URL", "https://restapi.amap.com/v3/geocode/regeo")
AMAP_DRIVING_URL = os.getenv("AMAP_DRIVING_URL", "https://restapi.amap.com/v5/direction/driving")
AMAP_WALKING_URL = os.getenv("AMAP_WALKING_URL", "https://restapi.amap.com/v5/direction/walking")
AMAP_BICYCLING_URL = os.getenv("AMAP_BICYCLING_URL", "https://restapi.amap.com/v5/direction/bicycling")
AMAP_EBIKE_URL = os.getenv("AMAP_EBIKE_URL", "https://restapi.amap.com/v5/direction/electrobike")
AMAP_BUS_URL = os.getenv("AMAP_BUS_URL", "https://restapi.amap.com/v5/direction/transit/integrated")
AMAP_REGION_QUERY_URL = os.getenv("AMAP_REGION_QUERY_URL", "https://restapi.amap.com/v3/config/district")
AMAP_IP_URL = os.getenv("AMAP_IP_URL", "https://restapi.amap.com/v3/ip")
AMAP_SEARCH_POI_URL = os.getenv("AMAP_SEARCH_POI_URL", "https://restapi.amap.com/v5/place/text")
AMAP_SEARCH_POI_AROUND_URL = os.getenv("AMAP_SEARCH_POI_AROUND_URL", "https://restapi.amap.com/v5/place/around")
AMAP_SEARCH_POI_POLYGON_URL = os.getenv("AMAP_SEARCH_POI_POLYGON_URL", "https://restapi.amap.com/v5/place/polygon")
AMAP_SEARCH_POI_DETAIL_URL = os.getenv("AMAP_SEARCH_POI_DETAIL_URL", "https://restapi.amap.com/v5/place/detail")
AMAP_AOI_POLYLINE_URL = os.getenv("AMAP_AOI_POLYLINE_URL", "https://restapi.amap.com/v5/aoi/polyline")
AMAP_SUBWAY_TRANSIT = os.getenv("AMAP_SUBWAY_TRANSIT", "https://restapi.amap.com/v5/direction/transit/integrated")


# =========================================
# 服务器配置
# =========================================

SERVER_NAME = "amap-mcp"
SERVER_VERSION = "0.1.0"
USER_AGENT = f"{SERVER_NAME}/{SERVER_VERSION}"
DEFAULT_TIMEOUT = 10.0
DEFAULT_HEADERS = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}


# =========================================
# 验证工具函数
# =========================================

def validate_location_format(location: str) -> bool:
    """
    验证经纬度格式是否有效
    
    Args:
        location: 经纬度字符串，格式为 "lon,lat"
        
    Returns:
        bool: 格式是否有效
    """
    try:
        lon, lat = location.split(",")
        lon_f, lat_f = float(lon), float(lat)
        return -180 <= lon_f <= 180 and -90 <= lat_f <= 90
    except (ValueError, AttributeError):
        return False


def validate_ip_format(ip: str) -> bool:
    """
    验证 IP 地址格式是否有效
    
    Args:
        ip: IP 地址字符串
        
    Returns:
        bool: 格式是否有效
    """
    import re
    ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    return bool(re.match(ip_pattern, ip)) if ip else False


def validate_polygon_format(polygon: str) -> tuple[bool, str]:
    """
    验证多边形坐标格式是否有效
    
    Args:
        polygon: 多边形坐标串，格式为 "lon1,lat1;lon2,lat2;..."
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    try:
        points = polygon.split(";")
        if len(points) < 3:
            return False, "多边形至少需要 3 个坐标点"
        for point in points:
            lon, lat = point.split(",")
            lon_f, lat_f = float(lon), float(lat)
            if not (-180 <= lon_f <= 180 and -90 <= lat_f <= 90):
                return False, f"无效的坐标格式: {point}"
        return True, ""
    except Exception as e:
        return False, f"无效的多边形格式: {str(e)}"


# =========================================
# 日志配置
# =========================================

LOG_FORMAT = "%(asctime)s %(log_color)s%(levelname)s:%(name)s: %(message)s"
LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red",
}


def setup_logger(
    name: str = "amap_mcp",
    level: int = logging.INFO,
    log_file: Optional[str] = "amap_mcp.log",
) -> logging.Logger:
    """
    设置日志配置
    
    Args:
        name: logger 名称
        level: 日志级别
        log_file: 日志文件路径，None 表示不输出到文件
        
    Returns:
        配置好的 logger 实例
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    logger.propagate = False
    logger.setLevel(level)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.stream.reconfigure(encoding="utf-8")
    console_handler.setLevel(level)
    console_handler.setFormatter(
        colorlog.ColoredFormatter(LOG_FORMAT, log_colors=LOG_COLORS)
    )
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
            )
            file_handler.setLevel(level)
            logger.addHandler(file_handler)
        except IOError as e:
            logger.warning(f"无法创建日志文件 {log_file}: {e}")
    
    return logger


# 初始化默认 logger
logger = setup_logger()


def log_request(logger_instance: logging.Logger, tool_name: str, params: dict) -> None:
    """
    记录 API 请求日志
    
    Args:
        logger_instance: logger 实例
        tool_name: 工具名称
        params: 请求参数（会自动脱敏敏感信息）
    """
    # 脱敏 API Key
    safe_params = params.copy()
    if "key" in safe_params:
        safe_params["key"] = f"{safe_params['key'][:8]}...***"
    
    logger_instance.info(f"📤 {tool_name} 请求参数:\n%s", safe_params)


def log_response(logger_instance: logging.Logger, tool_name: str, status: str, info: str) -> None:
    """
    记录 API 响应日志
    
    Args:
        logger_instance: logger 实例
        tool_name: 工具名称
        status: 响应状态
        info: 状态信息
    """
    if status == "1":
        logger_instance.info(f"📥 {tool_name} 响应: ✅ 成功 ({info})")
    else:
        logger_instance.warning(f"📥 {tool_name} 响应: ❌ 失败 ({info})")


def log_error(logger_instance: logging.Logger, tool_name: str, error: str) -> None:
    """
    记录错误日志
    
    Args:
        logger_instance: logger 实例
        tool_name: 工具名称
        error: 错误信息
    """
    logger_instance.error(f"💥 {tool_name} 错误: {error}")


def log_success(logger_instance: logging.Logger, tool_name: str, summary: dict = None) -> None:
    """
    记录成功日志
    
    Args:
        logger_instance: logger 实例
        tool_name: 工具名称
        summary: 可选的摘要信息
    """
    if summary:
        logger_instance.info(f"✅ {tool_name} 完成: {summary}")
    else:
        logger_instance.info(f"✅ {tool_name} 执行成功")
