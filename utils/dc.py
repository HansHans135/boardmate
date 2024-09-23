import json
import aiohttp
import asyncio


class Discord_User:
    def __init__(self, data):
        self.username = data["global_name"] or data["username"]
        self.avatar_url = f'https://cdn.discordapp.com/avatars/{data["id"]}/{data["avatar"]}'
        self.id = data["id"]
        self.email = data["email"]


class Dc:
    def __init__(self, token):
        self.token = token
        self.headers = {"Authorization": f'Bot {token}'}

    async def get_discord_user(self, token) -> Discord_User:
        async with aiohttp.ClientSession(headers={"Authorization": f'Bearer {token}'}) as session:
            async with session.get("https://discord.com/api/users/@me") as response:
                data = await response.json()
        return Discord_User(data)
