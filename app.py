# app.py

from flask import Flask,jsonify,redirect,request
from utils.ptero_api import Ptero
import os
import asyncio
import json

try_fix=0
app = Flask(__name__)
SETTING=json.load(open('setting.json',encoding="utf-8"))
app.config["SECRET_KEY"] = "mysecret"
ptero=Ptero(SETTING["pterodactyl"]["key"],SETTING["pterodactyl"]["url"])

if SETTING["boardmate"]["recache"]:
    print("> 正在啟動緩存")
    asyncio.run(ptero.get_servers(use_cache=False))
    print(f"  L 伺服器")
    asyncio.run(ptero.get_users(use_cache=False))
    print(f"  L 用戶")
    for i in SETTING["server"]["node"]:
        asyncio.run(ptero.get_allocations(SETTING["server"]["node"][i],use_cache=False))
        print(f"  L 節點 {i}")
    print("> 已啟動緩存")
else:
    print("> 已跳過緩存")


@app.errorhandler(404)
async def error_404(error):
    return "頁面不存在",404

@app.errorhandler(400)
async def error_400(error):
    return jsonify({"code":400,"message":"資料有誤"}),400

@app.errorhandler(500)
async def error_500(error):
    cache_error=False
    try:
        try_server=await ptero.get_servers()
        for i in try_server:
            i["attributes"]
    except:
        cache_error=True
        await ptero.get_servers(use_cache=False)
    try:
        try_user=await ptero.get_users()
        for i in try_user:
            i["attributes"]
    except:
        cache_error=True
        await ptero.get_users(use_cache=False)
    try:
        for i in SETTING["server"]["node"]:
            await ptero.get_allocations(SETTING["server"]["node"][i], use_cache=False)
    except:
        cache_error=True
        for i in SETTING["server"]["node"]:
            await ptero.get_allocations(SETTING["server"]["node"][i], use_cache=False)
    if cache_error:
        return {"status":"fixed","message":f"伺服器發生錯誤，已嘗試修復，請重整頁面"},200
    else:
        return {"status":"error","message":f"伺服器發生錯誤，請連絡管理員"},200

print("> 正在註冊檔案")
views_dir = os.path.join(os.path.dirname(__file__), 'views')
for filename in os.listdir(views_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        module_name = filename[:-3]
        module = __import__(f'views.{module_name}', fromlist=['*'])
        print(f"  L {module_name}.py")
        if hasattr(module, 'home'):
            app.register_blueprint(module.home)
print("> 已註冊檔案")

if __name__ == "__main__":
    app.run(host=SETTING["boardmate"]["host"],port=SETTING["boardmate"]["port"],debug=SETTING["boardmate"]["debug"])
