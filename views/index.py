from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from utils.dc import Dc
from utils.ptero_api import Ptero, get_settings
from utils.db import get_db
import random
import string
import asyncio
import time

SETTING = get_settings()
ADD_TMP = {}
CHEAK_TMP = {}
dc = Dc(SETTING["oauth"]["bot_token"], webhook=SETTING["oauth"]["webhook"])
home = APIRouter(tags=["home"])
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])
db = get_db()
templates = Jinja2Templates(directory="templates")

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
        return RedirectResponse(url="/login", status_code=302)
    current_user = await dc.get_discord_user(access_token)
    
    if str(current_user.id) in ADD_TMP:
        if ADD_TMP[str(current_user.id)] - int(time.time()) > 0:
            await asyncio.sleep(3)
            return templates.TemplateResponse("msg.html", {
                "request": request,
                "message": "你按的有點快，等一下再試試吧",
                "href": False
            })
    ADD_TMP[str(current_user.id)] = int(time.time()) + 10
    
    servers = await ptero.search_all_data(email=current_user.email, u_id=current_user.id)
    now = servers["now"]
    resource = servers["resource"]
    
    if now["servers"] + 1 > resource["servers"]:
        return templates.TemplateResponse("msg.html", {
            "request": request,
            "message": "已達伺服器數量上限",
            "href": False
        })
    if cpu <= 0 or now["cpu"] + cpu > resource["cpu"]:
        return templates.TemplateResponse("msg.html", {
            "request": request,
            "message": "你沒有足夠的CPU",
            "href": False
        })
    if memory <= 0 or now["memory"] + memory > resource["memory"]:
        return templates.TemplateResponse("msg.html", {
            "request": request,
            "message": "你沒有足夠的記憶體",
            "href": False
        })
    if disk <= 0 or now["disk"] + disk > resource["disk"]:
        return templates.TemplateResponse("msg.html", {
            "request": request,
            "message": "你沒有足夠的空間",
            "href": False
        })

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
        return server
        
    await dc.notifly(
        title="創建伺服器",
        description=f"用戶：{current_user.username} ({current_user.id})\n> Name：{name}\n> CPU：{cpu}\n> Memory：{memory}\n> Disk{disk}\n> Node：{node}\n> Type：{egg}",
        img=current_user.avatar_url
    )
    return RedirectResponse(url="/", status_code=302)

@home.get("/server/del/{server_identifier}")
async def index_server_del(request: Request, server_identifier: str, check: str = Query(None)):
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/login", status_code=302)
    current_user = await dc.get_discord_user(access_token)
    
    if check:
        if server_identifier in CHEAK_TMP:
            if check == CHEAK_TMP[server_identifier]:
                servers = await ptero.search_all_data(current_user.email, current_user.id)
                servers = servers["server"]
                for i in servers:
                    if i == server_identifier:
                        await ptero.delete_server(i)
                        return templates.TemplateResponse("msg.html", {
                            "request": request,
                            "message": "刪除成功",
                            "href": "/"
                        })
                return templates.TemplateResponse("msg.html", {
                    "request": request,
                    "message": "伺服器不存在",
                    "href": "/"
                })
            else:
                return templates.TemplateResponse("msg.html", {
                    "request": request,
                    "message": "授權失敗",
                    "href": "/"
                })
        return templates.TemplateResponse("msg.html", {
            "request": request,
            "message": "授權失敗",
            "href": "/"
        })
    else:
        check_token = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
        CHEAK_TMP[server_identifier] = check_token
        return templates.TemplateResponse("del_check.html", {
            "request": request,
            "identifier": server_identifier,
            "token": check_token
        })

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
        return RedirectResponse(url="/login", status_code=302)
    current_user = await dc.get_discord_user(access_token)
    
    servers = await ptero.search_all_data(email=current_user.email, u_id=current_user.id)
    now = servers["now"]
    resource = servers["resource"]
    old_servers = None
    for i in servers["server"]:
        if i == server_identifier:
            old_servers = servers["server"][i]
            break
    if not old_servers:
        return templates.TemplateResponse("msg.html", {
            "request": request,
            "message": "伺服器不存在",
            "href": False
        })
    
    ptero_user_id = await ptero.search_user(current_user.email)
    ptero_user_id = ptero_user_id['id']

    if cpu <= 0 or now["cpu"] - old_servers["cpu"] + cpu > resource["cpu"]:
        return templates.TemplateResponse("msg.html", {
            "request": request,
            "message": "你沒有足夠的CPU",
            "href": False
        })
    if memory <= 0 or now["memory"] - old_servers["memory"] + memory > resource["memory"]:
        return templates.TemplateResponse("msg.html", {
            "request": request,
            "message": "你沒有足夠的記憶體",
            "href": False
        })
    if disk <= 0 or now["disk"] - old_servers["disk"] + disk > resource["disk"]:
        return templates.TemplateResponse("msg.html", {
            "request": request,
            "message": "你沒有足夠的空間",
            "href": False
        })
    
    await ptero.edit_server(
        server_identifier=server_identifier,
        server_memory=memory,
        server_cpu=cpu,
        server_disk=disk
    )
    return templates.TemplateResponse("msg.html", {
        "request": request,
        "message": "修改成功",
        "href": "/"
    })