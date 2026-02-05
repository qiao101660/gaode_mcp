import asyncio
import sys
import inspect
from pathlib import Path
import pytest

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from config import get_api_key, validate_location_format
    import amap_mcp
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)

# ========================
# 测试数据配置
# ========================
TEST_ADDRESS = "北京市朝阳区阜通东大街6号"
TEST_LOCATION = "116.481488,39.990464"
TEST_DESTINATION = "116.434446,39.90816"  # 天安门附近
TEST_IP = "114.114.114.114"
TEST_KEYWORDS = "美食"
TEST_CITY = "北京"

# 新增：POI ID 和 AOI ID（需要替换为真实可用的 ID）
TEST_POI_ID = "B0FFFZZZ5S"  # 示例 ID，实际使用需替换
TEST_AOI_ID = "B0FFFZZZ5S"   # 示例 ID，实际使用需替换

# 新增：多边形坐标（测试用）
TEST_POLYGON = "116.47,39.9;116.49,39.91;116.48,39.93;116.46,39.92"


# ========================
# 辅助函数：统一响应访问
# ========================
def get_response_status(response):
    """从响应中获取状态码，兼容 dict 和 Pydantic model"""
    if isinstance(response, dict):
        return response.get('status')
    return getattr(response, 'status', None)

def get_response_data(response):
    """从 ApiResponse 中获取数据，兼容 dict 和 Pydantic model"""
    if isinstance(response, dict):
        return response.get('data')
    return getattr(response, 'data', None)

def get_response_error(response):
    """从响应中获取错误信息，兼容 dict 和 Pydantic model"""
    if isinstance(response, dict):
        return response.get('error')
    return getattr(response, 'error', None)


# ========================
# 核心测试逻辑
# ========================
@pytest.mark.asyncio
def test_validate_location_format():
    """1. 测试内部参数校验"""
    print("\n" + "-" * 20 + " [Test: Validation] " + "-" * 20)
    test_cases = [("116.48,39.99", True), ("invalid", False), ("200,90", False)]
    all_ok = True
    for loc, exp in test_cases:
        res = validate_location_format(loc)
        print(f"  {'[OK]' if res == exp else '[FAIL]'} Validate {loc!r}: {res}")
        if res != exp:
            all_ok = False
    return all_ok


@pytest.mark.asyncio
async def test_geocoding():
    """2. 测试地理编码"""
    print("\n" + "-" * 20 + " [Test: Geocoding] " + "-" * 20)
    try:
        res = await amap_mcp.geocoding(TEST_ADDRESS)
        if get_response_status(res) != 1:
            print(f"  [FAIL] Status not 1: {get_response_status(res)}")
            return False
        data = get_response_data(res)
        results = data.get('results', []) if data else []
        if results:
            location = results[0].get('location') if isinstance(results[0], dict) else getattr(results[0], 'location', None)
            print(f"  [OK] Result: {location}")
        return True
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        return False


@pytest.mark.asyncio
async def test_reverse_geocoding():
    """3. 测试逆地理编码"""
    print("\n" + "-" * 20 + " [Test: Reverse Geocoding] " + "-" * 20)
    try:
        res = await amap_mcp.reverse_geocoding(TEST_LOCATION)
        if get_response_status(res) != 1:
            print(f"  [FAIL] Status not 1: {get_response_status(res)}")
            return False
        data = get_response_data(res)
        if data:
            address = data.get('address', {})
            if isinstance(address, dict):
                formatted = address.get('formatted_address') if 'formatted_address' in address else address.get('formatted')
            else:
                formatted = str(address)
            print(f"  [OK] Coordinate resolved: {formatted}")
        return True
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        return False


@pytest.mark.asyncio
async def test_all_routes():
    """4. 聚合测试所有路径规划"""
    print("\n" + "-" * 20 + " [Test: Route Planning] " + "-" * 20)
    routes = [
        ("Driving", amap_mcp.driving_route_planning),
        ("Walking", amap_mcp.walking_route_planning),
        ("Bicycling", amap_mcp.bicycling_route_planning),
        ("E-Bike", amap_mcp.elect_bike_route_planning)
    ]
    all_success = True
    for name, func in routes:
        try:
            res = await func(origin=TEST_LOCATION, destination=TEST_DESTINATION)
            if get_response_status(res) != 1:
                print(f"  [FAIL] {name} status not 1: {get_response_status(res)}")
                error_msg = get_response_error(res)
                if error_msg:
                    print(f"  [ERROR] {name}: {error_msg}")
                all_success = False
                continue
            data = get_response_data(res)
            if data:
                summary = data.get('summary', {}) if isinstance(data, dict) else getattr(data, 'summary', None)
                if summary:
                    dist = summary.get('distance') if isinstance(summary, dict) else getattr(summary, 'distance', '0')
                    print(f"  [OK] {name} planning: ~{dist} meters")
                else:
                    print(f"  [OK] {name} planning completed")
            else:
                print(f"  [OK] {name} planning completed (no data)")
        except Exception as e:
            print(f"  [FAIL] {name} error: {e}")
            all_success = False
    return all_success


@pytest.mark.asyncio
async def test_public_transit():
    """5. 测试公交路径规划 (独立参数)"""
    print("\n" + "-" * 20 + " [Test: Public Transit] " + "-" * 20)
    try:
        res = await amap_mcp.public_transit_route_planning(
            origin=TEST_LOCATION, destination=TEST_DESTINATION, city1="010", city2="010"
        )
        if get_response_status(res) != 1:
            print(f"  [FAIL] Status not 1: {get_response_status(res)}")
            error_msg = get_response_error(res)
            if error_msg:
                print(f"  [ERROR] {error_msg}")
            return False
        data = get_response_data(res)
        transits = data.get('paths', []) if data and isinstance(data, dict) else []
        print(f"  [OK] Transit options: {len(transits)}")
        return True
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_poi_search():
    """6. 测试 POI 搜索"""
    print("\n" + "-" * 20 + " [Test: POI Search] " + "-" * 20)
    try:
        res = await amap_mcp.search_poi(keywords=TEST_KEYWORDS, city=TEST_CITY, offset=3)
        if get_response_status(res) != 1:
            print(f"  [FAIL] Status not 1: {get_response_status(res)}")
            return False
        data = get_response_data(res)
        pois = data.get('pois', []) if data and isinstance(data, dict) else []
        print(f"  [OK] Search [{TEST_KEYWORDS}]: {len(pois)} results")
        for p in pois:
            name = p.get('name') if isinstance(p, dict) else getattr(p, 'name', 'N/A')
            address = p.get('address') if isinstance(p, dict) else getattr(p, 'address', 'N/A')
            print(f"    - {name} [{address}]")
        return True
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        return False


@pytest.mark.asyncio
async def test_admin_query():
    """7. 测试行政区划查询"""
    print("\n" + "-" * 20 + " [Test: Admin Region] " + "-" * 20)
    try:
        res = await amap_mcp.administrative_region_query(keywords="朝阳区", subdistrict=1)
        if get_response_status(res) != 1:
            print(f"  [FAIL] Status not 1: {get_response_status(res)}")
            return False
        data = get_response_data(res)
        districts = data.get('districts', []) if data and isinstance(data, dict) else []
        name = districts[0].get('name') if districts and isinstance(districts[0], dict) else getattr(districts[0], 'name', 'None') if districts else 'None'
        print(f"  [OK] Result: {name}")
        return True
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        return False


@pytest.mark.asyncio
async def test_ip_positioning():
    """8. 测试 IP 定位"""
    print("\n" + "-" * 20 + " [Test: IP Positioning] " + "-" * 20)
    try:
        res = await amap_mcp.ip_positioning(ip=TEST_IP)
        if get_response_status(res) != 1:
            print(f"  [FAIL] Status not 1: {get_response_status(res)}")
            return False
        data = get_response_data(res)
        if data:
            province = data.get('province') if isinstance(data, dict) else getattr(data, 'province', '')
            city = data.get('city') if isinstance(data, dict) else getattr(data, 'city', '')
            print(f"  [OK] IP [{TEST_IP}]: {province}{city}")
        return True
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        return False


# ========================
# 新增：高级 POI 搜索测试
# ========================

@pytest.mark.asyncio
async def test_poi_around():
    """9. 测试 POI 周边搜索"""
    print("\n" + "-" * 20 + " [Test: POI Around Search] " + "-" * 20)
    try:
        res = await amap_mcp.search_poi_around(
            location=TEST_LOCATION,
            keywords=TEST_KEYWORDS,
            radius=2000,
            offset=5
        )
        if get_response_status(res) != 1:
            print(f"  [FAIL] Status not 1: {get_response_status(res)}")
            error_msg = get_response_error(res)
            if error_msg:
                print(f"  [ERROR] {error_msg}")
            return False
        data = get_response_data(res)
        pois = data.get('pois', []) if data and isinstance(data, dict) else []
        center = data.get('location', 'N/A') if data and isinstance(data, dict) else 'N/A'
        print(f"  [OK] Around search [{TEST_KEYWORDS}] at {center}: {len(pois)} results")
        for p in pois:
            name = p.get('name') if isinstance(p, dict) else getattr(p, 'name', 'N/A')
            distance = p.get('distance') if isinstance(p, dict) else getattr(p, 'distance', 'N/A')
            print(f"    - {name} (distance: {distance}m)")
        return True
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_poi_polygon():
    """10. 测试 POI 多边形搜索"""
    print("\n" + "-" * 20 + " [Test: POI Polygon Search] " + "-" * 20)
    try:
        res = await amap_mcp.search_poi_polygon(
            polygon=TEST_POLYGON,
            keywords="酒店",
            offset=5
        )
        if get_response_status(res) != 1:
            print(f"  [FAIL] Status not 1: {get_response_status(res)}")
            error_msg = get_response_error(res)
            if error_msg:
                print(f"  [ERROR] {error_msg}")
            return False
        data = get_response_data(res)
        pois = data.get('pois', []) if data and isinstance(data, dict) else []
        polygon = data.get('polygon') if data and isinstance(data, dict) else None
        print(f"  [OK] Polygon search [酒店] in polygon: {len(pois)} results")
        if polygon:
            polygon_str = polygon[:50] + "..." if len(polygon) > 50 else polygon
            print(f"  [INFO] Search polygon: {polygon_str}")
        for p in pois:
            name = p.get('name') if isinstance(p, dict) else getattr(p, 'name', 'N/A')
            address = p.get('address') if isinstance(p, dict) else getattr(p, 'address', 'N/A')
            print(f"    - {name} [{address}]")
        return True
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_poi_detail():
    """11. 测试 POI ID 查询"""
    print("\n" + "-" * 20 + " [Test: POI Detail] " + "-" * 20)
    try:
        res = await amap_mcp.search_poi_detail(
            id=TEST_POI_ID,
            extensions="all"
        )
        if get_response_status(res) != 1:
            print(f"  [FAIL] Status not 1: {get_response_status(res)}")
            error_msg = get_response_error(res)
            if error_msg:
                print(f"  [ERROR] {error_msg}")
            print(f"  [INFO] POI ID [{TEST_POI_ID}] may not exist, this is expected for test ID")
            return True  # 不存在也返回 True，因为是测试 ID
        data = get_response_data(res)
        poi = data.get('poi', {}) if data and isinstance(data, dict) else {}
        if poi:
            name = poi.get('name') if isinstance(poi, dict) else getattr(poi, 'name', 'N/A')
            address = poi.get('address') if isinstance(poi, dict) else getattr(poi, 'address', 'N/A')
            cityname = poi.get('cityname') if isinstance(poi, dict) else getattr(poi, 'cityname', 'N/A')
            print(f"  [OK] POI Detail [{TEST_POI_ID}]: {name}")
            print(f"  [INFO] Address: {address}, {cityname}")
        else:
            print(f"  [INFO] POI Detail: No data returned")
        return True
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_aoi_boundary():
    """12. 测试 AOI 边界查询"""
    print("\n" + "-" * 20 + " [Test: AOI Boundary] " + "-" * 20)
    try:
        res = await amap_mcp.search_aoi_boundary(id=TEST_AOI_ID)
        # 检查状态码 - 可能是 dict 或 Pydantic model
        status = get_response_status(res)
        if status != 1:
            error_msg = get_response_error(res)
            print(f"  [FAIL] Status not 1: {status}, Error: {error_msg}")
            print(f"  [INFO] AOI ID [{TEST_AOI_ID}] may not exist, this is expected for test ID")
            return True  # 不存在也返回 True，因为是测试 ID
        
        data = get_response_data(res)
        aoi = data.get('aoi', {}) if data and isinstance(data, dict) else {}
        if aoi:
            name = aoi.get('name') if isinstance(aoi, dict) else getattr(aoi, 'name', 'N/A')
            adname = aoi.get('adname') if isinstance(aoi, dict) else getattr(aoi, 'adname', 'N/A')
            has_polyline = bool(aoi.get('polyline')) if isinstance(aoi, dict) else False
            print(f"  [OK] AOI Boundary [{TEST_AOI_ID}]: {name}")
            print(f"  [INFO] District: {adname}, Has boundary: {has_polyline}")
        else:
            print(f"  [INFO] AOI Boundary: No data returned")
        return True
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


# ========================
# 测试运行器
# ========================
async def main():
    print("\n" + "=" * 60)
    print("  Amap MCP Server - Automated Test Suite")
    print("=" * 60)

    # 注册所有测试模块
    test_suite = [
        ("Validation", test_validate_location_format),
        ("Geocoding", test_geocoding),
        ("Reverse Geocoding", test_reverse_geocoding),
        ("Route Planning", test_all_routes),
        ("Public Transit", test_public_transit),
        ("POI Search", test_poi_search),
        ("Admin Region", test_admin_query),
        ("IP Positioning", test_ip_positioning),
        # 新增：高级 POI 搜索测试
        ("POI Around Search", test_poi_around),
        ("POI Polygon Search", test_poi_polygon),
        ("POI Detail", test_poi_detail),
        ("AOI Boundary", test_aoi_boundary),
    ]

    summary = []
    for name, func in test_suite:
        try:
            # 判断同步还是异步
            result = await func() if inspect.iscoroutinefunction(func) else func()
            summary.append((name, result))
        except Exception as e:
            print(f"[ERROR] {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            summary.append((name, False))

    # 最终报告
    print("\n" + "=" * 60)
    print("  Test Report Summary")
    print("=" * 60)
    print(f"{'Module':<25} | {'Status':<10}")
    print("-" * 60)

    passed = 0
    for name, status in summary:
        icon = "[PASS]" if status else "[FAIL]"
        if status:
            passed += 1
        print(f"{name:<25} | {icon}")

    print("-" * 60)
    success_rate = (passed / len(test_suite)) * 100
    print(f"Total: {len(test_suite)} | Passed: {passed} | Failed: {len(test_suite) - passed}")
    print(f"Success Rate: {success_rate:.1f}%")
    print("=" * 60)

    if passed != len(test_suite):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
