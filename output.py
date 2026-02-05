"""
输出精简模块 - 高德地图 MCP 服务器

提供各 API 的输出精简功能，只返回核心有用字段
"""

from typing import Optional, List, Dict, Any


# ========================
# 地理编码输出精简
# ========================

def simplify_geocoding(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    精简地理编码输出
    
    原始返回大量字段，精简后只返回核心字段
    """
    if raw.get("status") != "1" or not raw.get("geocodes"):
        return raw
    
    simplified = {
        "status": "1",
        "count": raw.get("count"),
        "info": raw.get("info"),
        "results": []
    }
    
    for geo in raw.get("geocodes", []):
        simplified["results"].append({
            "location": geo.get("location"),          # 经纬度
            "formatted_address": str(geo.get("country", "")) + 
                                 str(geo.get("province", "")) + 
                                 str(geo.get("city", "")) + 
                                 str(geo.get("district", "")) + 
                                 str(geo.get("street", "")) + 
                                 str(geo.get("number", "")),
            "country": geo.get("country"),
            "province": geo.get("province"),
            "city": geo.get("city"),
            "citycode": geo.get("citycode"),
            "district": geo.get("district"),
            "township": geo.get("township"),
            "street": geo.get("street"),
            "number": geo.get("number"),
            "adcode": geo.get("adcode"),
            "level": geo.get("level"),
        })
    
    return simplified


# ========================
# 逆地理编码输出精简
# ========================

def simplify_reverse_geocoding(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    精简逆地理编码输出
    """
    if raw.get("status") != "1":
        return raw
    
    regeo = raw.get("regeocode", {})
    if not regeo:
        return raw
    
    addr = regeo.get("addressComponent", {})
    
    simplified = {
        "status": "1",
        "info": raw.get("info"),
        "location": {
            "lat": regeo.get("location", "").split(",")[1] if regeo.get("location") else None,
            "lng": regeo.get("location", "").split(",")[0] if regeo.get("location") else None,
        },
        "address": {
            "country": addr.get("country"),
            "province": addr.get("province"),
            "city": addr.get("city"),
            "citycode": addr.get("citycode"),
            "district": addr.get("district"),
            "adcode": addr.get("adcode"),
            "township": addr.get("township"),
            "street": addr.get("street"),
            "street_number": addr.get("streetNumber"),
            "formatted": regeo.get("formatted_address"),
        },
        "pois": []
    }
    
    # 只返回 POI 核心字段
    for poi in regeo.get("pois", [])[:10]:  # 最多返回 10 个
        simplified["pois"].append({
            "id": poi.get("id"),
            "name": poi.get("name"),
            "type": poi.get("type"),
            "typecode": poi.get("typecode"),
            "address": poi.get("address"),
            "location": poi.get("location"),
            "distance": poi.get("distance"),
        })
    
    return simplified


# ========================
# 路线规划输出精简（统一处理所有路线类型）
# ========================

def simplify_route(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    精简路线规划输出
    
    统一处理：驾车、步行、骑行、公交、地铁
    """
    if raw.get("status") != "1":
        return raw
    
    route = raw.get("route", {})
    if not route:
        return raw
    
    simplified = {
        "status": "1",
        "info": raw.get("info"),
        "origin": route.get("origin"),
        "destination": route.get("destination"),
        "paths": []
    }
    
    # 判断是 transit 还是 paths
    if "transits" in route:
        # 公交/地铁路线
        simplified.update(_simplify_transit(route["transits"]))
    elif "paths" in route:
        # 驾车/步行/骑行/电动车
        simplified.update(_simplify_paths(route["paths"]))
    
    return simplified


def _simplify_transit(transits: List[Dict]) -> Dict[str, Any]:
    """精简公交路线"""
    if not transits:
        return {"paths": [], "summary": {}}
    
    # 选择耗时最短的方案
    best = min(transits, key=lambda t: int(t.get("duration", 999999)))
    
    summary = {
        "duration": int(best.get("duration", 0)),
        "distance": int(best.get("distance", 0)),
        "walking_distance": int(best.get("walking_distance", 0)),
        "cost": best.get("cost", {}).get("price") if best.get("cost") else None,
    }
    
    steps = []
    for seg in best.get("segments", []):
        # 步行段
        if seg.get("walking"):
            walk = seg["walking"]
            steps.append({
                "type": "walking",
                "from": walk.get("origin"),
                "to": walk.get("destination"),
                "distance": int(walk.get("distance", 0)),
                "action": walk.get("action"),
            })
        
        # 公交段
        if seg.get("bus"):
            for line in seg["bus"].get("buslines", []):
                steps.append({
                    "type": "bus",
                    "line_name": line.get("name"),
                    "from_stop": line.get("departure_stop", {}).get("name"),
                    "to_stop": line.get("arrival_stop", {}).get("name"),
                    "distance": int(line.get("distance", 0)),
                    "duration": int(line.get("duration", 0)),
                })
        
        # 地铁段
        if seg.get("railway"):
            rail = seg["railway"]
            steps.append({
                "type": "subway",
                "line_name": rail.get("name"),
                "from_stop": rail.get("departure_stop", {}).get("name"),
                "to_stop": rail.get("arrival_stop", {}).get("name"),
                "distance": int(rail.get("distance", 0)),
                "duration": int(rail.get("duration", 0)),
            })
    
    return {"paths": steps, "summary": summary}


def _simplify_paths(paths: List[Dict]) -> Dict[str, Any]:
    """精简驾车/步行/骑行路线"""
    if not paths:
        return {"paths": [], "summary": {}}
    
    best = paths[0]
    
    summary = {
        "duration": int(best.get("duration", 0)),
        "distance": int(best.get("distance", 0)),
    }
    
    # 如果有 cost 信息
    if best.get("cost"):
        summary["cost_info"] = best.get("cost")
    
    steps = []
    for step in best.get("steps", []):
        steps.append({
            "instruction": step.get("instruction"),
            "orientation": step.get("orientation"),
            "road_name": step.get("road_name"),
            "distance": int(step.get("step_distance", 0)),
            "polyline": step.get("polyline")[:200] + "..." if step.get("polyline") and len(step.get("polyline", "")) > 200 else step.get("polyline"),
        })
    
    return {"paths": steps, "summary": summary}


# ========================
# POI 搜索输出精简
# ========================

def simplify_poi_search(raw: Dict[str, Any], limit: int = 10) -> Dict[str, Any]:
    """
    精简 POI 搜索输出
    
    Args:
        raw: 原始响应
        limit: 最大返回数量，默认 10
    """
    if raw.get("status") != "1":
        return raw
    
    simplified = {
        "status": "1",
        "count": raw.get("count"),
        "info": raw.get("info"),
        "pois": []
    }
    
    # 建议信息
    if raw.get("suggestion"):
        simplified["suggestion"] = {
            "keywords": raw["suggestion"].get("keywords", []),
            "cities": [{"name": c.get("name"), "citycode": c.get("citycode"), "adcode": c.get("adcode")} 
                      for c in raw["suggestion"].get("cities", [])]
        }
    
    # POI 列表（精简）
    for poi in raw.get("pois", [])[:limit]:
        simplified["pois"].append({
            "id": poi.get("id"),
            "name": poi.get("name"),
            "type": poi.get("type"),
            "typecode": poi.get("typecode"),
            "address": poi.get("address"),
            "location": poi.get("location"),
            "distance": poi.get("distance"),
            "citycode": poi.get("citycode"),
            "adcode": poi.get("adcode"),
            "biz_ext": poi.get("biz_ext") if poi.get("extensions") == "all" else None,
        })
    
    return simplified


# ========================
# 行政区划输出精简
# ========================

def simplify_region_query(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    精简行政区划查询输出
    """
    if raw.get("status") != "1":
        return raw
    
    simplified = {
        "status": "1",
        "info": raw.get("info"),
        "districts": []
    }
    
    def extract_district(d: Dict) -> Dict:
        return {
            "name": d.get("name"),
            "citycode": d.get("citycode"),
            "adcode": d.get("adcode"),
            "center": d.get("center"),
            "level": d.get("level"),
            "sub_districts": [extract_district(sd) for sd in d.get("districts", [])]
        }
    
    for district in raw.get("districts", []):
        simplified["districts"].append(extract_district(district))
    
    return simplified


# ========================
# IP 定位输出精简
# ========================

def simplify_ip_positioning(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    精简 IP 定位输出
    """
    if raw.get("status") != "1":
        return raw
    
    result = raw.get("result", {})
    
    return {
        "status": "1",
        "info": raw.get("info"),
        "ip": result.get("ip"),
        "location": {
            "province": result.get("province"),
            "city": result.get("city"),
            "adcode": result.get("adcode"),
        },
        "bounds": result.get("rectangel")
    }


# ========================
# POI 周边搜索输出精简
# ========================

def simplify_poi_around(raw: Dict[str, Any], limit: int = 20) -> Dict[str, Any]:
    """
    精简 POI 周边搜索输出

    Args:
        raw: 原始响应
        limit: 最大返回数量，默认 20
    """
    if raw.get("status") != "1":
        return raw

    simplified = {
        "status": "1",
        "count": raw.get("count"),
        "info": raw.get("info"),
        "location": raw.get("location"),  # 搜索中心点
        "pois": []
    }

    # POI 列表（精简）
    for poi in raw.get("pois", [])[:limit]:
        simplified["pois"].append({
            "id": poi.get("id"),
            "name": poi.get("name"),
            "type": poi.get("type"),
            "typecode": poi.get("typecode"),
            "address": poi.get("address"),
            "location": poi.get("location"),
            "distance": poi.get("distance"),  # 距中心点的距离（米）
            "citycode": poi.get("citycode"),
            "adcode": poi.get("adcode"),
            "biz_ext": poi.get("biz_ext") if poi.get("extensions") == "all" else None,
        })

    return simplified


# ========================
# POI 多边形搜索输出精简
# ========================

def simplify_poi_polygon(raw: Dict[str, Any], limit: int = 20) -> Dict[str, Any]:
    """
    精简 POI 多边形搜索输出

    Args:
        raw: 原始响应
        limit: 最大返回数量，默认 20
    """
    if raw.get("status") != "1":
        return raw

    simplified = {
        "status": "1",
        "count": raw.get("count"),
        "info": raw.get("info"),
        "polygon": raw.get("polygon"),  # 搜索多边形
        "pois": []
    }

    # POI 列表（精简）
    for poi in raw.get("pois", [])[:limit]:
        simplified["pois"].append({
            "id": poi.get("id"),
            "name": poi.get("name"),
            "type": poi.get("type"),
            "typecode": poi.get("typecode"),
            "address": poi.get("address"),
            "location": poi.get("location"),
            "citycode": poi.get("citycode"),
            "adcode": poi.get("adcode"),
            "biz_ext": poi.get("biz_ext") if poi.get("extensions") == "all" else None,
        })

    return simplified


# ========================
# POI ID 查询输出精简
# ========================

def simplify_poi_detail(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    精简 POI ID 查询输出

    Args:
        raw: 原始响应
    """
    if raw.get("status") != "1":
        return raw

    poi = raw.get("poi", {})

    simplified = {
        "status": "1",
        "info": raw.get("info"),
        "poi": {
            "id": poi.get("id"),
            "name": poi.get("name"),
            "type": poi.get("type"),
            "typecode": poi.get("typecode"),
            "address": poi.get("address"),
            "location": poi.get("location"),
            "citycode": poi.get("citycode"),
            "adcode": poi.get("adcode"),
            "pname": poi.get("pname"),  # 所属省份
            "cityname": poi.get("cityname"),  # 所属城市
            "adname": poi.get("adname"),  # 所属区域
            "biz_ext": poi.get("biz_ext"),  # 扩展信息
        }
    }

    return simplified


# ========================
# AOI 边界查询输出精简
# ========================

def simplify_aoi_boundary(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    精简 AOI 边界查询输出

    Args:
        raw: 原始响应
    """
    if raw.get("status") != "1":
        return raw

    aoi = raw.get("aois", [{}])[0] if raw.get("aois") else {}

    simplified = {
        "status": "1",
        "info": raw.get("info"),
        "aoi": {
            "id": aoi.get("id"),
            "name": aoi.get("name"),
            "location": aoi.get("location"),  # 中心点经纬度
            "polyline": aoi.get("polyline"),  # 边界坐标串
            "type": aoi.get("type"),  # AOI 所属分类
            "typecode": aoi.get("typecode"),  # AOI 分类编码
            "pname": aoi.get("pname"),  # 所属省份
            "cityname": aoi.get("cityname"),  # 所属城市
            "adname": aoi.get("adname"),  # 所属区域
            "address": aoi.get("address"),  # 详细地址
        }
    }

    return simplified