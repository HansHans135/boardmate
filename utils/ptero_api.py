import secrets
import subprocess
import aiohttp
import json

SETTING = json.load(open('setting.json', encoding="utf-8"))


class Ptero:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.base_url = base_url

    async def get_users(self, use_cache=True):
        if use_cache:
            with open("data/user_tmp.cache", "r", encoding="utf-8") as f:
                user_list = json.load(f)
                return user_list
        else:
            headers = self.headers
            url = f'{self.base_url}api/application/users'
            user_list = []
            while True:
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(url) as response:
                        data = await response.json()
                        user_list += data["data"]
                        try:
                            url = data["meta"]["pagination"]["links"]["next"]
                        except:
                            with open("data/user_tmp.cache", "w", encoding="utf-8") as f:
                                json.dump(user_list, f,
                                          ensure_ascii=False, indent=4)
                            return user_list

    async def get_servers(self, use_cache=True) -> list:
        if use_cache:
            with open("data/server_tmp.cache", "r", encoding="utf-8") as f:
                server_list = json.load(f)
                return server_list
        else:
            headers = self.headers
            url = f'{self.base_url}api/application/servers'
            server_list = []
            while True:
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(url) as response:
                        data = await response.json()
                        server_list += data["data"]
                        try:
                            url = data["meta"]["pagination"]["links"]["next"]
                        except:
                            with open("data/server_tmp.cache", "w", encoding="utf-8") as f:
                                json.dump(server_list, f,
                                          ensure_ascii=False, indent=4)
                            return server_list

    async def get_allocations(self, node_id, use_cache=True):
        if use_cache:
            with open(f"data/node_{node_id}_allocation_tmp.cache", "r", encoding="utf-8") as f:
                allocation_list = json.load(f)
                return allocation_list
        else:
            headers = self.headers
            url = f'{self.base_url}api/application/nodes/{node_id}/allocations'
            allocation_list = []
            while True:
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(url) as response:
                        data = await response.json()
                        allocation_list += data["data"]
                        try:
                            url = data["meta"]["pagination"]["links"]["next"]
                        except:
                            with open(f"data/node_{node_id}_allocation_tmp.cache", "w", encoding="utf-8") as f:
                                json.dump(allocation_list, f,
                                          ensure_ascii=False, indent=4)
                            return allocation_list

    async def search_user(self, email):
        data = await self.get_users()
        for i in data:
            if i["attributes"]["email"] == email:
                return i["attributes"]
        return None

    async def search_server(self, u_id):
        data = await self.get_servers()
        servers = {}
        now = {
            "cpu": 0,
            "disk": 0,
            "memory": 0,
            "servers": 0
        }

        for server in data:
            attributes = server["attributes"]
            if attributes["user"] == u_id:
                now["servers"] += 1
                now["cpu"] += attributes["limits"]["cpu"]
                now["disk"] += attributes["limits"]["disk"]
                now["memory"] += attributes["limits"]["memory"]

                identifier = attributes["identifier"]
                servers[identifier] = attributes["limits"]
                servers[identifier]["id"] = identifier
                servers[identifier]["description"] = attributes["description"]
                servers[identifier]["name"] = attributes["name"]
                servers[identifier]["url"] = f'{SETTING["pterodactyl"]["url"]}server/{identifier}'

        return servers, now

    async def search_all_data(self, email, u_id):
        with open("data/user.json", "r", encoding="utf-8") as f:
            resource = json.load(f)[str(u_id)]["resource"]
        user_data = await self.search_user(email)
        server = await self.search_server(user_data["id"])
        resource["memory"]+=SETTING["server"]["default_resource"]["memory"]
        resource["cpu"]+=SETTING["server"]["default_resource"]["cpu"]
        resource["disk"]+=SETTING["server"]["default_resource"]["disk"]
        resource["servers"]+=SETTING["server"]["default_resource"]["servers"]
        now, server = server
        return {"now": server, "resource": resource, "server": now}
    
    async def create_user(self,email,username):
        password=secrets.token_urlsafe()
        data={
            "username": username,
            "first_name": username,
            "last_name": username,
            "email": email,
            "password": password
        }
        headers = self.headers
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(f'{self.base_url}api/application/users', data=json.dumps(data)) as response:
                data = await response.json()
                with open("data/user_tmp.cache","r",encoding="utf-8")as f:
                    uc=json.load(f)
                uc.append(data)
                with open("data/user_tmp.cache", "w", encoding="utf-8") as f:
                    json.dump(uc, f, ensure_ascii=False, indent=4)
                data=data["attributes"]
                data["password"]=password
        return data
    
    async def edit_user(self,u_id,email,username):
        password=secrets.token_urlsafe()
        data={
            "username": username,
            "first_name": username,
            "last_name": username,
            "email": email,
            "password": password
        }
        headers = self.headers
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.patch(f'{self.base_url}api/application/users/{u_id}', data=json.dumps(data)) as response:
                data = await response.json()
                data=data["attributes"]
                data["password"]=password
        return data
    
    async def create_server(self, ptero_user_id, server_name, server_egg, server_node, server_disk, server_cpu, server_memory):
        all_allocation = await self.get_allocations(server_node)
        for i in all_allocation:
            if i["attributes"]["assigned"] == False:
                allocation = i["attributes"]["id"]
                break
        await self.get_allocations(server_node, use_cache=False)
        data = {
            "name": server_name,
            "user": ptero_user_id,
            "egg": SETTING["server"]["eggs"][server_egg]["egg_id"],
            "docker_image": SETTING["server"]["eggs"][server_egg]["docker_image"],
            "startup": SETTING["server"]["eggs"][server_egg]["startup"],
            "environment": SETTING["server"]["eggs"][server_egg]["environment"],
            "limits": {
                "memory": server_memory,
                "swap": 0,
                "disk": server_disk,
                "io": 500,
                "cpu": server_cpu
            },
            "feature_limits": {
                "databases": SETTING["server"]["feature_limits"]["databases"],
                "backups": SETTING["server"]["feature_limits"]["backups"]
            },
            "allocation": {
                "default": allocation
            }
        }
        headers = self.headers
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(f'{self.base_url}api/application/servers', data=json.dumps(data)) as response:
                data = await response.json()
        tmp_data = await self.ptero.get_servers()
        tmp_data += data,
        with open("data/server_tmp.cache", "w", encoding="utf-8") as f:
            json.dump(tmp_data, f, indent=4)
        return data

    async def delete_server(self, server_identifier):
        servers = await self.get_servers()
        for i in servers:
            if i["attributes"]["identifier"] == server_identifier:
                server_id = i["attributes"]["id"]

        headers = self.headers
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.delete(f'{self.base_url}api/application/servers/{server_id}') as response:
                servers = [server for server in servers if server["attributes"]
                           ["identifier"] != server_identifier]
                with open("data/server_tmp.cache", "w", encoding="utf-8") as f:
                    json.dump(servers, f, ensure_ascii=False, indent=4)
                return

    async def edit_server(self, server_identifier, server_memory, server_cpu, server_disk):
        servers = await self.get_servers()
        for i in servers:
            if i["attributes"]["identifier"] == server_identifier:
                server_id = i["attributes"]["id"]
                break
        headers = self.headers
        payload = {
            "allocation": i["attributes"]["allocation"],
            "memory": server_memory,
            "swap": 0,
            "disk": server_disk,
            "io": 500,
            "cpu": server_cpu,
            "threads": None,
            "feature_limits": i["attributes"]["feature_limits"]
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.patch(f'{self.base_url}api/application/servers/{server_id}/build',data=json.dumps(payload)) as response:
                data = await response.json()
                servers = [server for server in servers if server["attributes"]
                           ["identifier"] != server_identifier]
                servers += [data]
                with open("data/server_tmp.cache", "w", encoding="utf-8") as f:
                    json.dump(servers, f, ensure_ascii=False, indent=4)
                return
