from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from utils.dc import Dc
from utils.ptero_api import Ptero, get_settings
from utils.db import get_db

SETTING = get_settings()
dc = Dc(SETTING["oauth"]["bot_token"], webhook=SETTING["oauth"]["webhook"])
home = APIRouter(tags=["shop"])
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])
db = get_db()
templates = Jinja2Templates(directory="templates")

@home.get("/shop")
async def shop(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/", status_code=302)
    current_user = await dc.get_discord_user(access_token)
    
    user_data = db.get_user(current_user.id)
    money = user_data["money"] if user_data else 0
    
    return templates.TemplateResponse("shop.html", {
        "request": request,
        "money": money,
        "user": current_user,
        "shop": SETTING["shop"]
    })

@home.post("/shop/{mode}")
async def shopmode(request: Request, mode: str):
    access_token = request.session.get("access_token")
    if not access_token:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "請先登入"}
        )
    
    current_user = await dc.get_discord_user(access_token)
    
    user_data = db.get_user(current_user.id)
    if not user_data:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "找不到用戶資料"}
        )
    
    # 動態接收表單數據
    form = await request.form()
    form_dict = dict(form)
    
    nmode = mode
    if mode == "servers":
        nmode = "server"
    
    try:
        value = int(form_dict[mode])
        item_cost = SETTING["shop"][nmode][form_dict[mode]]
        
        if item_cost <= user_data["money"]:
            new_money = user_data["money"] - item_cost
            updates = {"money": new_money}
            updates[mode] = user_data["resource"][mode] + value
            
            db.update_user(current_user.id, **updates)
            
            await dc.notifly(
                title="商店購買",
                description=f"用戶：{current_user.username} ({current_user.id})\n品項：{nmode} - {form_dict[mode]}",
                img=current_user.avatar_url
            )
            
            return JSONResponse(content={
                "success": True,
                "message": f"成功購買 {form_dict[mode]} {nmode}！",
                "new_money": new_money
            })
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "你沒有足夠的錢錢"}
            )
    except (KeyError, ValueError) as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "無效的購買選項"}
        )
