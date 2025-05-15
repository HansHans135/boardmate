from flask import Blueprint, jsonify, redirect, session, render_template, request
from utils.dc import Dc
from utils.ptero_api import Ptero, get_settings
from utils.db import get_db
import json
import asyncio
import subprocess

SETTING = get_settings()
dc = Dc(SETTING["oauth"]["bot_token"], webhook=SETTING["oauth"]["webhook"])
home = Blueprint("code", __name__)
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])
db = get_db()

@home.route("/code", methods=["POST", "GET"])
async def codes():
    access_token = session.get("access_token")
    if not access_token:
        return redirect(f"/")
    current_user = await dc.get_discord_user(access_token)
    
    if request.method == "POST":
        code = request.form["code"]
        success, result = db.use_code(code, current_user.id)
        
        if not success:
            return render_template("msg.html", message=result, href="/code")
            
        # 成功兌換代碼
        codes = db.get_codes()
        code_info = codes.get(code, {})
        code_usage = len(code_info.get("user", []))
        code_limit = code_info.get("use", 0)
        
        await dc.notifly(
            title="兌換代碼",
            description=f"用戶：{current_user.username} ({current_user.id})\n代碼：{code} (已使用 {code_usage}/{code_limit})",
            img=f"{SETTING['oauth']['url']}static/notifly/code.png"
        )
        return render_template("msg.html", message=f"兌換成功", href="/")
        
    return render_template("code.html", user=current_user)
