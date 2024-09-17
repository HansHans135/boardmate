import random
import string
from flask import Blueprint, jsonify, redirect, session, render_template,request
from utils.dc import Dc
from utils.ptero_api import Ptero
import json
import asyncio
import hashlib
from urllib.parse import urlencode

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
    with open("data/api.txt", "r", encoding="utf-8") as f:
        apis = len(f.read().splitlines())-1
    return {"users":len(users),"servers":len(servers),"codes":codes,"apis":apis}

@home.route("/admin")
async def admin_home():
    access_token = session.get("access_token")
    if not access_token:
        return render_template("login.html")
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:return redirect("/")
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
        email = ptero_user["email"]
        size = 40
        email_encoded = email.lower().encode('utf-8')
        email_hash = hashlib.sha256(email_encoded).hexdigest()
        query_params = urlencode({'s': str(size)})
        gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?{query_params}"
        data[i]["avatar"]=gravatar_url
    statistics=await statistics_all()
    return render_template("admin/index.html", user=current_user,user_data=data,statistics=statistics)

@home.route("/admin/code", methods=["POST", "GET"])
async def admin_code():
    access_token = session.get("access_token")
    if not access_token:
        return render_template("login.html")
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:return redirect("/")
    with open("data/code.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    for i in data:
        data[i]["len"]=len(data[i]["user"])
    statistics=await statistics_all()
    if request.method == "POST":
        name=request.form["name"]
        times=request.form["times"]
        money=request.form["money"]
        data[name]={
            "user":[],
            "use":int(times),
            "money":int(money)
        }
        with open("data/code.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return render_template("msg.html", message=f"新增 {name} 成功 (可用 {times} 次/可取得 {money} $)", href="/admin/code")
    return render_template("admin/code.html", user=current_user,codes=data,statistics=statistics)

@home.route("/admin/code/del/<code>")
async def admin_code_del(code):
    access_token = session.get("access_token")
    if not access_token:
        return render_template("login.html")
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:return redirect("/")
    with open("data/code.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    data.pop(code)
    with open("data/code.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return render_template("msg.html", message=f"刪除 {code} 成功", href="/admin/code")

@home.route("/admin/setting", methods=["POST", "GET"])
async def admin_setting():
    access_token = session.get("access_token")
    if not access_token:
        return render_template("login.html")
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:return redirect("/")
    statistics=await statistics_all()
    if request.method == "POST":
        SETTING['server']['default_resource']['memory']=int(request.form.get("memory"))
        SETTING['server']['default_resource']['cpu']=int(request.form.get("cpu"))
        SETTING['server']['default_resource']['disk']=int(request.form.get("disk"))
        SETTING['boardmate']['admins']=[]
        for i in request.form.get("admins").split("\n"):
            if i.replace("\r","")!="":
                SETTING['boardmate']['admins'].append(i.replace("\r",""))
        with open("setting.json", "w", encoding="utf-8") as f:
            json.dump(SETTING, f, ensure_ascii=False, indent=4)
        return render_template("msg.html", message="設定成功，請重啟套用", href="/admin/setting")
    return render_template("admin/setting.html", user=current_user,setting=SETTING,statistics=statistics)