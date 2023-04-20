import json

print("歡迎使用BoardMate自動設定程式\n\n")

with open ("./setting.json","r")as f:
    data=json.load(f)

print("----------------------------")
print("discord oautch設定")

data["oauth"]["bot_token"] = input(f"機器人token: ")
data["oauth"]["client_secret"] = input(f"client_secret: ")
data["oauth"]["url"] = input(f"boardmate網址: ")

with open ("./setting.json","w+")as f:
    json.dump(data,f)

print("----------------------------")
print("pterodactyl設定")

data["pterodactyl"]["url"] = input(f"pterodactyl面板網址: ")
data["pterodactyl"]["key"] = input(f"pterodactyl api key: ")

with open ("./setting.json","w+")as f:
    json.dump(data,f)

print("----------------------------")
print("boardmate設定")

data["boardmate"]["port"] = int(input(f"boardmate運行端口: "))

with open ("./setting.json","w+")as f:
    json.dump(data,f)

with open ("./setting.json","r")as f:
    data=json.load(f)


print("----------------------------")
print("設定成功 以下是你的設定")
print(data)