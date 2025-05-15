from flask import Blueprint, jsonify, redirect, session, render_template, request
from utils.dc import Dc
from utils.ptero_api import Ptero, get_settings
from utils.db import get_db
import json
import asyncio
import subprocess

SETTING = get_settings()
dc = Dc(SETTING["oauth"]["bot_token"], webhook=SETTING["oauth"]["webhook"])
home = Blueprint("shop", __name__)
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])
db = get_db()

@home.route("/shop")
async def shop():
    access_token = session.get("access_token")
    if not access_token:
        return redirect("/")
    current_user = await dc.get_discord_user(access_token)
    
    user_data = db.get_user(current_user.id)
    money = user_data["money"] if user_data else 0
    
    return render_template("shop.html", money=money, user=current_user, shop=SETTING["shop"])


@home.route("/shop/<mode>", methods=["POST"])
async def shopmode(mode):
    access_token = session.get("access_token")
    if not access_token:
        return redirect(f"/")
    current_user = await dc.get_discord_user(access_token)
    
    user_data = db.get_user(current_user.id)
    if not user_data:
        return render_template("msg.html", message="找不到用戶資料", href=False)
    
    nmode = mode
    if mode == "servers":
        nmode = "server"
    
    value = int(request.form[mode])
    item_cost = SETTING["shop"][nmode][request.form[mode]]
    
    if item_cost <= user_data["money"]:
        # 更新資料
        updates = {"money": user_data["money"] - item_cost}
        updates[mode] = user_data["resource"][mode] + value
        
        db.update_user(current_user.id, **updates)
        
        await dc.notifly(
            title="商店購買",
            description=f"用戶：{current_user.username} ({current_user.id})\n品項：{nmode} - {request.form[mode]}",
            img=current_user.avatar_url
        )
        return render_template("msg.html", message="購買成功！", href="/shop")
    else:
        return render_template("msg.html", message="你沒有足夠的錢錢", href=False)
