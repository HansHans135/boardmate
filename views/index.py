import random
import string
from flask import Blueprint, jsonify, redirect, session, render_template
from utils.dc import Dc
from utils.ptero_api import Ptero
import json
import asyncio
import threading
import time
from flask import request

SETTING = json.load(open("setting.json", "r", encoding="utf-8"))
ADD_TMP={}
CHEAK_TMP={}
dc=Dc(SETTING["oauth"]["bot_token"],webhook=SETTING["oauth"]["webhook"])
home = Blueprint("home", __name__)
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])


@home.route("/")
async def index_home():
    access_token = session.get("access_token")
    if not access_token:
        return render_template("login.html")
    current_user = await dc.get_discord_user(access_token)
    user=await ptero.search_user(current_user.email)
    with open("data/user.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    if user==None:
        user_data=await ptero.create_user(current_user.email, current_user.id)
        uid=user_data["id"]
        data[str(current_user.id)] = {
            "id": uid,
            "money": 0,
            "resource": {
                "memory": 0,
                "disk": 0,
                "cpu": 0,
                "servers": 0
            }
        }
        with open("data/user.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    elif current_user.id not in data:
        uid = user["id"]
        data[str(current_user.id)] = {
            "id": uid,
            "money": 0,
            "resource": {
                "memory": 0,
                "disk": 0,
                "cpu": 0,
                "servers": 0
            }
        }
        with open("data/user.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    return render_template("index.html", user=current_user)


@home.route("/rpa")
async def index_rpa():
    access_token = session.get("access_token")
    if not access_token:
        return redirect("/")
    current_user = await dc.get_discord_user(access_token)
    user=await ptero.search_user(current_user.email)
    user_data=await ptero.edit_user(username=current_user.id,u_id=user["id"],email=current_user.email)
    await dc.notifly(title="重設密碼",description=f"用戶：{current_user.username} ({current_user.id})\n密碼：||{user_data['password']}||",img=current_user.avatar_url)
    return redirect(f"/?passwd={user_data['password']}")

@home.route("/server/add", methods=["GET", "POST"])
async def index_server_add():
    access_token = session.get("access_token")
    if not access_token:
        return redirect("/login")
    current_user = await dc.get_discord_user(access_token)
    if request.method == "POST":
        if str(current_user.id) in ADD_TMP:
            if ADD_TMP[str(current_user.id)]-int(time.time())>0:
                await asyncio.sleep(3)
                return render_template("msg.html",message="你按的有點快，等一下再試試吧",href=False)
        ADD_TMP[str(current_user.id)]=int(time.time())+10
        server_name = request.form["name"]
        server_memory = int(request.form["memory"])
        server_cpu = int(request.form["cpu"])
        server_disk = int(request.form["disk"])
        server_node = request.form["node"]
        server_egg = request.form["egg"]
        ptero_user_id = await ptero.search_user(current_user.email)
        ptero_user_id = ptero_user_id['id']
        servers = await ptero.search_all_data(email=current_user.email, u_id=current_user.id)
        now = servers["now"]
        resource = servers["resource"]
        if now["servers"]+1 > resource["servers"]:
            return render_template("msg.html", message="已達伺服器數量上限",href=False)
        if server_cpu <= 0 or now["cpu"]+server_cpu > resource["cpu"]:
            return render_template("msg.html", message="你沒有足夠的CPU",href=False)
        if server_memory <= 0 or now["memory"]+server_memory > resource["memory"]:
            return render_template("msg.html", message="你沒有足夠的記憶體",href=False)
        if server_disk <= 0 or now["disk"]+server_disk > resource["disk"]:
            return render_template("msg.html", message="你沒有足夠的空間",href=False)

        server = await ptero.create_server(
            ptero_user_id=ptero_user_id,
            server_name=server_name,
            server_memory=server_memory,
            server_cpu=server_cpu,
            server_disk=server_disk,
            server_node=server_node,
            server_egg=server_egg
        )
        await dc.notifly(title="創建伺服器",description=f"用戶：{current_user.username} ({current_user.id})\n> Name：{server_name}\n> CPU：{server_cpu}\n> Memory：{server_memory}\n> Disk{server_disk}\n> Node：{server_node}\n> Type：{server_egg}",img=current_user.avatar_url)
        return redirect("/")
    return render_template("add.html", user=current_user, eggs=SETTING["server"]["eggs"], nodes=SETTING["server"]["node"])


@home.route("/server/del/<server_identifier>", methods=["GET"])
async def index_server_del(server_identifier):
    access_token = session.get("access_token")
    if not access_token:
        return redirect("/login")
    current_user = await dc.get_discord_user(access_token)
    if request.values.get("check"):
        if server_identifier in CHEAK_TMP:
            if request.values.get("check")==CHEAK_TMP[server_identifier]:
                servers = await ptero.search_all_data(current_user.email, current_user.id)
                servers = servers["server"]
                for i in servers:
                    if i == server_identifier:
                        await ptero.delete_server(i)
                        return render_template("msg.html",message="刪除成功",href="/")
                return render_template("msg.html", message="伺服器不存在",href="/")
            else:
                return render_template("msg.html",message="授權失敗",href="/")
        return render_template("msg.html",message="授權失敗",href="/")
    else:
        check_token=''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
        CHEAK_TMP[server_identifier]=check_token
        return render_template("del_check.html",identifier=server_identifier,token=check_token)

@home.route("/server/edit/<server_identifier>", methods=["GET", "POST"])
async def index_server_edit(server_identifier):
    access_token = session.get("access_token")
    if not access_token:
        return redirect("/login")
    current_user = await dc.get_discord_user(access_token)
    if request.method == "POST":
        servers=await ptero.search_all_data(email=current_user.email, u_id=current_user.id)
        now = servers["now"]
        resource = servers["resource"]
        old_servers=None
        for i in servers["server"]:
            if i == server_identifier:
                old_servers=servers["server"][i]
                break
        if not old_servers:
            return render_template("msg.html", message="伺服器不存在",href=False)
        
        server_memory = int(request.form["memory"])
        server_cpu = int(request.form["cpu"])
        server_disk = int(request.form["disk"])
        ptero_user_id = await ptero.search_user(current_user.email)
        ptero_user_id = ptero_user_id['id']

        if server_cpu <= 0 or now["cpu"]-old_servers["cpu"]+server_cpu > resource["cpu"]:
            return render_template("msg.html", message="你沒有足夠的CPU",href=False)
        if server_memory <= 0 or now["memory"]-old_servers["memory"]+server_memory > resource["memory"]:
            return render_template("msg.html", message="你沒有足夠的記憶體",href=False)
        if server_disk <= 0 or now["disk"]-old_servers["disk"]+server_disk > resource["disk"]:
            return render_template("msg.html", message="你沒有足夠的空間",href=False)
        
        await ptero.edit_server(
            server_identifier=server_identifier,
            server_memory=server_memory,
            server_cpu=server_cpu,
            server_disk=server_disk
        )
        return render_template("msg.html", message="修改成功",href="/")
    return render_template("edit.html", user=current_user)