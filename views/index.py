import asyncio
import random
import string
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from utils.dc import Dc
from utils.db import get_db
from utils.ptero_api import Ptero, get_settings

SETTING = get_settings()
ADD_TMP = {}
CHEAK_TMP = {}
dc = Dc(SETTING["oauth"]["bot_token"], webhook=SETTING["oauth"]["webhook"])
home = APIRouter(tags=["home"])
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])
db = get_db()
templates = Jinja2Templates(directory="templates")

class RateLimitManager:
    def __init__(self):
        self.limits: Dict[str, Dict[str, float]] = {}
        self.cleanup_interval = 300
        self.last_cleanup = time.time()
    
    def _cleanup_expired(self):
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            for user_id in list(self.limits.keys()):
                user_limits = self.limits[user_id]
                expired_actions = [
                    action for action, expire_time in user_limits.items()
                    if expire_time <= current_time
                ]
                for action in expired_actions:
                    del user_limits[action]
                if not user_limits:
                    del self.limits[user_id]
            self.last_cleanup = current_time
    
    def is_rate_limited(self, user_id: str, action: str, cooldown_seconds: int = 10) -> tuple[bool, Optional[int]]:
        self._cleanup_expired()
        current_time = time.time()
        
        if user_id not in self.limits:
            self.limits[user_id] = {}
        
        if action in self.limits[user_id]:
            remaining_time = self.limits[user_id][action] - current_time
            if remaining_time > 0:
                return True, int(remaining_time)
        
        self.limits[user_id][action] = current_time + cooldown_seconds
        return False, None
    
    def get_remaining_time(self, user_id: str, action: str) -> Optional[int]:
        if user_id not in self.limits or action not in self.limits[user_id]:
            return None
        
        remaining = self.limits[user_id][action] - time.time()
        return max(0, int(remaining))

rate_limiter = RateLimitManager()

@home.get("/")
async def index_home(request: Request, passwd: str = Query(None)):
    access_token = request.session.get("access_token")
    if not access_token:
        return templates.TemplateResponse("login.html", {"request": request})
    current_user = await dc.get_discord_user(access_token)
    user = await ptero.search_user(current_user.email)
    
    if user is None:
        user_data = await ptero.create_user(current_user.email, current_user.id)
        db.ensure_user_exists(str(current_user.id), user_data["id"])
    else:
        db.ensure_user_exists(str(current_user.id), user["id"])
        
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "user": current_user,
        "passwd": passwd
    })

@home.get("/rpa")
async def index_rpa(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/", status_code=302)
    current_user = await dc.get_discord_user(access_token)
    user = await ptero.search_user(current_user.email)
    user_data = await ptero.edit_user(username=current_user.id, u_id=user["id"], email=current_user.email)
    await dc.notifly(title="重設密碼", description=f"用戶：{current_user.username} ({current_user.id})\n密碼：||{user_data['password']}||", img=current_user.avatar_url)
    return RedirectResponse(url=f"/?passwd={user_data['password']}", status_code=302)

@home.get("/server/add")
async def index_server_add_get(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/login", status_code=302)
    current_user = await dc.get_discord_user(access_token)
    
    return templates.TemplateResponse("add.html", {
        "request": request,
        "user": current_user,
        "eggs": SETTING["server"]["eggs"],
        "nodes": SETTING["server"]["node"]
    })

@home.post("/server/add")
async def index_server_add_post(
    request: Request,
    name: str = Form(...),
    memory: int = Form(...),
    cpu: int = Form(...),
    disk: int = Form(...),
    node: str = Form(...),
    egg: str = Form(...)
):
    access_token = request.session.get("access_token")
    if not access_token:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "未登入，請重新登入"}
        )
    
    current_user = await dc.get_discord_user(access_token)
    
    is_limited, remaining_time = rate_limiter.is_rate_limited(
        str(current_user.id), 
        "create_server", 
        cooldown_seconds=10
    )
    
    if is_limited:
        return JSONResponse(
            status_code=429,
            content={
                "success": False, 
                "message": f"操作過於頻繁，請等待 {remaining_time} 秒後再試",
                "remaining_time": remaining_time
            }
        )
    
    servers = await ptero.search_all_data(email=current_user.email, u_id=current_user.id)
    now = servers["now"]
    resource = servers["resource"]
    
    if now["servers"] + 1 > resource["servers"]:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "已達伺服器數量上限"}
        )
    if cpu <= 0 or now["cpu"] + cpu > resource["cpu"]:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "你沒有足夠的CPU"}
        )
    if memory <= 0 or now["memory"] + memory > resource["memory"]:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "你沒有足夠的記憶體"}
        )
    if disk <= 0 or now["disk"] + disk > resource["disk"]:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "你沒有足夠的空間"}
        )
    max_resource = SETTING['server']['eggs'][egg]["max_resource"]

    if disk > max_resource['disk'] and max_resource['disk'] != 0:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"超過空間上限（最高 {max_resource['disk']} MB）"}
        )
    if cpu > max_resource['cpu'] and max_resource['cpu'] != 0:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"超過 CPU 上限（最高 {max_resource['cpu']} %）"}
        )
    if memory > max_resource['memory'] and max_resource['memory'] != 0:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"超過記憶體上限（最高 {max_resource['memory']} MB）"}
        )
    

    ptero_user = await ptero.search_user(current_user.email)
    server = await ptero.create_server(
        ptero_user_id=ptero_user["id"],
        server_name=name,
        server_memory=memory,
        server_cpu=cpu,
        server_disk=disk,
        server_node=node,
        server_egg=egg
    )
    
    if "errors" in server:
        if str(current_user.id) in rate_limiter.limits:
            rate_limiter.limits[str(current_user.id)].pop("create_server", None)
        
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "創建伺服器時發生錯誤，請稍後再試"}
        )
        
    await dc.notifly(
        title="創建伺服器",
        description=f"用戶：{current_user.username} ({current_user.id})\n> Name：{name}\n> CPU：{cpu}\n> Memory：{memory}\n> Disk：{disk}\n> Node：{node}\n> Type：{egg}",
        img=current_user.avatar_url
    )
    
    return JSONResponse(
        status_code=200,
        content={"success": True, "message": f"伺服器 '{name}' 創建成功！"}
    )

@home.post("/server/del/{server_identifier}")
async def index_server_del_post(request: Request, server_identifier: str):
    """安全的 POST 刪除伺服器端點"""
    access_token = request.session.get("access_token")
    if not access_token:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "未登入，請重新登入"}
        )
    
    current_user = await dc.get_discord_user(access_token)
    
    is_limited, remaining_time = rate_limiter.is_rate_limited(
        str(current_user.id), 
        "delete_server", 
        cooldown_seconds=5
    )
    
    if is_limited:
        return JSONResponse(
            status_code=429,
            content={
                "success": False, 
                "message": f"操作過於頻繁，請等待 {remaining_time} 秒後再試",
                "remaining_time": remaining_time
            }
        )
    
    current_user = await dc.get_discord_user(access_token)
    
    try:
        servers = await ptero.search_all_data(current_user.email, current_user.id)
        server_found = False
        server_name = ""
        
        for sid, server_info in servers["server"].items():
            if sid == server_identifier:
                server_found = True
                server_name = server_info.get("name", "未知伺服器")
                break
        
        if not server_found:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "伺服器不存在或您沒有權限刪除此伺服器"}
            )
        
        await ptero.delete_server(server_identifier)
        
        await dc.notifly(
            title="刪除伺服器",
            description=f"用戶：{current_user.username} ({current_user.id})\n> 伺服器：{server_name}\n> ID：{server_identifier}",
            img=current_user.avatar_url
        )
        
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": f"伺服器 '{server_name}' 已成功刪除"}
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "刪除伺服器時發生錯誤，請稍後再試"}
        )

@home.get("/server/edit/{server_identifier}")
async def index_server_edit_get(request: Request, server_identifier: str):
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/login", status_code=302)
    current_user = await dc.get_discord_user(access_token)
    
    servers = await ptero.search_all_data(email=current_user.email, u_id=current_user.id)
    server_info = None
    
    for i in servers["server"]:
        if i == server_identifier:
            server_info = servers["server"][i]
            break
            
    if not server_info:
        return templates.TemplateResponse("msg.html", {
            "request": request,
            "message": "伺服器不存在",
            "href": "/"
        })
    
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "user": current_user,
        "server": server_info,
        "identifier": server_identifier
    })

@home.post("/server/edit/{server_identifier}")
async def index_server_edit_post(
    request: Request,
    server_identifier: str,
    memory: int = Form(...),
    cpu: int = Form(...),
    disk: int = Form(...)
):
    access_token = request.session.get("access_token")
    if not access_token:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "未登入，請重新登入"}
        )
    current_user = await dc.get_discord_user(access_token)
    
    is_limited, remaining_time = rate_limiter.is_rate_limited(
        str(current_user.id), 
        "edit_server", 
        cooldown_seconds=5
    )
    
    if is_limited:
        return JSONResponse(
            status_code=429,
            content={
                "success": False, 
                "message": f"操作過於頻繁，請等待 {remaining_time} 秒後再試",
                "remaining_time": remaining_time
            }
        )
    
    servers = await ptero.search_all_data(email=current_user.email, u_id=current_user.id)
    now = servers["now"]
    resource = servers["resource"]
    old_servers = None
    for i in servers["server"]:
        if i == server_identifier:
            old_servers = servers["server"][i]
            break
    if not old_servers:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "伺服器不存在"}
        )
    
    ptero_user_id = await ptero.search_user(current_user.email)
    ptero_user_id = ptero_user_id['id']

    if cpu <= 0 or now["cpu"] - old_servers["cpu"] + cpu >= resource["cpu"]:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "你沒有足夠的CPU"}
        )
    if memory <= 0 or now["memory"] - old_servers["memory"] + memory >= resource["memory"]:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "你沒有足夠的記憶體"}
        )
    if disk <= 0 or now["disk"] - old_servers["disk"] + disk >= resource["disk"]:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "你沒有足夠的空間"}
        )
    
    await ptero.edit_server(
        server_identifier=server_identifier,
        server_memory=memory,
        server_cpu=cpu,
        server_disk=disk
    )
    return JSONResponse(
        status_code=200,
        content={"success": True, "message": "修改成功"}
    )