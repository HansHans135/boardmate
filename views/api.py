import random
import string
from fastapi import APIRouter, HTTPException, Request, Form, Query
from fastapi.responses import JSONResponse, RedirectResponse
from utils.dc import Dc
from utils.ptero_api import Ptero, get_settings
from utils.db import get_db
import json
import os
import time

SETTING = get_settings()
dc = Dc(SETTING["oauth"]["bot_token"], webhook=SETTING["oauth"]["webhook"])
home = APIRouter(prefix="/api", tags=["api"])
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])
db = get_db()

@home.get("/servers")
async def api_get_servers(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/", status_code=302)
    current_user = await dc.get_discord_user(access_token)
    data = await ptero.search_all_data(current_user.email, current_user.id)
    return JSONResponse(content=data)

@home.get("/user/{dc_user_id}")
async def api_user_get(dc_user_id: str, key: str = Query(...)):
    if key != db.get_api_key():
        raise HTTPException(status_code=403, detail={"code": 403, "message": "API Key錯誤"})
    
    user_data = db.get_user(dc_user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "未找到此用戶"})
    
    ptero_user_list = await ptero.get_users()
    ptero_id = user_data['id']
    user_email = None
    
    for i in ptero_user_list:
        try:
            if i["attributes"]["id"] == ptero_id:
                user_email = i["attributes"]['email']
        except:
            pass
    
    data = await ptero.search_all_data(user_email, dc_user_id)
    db.add_log(f"搜尋用戶 {dc_user_id}")
    return JSONResponse(content=data)

@home.post("/user/{dc_user_id}")
async def api_user_post(
    dc_user_id: str, 
    key: str = Form(...),
    money: int = Form(None),
    memory: int = Form(None),
    disk: int = Form(None),
    cpu: int = Form(None),
    servers: int = Form(None)
):
    if key != db.get_api_key():
        raise HTTPException(status_code=403, detail={"code": 403, "message": "API Key錯誤"})
    
    user_data = db.get_user(dc_user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "未找到此用戶"})
    
    updates = {}
    if money is not None:
        updates["money"] = money
    if memory is not None:
        updates["memory"] = memory
    if disk is not None:
        updates["disk"] = disk
    if cpu is not None:
        updates["cpu"] = cpu
    if servers is not None:
        updates["servers"] = servers
    
    # 更新用戶資料
    db.update_user(dc_user_id, **updates)
    
    # 構建回應資料
    re_data = {
        "money": updates.get("money", user_data['money']),
        "resource": {
            "memory": updates.get("memory", user_data["resource"]['memory']),
            "disk": updates.get("disk", user_data["resource"]['disk']),
            "cpu": updates.get("cpu", user_data["resource"]['cpu']),
            "servers": updates.get("servers", user_data["resource"]['servers'])
        }
    }
    
    db.add_log(f"編輯用戶 {dc_user_id} : {re_data}")
    return JSONResponse(content=re_data, status_code=200)

@home.get("/code")
async def api_code_get(key: str = Query(...)):
    if key != db.get_api_key():
        raise HTTPException(status_code=403, detail={"code": 403, "message": "API Key錯誤"})
    
    db.add_log(f"查詢代碼")
    return JSONResponse(content=db.get_codes())

@home.post("/code")
async def api_code_post(key: str = Form(...), code: str = Form(...), use: int = Form(...), money: int = Form(...)):
    if key != db.get_api_key():
        raise HTTPException(status_code=403, detail={"code": 403, "message": "API Key錯誤"})
    
    result = db.add_code(code, use, money)
    db.add_log(f"新增/編輯代碼 {code} 可使用{use}次 可獲得{money}$")
    return JSONResponse(content=result, status_code=200)

@home.delete("/code")
async def api_code_delete(key: str = Form(...), code: str = Form(...)):
    if key != db.get_api_key():
        raise HTTPException(status_code=403, detail={"code": 403, "message": "API Key錯誤"})
    
    success = db.delete_code(code)
    if not success:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "未找到此代碼"})
    
    db.add_log(f"刪除代碼 {code}")
    return JSONResponse(content={"code": 200, "message": "刪除成功"}, status_code=200)
