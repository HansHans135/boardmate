import random
import string
from flask import Blueprint, jsonify, redirect, session, render_template,request
from utils.dc import Dc
from utils.ptero_api import Ptero
import json
import os
import time


SETTING = json.load(open("setting.json", "r", encoding="utf-8"))
dc = Dc(SETTING["oauth"]["bot_token"], webhook=SETTING["oauth"]["webhook"])
home = Blueprint("api", __name__)
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])

# 初始化
if not os.path.isfile("data/api.json"):
    api_key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(50))
    api_data = {
        "key": api_key,
        "log": []
    }
    with open("data/api.json", "w", encoding="utf-8")as f:
        json.dump(api_data, f, ensure_ascii=False, indent=4)
    print(f"  L 初始化API完成，你的新API Key為 {api_key}")

with open("data/api.json", "r", encoding="utf-8")as f:
    api_data=json.load(f)
    api_key=api_data["key"]

async def add_log(message):
    with open("data/api.json", "r", encoding="utf-8")as f:
        api_data=json.load(f)
    api_data['log'].append({
        "time":int(time.time()),
        "message":message
    })
    with open("data/api.json", "w", encoding="utf-8")as f:
        json.dump(api_data, f, ensure_ascii=False, indent=4)
    return None


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
    if request.form['key'] != api_key:
        return jsonify({"code":403,"message":"API Key錯誤"}),403
    with open("data/user.json","r",encoding="utf-8")as f:
        user_list=json.load(f)
    ptero_user_list=await ptero.get_users()
    if dc_user_id not in user_list:
        return jsonify({"code":404,"message":"未找到此用戶"}),404
    ptero_id=user_list[dc_user_id]['id']
    for i in ptero_user_list:
        try:
            if i["attributes"]["id"]==ptero_id:
                user_email=i["attributes"]['email']
        except:
            pass
    if request.method == "POST":
        with open("data/user.json","r",encoding="utf-8")as f:
            user_list=json.load(f)
        user_list[dc_user_id]['money'] = int(request.form.get("money")) if request.form.get("money") is not None else user_list[dc_user_id]['money']
        user_list[dc_user_id]["resource"]['memory'] = int(request.form.get("memory")) if request.form.get("memory") is not None else user_list[dc_user_id]["resource"]['memory']
        user_list[dc_user_id]["resource"]['disk'] = int(request.form.get("disk")) if request.form.get("disk") is not None else user_list[dc_user_id]["resource"]['disk']
        user_list[dc_user_id]["resource"]['cpu'] = int(request.form.get("cpu")) if request.form.get("cpu") is not None else user_list[dc_user_id]["resource"]['cpu']
        user_list[dc_user_id]["resource"]['servers'] = int(request.form.get("servers")) if request.form.get("servers") is not None else user_list[dc_user_id]["resource"]['servers']

        re_data={"resource":{}}
        re_data['money']=request.form.get("money") or user_list[dc_user_id]['money']
        re_data["resource"]['memory']=request.form.get("memory") or user_list[dc_user_id]["resource"]['memory']
        re_data["resource"]['disk']=request.form.get("disk") or user_list[dc_user_id]["resource"]['disk']
        re_data["resource"]['cpu']=request.form.get("cpu") or user_list[dc_user_id]["resource"]['cpu']
        re_data["resource"]['servers']=request.form.get("servers") or user_list[dc_user_id]["resource"]['servers']
        with open("data/user.json","w",encoding="utf-8")as f:
            json.dump(user_list,f,ensure_ascii=False,indent=4)
        await add_log(f"編輯用戶 {dc_user_id} : {re_data}")
        return re_data,200
    else:
        data = await ptero.search_all_data(user_email, dc_user_id)
        await add_log(f"搜尋用戶 {dc_user_id}")
        return data
    
@home.route("/api/code", methods=["GET","DELETE","POST"])
async def api_code():
    if request.form['key'] != api_key:
        return jsonify({"code":403,"message":"API Key錯誤"}),403
    with open("data/code.json","r",encoding="utf-8")as f:
        data= json.load(f)
    if request.method == "POST":
        data[request.form['code']]={
            "user": [],
            "use": int(request.form['use']),
            "money": int(request.form['money'])
        }
        with open("data/code.json","w",encoding="utf-8")as f:
            json.dump(data,f,ensure_ascii=False,indent=4)
        await add_log(f"新增/編輯代碼 {request.form['code']} 可使用{request.form['use']}次 可獲得{request.form['money']}$")
        return data[request.form['code']],200
    elif request.method == "DELETE":
        if request.form['code'] in data:
            data.pop(request.form['code'])
        else:
            return jsonify({"code":404, "message":"未找到此代碼"}),404
        
        with open("data/code.json","w",encoding="utf-8")as f:
            json.dump(data,f,ensure_ascii=False,indent=4)
        await add_log(f"刪除代碼 {request.form['code']}")
        return {"code":200, "message":"刪除成功"},200
    else:
        await add_log(f"查詢代碼")
        return data
