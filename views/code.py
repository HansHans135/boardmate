from flask import Blueprint, jsonify, redirect, session, render_template, request
from utils.dc import Dc
from utils.ptero_api import Ptero
import json
import asyncio
import subprocess

SETTING = json.load(open("setting.json", "r", encoding="utf-8"))
dc = Dc(SETTING["oauth"]["bot_token"])
home = Blueprint("code", __name__)
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])


@home.route("/code", methods=["POST", "GET"])
async def codes():
    access_token = session.get("access_token")
    if not access_token:
        return redirect(f"/")
    current_user = await dc.get_discord_user(access_token)
    if request.method == "POST":
        with open(f"data/code.json", "r")as f:
            data = json.load(f)
        if request.form["code"] in data:
            code = data[request.form["code"]]
            if len(code["user"]) == code["use"]:
                return render_template("msg.html", message=f"代碼已被使用完畢", href="/code")
            else:
                if current_user.id in code["user"]:
                    return render_template("msg.html", message=f"你已經兌換過", href="/code")
                with open(f"data/user.json", "r")as f:
                    udata = json.load(f)
                code["user"].append(current_user.id)
                data[request.form["code"]] = code
                udata[str(current_user.id)]["money"] += code["money"]
                with open(f"data/user.json", "w")as f:
                    json.dump(udata, f, ensure_ascii=False, indent=4)
                with open(f"data/code.json", "w")as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                return render_template("msg.html", message=f"兌換成功", href="/")
        else:
            return render_template("msg.html", message=f"錯誤的代碼", href=False)
    return render_template("code.html", user=current_user)
