"""
高德地图 MCP 服务器主模块

提供完整的地理信息服务和路线规划功能

功能：
- 地理编码（地址 <-> 坐标）
- 路线规划（驾车/步行/骑行/公交/地铁）
- POI搜索（关键字/周边/多边形/详情）
- 行政区划查询
- IP定位
"""
import os
import re
import json
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, model_validator

from mcp.server.fastmcp import FastMCP
import httpx
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ⚠️ 重要：移除硬编码的 API Key，所有配置通过环境变量或 .env 文件管理
# 请在 .env 文件中设置：AMAP_API_KEY=your_api_key_here

from config import (
    get_api_key, DEFAULT_HEADERS, DEFAULT_TIMEOUT,
    validate_location_format, validate_ip_format, validate_polygon_format,
    AMAP_GEO_URL, AMAP_REGEO_URL,
    AMAP_DRIVING_URL, AMAP_WALKING_URL, AMAP_BICYCLING_URL,
    AMAP_EBIKE_URL, AMAP_BUS_URL, AMAP_SEARCH_POI_URL,
    AMAP_SEARCH_POI_AROUND_URL, AMAP_SEARCH_POI_POLYGON_URL,
    AMAP_SEARCH_POI_DETAIL_URL, AMAP_AOI_POLYLINE_URL,
    AMAP_REGION_QUERY_URL, AMAP_IP_URL, AMAP_SUBWAY_TRANSIT,
    logger, log_request, log_response, log_error, log_success,
)
from models import ApiResponse
from output import (
    simplify_geocoding, simplify_reverse_geocoding, simplify_route,
    simplify_poi_search, simplify_poi_around, simplify_poi_polygon,
    simplify_poi_detail, simplify_aoi_boundary,
    simplify_region_query, simplify_ip_positioning,
)


# ========================
# Pydantic Input Models
# ========================

class GeocodingInput(BaseModel):
    """高德地图 - 地理编码输入参数"""
    address: str = Field(..., description="结构化地址，如 \"北京市朝阳区阜通东大街6号\"")
    city: Optional[str] = Field(None, description="指定城市（可选）")
    sig: Optional[str] = Field(None, description="数字签名（可选）")
    key: Optional[str] = Field(None, description="API Key（可选）")


class ReverseGeocodingInput(BaseModel):
    """高德地图 - 逆地理编码输入参数"""
    location: str = Field(..., description="经纬度 \"lon,lat\"")
    radius: str = Field("1000", description="搜索半径，默认 1000")
    poitype: Optional[str] = Field(None, description="POI 类型（可选）")
    extensions: str = Field("base", description="扩展信息，base/all")
    roadlevel: Optional[str] = Field(None, description="道路等级（可选）")
    sig: Optional[str] = Field(None, description="数字签名（可选）")
    key: Optional[str] = Field(None, description="API Key（可选）")


class DrivingRoutePlanningInput(BaseModel):
    """高德地图 - 驾车路线规划输入参数"""
    origin: str = Field(..., description="起点经纬度 \"lon,lat\"")
    destination: str = Field(..., description="终点经纬度 \"lon,lat\"")
    strategy: int = Field(32, description="路线策略，默认 32")
    show_fields: Optional[str] = Field(None, description="返回增强字段")
    plate: Optional[str] = Field(None, description="车牌号（可选）")
    cartype: int = Field(0, description="车辆类型，0=燃油/1=电动/2=混动")
    key: Optional[str] = Field(None, description="API Key（可选）")


class WalkingRoutePlanningInput(BaseModel):
    """高德地图 - 步行路线规划输入参数"""
    origin: str = Field(..., description="起点经纬度 \"lon,lat\"")
    destination: str = Field(..., description="终点经纬度 \"lon,lat\"")
    origin_id: Optional[str] = Field(None, description="起点POI ID（可选）")
    destination_id: Optional[str] = Field(None, description="终点POI ID（可选）")
    alternative_route: Optional[int] = Field(None, description="备选路线数量（可选）")
    show_fields: Optional[str] = Field(None, description="返回增强字段（可选）")
    isindoor: int = Field(0, description="是否规划室内路线，0-否，1-是")
    key: Optional[str] = Field(None, description="API Key（可选）")


class BicyclingRoutePlanningInput(BaseModel):
    """高德地图 - 骑行路线规划输入参数"""
    origin: str = Field(..., description="起点经纬度 \"lon,lat\"")
    destination: str = Field(..., description="终点经纬度 \"lon,lat\"")
    show_fields: Optional[str] = Field(None, description="返回增强字段（可选）")
    alternative_route: Optional[int] = Field(None, description="备选路线数量（可选）")
    key: Optional[str] = Field(None, description="API Key（可选）")


class ElectBikeRoutePlanningInput(BaseModel):
    """高德地图 - 电动车路线规划输入参数"""
    origin: str = Field(..., description="起点经纬度 \"lon,lat\"")
    destination: str = Field(..., description="终点经纬度 \"lon,lat\"")
    show_fields: Optional[str] = Field(None, description="返回增强字段（可选）")
    alternative_route: Optional[int] = Field(None, description="备选路线数量（可选）")
    key: Optional[str] = Field(None, description="API Key（可选）")


class PublicTransitRoutePlanningInput(BaseModel):
    """高德地图 - 公交路线规划输入参数"""
    origin: str = Field(..., description="起点经纬度 \"lon,lat\"")
    destination: str = Field(..., description="终点经纬度 \"lon,lat\"")
    city1: str = Field(..., description="起点城市")
    city2: str = Field(..., description="终点城市")
    strategy: int = Field(0, description="策略，0-最经济/不换乘最少，1-最经济/步行最少，2-时间最短，3-换乘最少")
    date: Optional[str] = Field(None, description="出发日期 YYYYMMDD（可选）")
    time: Optional[str] = Field(None, description="出发时间 HHmm（可选）")
    show_fields: Optional[str] = Field(None, description="返回增强字段（可选）")
    alternative_route: Optional[int] = Field(None, description="备选路线数量（可选）")
    key: Optional[str] = Field(None, description="API Key（可选）")


class SearchPOIInput(BaseModel):
    """高德 POI 关键字搜索输入参数"""
    keywords: str = Field(..., description="地点关键字（必填）")
    types: Optional[str] = Field(None, description="地点类型（可选，多个用 | 分隔）")
    region: Optional[str] = Field(None, description="搜索区域（citycode/adcode/cityname 等）")
    city_limit: Optional[bool] = Field(None, description="是否限制在 region 内")
    show_fields: Optional[str] = Field(None, description="返回字段控制")
    page_size: int = Field(10, description="1-25")
    page_num: int = Field(1, description=">=1")
    sig: Optional[str] = Field(None, description="数字签名（可选）")
    output: Literal["json", "xml"] = Field("json", description="输出格式")
    callback: Optional[str] = Field(None, description="回调函数名（可选）")


class SearchPOIAroundInput(BaseModel):
    """高德地图 - POI 周边搜索输入参数"""
    location: str = Field(..., description="中心坐标 \"lon,lat\"")
    keywords: Optional[str] = Field(None, description="搜索关键字（可选）")
    types: Optional[str] = Field(None, description="POI 类型代码（可选）")
    radius: int = Field(5000, description="搜索半径，单位米，默认 5000，最大 50000")
    sortrule: str = Field("sort", description="排序规则，sort-距离排序，weight-综合排序")
    offset: int = Field(20, description="每页数量，默认 20，最大 25")
    page: int = Field(1, description="页码，默认 1")
    extensions: str = Field("base", description="扩展信息，base/all")
    key: Optional[str] = Field(None, description="API Key（可选）")


class SearchPOIPolygonInput(BaseModel):
    """高德地图 - POI 多边形搜索输入参数"""
    polygon: str = Field(..., description="多边形坐标串，格式 \"lon1,lat1;lon2,lat2;lon3,lat3...\"")
    keywords: Optional[str] = Field(None, description="搜索关键字（可选）")
    types: Optional[str] = Field(None, description="POI 类型代码（可选）")
    offset: int = Field(20, description="每页数量，默认 20，最大 25")
    page: int = Field(1, description="页码，默认 1")
    extensions: str = Field("base", description="扩展信息，base/all")
    key: Optional[str] = Field(None, description="API Key（可选）")


class SearchPOIDetailInput(BaseModel):
    """高德地图 - POI ID 查询输入参数"""
    id: str = Field(..., description="POI 唯一标识")
    extensions: str = Field("base", description="扩展信息，base/all")
    key: Optional[str] = Field(None, description="API Key（可选）")


class SearchAOIBoundaryInput(BaseModel):
    """高德地图 - AOI 边界查询输入参数"""
    id: str = Field(..., description="AOI 的 poiid")
    key: Optional[str] = Field(None, description="API Key（可选）")


class AdministrativeRegionQueryInput(BaseModel):
    """高德地图 - 行政区划查询输入参数"""
    keywords: str = Field(..., description="关键字")
    subdistrict: int = Field(1, description="子级行政区深度，0-3")
    page: int = Field(1, description="页码")
    offset: int = Field(20, description="每页数量")
    extensions: str = Field("base", description="扩展信息")
    filter: Optional[str] = Field(None, description="过滤条件")
    key: Optional[str] = Field(None, description="API Key（可选）")


class IPPositioningInput(BaseModel):
    """高德地图 - IP 定位输入参数"""
    ip: str = Field(..., description="IP 地址")
    sig: Optional[str] = Field(None, description="数字签名（可选）")
    key: Optional[str] = Field(None, description="API Key（可选）")


class AmapRouteSubwayInput(BaseModel):
    """高德地图 - 地铁公交路线规划输入参数"""
    origin: str = Field(..., description="起点经纬度 \"lon,lat\"")
    destination: str = Field(..., description="终点经纬度 \"lon,lat\"")
    city: str = Field(..., description="城市名称")
    strategy: int = Field(0, description="策略，0-最经济，1-步行最少，2-时间最短，3-换乘最少")
    date: Optional[str] = Field(None, description="出发日期 YYYYMMDD（可选）")
    time: Optional[str] = Field(None, description="出发时间 HHmm（可选）")
    show_fields: Optional[str] = Field(None, description="返回增强字段（可选）")
    key: Optional[str] = Field(None, description="API Key（可选）")


load_dotenv()
mcp = FastMCP(name="amap-mcp")


def _build_params(**kwargs) -> dict:
    """构建 API 请求参数，自动过滤 None 值"""
    return {k: v for k, v in kwargs.items() if v is not None}


def _normalize_input(model_class, input_data):
    """
    规范化输入数据，处理被序列化为字符串的情况。

    如果 input_data 是字符串，尝试将其解析为 JSON 并用 model_class 验证。
    否则，直接用 model_class 验证（如果已经是字典）。
    """
    if isinstance(input_data, str):
        try:
            data_dict = json.loads(input_data)
            if isinstance(data_dict, dict):
                return model_class(**data_dict)
            else:
                raise ValueError("input_data 解析后不是对象")
        except json.JSONDecodeError:
            raise ValueError("input_data JSON 解析失败")
        except Exception as e:
            raise ValueError(f"input_data 验证失败: {str(e)}")
    elif isinstance(input_data, dict):
        return model_class(**input_data)
    else:
        # 如果是 Pydantic 模型实例（通常不会发生，除非 FastMCP 内部处理了）
        return input_data


async def _api_request(url: str, params: dict, method: str = "GET") -> dict:
    """统一 API 请求方法"""
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        if method.upper() == "POST":
            response = await client.post(url, params=params, headers=DEFAULT_HEADERS)
        else:
            response = await client.get(url, params=params, headers=DEFAULT_HEADERS)

        response.raise_for_status()
        return response.json()

@mcp.tool(name="geocoding")
async def geocoding(input_data: GeocodingInput) -> dict:
    """
    高德地图 - 地理编码（地址转坐标）

    Args:
        input_data: 包含地址和可选城市信息的 GeocodingInput 模型

    Returns:
        精简响应：包含 location, adcode, citycode 等核心字段

    Example:

        {"status": 1, "results": [{"location": "116.481488,39.990464", "city": "北京市", ...}]}
    """
    try:
        validated_data = _normalize_input(GeocodingInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    address = validated_data.address
    city = validated_data.city

    if not address:
        error_msg = "地址不能为空，请提供 address 参数"
        log_error(logger, "geocoding", error_msg)
        return ApiResponse.error(error_msg)

    api_key = validated_data.key or get_api_key()
    params = _build_params(key=api_key, address=address, city=city, sig=validated_data.sig)
    
    # 记录请求日志
    log_request(logger, "geocoding", params)
    data = await _api_request(AMAP_GEO_URL, params)
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "geocoding", status, info)
    
    if status != "1":
        error_msg = data.get("info", "地理编码失败")
        log_error(logger, "geocoding", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_geocoding(data)
    log_success(logger, "geocoding", {"location": simplified[0].get("location") if simplified else None})
    return ApiResponse.success(simplified, info)


@mcp.tool(name="reverse_geocoding")
async def reverse_geocoding(input_data: ReverseGeocodingInput) -> dict:
    """
    高德地图 - 逆地理编码（坐标转地址）

    Args:
        input_data: 包含经纬度和可选参数的 ReverseGeocodingInput 模型

    Returns:
        精简响应：包含 address、pois 等核心字段，最多返回 10 个 POI

    Example:
        >>> await reverse_geocoding("116.481488,39.990464")
        {"status": 1, "address": {"city": "北京市", "district": "朝阳区", ...}, "pois": [...]}
    """
    try:
        validated_data = _normalize_input(ReverseGeocodingInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    location = validated_data.location

    if not validate_location_format(location):
        error_msg = f"无效的经纬度格式: {location}"
        log_error(logger, "reverse_geocoding", error_msg)
        return ApiResponse.error(error_msg)
    
    api_key = validated_data.key or get_api_key()
    params = _build_params(key=api_key, location=location, radius=validated_data.radius, poitype=validated_data.poitype, extensions=validated_data.extensions,
                           roadlevel=validated_data.roadlevel, sig=validated_data.sig)
    
    # 记录请求日志
    log_request(logger, "reverse_geocoding", params)
    data = await _api_request(AMAP_REGEO_URL, params)
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "reverse_geocoding", status, info)
    
    if status != "1":
        error_msg = data.get("info", "逆地理编码失败")
        log_error(logger, "reverse_geocoding", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_reverse_geocoding(data)
    log_success(logger, "reverse_geocoding", {"pois_count": len(simplified.get("pois", []))})
    return ApiResponse.success(simplified, info)


@mcp.tool(name="driving_route_planning")
async def driving_route_planning(input_data: DrivingRoutePlanningInput) -> dict:
    """
    高德地图 - 驾车路线规划

    Args:
        input_data: 包含起点、终点和策略的 DrivingRoutePlanningInput 模型

    Returns:
        精简响应：包含 summary、paths（每步导航指引）

    Example:
        >>> await driving_route_planning("116.481028,39.989643", "116.434446,39.90816")
        {"status": 1, "summary": {"duration": 1800, "distance": 15000}, "paths": [...]}
    """
    try:
        validated_data = _normalize_input(DrivingRoutePlanningInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    origin = validated_data.origin
    destination = validated_data.destination

    if not validate_location_format(origin):
        error_msg = f"无效的起点经纬度: {origin}"
        log_error(logger, "driving_route_planning", error_msg)
        return ApiResponse.error(error_msg)
    if not validate_location_format(destination):
        error_msg = f"无效的终点经纬度: {destination}"
        log_error(logger, "driving_route_planning", error_msg)
        return ApiResponse.error(error_msg)
    api_key = validated_data.key or get_api_key()
    params = _build_params(key=api_key, origin=origin, destination=destination, strategy=validated_data.strategy,
                           show_fields=validated_data.show_fields, plate=validated_data.plate, cartype=validated_data.cartype)
    
    # 记录请求日志
    log_request(logger, "driving_route_planning", params)
    data = await _api_request(AMAP_DRIVING_URL, params)
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "driving_route_planning", status, info)
    
    if status != "1":
        error_msg = data.get("info", "路线规划失败")
        log_error(logger, "driving_route_planning", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_route(data)
    log_success(logger, "driving_route_planning", {
        "distance": simplified.get("summary", {}).get("distance"),
        "duration": simplified.get("summary", {}).get("duration")
    })
    return ApiResponse.success(simplified, info)


@mcp.tool(name="walking_route_planning")
async def walking_route_planning(input_data: WalkingRoutePlanningInput) -> dict:
    """
    高德地图 - 步行路线规划

    Args:
        input_data: 包含起点、终点和可选参数的 WalkingRoutePlanningInput 模型

    Returns:
        精简响应：包含路线信息和导航指引
    """
    try:
        validated_data = _normalize_input(WalkingRoutePlanningInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    origin = validated_data.origin
    destination = validated_data.destination

    if not validate_location_format(origin):
        error_msg = f"无效的起点经纬度: {origin}"
        log_error(logger, "walking_route_planning", error_msg)
        return ApiResponse.error(error_msg)
    if not validate_location_format(destination):
        error_msg = f"无效的终点经纬度: {destination}"
        log_error(logger, "walking_route_planning", error_msg)
        return ApiResponse.error(error_msg)
    api_key = validated_data.key or get_api_key()
    params = _build_params(key=api_key, origin=origin, destination=destination, origin_id=validated_data.origin_id,
                           destination_id=validated_data.destination_id, alternative_route=validated_data.alternative_route, show_fields=validated_data.show_fields,
                           isindoor=validated_data.isindoor)
    
    # 记录请求日志
    log_request(logger, "walking_route_planning", params)
    data = await _api_request(AMAP_WALKING_URL, params)
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "walking_route_planning", status, info)
    
    if status != "1":
        error_msg = data.get("info", "路线规划失败")
        log_error(logger, "walking_route_planning", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_route(data)
    log_success(logger, "walking_route_planning", {
        "distance": simplified.get("summary", {}).get("distance"),
        "duration": simplified.get("summary", {}).get("duration")
    })
    return ApiResponse.success(simplified, info)


@mcp.tool(name="bicycling_route_planning")
async def bicycling_route_planning(input_data: BicyclingRoutePlanningInput) -> dict:
    """
    高德地图 - 骑行路线规划

    Args:
        input_data: 包含起点、终点和可选参数的 BicyclingRoutePlanningInput 模型

    Returns:
        精简响应：包含骑行路线信息
    """
    try:
        validated_data = _normalize_input(BicyclingRoutePlanningInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    origin = validated_data.origin
    destination = validated_data.destination

    if not validate_location_format(origin):
        error_msg = f"无效的起点经纬度: {origin}"
        log_error(logger, "bicycling_route_planning", error_msg)
        return ApiResponse.error(error_msg)
    if not validate_location_format(destination):
        error_msg = f"无效的终点经纬度: {destination}"
        log_error(logger, "bicycling_route_planning", error_msg)
        return ApiResponse.error(error_msg)
    api_key = validated_data.key or get_api_key()
    params = _build_params(key=api_key, origin=origin, destination=destination, show_fields=validated_data.show_fields,
                           alternative_route=validated_data.alternative_route)
    
    # 记录请求日志
    log_request(logger, "bicycling_route_planning", params)
    data = await _api_request(AMAP_BICYCLING_URL, params)
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "bicycling_route_planning", status, info)
    
    if status != "1":
        error_msg = data.get("info", "路线规划失败")
        log_error(logger, "bicycling_route_planning", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_route(data)
    log_success(logger, "bicycling_route_planning", {
        "distance": simplified.get("summary", {}).get("distance"),
        "duration": simplified.get("summary", {}).get("duration")
    })
    return ApiResponse.success(simplified, info)


@mcp.tool(name="elect_bike_route_planning")
async def elect_bike_route_planning(input_data: ElectBikeRoutePlanningInput) -> dict:
    """
    高德地图 - 电动车路线规划

    Args:
        input_data: 包含起点、终点和可选参数的 ElectBikeRoutePlanningInput 模型

    Returns:
        精简响应：包含电动车路线信息
    """
    try:
        validated_data = _normalize_input(ElectBikeRoutePlanningInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    origin = validated_data.origin
    destination = validated_data.destination

    if not validate_location_format(origin):
        error_msg = f"无效的起点经纬度: {origin}"
        log_error(logger, "elect_bike_route_planning", error_msg)
        return ApiResponse.error(error_msg)
    if not validate_location_format(destination):
        error_msg = f"无效的终点经纬度: {destination}"
        log_error(logger, "elect_bike_route_planning", error_msg)
        return ApiResponse.error(error_msg)
    api_key = validated_data.key or get_api_key()
    params = _build_params(key=api_key, origin=origin, destination=destination, show_fields=validated_data.show_fields,
                           alternative_route=validated_data.alternative_route)
    
    # 记录请求日志
    log_request(logger, "elect_bike_route_planning", params)
    data = await _api_request(AMAP_EBIKE_URL, params)
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "elect_bike_route_planning", status, info)
    
    if status != "1":
        error_msg = data.get("info", "路线规划失败")
        log_error(logger, "elect_bike_route_planning", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_route(data)
    log_success(logger, "elect_bike_route_planning", {
        "distance": simplified.get("summary", {}).get("distance"),
        "duration": simplified.get("summary", {}).get("duration")
    })
    return ApiResponse.success(simplified, info)


@mcp.tool(name="public_transit_route_planning")
async def public_transit_route_planning(input_data: PublicTransitRoutePlanningInput) -> dict:
    """
    高德地图 - 公交路线规划

    Args:
        input_data: 包含起点、终点、城市和策略的 PublicTransitRoutePlanningInput 模型

    Returns:
        精简响应：包含公交路线方案
    """
    try:
        validated_data = _normalize_input(PublicTransitRoutePlanningInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    origin = validated_data.origin
    destination = validated_data.destination
    city1 = validated_data.city1
    city2 = validated_data.city2

    # 验证必填参数
    if not origin:
        error_msg = "起点坐标不能为空，请提供 origin 参数"
        log_error(logger, "public_transit_route_planning", error_msg)
        return ApiResponse.error(error_msg)
    if not destination:
        error_msg = "终点坐标不能为空，请提供 destination 参数"
        log_error(logger, "public_transit_route_planning", error_msg)
        return ApiResponse.error(error_msg)
    if not city1:
        error_msg = "起点城市不能为空，请提供 city1 参数"
        log_error(logger, "public_transit_route_planning", error_msg)
        return ApiResponse.error(error_msg)
    if not city2:
        error_msg = "终点城市不能为空，请提供 city2 参数"
        log_error(logger, "public_transit_route_planning", error_msg)
        return ApiResponse.error(error_msg)

    if not validate_location_format(origin):
        error_msg = f"无效的起点经纬度: {origin}"
        log_error(logger, "public_transit_route_planning", error_msg)
        return ApiResponse.error(error_msg)
    if not validate_location_format(destination):
        error_msg = f"无效的终点经纬度: {destination}"
        log_error(logger, "public_transit_route_planning", error_msg)
        return ApiResponse.error(error_msg)
    api_key = validated_data.key or get_api_key()
    params = _build_params(key=api_key, origin=origin, destination=destination, city1=city1, city2=city2,
                           strategy=validated_data.strategy, date=validated_data.date, time=validated_data.time, show_fields=validated_data.show_fields,
                           alternative_route=validated_data.alternative_route)
    
    # 记录请求日志
    log_request(logger, "public_transit_route_planning", params)
    data = await _api_request(AMAP_BUS_URL, params, method="POST")
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "public_transit_route_planning", status, info)
    
    if status != "1":
        error_msg = data.get("info", "路线规划失败")
        log_error(logger, "public_transit_route_planning", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_route(data)
    log_success(logger, "public_transit_route_planning", {
        "distance": simplified.get("summary", {}).get("distance"),
        "duration": simplified.get("summary", {}).get("duration")
    })
    return ApiResponse.success(simplified, info)


@mcp.tool(name="search_poi")
async def search_poi(input_data: SearchPOIInput) -> dict:
    """
    高德 POI 关键字搜索（POI 2.0 /v5/place/text）

    Args:
        input_data: 包含搜索关键字和可选参数的 SearchPOIInput 模型
    """
    try:
        validated_data = _normalize_input(SearchPOIInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    keywords = validated_data.keywords
    page_size = validated_data.page_size
    page_num = validated_data.page_num

    if not keywords or not keywords.strip():
        error_msg = "keywords 不能为空"
        log_error(logger, "search_poi", error_msg)
        return ApiResponse.error(error_msg)

    # 使用统一的 API Key 获取方式
    api_key = get_api_key()

    if not (1 <= page_size <= 25):
        error_msg = "page_size 必须在 1-25 之间"
        log_error(logger, "search_poi", error_msg)
        return ApiResponse.error(error_msg)
    if page_num < 1:
        error_msg = "page_num 必须 >= 1"
        log_error(logger, "search_poi", error_msg)
        return ApiResponse.error(error_msg)

    url = AMAP_SEARCH_POI_URL

    params = {
        "key": api_key,
        "keywords": keywords,
        "page_size": str(page_size),
        "page_num": str(page_num),
        "output": validated_data.output,
    }
    if validated_data.types:
        params["types"] = validated_data.types
    if validated_data.region:
        params["region"] = validated_data.region
    if validated_data.city_limit is not None:
        params["city_limit"] = "true" if validated_data.city_limit else "false"
    if validated_data.show_fields:
        params["show_fields"] = validated_data.show_fields
    if validated_data.sig:
        params["sig"] = validated_data.sig
    if validated_data.callback:
        params["callback"] = validated_data.callback

    # 记录请求日志（已脱敏）
    log_request(logger, "search_poi", params)
    
    timeout = httpx.Timeout(DEFAULT_TIMEOUT, connect=5.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

        # 高德通常返回 JSON（output=json），这里按 JSON 优先解析；解析失败就返回原文
        try:
            data = resp.json()
        except Exception:
            error_msg = f"JSON 解析失败: {resp.text[:100]}..."
            log_error(logger, "search_poi", error_msg)
            return {"raw": resp.text}

    # 记录响应日志
    status = str(data.get("status", "0"))
    info = data.get("info", "")
    log_response(logger, "search_poi", status, info)

    # 如果高德返回 status!=1，也视为业务错误（可按你需要调整）
    if isinstance(data, dict) and data.get("status") not in (None, "1", 1):
        error_msg = f"AMap业务错误: {data.get('info')} ({data.get('infocode')})"
        log_error(logger, "search_poi", error_msg)
        return ApiResponse.error(error_msg)

    log_success(logger, "search_poi", {"count": data.get("count", "0")})
    return data


@mcp.tool(name="search_poi_around")
async def search_poi_around(input_data: SearchPOIAroundInput) -> dict:
    """
    高德地图 - POI 周边搜索

    Args:
        input_data: 包含中心坐标和搜索参数的 SearchPOIAroundInput 模型

    Returns:
        精简响应：包含 location 中心点和 pois 列表

    Example:
        >>> await search_poi_around("116.481488,39.990464", keywords="美食", radius=1000)
        {"status": 1, "location": "116.481488,39.990464", "pois": [{"name": "某餐厅", "distance": "500", ...}]}
    """
    try:
        validated_data = _normalize_input(SearchPOIAroundInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    location = validated_data.location
    radius = validated_data.radius
    offset = validated_data.offset

    # 验证必填参数
    if not location:
        error_msg = "中心坐标不能为空，请提供 location 参数"
        log_error(logger, "search_poi_around", error_msg)
        return ApiResponse.error(error_msg)

    if not validate_location_format(location):
        error_msg = f"无效的经纬度格式: {location}"
        log_error(logger, "search_poi_around", error_msg)
        return ApiResponse.error(error_msg)

    if radius > 50000:
        error_msg = "radius 最大值为 50000"
        log_error(logger, "search_poi_around", error_msg)
        return ApiResponse.error(error_msg)
    if radius < 1:
        error_msg = "radius 最小值为 1"
        log_error(logger, "search_poi_around", error_msg)
        return ApiResponse.error(error_msg)

    if offset > 25:
        error_msg = "offset 最大值为 25"
        log_error(logger, "search_poi_around", error_msg)
        return ApiResponse.error(error_msg)
    if offset < 1:
        error_msg = "offset 最小值为 1"
        log_error(logger, "search_poi_around", error_msg)
        return ApiResponse.error(error_msg)

    api_key = validated_data.key or get_api_key()
    params = _build_params(
        key=api_key, location=location, keywords=validated_data.keywords, types=validated_data.types,
        radius=radius, sortrule=validated_data.sortrule, offset=offset, page=validated_data.page, extensions=validated_data.extensions
    )
    
    # 记录请求日志
    log_request(logger, "search_poi_around", params)
    data = await _api_request(AMAP_SEARCH_POI_AROUND_URL, params)
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "search_poi_around", status, info)
    
    if status != "1":
        error_msg = data.get("info", "POI 周边搜索失败")
        log_error(logger, "search_poi_around", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_poi_around(data, limit=offset)
    log_success(logger, "search_poi_around", {"pois_count": len(simplified.get("pois", []))})
    return ApiResponse.success(simplified, info)


@mcp.tool(name="search_poi_polygon")
async def search_poi_polygon(input_data: SearchPOIPolygonInput) -> dict:
    """
    高德地图 - POI 多边形搜索

    Args:
        input_data: 包含多边形坐标和搜索关键字的 SearchPOIPolygonInput 模型

    Returns:
        精简响应：包含 polygon 和 pois 列表

    Example:
        >>> await search_poi_polygon("116.47,39.9;116.49,39.91;116.48,39.92", keywords="美食")
        {"status": 1, "polygon": "...", "pois": [...]}
    """
    try:
        validated_data = _normalize_input(SearchPOIPolygonInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    polygon = validated_data.polygon
    offset = validated_data.offset

    # 验证多边形格式
    is_valid, error_msg_validate = validate_polygon_format(polygon)
    if not is_valid:
        log_error(logger, "search_poi_polygon", error_msg_validate)
        return ApiResponse.error(error_msg_validate)

    if offset > 25:
        error_msg = "offset 最大值为 25"
        log_error(logger, "search_poi_polygon", error_msg)
        return ApiResponse.error(error_msg)
    if offset < 1:
        error_msg = "offset 最小值为 1"
        log_error(logger, "search_poi_polygon", error_msg)
        return ApiResponse.error(error_msg)

    api_key = validated_data.key or get_api_key()
    params = _build_params(
        key=api_key, polygon=polygon, keywords=validated_data.keywords, types=validated_data.types,
        offset=offset, page=validated_data.page, extensions=validated_data.extensions
    )
    
    # 记录请求日志
    log_request(logger, "search_poi_polygon", params)
    data = await _api_request(AMAP_SEARCH_POI_POLYGON_URL, params)
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "search_poi_polygon", status, info)
    
    if status != "1":
        error_msg = data.get("info", "POI 多边形搜索失败")
        log_error(logger, "search_poi_polygon", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_poi_polygon(data, limit=offset)
    log_success(logger, "search_poi_polygon", {"pois_count": len(simplified.get("pois", []))})
    return ApiResponse.success(simplified, info)


@mcp.tool(name="search_poi_detail")
async def search_poi_detail(input_data: SearchPOIDetailInput) -> dict:
    """
    高德地图 - POI ID 查询

    Args:
        input_data: 包含 POI ID 的 SearchPOIDetailInput 模型

    Returns:
        精简响应：包含 POI 详细信息

    Example:
        >>> await search_poi_detail("B0FFFZZZ5S")
        {"status": 1, "poi": {"name": "某餐厅", "address": "某路", "biz_ext": {...}}}
    """
    try:
        validated_data = _normalize_input(SearchPOIDetailInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    id = validated_data.id

    if not id or not id.strip():
        error_msg = "POI ID 不能为空"
        log_error(logger, "search_poi_detail", error_msg)
        return ApiResponse.error(error_msg)

    api_key = validated_data.key or get_api_key()
    params = _build_params(key=api_key, id=id, extensions=validated_data.extensions)
    
    # 记录请求日志
    log_request(logger, "search_poi_detail", params)
    data = await _api_request(AMAP_SEARCH_POI_DETAIL_URL, params)
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "search_poi_detail", status, info)
    
    if status != "1":
        error_msg = data.get("info", "POI ID 查询失败")
        log_error(logger, "search_poi_detail", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_poi_detail(data)
    log_success(logger, "search_poi_detail", {"name": simplified.get("poi", {}).get("name")})
    return ApiResponse.success(simplified, info)


@mcp.tool(name="search_aoi_boundary")
async def search_aoi_boundary(input_data: SearchAOIBoundaryInput) -> dict:
    """
    高德地图 - AOI 边界查询

    Args:
        input_data: 包含 AOI ID 的 SearchAOIBoundaryInput 模型

    Returns:
        精简响应：包含 AOI 名称、边界 polyline、所属区域等信息

    Example:
        >>> await search_aoi_boundary("B0FFFZZZ5S")
        {"status": 1, "aoi": {"name": "某商圈", "polyline": "116.1,39.1_116.2,39.2_...", ...}}
    """
    try:
        validated_data = _normalize_input(SearchAOIBoundaryInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    id = validated_data.id

    # 验证必填参数
    if not id or not str(id).strip():
        error_msg = "AOI ID 不能为空，请提供 id 参数"
        log_error(logger, "search_aoi_boundary", error_msg)
        return ApiResponse.error(error_msg)

    api_key = validated_data.key or get_api_key()
    params = _build_params(key=api_key, id=id)
    
    # 记录请求日志
    log_request(logger, "search_aoi_boundary", params)
    data = await _api_request(AMAP_AOI_POLYLINE_URL, params)
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "search_aoi_boundary", status, info)
    
    if status != "1":
        error_msg = data.get("info", "AOI 边界查询失败")
        log_error(logger, "search_aoi_boundary", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_aoi_boundary(data)
    log_success(logger, "search_aoi_boundary", {"name": simplified.get("aoi", {}).get("name")})
    return ApiResponse.success(simplified, info)


@mcp.tool(name="administrative_region_query")
async def administrative_region_query(input_data: AdministrativeRegionQueryInput) -> dict:
    """
    高德地图 - 行政区划查询

    Args:
        input_data: 包含关键字和深度的 AdministrativeRegionQueryInput 模型

    Returns:
        精简响应：包含行政区划信息
    """
    try:
        validated_data = _normalize_input(AdministrativeRegionQueryInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    keywords = validated_data.keywords
    subdistrict = validated_data.subdistrict

    # 验证必填参数
    if not keywords:
        error_msg = "关键字不能为空，请提供 keywords 参数"
        log_error(logger, "administrative_region_query", error_msg)
        return ApiResponse.error(error_msg)

    if subdistrict < 0 or subdistrict > 3:
        error_msg = "subdistrict 有效值为 0-3"
        log_error(logger, "administrative_region_query", error_msg)
        return ApiResponse.error(error_msg)
    api_key = validated_data.key or get_api_key()
    params = _build_params(key=api_key, keywords=keywords, subdistrict=subdistrict, page=validated_data.page, offset=validated_data.offset,
                           extensions=validated_data.extensions, filter=validated_data.filter)
    
    # 记录请求日志
    log_request(logger, "administrative_region_query", params)
    data = await _api_request(AMAP_REGION_QUERY_URL, params)
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "administrative_region_query", status, info)
    
    if status != "1":
        error_msg = data.get("info", "行政区划查询失败")
        log_error(logger, "administrative_region_query", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_region_query(data)
    log_success(logger, "administrative_region_query", {"districts_count": len(simplified.get("districts", []))})
    return ApiResponse.success(simplified, info)


@mcp.tool(name="ip_positioning")
async def ip_positioning(input_data: IPPositioningInput) -> dict:
    """
    高德地图 - IP 定位

    Args:
        input_data: 包含 IP 地址的 IPPositioningInput 模型

    Returns:
        精简响应：包含 IP 定位信息
    """
    try:
        validated_data = _normalize_input(IPPositioningInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    ip = validated_data.ip
    
    # 验证 IP 格式
    if not validate_ip_format(ip):
        error_msg = f"无效的 IP 地址格式: {ip}"
        log_error(logger, "ip_positioning", error_msg)
        return ApiResponse.error(error_msg)
    
    api_key = validated_data.key or get_api_key()
    params = _build_params(key=api_key, ip=ip, sig=validated_data.sig)
    
    # 记录请求日志
    log_request(logger, "ip_positioning", params)
    data = await _api_request(AMAP_IP_URL, params)
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "ip_positioning", status, info)
    
    if status != "1":
        error_msg = data.get("info", "IP 定位失败")
        log_error(logger, "ip_positioning", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_ip_positioning(data)
    log_success(logger, "ip_positioning", {
        "province": simplified.get("location", {}).get("province"),
        "city": simplified.get("location", {}).get("city")
    })
    return ApiResponse.success(simplified, info)


@mcp.tool(name="amap_route_subway")
async def amap_route_subway(input_data: AmapRouteSubwayInput) -> dict:
    """
    高德地图 - 地铁公交路线规划

    Args:
        input_data: 包含起点、终点和城市的 AmapRouteSubwayInput 模型

    Returns:
        精简响应：包含地铁路线信息
    """
    try:
        validated_data = _normalize_input(AmapRouteSubwayInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    origin = validated_data.origin
    destination = validated_data.destination

    if not validate_location_format(origin):
        error_msg = f"无效的起点经纬度: {origin}"
        log_error(logger, "amap_route_subway", error_msg)
        return ApiResponse.error(error_msg)
    if not validate_location_format(destination):
        error_msg = f"无效的终点经纬度: {destination}"
        log_error(logger, "amap_route_subway", error_msg)
        return ApiResponse.error(error_msg)
    api_key = validated_data.key or get_api_key()
    params = _build_params(key=api_key, origin=origin, destination=destination, city=validated_data.city, strategy=validated_data.strategy, date=validated_data.date,
                           time=validated_data.time, show_fields=validated_data.show_fields)
    
    # 记录请求日志
    log_request(logger, "amap_route_subway", params)
    data = await _api_request(AMAP_SUBWAY_TRANSIT, params)
    
    # 记录响应日志
    status = data.get("status", "0")
    info = data.get("info", "")
    log_response(logger, "amap_route_subway", status, info)
    
    if status != "1":
        error_msg = data.get("info", "路线规划失败")
        log_error(logger, "amap_route_subway", error_msg)
        return ApiResponse.error(error_msg)

    simplified = simplify_route(data)
    log_success(logger, "amap_route_subway", {
        "distance": simplified.get("summary", {}).get("distance"),
        "duration": simplified.get("summary", {}).get("duration")
    })
    return ApiResponse.success(simplified, info)


# 向后兼容工具
@mcp.tool(name="reverse_Geocoding")
async def reverse_Geocoding(input_data: ReverseGeocodingInput) -> dict:
    """逆地理编码（向后兼容）"""
    log_request(logger, "reverse_Geocoding", {"input": str(input_data)})
    result = await reverse_geocoding(input_data=input_data)
    return result


@mcp.tool(name="search_re_geo_all")
async def search_re_geo_all(input_data: ReverseGeocodingInput) -> dict:
    """逆地理编码全量POI（向后兼容）"""
    try:
        validated_data = _normalize_input(ReverseGeocodingInput, input_data)
    except ValueError as e:
        return ApiResponse.error(str(e))

    # 验证必填参数
    if not validated_data.location:
        error_msg = "坐标不能为空，请提供 location 参数"
        log_error(logger, "search_re_geo_all", error_msg)
        return ApiResponse.error(error_msg)
    if not validated_data.poitype:
        error_msg = "POI 类型不能为空，请提供 poitype 参数"
        log_error(logger, "search_re_geo_all", error_msg)
        return ApiResponse.error(error_msg)

    log_request(logger, "search_re_geo_all", {"location": validated_data.location, "poitype": validated_data.poitype})
    result = await reverse_geocoding(input_data=validated_data)
    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
