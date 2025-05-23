import aiohttp
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from utils.dc import Dc
from utils.db import get_db
from utils.ptero_api import get_settings

home = APIRouter(tags=['oauth'])
SETTING = get_settings()
dc = Dc(SETTING["oauth"]["bot_token"], webhook=SETTING["oauth"]["webhook"])
db = get_db()

@home.get("/oauth/callback")
async def oauth_callback(request: Request, code: str = Query(...)):
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': SETTING["oauth"]["id"],
        'client_secret': SETTING["oauth"]["client_secret"],
        'redirect_uri': f'{SETTING["oauth"]["url"]}oauth/callback'
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://discord.com/api/oauth2/token", data=payload) as response:
            token_data = await response.json()
    access_token = token_data.get('access_token')
    current_user = await dc.get_discord_user(access_token)

    db.ensure_user_exists(current_user.id)

    if SETTING["boardmate"]["account_sharing"] == False:
        user_id_cookie = request.cookies.get("user_id")
        if str(user_id_cookie) != "None":
            if str(user_id_cookie) != str(current_user.id):
                await dc.notifly(title="分帳登入通知",description=f"用戶：{current_user.username}\nID：{current_user.id}\nEmail：{current_user.email}\n\n上次使用的帳號：<@{user_id_cookie}>",img=current_user.avatar_url)
                raise HTTPException(status_code=403, detail={"status":"error","message":"不允許的操作"})
        
    request.session["access_token"] = access_token
    await dc.notifly(title="登入通知",description=f"用戶：{current_user.username}\nID：{current_user.id}\nEmail：{current_user.email}",img=current_user.avatar_url)

    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie("user_id", str(current_user.id), httponly=True, secure=True)
    return response

@home.get("/login")
async def login():
    url = SETTING["oauth"]["url"]
    id = SETTING["oauth"]["id"]
    return RedirectResponse(url=f"https://discord.com/api/oauth2/authorize?client_id={id}&redirect_uri={url}oauth/callback&response_type=code&scope=identify%20guilds%20email", status_code=302)

@home.get("/logout")
async def logout(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/", status_code=302)
    current_user = await dc.get_discord_user(access_token)
    await dc.notifly(title="登出通知",description=f"用戶：{current_user.username}\nID：{current_user.id}\nEmail：{current_user.email}",img=current_user.avatar_url)
    request.session.pop("access_token", None)
    return RedirectResponse(url="/", status_code=302)


