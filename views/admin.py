from datetime import datetime
import hashlib
from urllib.parse import urlencode

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from utils.dc import Dc
from utils.ptero_api import Ptero, get_settings
from utils.db import get_db

SETTING = get_settings()
ADD_TMP={}
CHEAK_TMP={}
dc=Dc(SETTING["oauth"]["bot_token"],webhook=SETTING["oauth"]["webhook"])
home = APIRouter(prefix="/admin", tags=["admin"])
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])
db = get_db()
templates = Jinja2Templates(directory="templates")

async def statistics_all():
    users = await ptero.get_users()
    servers = await ptero.get_servers()
    codes = len(db.get_codes())
    logs = len(db.get_logs())
    return {"users": len(users), "servers": len(servers), "codes": codes, "apis": logs}

@home.get("/")
async def admin_home(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        return templates.TemplateResponse("login.html", {"request": request})
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:
        return RedirectResponse(url="/", status_code=302)
        
    user = await ptero.search_user(current_user.email)
    all_users = {}
    all_ptero_users = await ptero.get_users()
    
    db_users = db.get_all_users()
    
    for dc_id, user_data in db_users.items():
        for ptero_user in all_ptero_users:
            if ptero_user["attributes"]["id"] == user_data["id"]:
                email = ptero_user["attributes"]["email"]
                username = ptero_user["attributes"]["username"]
                break
                
        all_users[dc_id] = {
            "id": user_data["id"],
            "money": user_data["money"],
            "email": email,
            "name": username,
            "resource": {
                "memory": user_data["resource"]["memory"] / 1024,
                "cpu": user_data["resource"]["cpu"],
                "disk": user_data["resource"]["disk"] / 1024,
                "servers": user_data["resource"]["servers"]
            }
        }
        
        # 生成 Gravatar URL
        email_encoded = email.lower().encode('utf-8')
        email_hash = hashlib.sha256(email_encoded).hexdigest()
        query_params = urlencode({'s': str(40)})
        all_users[dc_id]["avatar"] = f"https://www.gravatar.com/avatar/{email_hash}?{query_params}"
    
    statistics = await statistics_all()
    return templates.TemplateResponse("admin/index.html", {
        "request": request,
        "user": current_user,
        "user_data": all_users,
        "statistics": statistics
    })

@home.get("/code")
async def admin_code_get(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        return templates.TemplateResponse("login.html", {"request": request})
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:
        return RedirectResponse(url="/", status_code=302)
        
    codes = db.get_codes()
    statistics = await statistics_all()
    
    return templates.TemplateResponse("admin/code.html", {
        "request": request,
        "user": current_user,
        "codes": codes,
        "statistics": statistics
    })

@home.post("/code")
async def admin_code_post(request: Request, name: str = Form(...), times: int = Form(...), money: int = Form(...)):
    access_token = request.session.get("access_token")
    if not access_token:
        return templates.TemplateResponse("login.html", {"request": request})
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:
        return RedirectResponse(url="/", status_code=302)
        
    db.add_code(name, times, money)
    await dc.notifly(
        title="創建代碼",
        description=f"用戶：{current_user.username} ({current_user.id})\n新增 {name} 成功 (可用 {times} 次/可取得 {money} $)",
        img=current_user.avatar_url
    )
    return templates.TemplateResponse("msg.html", {
        "request": request,
        "message": f"新增 {name} 成功 (可用 {times} 次/可取得 {money} $)",
        "href": "/admin/code"
    })

@home.get("/code/del/{code}")
async def admin_code_del(request: Request, code: str):
    access_token = request.session.get("access_token")
    if not access_token:
        return templates.TemplateResponse("login.html", {"request": request})
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:
        return RedirectResponse(url="/", status_code=302)
        
    db.delete_code(code)
    await dc.notifly(
        title="刪除代碼",
        description=f"用戶：{current_user.username} ({current_user.id})\n代碼：{code}",
        img=current_user.avatar_url
    )
    return templates.TemplateResponse("msg.html", {
        "request": request,
        "message": f"刪除 {code} 成功",
        "href": "/admin/code"
    })

@home.get("/log")
async def admin_log(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        return templates.TemplateResponse("login.html", {"request": request})
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:
        return RedirectResponse(url="/", status_code=302)
        
    statistics = await statistics_all()
    logs = db.get_logs()
    
    for log in logs:
        log["time"] = datetime.utcfromtimestamp(log["time"])
        
    return templates.TemplateResponse("admin/log.html", {
        "request": request,
        "user": current_user,
        "logs": logs,
        "statistics": statistics
    })

@home.get("/setting")
async def admin_setting_get(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        return templates.TemplateResponse("login.html", {"request": request})
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:
        return RedirectResponse(url="/", status_code=302)
        
    statistics = await statistics_all()
    return templates.TemplateResponse("admin/setting.html", {
        "request": request,
        "user": current_user,
        "setting": SETTING,
        "statistics": statistics
    })

@home.post("/setting")
async def admin_setting_post(request: Request, memory: int = Form(...), cpu: int = Form(...), disk: int = Form(...), admins: str = Form(...)):
    access_token = request.session.get("access_token")
    if not access_token:
        return templates.TemplateResponse("login.html", {"request": request})
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:
        return RedirectResponse(url="/", status_code=302)
        
    SETTING['server']['default_resource']['memory'] = memory
    SETTING['server']['default_resource']['cpu'] = cpu
    SETTING['server']['default_resource']['disk'] = disk
    SETTING['boardmate']['admins'] = []
    for admin in admins.split("\n"):
        if admin.strip():
            SETTING['boardmate']['admins'].append(admin.strip())
    
    await dc.notifly(
        title="更新設定",
        description=f"用戶：{current_user.username} ({current_user.id})",
        img=current_user.avatar_url
    )
    return templates.TemplateResponse("msg.html", {
        "request": request,
        "message": "設定成功，請重啟套用",
        "href": "/admin/setting"
    })