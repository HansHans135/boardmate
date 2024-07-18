# app.py

from flask import Flask,jsonify
from utils.ptero_api import Ptero
import os
import asyncio
import json

app = Flask(__name__)
SETTING=json.load(open('setting.json',encoding="utf-8"))
app.config["SECRET_KEY"] = "mysecret"
ptero=Ptero(SETTING["pterodactyl"]["key"],SETTING["pterodactyl"]["url"])

print("> 正在啟動緩存")
asyncio.run(ptero.get_servers(use_cache=False))
print(f"  L 伺服器")
asyncio.run(ptero.get_users(use_cache=False))
print(f"  L 用戶")
for i in SETTING["server"]["node"]:
    asyncio.run(ptero.get_allocations(SETTING["server"]["node"][i],use_cache=False))
    print(f"  L 節點 {i}")
print("> 已啟動緩存")


@app.errorhandler(404)
async def error_404(error):
    return jsonify({}),404

@app.errorhandler(400)
async def error_400(error):
    return jsonify({}),400

@app.errorhandler(500)
async def error_500(error):
    return jsonify({}),500

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
    app.run(host=SETTING["boardmate"]["host"],port=SETTING["boardmate"]["port"])
