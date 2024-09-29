from flask import Blueprint, jsonify, redirect, session, render_template
from utils.dc import Dc
from utils.ptero_api import Ptero
import json
import asyncio
import subprocess

SETTING = json.load(open("setting.json", "r", encoding="utf-8"))
dc=Dc(SETTING["oauth"]["bot_token"],webhook=SETTING["oauth"]["webhook"])
home = Blueprint("api", __name__)
ptero = Ptero(SETTING["pterodactyl"]["key"], SETTING["pterodactyl"]["url"])


@home.route("/api/servers")
async def api_get_servers():
    access_token = session.get("access_token")
    if not access_token:
        return redirect("/")
    current_user = await dc.get_discord_user(access_token)
    data = await ptero.search_all_data(current_user.email, current_user.id)
    #subprocess.Popen("python cache.py")
    return jsonify(data)
