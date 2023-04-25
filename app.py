from flask import Flask, render_template, request, redirect, session,jsonify
from zenora import APIClient
import json
app = Flask(__name__)

with open ("./setting.json","r")as f:
    config=json.load(f)
client = APIClient(config["oauth"]["bot_token"], client_secret=config["oauth"]["client_secret"])
app.config["SECRET_KEY"] = "mysecret"

@app.route("/")
def home():
    return render_template("index.html")
    

@app.route("/login")
def login():
    url=config["oauth2"]["url"]
    id=url=config["oauth2"]["id"]
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={id}&redirect_uri={url}%2Foauth%2Fcallback&response_type=code&scope=identify%20email")


@app.route("/logout")
def logout():
    session.pop("access_token")
    return redirect("/")


@app.route("/oauth/callback")
def oauth_callback():
    code = request.args["code"]
    url=config["oauth2"]["url"]
    access_token = client.oauth.get_access_token(
        code, redirect_uri=f"{url}/oauth/callback"
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

app.run(host=config["boardmate"]["host"],port=config["boardmate"]["port"],debug=True)