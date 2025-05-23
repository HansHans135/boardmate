# app.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from utils.ptero_api import Ptero, get_settings
from utils.db import get_db
import os
import asyncio
import json
import secrets

try_fix=0
app = FastAPI()
SETTING = get_settings()

# 添加會話中間件
secret_key = (SETTING["oauth"]["client_secret"]*2)[5:25]
app.add_middleware(SessionMiddleware, secret_key=secret_key)

# 掛載靜態檔案（如果需要）
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

ptero=Ptero(SETTING["pterodactyl"]["key"],SETTING["pterodactyl"]["url"])

# 初始化資料庫
db = get_db()

if SETTING["boardmate"]["recache"]:
    print("> 正在啟動緩存")
    asyncio.run(ptero.get_servers(use_cache=False))
    print(f"  L 伺服器")
    asyncio.run(ptero.get_users(use_cache=False))
    print(f"  L 用戶")
    for i in SETTING["server"]["node"]:
        asyncio.run(ptero.get_allocations(SETTING["server"]["node"][i],use_cache=False))
        print(f"  L 節點 {i}")
    print("> 已啟動緩存")
else:
    print("> 已跳過緩存")


@app.exception_handler(404)
async def error_404(request: Request, exc: HTTPException):
    return HTMLResponse(content="頁面不存在", status_code=404)

@app.exception_handler(400)
async def error_400(request: Request, exc: HTTPException):
    return JSONResponse(content={"code": 400, "message": "資料有誤"}, status_code=400)

@app.exception_handler(500)
async def error_500(request: Request, exc: HTTPException):
    cache_error=False
    try:
        try_server=await ptero.get_servers()
        for i in try_server:
            i["attributes"]
    except:
        cache_error=True
        await ptero.get_servers(use_cache=False)
    try:
        try_user=await ptero.get_users()
        for i in try_user:
            i["attributes"]
    except:
        cache_error=True
        await ptero.get_users(use_cache=False)
    try:
        for i in SETTING["server"]["node"]:
            await ptero.get_allocations(SETTING["server"]["node"][i], use_cache=False)
    except:
        cache_error=True
        for i in SETTING["server"]["node"]:
            await ptero.get_allocations(SETTING["server"]["node"][i], use_cache=False)
    if cache_error:
        return JSONResponse(content={"status":"fixed","message":f"伺服器發生錯誤，已嘗試修復，請重整頁面"}, status_code=200)
    else:
        return JSONResponse(content={"status":"error","message":f"伺服器發生錯誤，請連絡管理員"}, status_code=200)

print("> 正在註冊檔案")
views_dir = os.path.join(os.path.dirname(__file__), 'views')
for filename in os.listdir(views_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        module_name = filename[:-3]
        module = __import__(f'views.{module_name}', fromlist=['*'])
        print(f"  L {module_name}.py")
        if hasattr(module, 'home'):
            # FastAPI 使用 include_router 而不是 register_blueprint
            app.include_router(module.home)
print("> 已註冊檔案")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SETTING["boardmate"]["host"], port=SETTING["boardmate"]["port"])
