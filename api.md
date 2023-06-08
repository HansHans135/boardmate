# api
請求位置 `/api`<br>
api key可以在資料夾`/data/api.txt`裡面第一行找到 <br>
(若未出現api.txt請啟動一次`app.py`)<br>
(若需創建新的key請刪除`api.txt`並重新運行`app.py`)

## /api/code
創建/編輯兌換碼

- curl
```curl
curl -X POST -d "key=你的api_key&name=代碼名稱&money=金額&use=可使用次數" https://your.url/api/code

```
- python
```py
import requests

data = {
    "key": "你的api_key",
    "name":"代碼名稱",
    "money":50, #金額
    "use":10 #可使用次數
    }
a = requests.post(url="https://your.url/api/code",data=data)
print(a.text)

```