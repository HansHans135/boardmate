import json
import os
eggs={}
all = os.listdir("./")

for i in all:
    if ".json" in i:
        print(i)
        with open (f"./{i}","r")as f:
            data=json.load(f)
        eggs[data["name"]]={}
        eggs[data["name"]]["egg_id"]=0
        eggs[data["name"]]["startup"]=data["startup"].replace('"',"'")
        for d in data["docker_images"]:
            eggs[data["name"]]["docker_image"]=d
        eggs[data["name"]]["environment"]={}
        for a in data["variables"]:
            
            eggs[data["name"]]["environment"][a["env_variable"]]=a["default_value"]
print("========複製以下內容========")
print(json.dumps(eggs))
#print(eggs)