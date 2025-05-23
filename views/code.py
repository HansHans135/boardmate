from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from utils.dc import Dc
from utils.db import get_db
from utils.ptero_api import Ptero, get_settings

SETTING = get_settings()
dc = Dc(SETTING["oauth"]["bot_token"], webhook=SETTING["oauth"]["webhook"])
home = APIRouter(tags=["code"])
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])
db = get_db()
templates = Jinja2Templates(directory="templates")

@home.get("/code")
async def codes_get(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/", status_code=302)
    current_user = await dc.get_discord_user(access_token)
    
    return templates.TemplateResponse("code.html", {"request": request, "user": current_user})

@home.post("/code")
async def codes_post(request: Request, code: str = Form(...)):
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/", status_code=302)
    current_user = await dc.get_discord_user(access_token)
    
    success, result = db.use_code(code, current_user.id)
    
    if not success:
        return templates.TemplateResponse("msg.html", {
            "request": request,
            "message": result,
            "href": "/code"
        })
        
    codes = db.get_codes()
    code_info = codes.get(code, {})
    code_usage = len(code_info.get("user", []))
    code_limit = code_info.get("use", 0)
    
    await dc.notifly(
        title="兌換代碼",
        description=f"用戶：{current_user.username} ({current_user.id})\n代碼：{code} (已使用 {code_usage}/{code_limit})",
        img=f"{SETTING['oauth']['url']}static/notifly/code.png"
    )
    return templates.TemplateResponse("msg.html", {
        "request": request,
        "message": "兌換成功",
        "href": "/"
    })
