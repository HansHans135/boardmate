from utils.ptero_api import Ptero
import json
import asyncio
SETTING = json.load(open("setting.json", "r", encoding="utf-8"))
ptero=Ptero(SETTING["pterodactyl"]["key"],SETTING["pterodactyl"]["url"])

asyncio.run(ptero.get_servers(False))
asyncio.run(ptero.get_users(False))