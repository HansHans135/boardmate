# API 使用文檔

## 概述
此API允許您與伺服器資源、用戶數據以及代碼管理進行交互。它使用Flask構建，提供獲取和更新用戶及伺服器數據的端點，並管理代碼和日誌。

### 基本URL
所有API端點都以 `/api` 為前綴。

### 驗證
所有API請求都需要一個有效的 `API Key`。此Key會在伺服器啟動時自動生成，用於POST和DELETE請求的授權。

---

## 端點


### 獲取或更新用戶數據

- **URL**: `/api/user/<dc_user_id>`
- **方法**: `GET`, `POST`
- **描述**: 
  - `GET`: 根據Discord用戶ID獲取用戶數據。
  - `POST`: 更新用戶的金錢和資源分配（記憶體、硬碟、CPU、伺服器數量）。

#### 參數（POST）:
- `key` (必填): 您的API Key。
- `money`, `memory`, `disk`, `cpu`, `servers` (可選): 您要更新的用戶數據值。

#### 範例回應 (GET):
```json
{
    "money": 5269,
    "now": {
        "cpu": 50,
        "disk": 1024,
        "memory": 1024,
        "servers": 1
    },
    "resource": {
        "cpu": 100,
        "disk": 5120,
        "memory": 5120,
        "servers": 3
    },
    "server": {
        "22389661": {
            "cpu": 50,
            "description": "",
            "disk": 1024,
            "id": "22389661",
            "io": 500,
            "memory": 1024,
            "name": "My Python Server",
            "oom_disabled": false,
            "swap": 0,
            "threads": null,
            "url": "https://fmdb.maybeisfree.host/server/22389661"
        }
    }
}
```

#### Python範例 (POST):
```python
import requests

data = {
    'key': 'your_api_key',
    'money': 200,
    'memory': 4096
}
response = requests.post('http://yourapi.com/api/user/123456', data=data)
print(response.json())
```

---

### 管理代碼

- **URL**: `/api/code`
- **方法**: `GET`, `POST`, `DELETE`
- **描述**: 
  - `GET`: 獲取所有代碼。
  - `POST`: 新增或更新代碼。
  - `DELETE`: 刪除代碼。

#### 參數 (POST/DELETE):
- `key` (必填): 您的API Key。
- `code` (必填): 您想管理的代碼。
- `use`, `money` (POST必填): 代碼的使用次數和金錢數量。

#### 範例回應 (POST):
```json
{
  "user": [],
  "use": 5,
  "money": 100
}
```

#### Python範例 (POST):
```python
import requests

data = {
    'key': 'your_api_key',
    'code': 'MYCODE',
    'use': 5,
    'money': 100
}
response = requests.post('http://yourapi.com/api/code', data=data)
print(response.json())
```

#### Python範例 (DELETE):
```python
import requests

data = {
    'key': 'your_api_key',
    'code': 'MYCODE'
}
response = requests.delete('http://yourapi.com/api/code', data=data)
print(response.status_code)
```

---

### 日誌管理

每當用戶數據更新或管理代碼時，日誌會自動添加，並保存到 `data/api.json`。

---

## 錯誤碼

- `403`: API Key 錯誤。當提供的API Key不正確時返回。
- `404`: 找不到。當請求的用戶或代碼不存在時返回。

---

### 設置說明

1. 確保 `setting.json` 包含Discord OAuth和Pterodactyl API的必要配置。
2. 運行後端程式，會自動生成 `API Key`。

---