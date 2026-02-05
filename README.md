# 🌐 Amap MCP Server

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Protocol-orange.svg)](https://modelcontextprotocol.io/)
[![Version](https://img.shields.io/badge/Version-0.1.0-yellow.svg)](https://pypi.org/project/amap-mcp/)

> 🗺️ **高德地图 MCP (Model Context Protocol) 服务器** - 为 AI 智能体提供完整的地理信息服务和路线规划功能

基于 Model Context Protocol (MCP) 协议的高德地图服务集成，支持地理编码、路线规划、POI搜索等核心功能，专为 AI 智能体和 LLM 应用设计。

## ✨ 核心特性

| 功能模块 | 描述 | 工具数量 |
|---------|------|---------|
| 🗺️ **地理编码** | 地址与坐标相互转换 | 2 |
| 🚗 **路线规划** | 驾车/步行/骑行/公交/地铁 | 6 |
| 🔍 **POI搜索** | 关键字/周边/多边形/详情查询 | 4 |
| 🏛️ **行政区划** | 城市区域层级查询 | 1 |
| 🌐 **IP定位** | 基于IP的地理位置 | 1 |
| 📍 **AOI边界** | 兴趣区域边界查询 | 1 |

**总计：15+ 个专业工具**

---

## 🚀 快速开始

### 1️⃣ 安装依赖

```bash
# 使用 pip
pip install -r requirements.txt

# 使用 uv (推荐，更快)
uv pip install -r requirements.txt
```

### 2️⃣ 配置环境变量

**方式一：复制配置文件（推荐）**

```bash
# 复制环境变量模板
cp .env.example .env
# 编辑 .env 文件，填入您的 API Key
```

**方式二：直接创建 .env 文件**

创建 `.env` 文件并配置高德 API 密钥：

```env
# ========== 必需配置 ==========
# 高德地图 Web 服务 API Key
# 获取地址：https://lbs.amap.com/dev/
AMAP_API_KEY=your_amap_api_key_here

# ========== API 地址配置（可选，使用默认值） ==========
# 地理编码
AMAP_GEO_URL=https://restapi.amap.com/v3/geocode/geo
AMAP_REGEO_URL=https://restapi.amap.com/v3/geocode/regeo

# 路线规划
AMAP_DRIVING_URL=https://restapi.amap.com/v5/direction/driving
AMAP_WALKING_URL=https://restapi.amap.com/v5/direction/walking
AMAP_BICYCLING_URL=https://restapi.amap.com/v5/direction/bicycling
AMAP_EBIKE_URL=https://restapi.amap.com/v5/direction/electrobike
AMAP_BUS_URL=https://restapi.amap.com/v5/direction/transit/integrated
AMAP_SUBWAY_TRANSIT=https://restapi.amap.com/v5/direction/transit/integrated

# POI 搜索
AMAP_SEARCH_POI_URL=https://restapi.amap.com/v5/place/text
AMAP_SEARCH_POI_AROUND_URL=https://restapi.amap.com/v5/place/around
AMAP_SEARCH_POI_POLYGON_URL=https://restapi.amap.com/v5/place/polygon
AMAP_SEARCH_POI_DETAIL_URL=https://restapi.amap.com/v5/place/detail
AMAP_AOI_POLYLINE_URL=https://restapi.amap.com/v5/aoi/polyline

# 行政区划 & IP
AMAP_REGION_QUERY_URL=https://restapi.amap.com/v3/config/district
AMAP_IP_URL=https://restapi.amap.com/v3/ip

# ========== 日志配置（可选） ==========
# 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
# AMAP_LOG_LEVEL=INFO
# 日志文件路径
# AMAP_LOG_FILE=amap_mcp.log
```

### 3️⃣ 获取 API 密钥

1. 访问 [高德开放平台](https://lbs.amap.com/dev/)
2. 注册/登录账号
3. 创建应用 → 选择「Web服务」
4. 获取 API Key

### 4️⃣ 启动服务

```bash
# 方式1: 直接运行 MCP 服务器
python amap_mcp.py

# 方式2: 使用 MCP CLI
mcp run amap_mcp.py
```

---

## 🔧 MCP Server 集成配置

### Claude Desktop / Cursor 等 MCP 客户端

在 MCP 客户端配置文件中添加：

```json
{
  "mcpServers": {
    "amap-mcp-server": {
      "transport": "stdio",
      "command": "python",
      "args": ["D:\\mycode\\travelagent\\amap_mcp\\amap_mcp.py"],
      "env": {
        "AMAP_API_KEY": "your_amap_api_key_here"
      }
    }
  }
}
```

### 环境变量配置（推荐）

```json
{
  "mcpServers": {
    "amap-mcp-server": {
      "transport": "stdio",
      "command": "python",
      "args": ["D:\\mycode\\travelagent\\amap_mcp\\amap_mcp.py"]
    }
  }
}
```

配合 `.env` 文件使用：

```env
AMAP_API_KEY=your_amap_api_key_here
```

### Linux/macOS 路径示例

```json
{
  "mcpServers": {
    "amap-mcp-server": {
      "transport": "stdio",
      "command": "python",
      "args": ["/home/user/travelagent/amap_mcp/amap_mcp.py"]
    }
  }
}
```

---

## 📚 API 工具列表

### 📍 地理编码

| 工具名称 | 功能描述 | 输入示例 |
|---------|---------|---------|
| `geocoding` | 地址转坐标 | `{"address": "北京市朝阳区阜通东大街6号"}` |
| `reverse_geocoding` | 坐标转地址 | `{"location": "116.481488,39.990464"}` |

### 🚗 路线规划

| 工具名称 | 功能描述 | 策略选项 |
|---------|---------|---------|
| `driving_route_planning` | 驾车路线 | 速度优先/费用最低/距离最短/推荐路线 |
| `walking_route_planning` | 步行路线 | 室内外路线规划 |
| `bicycling_route_planning` | 骑行路线 | 自行车专用路线 |
| `elect_bike_route_planning` | 电动车路线 | 续航/充电站优化 |
| `public_transit_route_planning` | 公交路线 | 地铁/公交/换乘方案 |
| `amap_route_subway` | 地铁路线 | 城市地铁换乘 |

### 🔍 POI 搜索

| 工具名称 | 功能描述 |
|---------|---------|
| `search_poi` | 关键字搜索 POI |
| `search_poi_around` | 周边 POI 搜索 |
| `search_poi_polygon` | 多边形区域 POI 搜索 |
| `search_poi_detail` | POI 详情查询 |
| `search_aoi_boundary` | AOI 边界查询 |

### 🏛️ 行政区划 & IP

| 工具名称 | 功能描述 |
|---------|---------|
| `administrative_region_query` | 行政区划查询 |
| `ip_positioning` | IP 定位 |

---

## 💡 使用示例

### Python 示例

```python
import asyncio
from amap_mcp import geocoding, driving_route_planning

async def travel_planner():
    """智能行程规划示例"""
    
    # 1️⃣ 地址转坐标
    address_result = await geocoding({
        "address": "北京市朝阳区望京soho",
        "city": "北京"
    })
    origin = address_result["data"]["location"]
    
    # 2️⃣ 获取目的地坐标
    dest_result = await geocoding({
        "address": "上海浦东新区陆家嘴",
        "city": "上海"
    })
    destination = dest_result["data"]["location"]
    
    # 3️⃣ 规划驾车路线
    route = await driving_route_planning({
        "origin": origin,
        "destination": destination,
        "strategy": 32,  # 推荐路线
        "show_fields": "cost,navi"
    })
    
    # 4️⃣ 输出路线信息
    print(f"总距离: {route['data']['summary']['distance']}米")
    print(f"预计时间: {route['data']['summary']['duration']}秒")
    
    return route

# 运行
asyncio.run(travel_planner())
```

### MCP Client 示例

```python
from mcp import Client

async def use_amap_mcp():
    async with Client("amap_mcp.py") as client:
        # 地理编码
        result = await client.call_tool(
            "geocoding",
            {"address": "杭州市西湖区"}
        )
        print(result)
        
        # POI搜索
        pois = await client.call_tool(
            "search_poi",
            {"keywords": "美食", "page_size": 5}
        )
        return pois
```

---

## ⚙️ 环境配置

### 完整环境变量

```env
# ========== 必需 ==========
AMAP_API_KEY=your_api_key_here

# ========== 地理编码 ==========
AMAP_GEO_URL=https://restapi.amap.com/v3/geocode/geo
AMAP_REGEO_URL=https://restapi.amap.com/v3/geocode/regeo

# ========== 路线规划 ==========
AMAP_DRIVING_URL=https://restapi.amap.com/v5/direction/driving
AMAP_WALKING_URL=https://restapi.amap.com/v5/direction/walking
AMAP_BICYCLING_URL=https://restapi.amap.com/v5/direction/bicycling
AMAP_EBIKE_URL=https://restapi.amap.com/v5/direction/electrobike
AMAP_BUS_URL=https://restapi.amap.com/v5/direction/transit/integrated
AMAP_SUBWAY_TRANSIT=https://restapi.amap.com/v5/direction/transit/integrated

# ========== POI搜索 ==========
AMAP_SEARCH_POI_URL=https://restapi.amap.com/v3/place/text
AMAP_SEARCH_POI_AROUND_URL=https://restapi.amap.com/v5/place/around
AMAP_SEARCH_POI_POLYGON_URL=https://restapi.amap.com/v5/place/polygon
AMAP_SEARCH_POI_DETAIL_URL=https://restapi.amap.com/v5/place/detail
AMAP_AOI_POLYLINE_URL=https://restapi.amap.com/v5/aoi/polyline

# ========== 行政区划 & IP ==========
AMAP_REGION_QUERY_URL=https://restapi.amap.com/v3/config/district
AMAP_IP_URL=https://restapi.amap.com/v3/ip
```

---

## 🛠️ 开发指南

### 项目结构

```
amap_mcp/
├── amap_mcp.py          # MCP 服务器主入口
├── models.py            # 数据模型定义
├── config.py            # 配置和工具函数
├── output.py           # 响应格式化处理
├── main.py             # IP 查询服务入口
├── amap_enum.py        # API 地址枚举
├── config_log.py       # 日志配置
├── requirements.txt    # 依赖列表
├── pyproject.toml      # 项目配置
├── README.md           # 项目文档
└── utils/              # 工具函数
```

### 添加新工具

```python
from mcp.server.fastmcp import FastMCP
from config import get_api_key, validate_location_format

mcp = FastMCP(name="amap-mcp")

@mcp.tool(name="custom_tool")
async def custom_function(param: str) -> dict:
    """
    自定义工具描述
    
    Args:
        param: 参数描述
        
    Returns:
        标准化响应
    """
    # 1. 获取 API Key
    api_key = get_api_key()
    
    # 2. 构建请求参数
    params = {"key": api_key, "param": param}
    
    # 3. 发起请求（使用 httpx）
    # 4. 处理响应
    
    return {"status": 1, "data": {...}}
```

### 运行测试

```bash
# 运行所有测试
pytest test_amap_mcp.py -v

# 运行特定测试
pytest test_amap_mcp.py::test_geocoding -v

# 生成覆盖率报告
pytest --cov=amap_mcp test_amap_mcp.py
```

---

## 📊 响应格式

所有 API 返回统一格式：

```json
{
  "status": 1,
  "data": {...},
  "error": null,
  "info": "OK"
}
```

**错误响应：**

```json
{
  "status": 0,
  "data": null,
  "error": "详细错误信息",
  "info": "请求失败"
}
```

---

## 🧪 测试覆盖

本项目包含完整的测试用例：

```python
# 地理编码测试
pytest test_amap_mcp.py -k "geocoding"

# 路线规划测试
pytest test_amap_mcp.py -k "route"

# POI搜索测试
pytest test_amap_mcp.py -k "poi"

# 完整测试套件
pytest test_amap_mcp.py -v --tb=short
```

---

## 🤝 贡献指南

1. **Fork** 本项目
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 创建 **Pull Request**

### 开发规范

- 使用 `black` 格式化代码
- 运行 `mypy` 进行类型检查
- 添加必要的测试用例
- 更新相关文档

---

## 📚 相关文档

| 资源 | 链接 |
|------|------|
| 高德开放平台 | https://lbs.amap.com/ |
| 地理编码 API | https://lbs.amap.com/api/webservice/guide/api/geocode |
| 路线规划 API | https://lbs.amap.com/api/webservice/guide/api/newroute |
| POI 搜索 API | https://lbs.amap.com/api/webservice/guide/api/search |
| MCP 协议文档 | https://modelcontextprotocol.io/ |
| FastMCP 框架 | https://github.com/modelcontextprotocol/servers/tree/main/src/fastmcp |

---

## 📄 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。

---

## 🙏 致谢

- [高德地图](https://lbs.amap.com/) - 提供优质的地图 API 服务
- [Model Context Protocol](https://modelcontextprotocol.io/) - 标准化的 AI 工具协议
- [FastMCP](https://github.com/modelcontextprotocol/servers) - 快速 MCP 服务器框架

---

## ❓ 常见问题

**Q: API 调用频率限制？**
> A: 高德地图 Web 服务 API 免费用户：30万次/天

**Q: 坐标系说明？**
> A: 高德地图使用 GCJ-02 坐标系（国测局坐标）

**Q: 如何获取高德 POI 类型代码？**
> A: 参考 [POI 分类代码表](https://lbs.amap.com/api/webservice/download)

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给它一个 Star！**

</div>
