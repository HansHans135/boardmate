from flask import Blueprint, jsonify, redirect, session, render_template, request
from utils.dc import Dc
from utils.ptero_api import Ptero
import json
import asyncio
import subprocess

SETTING = json.load(open("setting.json", "r", encoding="utf-8"))
dc=Dc(SETTING["oauth"]["bot_token"],webhook=SETTING["oauth"]["webhook"])
home = Blueprint("shop", __name__)
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])


@home.route("/shop")
async def shop():
    access_token = session.get("access_token")
    if not access_token:
        return redirect("/")
    current_user = await dc.get_discord_user(access_token)
    with open(f"data/user.json", "r")as f:
        data = json.load(f)
    money = data[str(current_user.id)]["money"]
    return render_template("shop.html", money=money, user=current_user, shop=SETTING["shop"])


@home.route("/shop/<mode>", methods=["POST"])
async def shopmode(mode):
    access_token = session.get("access_token")
    if not access_token:
        return redirect(f"/")
    current_user = await dc.get_discord_user(access_token)
    with open(f"data/user.json", "r")as f:
        data = json.load(f)
    nmode = mode
    if mode == "servers":
        nmode = "server"
    if SETTING["shop"][nmode][request.form[mode]] <= data[str(current_user.id)]["money"]:
        data[str(current_user.id)]["money"] -= SETTING["shop"][nmode][request.form[mode]]
        data[str(current_user.id)]["resource"][mode] += int(request.form[mode])
        with open(f"data/user.json", "w")as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        await dc.notifly(title="商店購買",description=f"用戶：{current_user.username} ({current_user.id})\n品項：{nmode} - {request.form[mode]}",img=current_user.avatar_url)
        return render_template("msg.html", message="購買成功！", href="/shop")
    else:
        return render_template("msg.html", message="你沒有足夠的錢錢", href=False)
