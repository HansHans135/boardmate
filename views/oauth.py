from flask import Blueprint, jsonify, request, url_for, redirect, session as flask_session
from utils.dc import Dc
import aiohttp
import json
import discord

home = Blueprint('oauth', __name__)
SETTING = json.load(open("setting.json", "r", encoding="utf-8"))
dc=Dc(SETTING["oauth"]["bot_token"],webhook=SETTING["oauth"]["webhook"])

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
    flask_session["access_token"] = access_token
    current_user = await dc.get_discord_user(access_token)
    await dc.notifly(title="登入通知",description=f"用戶：{current_user.username}\nID：{current_user.id}\nEmail：{current_user.email}",img=current_user.avatar_url)
    return redirect("/")


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


