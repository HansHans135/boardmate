from datetime import datetime
import random
import string
from flask import Blueprint, jsonify, redirect, session, render_template,request
from utils.dc import Dc
from utils.ptero_api import Ptero, get_settings
from utils.db import get_db
import json
import asyncio
import hashlib
from urllib.parse import urlencode

SETTING = get_settings()
ADD_TMP={}
CHEAK_TMP={}
dc=Dc(SETTING["oauth"]["bot_token"],webhook=SETTING["oauth"]["webhook"])
home = Blueprint("admin", __name__)
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])
db = get_db()

async def statistics_all():
    users = await ptero.get_users()
    servers = await ptero.get_servers()
    codes = len(db.get_codes())
    logs = len(db.get_logs())
    return {"users": len(users), "servers": len(servers), "codes": codes, "apis": logs}

@home.route("/admin")
async def admin_home():
    access_token = session.get("access_token")
    if not access_token:
        return render_template("login.html")
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:
        return redirect("/")
        
    user = await ptero.search_user(current_user.email)
    all_users = {}
    all_ptero_users = await ptero.get_users()
    
    # 獲取所有用戶資料
    db_users = db.get_all_users()  # 需要在 Database 類中添加此方法
    
    for dc_id, user_data in db_users.items():
        for ptero_user in all_ptero_users:
            if ptero_user["attributes"]["id"] == user_data["id"]:
                email = ptero_user["attributes"]["email"]
                username = ptero_user["attributes"]["username"]
                break
                
        all_users[dc_id] = {
            "id": user_data["id"],
            "money": user_data["money"],
            "email": email,
            "name": username,
            "resource": {
                "memory": user_data["resource"]["memory"] / 1024,
                "cpu": user_data["resource"]["cpu"],
                "disk": user_data["resource"]["disk"] / 1024,
                "servers": user_data["resource"]["servers"]
            }
        }
        
        # 生成 Gravatar URL
        email_encoded = email.lower().encode('utf-8')
        email_hash = hashlib.sha256(email_encoded).hexdigest()
        query_params = urlencode({'s': str(40)})
        all_users[dc_id]["avatar"] = f"https://www.gravatar.com/avatar/{email_hash}?{query_params}"
    
    statistics = await statistics_all()
    return render_template("admin/index.html", user=current_user, user_data=all_users, statistics=statistics)

@home.route("/admin/code", methods=["POST", "GET"])
async def admin_code():
    access_token = session.get("access_token")
    if not access_token:
        return render_template("login.html")
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:
        return redirect("/")
        
    codes = db.get_codes()
    statistics = await statistics_all()
    
    if request.method == "POST":
        code = request.form["name"]
        use_limit = int(request.form["times"])
        money = int(request.form["money"])
        
        db.add_code(code, use_limit, money)
        await dc.notifly(
            title="創建代碼",
            description=f"用戶：{current_user.username} ({current_user.id})\n新增 {code} 成功 (可用 {use_limit} 次/可取得 {money} $)",
            img=current_user.avatar_url
        )
        return render_template("msg.html", message=f"新增 {code} 成功 (可用 {use_limit} 次/可取得 {money} $)", href="/admin/code")
        
    return render_template("admin/code.html", user=current_user, codes=codes, statistics=statistics)

@home.route("/admin/code/del/<code>")
async def admin_code_del(code):
    access_token = session.get("access_token")
    if not access_token:
        return render_template("login.html")
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:
        return redirect("/")
        
    db.delete_code(code)
    await dc.notifly(
        title="刪除代碼",
        description=f"用戶：{current_user.username} ({current_user.id})\n代碼：{code}",
        img=current_user.avatar_url
    )
    return render_template("msg.html", message=f"刪除 {code} 成功", href="/admin/code")

@home.route("/admin/log")
async def admin_log():
    access_token = session.get("access_token")
    if not access_token:
        return render_template("login.html")
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:
        return redirect("/")
        
    statistics = await statistics_all()
    logs = db.get_logs()
    
    # 轉換時間戳為datetime物件
    for log in logs:
        log["time"] = datetime.utcfromtimestamp(log["time"])
        
    return render_template("admin/log.html", user=current_user, logs=logs, statistics=statistics)

@home.route("/admin/setting", methods=["POST", "GET"])
async def admin_setting():
    access_token = session.get("access_token")
    if not access_token:
        return render_template("login.html")
    current_user = await dc.get_discord_user(access_token)
    if current_user.id not in SETTING["boardmate"]["admins"]:
        return redirect("/")
        
    statistics = await statistics_all()
    if request.method == "POST":
        SETTING['server']['default_resource']['memory'] = int(request.form.get("memory"))
        SETTING['server']['default_resource']['cpu'] = int(request.form.get("cpu"))
        SETTING['server']['default_resource']['disk'] = int(request.form.get("disk"))
        SETTING['boardmate']['admins'] = []
        for admin in request.form.get("admins").split("\n"):
            if admin.strip():
                SETTING['boardmate']['admins'].append(admin.strip())
        db.update_settings(SETTING)
        await dc.notifly(
            title="更新設定",
            description=f"用戶：{current_user.username} ({current_user.id})",
            img=current_user.avatar_url
        )
        return render_template("msg.html", message="設定成功，請重啟套用", href="/admin/setting")
        
    return render_template("admin/setting.html", user=current_user, setting=SETTING, statistics=statistics)