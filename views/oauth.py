from flask import Blueprint, jsonify, request, url_for, redirect,make_response, session as flask_session
from utils.dc import Dc
from utils.ptero_api import get_settings
from utils.db import get_db
import aiohttp
import json
import discord

home = Blueprint('oauth', __name__)
SETTING = get_settings()
dc = Dc(SETTING["oauth"]["bot_token"], webhook=SETTING["oauth"]["webhook"])
db = get_db()

@home.route("/oauth/callback")
async def oauth_callback():
    payload = {
        'grant_type': 'authorization_code',
        'code': request.args["code"],
        'client_id': SETTING["oauth"]["id"],
        'client_secret': SETTING["oauth"]["client_secret"],
        'redirect_uri': f'{SETTING["oauth"]["url"]}oauth/callback'
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://discord.com/api/oauth2/token", data=payload) as response:
            token_data = await response.json()
    access_token = token_data.get('access_token')
    current_user = await dc.get_discord_user(access_token)

    # 確保用戶存在於資料庫
    db.ensure_user_exists(current_user.id)

    if SETTING["boardmate"]["account_sharing"] == False:
        if str(request.cookies.get("user_id")) != "None":
            if str(request.cookies.get("user_id")) != str(current_user.id):
                await dc.notifly(title="分帳登入通知",description=f"用戶：{current_user.username}\nID：{current_user.id}\nEmail：{current_user.email}\n\n上次使用的帳號：<@{request.cookies.get('user_id')}>",img=current_user.avatar_url)
                return jsonify({"status":"error","message":f"不允許的操作"}),403
        
    flask_session["access_token"] = access_token
    await dc.notifly(title="登入通知",description=f"用戶：{current_user.username}\nID：{current_user.id}\nEmail：{current_user.email}",img=current_user.avatar_url)

    response = make_response(redirect("/"))
    response.set_cookie("user_id", str(current_user.id), httponly=True, secure=True)  # 設定為 httponly 並啟用 secure
    return response


@home.route("/login")
async def login():
    url = SETTING["oauth"]["url"]
    id = SETTING["oauth"]["id"]
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={id}&redirect_uri={url}oauth/callback&response_type=code&scope=identify%20guilds%20email")


@home.route("/logout")
async def logout():
    access_token = flask_session.get("access_token")
    if not access_token:
        return redirect("/")
    current_user = await dc.get_discord_user(access_token)
    await dc.notifly(title="登出通知",description=f"用戶：{current_user.username}\nID：{current_user.id}\nEmail：{current_user.email}",img=current_user.avatar_url)
    flask_session.pop("access_token")
    return redirect("/")


