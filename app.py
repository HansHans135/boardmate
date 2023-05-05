from flask import Flask, render_template, request, redirect, session, jsonify
from zenora import APIClient
from pteropy import Pterodactyl_Application
import json
import requests
import string
import random

app = Flask(__name__)


def get_user_server(current_user):
    with open("data/user.json", "r")as f:
        data = json.load(f)
    try:
        resource = data[str(current_user.id)]["resource"]
        try:
            uid = data[str(current_user.id)]["id"]
        except:
            key = config["pterodactyl"]["key"]
            url = f'{config["pterodactyl"]["url"]}api/application/users'
            headers = {
                "Authorization": f"Bearer {key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            response = requests.request('GET', url, headers=headers)

            for i in response.json()["data"]:
                if i["attributes"]["email"] == current_user.email:
                    uid = i["attributes"]["id"]
            data[str(current_user.id)]["id"] = uid
            with open("data/user.json", "w+")as f:
                json.dump(data, f)
    except:
        d = ptero.create_user(username=str(current_user.id), email=current_user.email, password=''.join(
            random.choice(string.ascii_letters + string.digits) for _ in range(20)))
        try:
            uid = d["attributes"]["id"]
        except:
            key = config["pterodactyl"]["key"]
            url = f'{config["pterodactyl"]["url"]}api/application/users'
            headers = {
                "Authorization": f"Bearer {key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            response = requests.request('GET', url, headers=headers)

            for i in response.json()["data"]:
                if i["attributes"]["email"] == current_user.email:
                    uid = i["attributes"]["id"]
        data[str(current_user.id)] = {
            "id": uid,
            "money": 0,
            "resource": {
                "memory": 0,
                "disk": 0,
                "cpu": 0,
                "servers": 0
            }
        }
        with open("data/user.json", "w+")as f:
            json.dump(data, f)
        with open("data/user.json", "r")as f:
            data = json.load(f)
        resource = data[str(current_user.id)]["resource"]

    resource = {
        "memory": resource["memory"]+config["server"]["default_resource"]["memory"],
        "disk": resource["disk"]+config["server"]["default_resource"]["disk"],
        "cpu": resource["cpu"]+config["server"]["default_resource"]["cpu"],
        "servers": resource["servers"]+config["server"]["default_resource"]["servers"]
    }
    key = config["pterodactyl"]["key"]
    url = f'{config["pterodactyl"]["url"]}api/application/servers'
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = requests.request('GET', url, headers=headers)
    server = {}
    now = {
        "memory": 0,
        "disk": 0,
        "cpu": 0,
        "servers": 0
    }
    for i in response.json()["data"]:
        if i["attributes"]["user"] == uid:
            purl = config["pterodactyl"]["url"]
            id = i["attributes"]["identifier"]
            url = f"{purl}server/{id}"
            server[i["attributes"]["name"]] = i["attributes"]["limits"]
            server[i["attributes"]["name"]]["url"] = url
            server[i["attributes"]["name"]]["id"] = i["attributes"]["id"]
            now["memory"] += i["attributes"]["limits"]["memory"]
            now["disk"] += i["attributes"]["limits"]["disk"]
            now["cpu"] += i["attributes"]["limits"]["cpu"]
            now["servers"] += 1
    data = {
        "resource": resource,
        "server": server,
        "now": now
    }
    return data


with open("./setting.json", "r")as f:
    config = json.load(f)
client = APIClient(config["oauth"]["bot_token"],
                   client_secret=config["oauth"]["client_secret"])
app.config["SECRET_KEY"] = "mysecret"
ptero = Pterodactyl_Application(
    config["pterodactyl"]["url"], config["pterodactyl"]["key"])


@app.route("/")
def home():
    access_token = session.get("access_token")

    if not access_token:
        return render_template("login.html")

    bearer_client = APIClient(access_token, bearer=True)
    current_user = bearer_client.users.get_current_user()

    get = get_user_server(current_user)
    if not request.values.get("new") == None:
        new = request.values.get("new")
        return render_template("index.html", pas=new, resource=get["resource"], user=current_user, server=get["server"], now=get["now"])
    else:
        return render_template("index.html", resource=get["resource"], user=current_user, server=get["server"], now=get["now"])


@app.route("/server/add", methods=["GET", "POST"])
def add():
    access_token = session.get("access_token")

    if not access_token:
        return redirect(f"/")

    bearer_client = APIClient(access_token, bearer=True)
    current_user = bearer_client.users.get_current_user()
    get = get_user_server(current_user)
    if request.method == "POST":
        with open("data/user.json", "r")as f:
            udata = json.load(f)
        resource = get["resource"]
        now = get["now"]
        if int(request.form["cpu"]) > resource["cpu"]-now["cpu"] or int(request.form["cpu"]) == 0:
            error = "你沒有足夠的cpu"
            return redirect(f"/server/add?error={error}")
        if int(request.form["memory"]) > resource["memory"]-now["memory"] or int(request.form["memory"]) == 0:
            error = "你沒有足夠的記憶體"
            return redirect(f"/server/add?error={error}")
        if int(request.form["disk"]) > resource["disk"]-now["disk"] or int(request.form["disk"]) == 0:
            error = "你沒有足夠的空間"
            return redirect(f"/server/add?error={error}")
        nid = str(config["server"]["node"][request.form["node"]])
        key = config["pterodactyl"]["key"]
        url = f'{config["pterodactyl"]["url"]}api/application/nodes/{nid}/allocations'
        headers = {
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        response = requests.request('GET', url,  headers=headers)
        t = False
        for i in response.json()["data"]:
            if t == False:
                if i["attributes"]["assigned"] == False:
                    allocation = i["attributes"]["id"]
                    t = True

        url = f'{config["pterodactyl"]["url"]}api/application/servers'
        headers = {
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "name": request.form["name"],
            "user": udata[str(current_user.id)]["id"],
            "egg": config["server"]["eggs"][request.form["egg"]]["egg_id"],
            "docker_image": config["server"]["eggs"][request.form["egg"]]["docker_image"],
            "startup": config["server"]["eggs"][request.form["egg"]]["startup"],
            "environment": config["server"]["eggs"][request.form["egg"]]["environment"],
            "limits": {
                "memory": int(request.form["memory"]),
                "swap": 0,
                "disk": int(request.form["disk"]),
                "io": 500,
                "cpu": int(request.form["cpu"])
            },
            "feature_limits": {
                "databases": config["server"]["feature_limits"]["databases"],
                "backups": config["server"]["feature_limits"]["backups"]
            },
            "allocation": {
                "default": allocation
            }
        }
        response = requests.request(
            'POST', url, data=json.dumps(payload), headers=headers)
        return redirect(f"/")
    eggs = []
    nodes = []
    for i in config["server"]["eggs"]:
        eggs.append(i)
    for i in config["server"]["node"]:
        nodes.append(i)
    if not request.values.get("error") == None:
        error = request.values.get("error")
        return render_template("add.html", nodes=nodes, eggs=eggs, resource=get["resource"], user=current_user, server=get["server"], now=get["now"], error=error)
    else:
        return render_template("add.html", nodes=nodes, eggs=eggs, resource=get["resource"], user=current_user, server=get["server"], now=get["now"])


@app.route("/server/edit/<id>", methods=["GET", "POST"])
def edit(id):
    access_token = session.get("access_token")

    if not access_token:
        return redirect(f"/")
    with open("data/user.json", "r")as f:
        udata = json.load(f)
    bearer_client = APIClient(access_token, bearer=True)
    current_user = bearer_client.users.get_current_user()
    get = get_user_server(current_user)
    key = config["pterodactyl"]["key"]
    url = f'{config["pterodactyl"]["url"]}api/application/servers/{id}'
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = requests.request('GET', url, headers=headers)
    name = response.json()["attributes"]["name"]
    if not response.json()["attributes"]["user"] == udata[str(current_user.id)]["id"]:
        return redirect(f"/")
    if request.method == "POST":
        resource = get["resource"]
        now = get["now"]
        if int(request.form["cpu"]) > resource["cpu"]-now["cpu"]+response.json()["attributes"]["limits"]["cpu"] or int(request.form["cpu"]) == 0:
            error = "你沒有足夠的cpu"
            return redirect(f"/server/edit/{id}?error={error}")
        if int(request.form["memory"]) > resource["memory"]-now["memory"]+response.json()["attributes"]["limits"]["memory"] or int(request.form["memory"]) == 0:
            error = "你沒有足夠的記憶體"
            return redirect(f"/server/edit/{id}?error={error}")
        if int(request.form["disk"]) > resource["disk"]-now["disk"]+response.json()["attributes"]["limits"]["disk"] or int(request.form["disk"]) == 0:
            error = "你沒有足夠的空間"
            return redirect(f"/server/edit/{id}?error={error}")

        url = f'{config["pterodactyl"]["url"]}api/application/servers/{id}/build'
        headers = {
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "allocation": response.json()["attributes"]["allocation"],
            "memory": int(request.form["memory"]),
            "swap": 0,
            "disk": int(request.form["disk"]),
            "io": 500,
            "cpu": int(request.form["cpu"]),
            "threads": None,
            "feature_limits": response.json()["attributes"]["feature_limits"]
        }

        response = requests.request(
            'PATCH', url, data=json.dumps(payload), headers=headers)
        return redirect(f"/")

    if not request.values.get("error") == None:
        error = request.values.get("error")
        return render_template("edit.html", name=name, resource=get["resource"], user=current_user, server=get["server"], now=get["now"], error=error)
    else:
        return render_template("edit.html", name=name, resource=get["resource"], user=current_user, server=get["server"], now=get["now"])


@app.route("/rpa")
def rpa():
    access_token = session.get("access_token")

    if not access_token:
        return redirect(f"/")

    bearer_client = APIClient(access_token, bearer=True)
    current_user = bearer_client.users.get_current_user()
    with open("data/user.json", "r")as f:
        udata = json.load(f)
    password = ''.join(
        random.choice(string.ascii_letters + string.digits) for _ in range(20))
    key = config["pterodactyl"]["key"]
    url = f'{config["pterodactyl"]["url"]}api/application/users/{udata[str(current_user.id)]["id"]}'
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "email": current_user.email,
        "username": str(current_user.id),
        "first_name": str(current_user.id),
        "last_name": str(current_user.id),
        "language": "en",
        "password": password
    }

    response = requests.request(
        'PATCH', url, data=json.dumps(payload), headers=headers)
    print(response.json())
    return redirect(f"/?new={password}")


@app.route("/server/del/<id>")
def dle(id):
    access_token = session.get("access_token")

    if not access_token:
        return redirect(f"/")

    bearer_client = APIClient(access_token, bearer=True)
    current_user = bearer_client.users.get_current_user()
    with open("data/user.json", "r")as f:
        udata = json.load(f)
    key = config["pterodactyl"]["key"]
    url = f'{config["pterodactyl"]["url"]}api/application/servers/{id}'
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = requests.request('GET', url, headers=headers)
    if response.json()["attributes"]["user"] == udata[str(current_user.id)]["id"]:
        print("y")
        url = f'{config["pterodactyl"]["url"]}api/application/servers/{id}'
        headers = {
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        response = requests.request('DELETE', url, headers=headers)
    else:
        print("n")
    return redirect(f"/")


@app.route("/shop")
def shop():
    access_token = session.get("access_token")

    if not access_token:
        return redirect(f"/")

    bearer_client = APIClient(access_token, bearer=True)
    current_user = bearer_client.users.get_current_user()

    get = get_user_server(current_user)
    with open(f"data/user.json", "r")as f:
        data = json.load(f)
    money = data[str(current_user.id)]["money"]
    return render_template("shop.html", money=money, shop=config["shop"], resource=get["resource"], user=current_user, server=get["server"], now=get["now"])


@app.route("/shop/<mode>", methods=["POST"])
def shopmode(mode):
    access_token = session.get("access_token")

    if not access_token:
        return redirect(f"/")

    bearer_client = APIClient(access_token, bearer=True)
    current_user = bearer_client.users.get_current_user()

    get = get_user_server(current_user)
    with open(f"data/user.json", "r")as f:
        data = json.load(f)
    nmode = mode
    if mode == "servers":
        nmode = "server"
    if config["shop"][nmode][request.form[mode]] <= data[str(current_user.id)]["money"]:

        data[str(current_user.id)
             ]["money"] -= config["shop"][nmode][request.form[mode]]
        data[str(current_user.id)]["resource"][mode] += int(request.form[mode])
        with open(f"data/user.json", "w")as f:
            json.dump(data, f)
        return redirect(f"/")
    else:
        return redirect(f"/shop?error=你沒有足夠的錢錢")


@app.route("/code", methods=["POST", "GET"])
def codes():
    access_token = session.get("access_token")
    if not access_token:
        return redirect(f"/")
    bearer_client = APIClient(access_token, bearer=True)
    current_user = bearer_client.users.get_current_user()
    get = get_user_server(current_user)
    if request.method == "POST":
        with open(f"data/code.json", "r")as f:
            data = json.load(f)
        try:
            code=data[request.form["code"]]
            if len(code["user"]) == code["use"]:
                return redirect(f"/code?error=代碼已被使用完畢")
            else:
                if current_user.id in code["user"]:
                    return redirect(f"/code?error=你已經兌換過")
                with open(f"data/user.json", "r")as f:
                    udata = json.load(f)
                code["user"].append(current_user.id)
                data[request.form["code"]]=code
                udata[str(current_user.id)]["money"]+=code["money"]
                with open(f"data/user.json", "w")as f:
                    json.dump(udata, f)
                with open(f"data/code.json", "w")as f:
                    json.dump(data, f)
                return redirect(f"/shop")
        except:
            return redirect(f"/code?error=錯誤的代碼")
    return render_template("code.html", shop=config["shop"], resource=get["resource"], user=current_user, server=get["server"], now=get["now"])


@app.route("/login")
def login():
    url = config["oauth"]["url"]
    id = config["oauth"]["id"]
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={id}&redirect_uri={url}oauth/callback&response_type=code&scope=identify%20guilds%20email")


@app.route("/logout")
def logout():
    session.pop("access_token")
    return redirect("/")


@app.route("/oauth/callback")
def oauth_callback():
    code = request.args["code"]
    url = config["oauth"]["url"]
    access_token = client.oauth.get_access_token(
        code, redirect_uri=f"{url}oauth/callback"
    ).access_token
    session["access_token"] = access_token
    return redirect("/log")


@app.route("/log")
def log():
    access_token = session.get("access_token")

    if not access_token:
        return redirect("/")

    bearer_client = APIClient(access_token, bearer=True)
    current_user = bearer_client.users.get_current_user()
    return redirect("/")


app.run(host=config["boardmate"]["host"],
        port=config["boardmate"]["port"], debug=True)
