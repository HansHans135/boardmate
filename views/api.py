import random
import string
from flask import Blueprint, jsonify, redirect, session, render_template,request
from utils.dc import Dc
from utils.ptero_api import Ptero, get_settings
from utils.db import get_db
import json
import os
import time


SETTING = get_settings()
dc = Dc(SETTING["oauth"]["bot_token"], webhook=SETTING["oauth"]["webhook"])
home = Blueprint("api", __name__)
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])
db = get_db()

@home.route("/api/servers")
async def api_get_servers():
    access_token = session.get("access_token")
    if not access_token:
        return redirect("/")
    current_user = await dc.get_discord_user(access_token)
    data = await ptero.search_all_data(current_user.email, current_user.id)
    return jsonify(data)

@home.route("/api/user/<dc_user_id>", methods=["GET", "POST"])
async def api_user(dc_user_id):
    if request.form['key'] != db.get_api_key():
        return jsonify({"code":403,"message":"API Key錯誤"}),403
    
    user_data = db.get_user(dc_user_id)
    if not user_data:
        return jsonify({"code":404,"message":"未找到此用戶"}),404
    
    ptero_user_list = await ptero.get_users()
    ptero_id = user_data['id']
    user_email = None
    
    for i in ptero_user_list:
        try:
            if i["attributes"]["id"] == ptero_id:
                user_email = i["attributes"]['email']
        except:
            pass
    
    if request.method == "POST":
        updates = {}
        if request.form.get("money") is not None:
            updates["money"] = int(request.form.get("money"))
        if request.form.get("memory") is not None:
            updates["memory"] = int(request.form.get("memory"))
        if request.form.get("disk") is not None:
            updates["disk"] = int(request.form.get("disk"))
        if request.form.get("cpu") is not None:
            updates["cpu"] = int(request.form.get("cpu"))
        if request.form.get("servers") is not None:
            updates["servers"] = int(request.form.get("servers"))
        
        # 更新用戶資料
        db.update_user(dc_user_id, **updates)
        
        # 構建回應資料
        re_data = {
            "money": updates.get("money", user_data['money']),
            "resource": {
                "memory": updates.get("memory", user_data["resource"]['memory']),
                "disk": updates.get("disk", user_data["resource"]['disk']),
                "cpu": updates.get("cpu", user_data["resource"]['cpu']),
                "servers": updates.get("servers", user_data["resource"]['servers'])
            }
        }
        
        db.add_log(f"編輯用戶 {dc_user_id} : {re_data}")
        return re_data, 200
    else:
        data = await ptero.search_all_data(user_email, dc_user_id)
        db.add_log(f"搜尋用戶 {dc_user_id}")
        return data
    
@home.route("/api/code", methods=["GET","DELETE","POST"])
async def api_code():
    if request.form['key'] != db.get_api_key():
        return jsonify({"code":403,"message":"API Key錯誤"}),403
    
    if request.method == "POST":
        result = db.add_code(
            request.form['code'],
            int(request.form['use']),
            int(request.form['money'])
        )
        db.add_log(f"新增/編輯代碼 {request.form['code']} 可使用{request.form['use']}次 可獲得{request.form['money']}$")
        return result, 200
    elif request.method == "DELETE":
        success = db.delete_code(request.form['code'])
        if not success:
            return jsonify({"code":404, "message":"未找到此代碼"}),404
        
        db.add_log(f"刪除代碼 {request.form['code']}")
        return {"code":200, "message":"刪除成功"}, 200
    else:
        db.add_log(f"查詢代碼")
        return db.get_codes()
