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
    return "awa"
    
app.run(host=config["boardmate"]["host"],port=config["boardmate"]["port"],debug=True)