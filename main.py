"""
IP 查询服务 - FastAPI 应用
"""

from fastapi import FastAPI, Request

app = FastAPI()


def get_real_ip(request: Request) -> str:
    """获取用户真实IP（支持代理、支持 Cloudflare、支持 Nginx）"""
    cf_ip = request.headers.get("Cf-Connecting-Ip")
    if cf_ip:
        return cf_ip
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    xri = request.headers.get("X-Real-IP")
    if xri:
        return xri
    return request.client.host


@app.get("/ip")
async def get_ip(request: Request):
    ip = get_real_ip(request)
    return {"client_ip": ip}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app="main:app", port=8889, reload=True, log_level="debug")
