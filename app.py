from flask import Flask, render_template, request, redirect, session, jsonify
from zenora import APIClient
from pteropy import Pterodactyl_Application
import json

app = Flask(__name__)

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

    with open("data/user.json", "r")as f:
        data = json.load(f)
    try:
        resource = data[str(current_user.id)]["resource"]
    except:
        data[str(current_user.id)] = {
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
    url = f'{ptero.url}/api/application/users'
    headers = {
    "Authorization": f"Bearer {ptero.url}",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "cookie": "pterodactyl_session=eyJpdiI6InhIVXp5ZE43WlMxUU1NQ1pyNWRFa1E9PSIsInZhbHVlIjoiQTNpcE9JV3FlcmZ6Ym9vS0dBTmxXMGtST2xyTFJvVEM5NWVWbVFJSnV6S1dwcTVGWHBhZzdjMHpkN0RNdDVkQiIsIm1hYyI6IjAxYTI5NDY1OWMzNDJlZWU2OTc3ZDYxYzIyMzlhZTFiYWY1ZjgwMjAwZjY3MDU4ZDYwMzhjOTRmYjMzNDliN2YifQ%253D%253D"
}

    response = requests.request('GET', url, data=payload, headers=headers)
    for i in response.json()["data"]:
        if i["attributes"]["email"] == current_user.email:
            uid=i["attributes"]["id"]

    url = f'{ptero.url}/api/application/servers'
    headers = {
        "Authorization": f"Bearer {ptero.key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        }

    response = requests.request('GET', url, headers=headers)
    server={}
    for i in response.json()["data"]:
        if i["attributes"]["user"] == uid:
            server[i["attributes"]["name"]]=i["attributes"]["limits"]

    return render_template("index.html", resource=resource, user=current_user,server=server)


@app.route("/server/add")
def add():
    access_token = session.get("access_token")

    if not access_token:
        return render_template("login.html")

    bearer_client = APIClient(access_token, bearer=True)
    current_user = bearer_client.users.get_current_user()

    with open("data/user.json", "r")as f:
        data = json.load(f)
    try:
        resource = data[str(current_user.id)]["resource"]
    except:
        return redirect("/")
    return render_template("add.html", resource=resource, user=current_user)


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
