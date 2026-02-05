"""
统一数据模型 - 高德地图 MCP 服务器

提供统一的请求/响应结构
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from enum import Enum


class OutputFormat(str, Enum):
    JSON = "json"
    XML = "xml"


class ExtensionType(str, Enum):
    BASE = "base"
    ALL = "all"


class ApiResponse(BaseModel):
    """
    统一 API 响应结构
    
    所有 API 调用都应返回此格式：
    - 成功: status=1, data=具体数据
    - 失败: status=0, error=错误信息
    """
    status: int = Field(..., description="1=成功, 0=失败")
    data: Optional[Any] = Field(None, description="响应数据")
    error: Optional[str] = Field(None, description="错误信息")
    info: Optional[str] = Field(None, description="状态说明")

    @classmethod
    def success(cls, data: Any = None, info: str = "OK") -> "ApiResponse":
        return cls(status=1, data=data, error=None, info=info)

    @classmethod
    def error(cls, error: str, info: Optional[str] = "请求失败") -> "ApiResponse":
        return cls(status=0, data=None, error=error, info=info)


# ========================
# 精简响应模型
# ========================

class Location(BaseModel):
    """位置信息"""
    lat: Optional[float] = None
    lng: Optional[float] = None


class AddressInfo(BaseModel):
    """地址信息"""
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    citycode: Optional[str] = None
    district: Optional[str] = None
    adcode: Optional[str] = None
    township: Optional[str] = None
    street: Optional[str] = None
    street_number: Optional[str] = None
    formatted: Optional[str] = None


class GeocodingResult(BaseModel):
    """地理编码结果（精简）"""
    location: Optional[str] = None  # "lon,lat"
    formatted_address: Optional[str] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    citycode: Optional[str] = None
    district: Optional[str] = None
    adcode: Optional[str] = None
    level: Optional[str] = None


class GeocodingResponse(BaseModel):
    """地理编码响应（精简）"""
    status: str
    count: Optional[str] = None
    info: Optional[str] = None
    results: List[GeocodingResult] = Field(default_factory=list)


class ReverseGeocodingAddress(BaseModel):
    """逆地理编码地址（精简）"""
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    citycode: Optional[str] = None
    district: Optional[str] = None
    adcode: Optional[str] = None
    township: Optional[str] = None
    street: Optional[str] = None
    street_number: Optional[str] = None
    formatted: Optional[str] = None


class SimplePOI(BaseModel):
    """精简 POI 信息"""
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    typecode: Optional[str] = None
    address: Optional[str] = None
    location: Optional[str] = None
    distance: Optional[str] = None


class ReverseGeocodingResponse(BaseModel):
    """逆地理编码响应（精简）"""
    status: str
    info: Optional[str] = None
    location: Optional[Location] = None
    address: Optional[ReverseGeocodingAddress] = None
    pois: List[SimplePOI] = Field(default_factory=list)


class RouteStep(BaseModel):
    """路线分段（精简）"""
    type: str = Field(..., description="walking/bus/subway/drive/bike/ebike")
    instruction: Optional[str] = None
    from_stop: Optional[str] = None
    to_stop: Optional[str] = None
    line_name: Optional[str] = None
    distance: int = 0
    duration: Optional[int] = None
    action: Optional[str] = None


class RouteSummary(BaseModel):
    """路线摘要"""
    duration: int = 0  # 秒
    distance: int = 0  # 米
    walking_distance: Optional[int] = None
    cost: Optional[str] = None


class RouteResponse(BaseModel):
    """路线规划响应（精简）"""
    status: str
    info: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    summary: Optional[RouteSummary] = None
    paths: List[RouteStep] = Field(default_factory=list)


class POIResult(BaseModel):
    """POI 搜索结果（精简）"""
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    typecode: Optional[str] = None
    address: Optional[str] = None
    location: Optional[str] = None
    distance: Optional[str] = None
    citycode: Optional[str] = None
    adcode: Optional[str] = None


class POISearchResponse(BaseModel):
    """POI 搜索响应（精简）"""
    status: str
    count: Optional[str] = None
    info: Optional[str] = None
    suggestion: Optional[dict] = None
    pois: List[POIResult] = Field(default_factory=list)


class SubDistrict(BaseModel):
    """子行政区"""
    name: Optional[str] = None
    citycode: Optional[str] = None
    adcode: Optional[str] = None
    center: Optional[str] = None
    level: Optional[str] = None
    sub_districts: List["SubDistrict"] = Field(default_factory=list)


class DistrictResult(BaseModel):
    """行政区结果（精简）"""
    name: Optional[str] = None
    citycode: Optional[str] = None
    adcode: Optional[str] = None
    center: Optional[str] = None
    level: Optional[str] = None
    sub_districts: List[SubDistrict] = Field(default_factory=list)


class RegionQueryResponse(BaseModel):
    """行政区划查询响应（精简）"""
    status: str
    info: Optional[str] = None
    districts: List[DistrictResult] = Field(default_factory=list)


class IPLocation(BaseModel):
    """IP 定位结果（精简）"""
    ip: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    adcode: Optional[str] = None


class IPPositioningResponse(BaseModel):
    """IP 定位响应（精简）"""
    status: str
    info: Optional[str] = None
    location: Optional[IPLocation] = None
    bounds: Optional[str] = None


# 保持向后兼容
class RouteSummaryOld(BaseModel):
    """路线摘要（旧版兼容）"""
    duration: int = Field(..., description="总耗时（秒）")
    distance: int = Field(..., description="总距离（米）")
    walk_distance: Optional[int] = Field(None, description="步行距离（米）")
    steps: int = Field(..., description="分段数量")


class RouteStepOld(BaseModel):
    """路线分段（旧版兼容）"""
    type: str = Field(..., description="类型: walk/bus/subway/railway/drive/bike/ebike")
    distance: int = Field(..., description="分段距离（米）")
    road: Optional[str] = Field(None, description="道路名称")
    instruction: Optional[str] = Field(None, description="导航指引")
    summary: Optional[str] = Field(None, description="摘要")


class RouteResponseOld(BaseModel):
    """路线规划响应（旧版兼容）"""
    status: int = Field(..., description="1=成功, 0=失败")
    summary: Optional[RouteSummaryOld] = Field(None, description="路线摘要")
    steps: List[RouteStepOld] = Field(default_factory=list, description="分段列表")
    error: Optional[str] = Field(None, description="错误信息")
    info: Optional[str] = Field(None, description="状态说明")


class POI(BaseModel):
    """POI 信息（旧版兼容）"""
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    typecode: Optional[str] = None
    address: Optional[str] = None
    location: Optional[str] = None
    distance: Optional[str] = None
    citycode: Optional[str] = None
    adcode: Optional[str] = None


class GeocodeResultOld(BaseModel):
    """地理编码结果（旧版兼容）"""
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    citycode: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    adcode: Optional[str] = None
    location: Optional[str] = None
    level: Optional[str] = None


class District(BaseModel):
    """行政区信息（旧版兼容）"""
    name: Optional[str] = None
    citycode: Optional[str] = None
    adcode: Optional[str] = None
    center: Optional[str] = None
    level: Optional[str] = None
    polyline: Optional[str] = None
