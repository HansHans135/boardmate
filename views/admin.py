import random
import string
from flask import Blueprint, jsonify, redirect, session, render_template
from utils.dc import Dc
from utils.ptero_api import Ptero
import json
import asyncio
import hashlib
from urllib.parse import urlencode
import time
from flask import request

SETTING = json.load(open("setting.json", "r", encoding="utf-8"))
ADD_TMP={}
CHEAK_TMP={}
dc = Dc(SETTING["oauth"]["bot_token"])
home = Blueprint("admin", __name__)
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])

async def statistics_all():
    users=await ptero.get_users()
    servers=await ptero.get_servers()
    with open("data/code.json", "r", encoding="utf-8") as f:
        codes = len(json.load(f))
    return {"users":len(users),"servers":len(servers),"codes":codes}

@home.route("/admin")
async def admin_home():
    access_token = session.get("access_token")
    if not access_token:
        return render_template("login.html")
    current_user = await dc.get_discord_user(access_token)
    user=await ptero.search_user(current_user.email)
    with open("data/user.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    all_ptero_user=await ptero.get_users()
    for i in data:
        for e in all_ptero_user:
            if e["attributes"]["id"]==data[i]["id"]:
                ptero_user=e["attributes"]
                break
        data[i]["email"]=ptero_user["email"]
        data[i]["name"]=ptero_user["username"]
        data[i]["resource"]["memory"]=data[i]["resource"]["memory"]/1024
        data[i]["resource"]["disk"]=data[i]["resource"]["disk"]/1024
        email = data[i]["email"]
        size = 40
        email_encoded = email.lower().encode('utf-8')
        email_hash = hashlib.sha256(email_encoded).hexdigest()
        query_params = urlencode({'s': str(size)})
        gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?{query_params}"
        data[i]["avatar"]=gravatar_url
    statistics=await statistics_all()
    return render_template("admin/index.html", user=current_user,user_data=data,statistics=statistics)
