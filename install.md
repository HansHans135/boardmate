# 1. 安裝
1. 下載此項目<br>
你也可以使用git

2. 安裝依賴<br>
你可以使用`requirements.txt`或是安裝以下套件
```txt
pteropy
requests
zenora
flask
```

# 2. 配置
1. 將檔案 `example_setting.json` 改名成 `setting.json`
- 以下是解釋
```json
{
    "oauth": {
        "bot_token": "", //discord app機器人token
        "client_secret": "", //discord app用戶端secret
        "url": "http://your.url/", //此面板網址(用於oauth登入導向 請將CUSTOM URL設為 http://your.url/oauth/callback/)
        "id": "", //discord app id
        "webhook":"" //通知位置
    },
    "pterodactyl": {
        "url": "http://yourpterodactyl.url/",  //pterodactyl面板網址
        "key": "" //pterodactyl面板kpi key
    },
    "boardmate": {
        "host": "0.0.0.0", //boardmate運行位置
        "port": 3000,//boardmate運行端口
        "debug":false,
        "recache":true,
        "admins":["851062442330816522"] //管理員Discord User ID
    },
    "server": {
        "node": {
            "node1":1,
            "node2":2
        }, //可用節點(其中nodeX是節點名稱,後面是節點id)
        "eggs": {}, //參考步驟3
        "feature_limits": {
            "databases": 0, //每台伺服器的資料庫數量
            "backups": 1 //每台伺服器的輩分數量
        },
        "default_resource": {
            "memory": 1024, //預設記憶體
            "swap": 0,
            "disk": 1024,//預設空間
            "io": 500,
            "cpu": 100,//預設CPU
            "servers": 3//預設伺服器數量
        }
    },
    "shop": { //商店("資源數量":價錢)
        "cpu": {
            "50": 10,
            "100": 20
        },
        "memory": {
            "512": 10,
            "1024": 20
        },
        "disk": {
            "512": 10,
            "1024": 20
        },
        "server": {
            "1": 10,
            "2": 15
        }
    }
}
```

# 3. egg配置
以[此egg](https://github.com/parkervcp/eggs/blob/master/generic/nodejs/egg-node-js-generic.json)作為範例<br>
1. 下載所需要的egg並和`egg.py`在同一個層級
2. 運行`egg.py`
- 你會得到
```json
"Node.js": {
    "max_resource": {//最高資源限制(0為不限制)
        "memory": 0,
        "disk": 0,
        "cpu": 0
    },
    "egg_id": 19, //此egg在面板上的id
    "startup": "if [[ -d .git ]] && [[ {{AUTO_UPDATE}} == '1' ]]; then git pull; fi; if [[ ! -z ${NODE_PACKAGES} ]]; then /usr/local/bin/npm install ${NODE_PACKAGES}; fi; if [[ ! -z ${UNNODE_PACKAGES} ]]; then /usr/local/bin/npm uninstall ${UNNODE_PACKAGES}; fi; if [ -f /home/container/package.json ]; then /usr/local/bin/npm install; fi; /usr/local/bin/node /home/container/{{JS_FILE}}",
    "docker_image": "ghcr.io/parkervcp/yolks:nodejs_12",
    "environment": {
        "GIT_ADDRESS": "",
        "BRANCH": "",
        "USER_UPLOAD": "0",
        "AUTO_UPDATE": "0",
        "JS_FILE": "index.js",
        "NODE_PACKAGES": "",
        "USERNAME": "",
        "ACCESS_TOKEN": "",
        "UNNODE_PACKAGES": ""
    }
}
```

# 4. run and enjoy!
啟動app.py
