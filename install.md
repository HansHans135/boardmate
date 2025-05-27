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
        "key": "" //pterodactyl面板api key
    },
    "boardmate": {
        "host": "0.0.0.0", //boardmate運行位置
        "port": 3000,//boardmate運行端口
        "debug":false,
        "account_sharing":false,//允許分帳
        "recache":true,
        "admins":["851062442330816522"] //管理員Discord User ID
    },
    "server": {
        "node": {
            "node1":1,
            "node2":2
        }, //可用節點(其中nodeX是節點名稱,後面是節點id)
        "eggs": {
            "Node.js": {
            "max_resource": {//最高資源限制(0為不限制)
                "memory": 0,
                "disk": 0,
                "cpu": 0
            },
            "egg_id": 19, //此egg在面板上的id
            "nest_id": 5,//此egg在nest的id
            }
        }, //以此類推增加更多類類型
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

# 3. run and enjoy!
啟動app.py
