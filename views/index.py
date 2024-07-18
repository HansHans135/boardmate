from flask import Blueprint, jsonify, redirect, session, render_template
from utils.dc import Dc
from utils.ptero_api import Ptero
import json
import asyncio
import threading
from flask import request

SETTING = json.load(open("setting.json", "r", encoding="utf-8"))
dc = Dc(SETTING["oauth"]["bot_token"])
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
                "memory": SETTING["server"]["default_resource"]["memory"],
                "disk": SETTING["server"]["default_resource"]["disk"],
                "cpu": SETTING["server"]["default_resource"]["cpu"],
                "servers": SETTING["server"]["default_resource"]["servers"]
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
                "memory": SETTING["server"]["default_resource"]["memory"],
                "disk": SETTING["server"]["default_resource"]["disk"],
                "cpu": SETTING["server"]["default_resource"]["cpu"],
                "servers": SETTING["server"]["default_resource"]["servers"]
            }
        }
        with open("data/user.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    return render_template("index.html", user=current_user)


@home.route("/rpa")
async def index_rpa():
    access_token = session.get("access_token")
    if not access_token:
        return render_template("login.html")
    current_user = await dc.get_discord_user(access_token)
    user=await ptero.search_user(current_user.email)
    user_data=await ptero.edit_user(user["id"])
    return redirect(f"/?passwd={user_data["password"]}")

@home.route("/server/add", methods=["GET", "POST"])
async def index_server_add():
    access_token = session.get("access_token")
    if not access_token:
        return redirect("/login")
    current_user = await dc.get_discord_user(access_token)
    if request.method == "POST":
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
            return render_template("msg.html", message="已達伺服器數量上限")
        if server_cpu <= 0 or now["cpu"]+server_cpu > resource["cpu"]:
            return render_template("msg.html", message="你沒有足夠的CPU")
        if server_memory <= 0 or now["memory"]+server_memory > resource["memory"]:
            return render_template("msg.html", message="你沒有足夠的記憶體")
        if server_disk <= 0 or now["disk"]+server_disk > resource["disk"]:
            return render_template("msg.html", message="你沒有足夠的空間")

        server = await ptero.create_server(
            ptero_user_id=ptero_user_id,
            server_name=server_name,
            server_memory=server_memory,
            server_cpu=server_cpu,
            server_disk=server_disk,
            server_node=server_node,
            server_egg=server_egg
        )
        tmp_data = await ptero.get_servers()
        tmp_data += server,
        with open("data/server_tmp.cache", "w", encoding="utf-8") as f:
            json.dump(tmp_data, f, indent=4)

        return redirect("/")
    return render_template("add.html", user=current_user, eggs=SETTING["server"]["eggs"], nodes=SETTING["server"]["node"])


@home.route("/server/del/<server_identifier>", methods=["GET"])
async def index_server_del(server_identifier):
    access_token = session.get("access_token")
    if not access_token:
        return redirect("/login")
    current_user = await dc.get_discord_user(access_token)
    if request.values.get("check"):
        servers = await ptero.search_all_data(current_user.email, current_user.id)
        servers = servers["server"]
        for i in servers:
            if i == server_identifier:
                await ptero.delete_server(i)
                return render_template("msg.html",message="刪除成功")
        return render_template("msg.html", message="伺服器不存在")
    else:
        return render_template("del_check.html",identifier=server_identifier)

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
            return render_template("msg.html", message="伺服器不存在")
        
        server_memory = int(request.form["memory"])
        server_cpu = int(request.form["cpu"])
        server_disk = int(request.form["disk"])
        ptero_user_id = await ptero.search_user(current_user.email)
        ptero_user_id = ptero_user_id['id']

        if server_cpu <= 0 or now["cpu"]-old_servers["cpu"]+server_cpu > resource["cpu"]:
            return render_template("msg.html", message="你沒有足夠的CPU")
        if server_memory <= 0 or now["memory"]-old_servers["memory"]+server_memory > resource["memory"]:
            return render_template("msg.html", message="你沒有足夠的記憶體")
        if server_disk <= 0 or now["disk"]-old_servers["disk"]+server_disk > resource["disk"]:
            return render_template("msg.html", message="你沒有足夠的空間")
        
        await ptero.edit_server(
            server_identifier=server_identifier,
            server_memory=server_memory,
            server_cpu=server_cpu,
            server_disk=server_disk
        )
        return render_template("msg.html", message="修改成功")
    return render_template("edit.html", user=current_user)