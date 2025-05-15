import sqlite3
import json
import os
import time

class Database:
    def __init__(self, db_file="data/boardmate.db"):
        self.db_file = db_file
        self.init_db()
    
    def init_db(self):
        """初始化資料庫表"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 用戶表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            dc_id TEXT PRIMARY KEY,
            ptero_id INTEGER,
            money INTEGER DEFAULT 0,
            memory INTEGER DEFAULT 0,
            cpu INTEGER DEFAULT 0,
            disk INTEGER DEFAULT 0,
            servers INTEGER DEFAULT 0
        )
        ''')
        
        # API表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL
        )
        ''')
        
        # API日誌表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time INTEGER NOT NULL,
            message TEXT NOT NULL
        )
        ''')
        
        # 代碼表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS codes (
            code TEXT PRIMARY KEY,
            use_limit INTEGER NOT NULL,
            money INTEGER NOT NULL
        )
        ''')
        
        # 代碼使用表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS code_usages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            user_id TEXT NOT NULL,
            FOREIGN KEY (code) REFERENCES codes(code),
            FOREIGN KEY (user_id) REFERENCES users(dc_id),
            UNIQUE(code, user_id)
        )
        ''')
        
        # 檢查API鍵是否存在，如果沒有則建立
        cursor.execute("SELECT key FROM api LIMIT 1")
        api_key = cursor.fetchone()
        if not api_key:
            import random
            import string
            new_key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(50))
            cursor.execute("INSERT INTO api (key) VALUES (?)", (new_key,))
            print(f"  L 初始化API完成，你的新API Key為 {new_key}")
        
        conn.commit()
        conn.close()
        
        # 從舊JSON檔案遷移數據(如果存在)
        self.migrate_from_json()
    
    def migrate_from_json(self):
        """從舊的JSON檔案遷移數據到SQLite"""
        # 遷移用戶資料
        if os.path.isfile("data/user.json"):
            try:
                with open("data/user.json", "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                
                for dc_id, data in user_data.items():
                    # 檢查用戶是否已存在
                    cursor.execute("SELECT dc_id FROM users WHERE dc_id=?", (dc_id,))
                    if not cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO users (dc_id, ptero_id, money, memory, cpu, disk, servers) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (dc_id, data["id"], data["money"], 
                             data["resource"]["memory"], data["resource"]["cpu"], 
                             data["resource"]["disk"], data["resource"]["servers"])
                        )
                        
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"遷移用戶數據時發生錯誤: {e}")
        
        # 遷移API資料
        if os.path.isfile("data/api.json"):
            try:
                with open("data/api.json", "r", encoding="utf-8") as f:
                    api_data = json.load(f)
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                
                # 更新API金鑰
                cursor.execute("UPDATE api SET key = ? WHERE id = 1", (api_data["key"],))
                
                # 遷移日誌數據
                for log in api_data.get("log", []):
                    cursor.execute(
                        "INSERT INTO api_logs (time, message) VALUES (?, ?)",
                        (log["time"], log["message"])
                    )
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"遷移API數據時發生錯誤: {e}")
        
        # 遷移代碼資料
        if os.path.isfile("data/code.json"):
            try:
                with open("data/code.json", "r", encoding="utf-8") as f:
                    code_data = json.load(f)
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                
                for code, data in code_data.items():
                    # 插入代碼數據
                    cursor.execute(
                        "INSERT OR IGNORE INTO codes (code, use_limit, money) VALUES (?, ?, ?)",
                        (code, data["use"], data["money"])
                    )
                    
                    # 插入代碼使用記錄
                    for user_id in data["user"]:
                        try:
                            cursor.execute(
                                "INSERT INTO code_usages (code, user_id) VALUES (?, ?)",
                                (code, user_id)
                            )
                        except sqlite3.IntegrityError:
                            pass  # 忽略重複記錄
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"遷移代碼數據時發生錯誤: {e}")
    
    def get_api_key(self):
        """獲取API金鑰"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT key FROM api LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def add_log(self, message):
        """添加API日誌"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO api_logs (time, message) VALUES (?, ?)", 
                       (int(time.time()), message))
        conn.commit()
        conn.close()
    
    def get_logs(self, limit=100):
        """獲取API日誌"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT time, message FROM api_logs ORDER BY time DESC LIMIT ?", (limit,))
        logs = [{"time": row[0], "message": row[1]} for row in cursor.fetchall()]
        conn.close()
        return logs
    
    def get_user(self, dc_id):
        """獲取用戶資料"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE dc_id = ?", (dc_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                "id": user["ptero_id"],
                "money": user["money"],
                "resource": {
                    "memory": user["memory"],
                    "cpu": user["cpu"],
                    "disk": user["disk"],
                    "servers": user["servers"]
                }
            }
        return None
    
    def get_all_users(self):
        """獲取所有用戶資料"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = {}
        for row in cursor.fetchall():
            users[row["dc_id"]] = {
                "id": row["ptero_id"],
                "money": row["money"],
                "resource": {
                    "memory": row["memory"],
                    "cpu": row["cpu"],
                    "disk": row["disk"],
                    "servers": row["servers"]
                }
            }
        conn.close()
        return users
    
    def ensure_user_exists(self, dc_id, ptero_id=None):
        """確保用戶存在，如不存在則創建"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT dc_id FROM users WHERE dc_id = ?", (dc_id,))
        user = cursor.fetchone()
        
        if not user:
            from utils.ptero_api import get_settings
            settings = get_settings()
            cursor.execute(
                "INSERT INTO users (dc_id, ptero_id, memory, cpu, disk, servers) VALUES (?, ?, ?, ?, ?, ?)",
                (dc_id, ptero_id, 
                 settings["server"]["default_resource"]["memory"],
                 settings["server"]["default_resource"]["cpu"], 
                 settings["server"]["default_resource"]["disk"], 
                 settings["server"]["default_resource"]["servers"])
            )
            conn.commit()
        elif ptero_id and user:
            cursor.execute("UPDATE users SET ptero_id = ? WHERE dc_id = ?", (ptero_id, dc_id))
            conn.commit()
            
        conn.close()
    
    def update_user(self, dc_id, **kwargs):
        """更新用戶資訊"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if "money" in kwargs:
            updates.append("money = ?")
            values.append(kwargs["money"])
        
        if "memory" in kwargs:
            updates.append("memory = ?")
            values.append(kwargs["memory"])
            
        if "cpu" in kwargs:
            updates.append("cpu = ?")
            values.append(kwargs["cpu"])
            
        if "disk" in kwargs:
            updates.append("disk = ?")
            values.append(kwargs["disk"])
            
        if "servers" in kwargs:
            updates.append("servers = ?")
            values.append(kwargs["servers"])
            
        if "ptero_id" in kwargs:
            updates.append("ptero_id = ?")
            values.append(kwargs["ptero_id"])
        
        if updates:
            query = f"UPDATE users SET {', '.join(updates)} WHERE dc_id = ?"
            values.append(dc_id)
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
    
    def get_codes(self):
        """獲取所有代碼"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT code, use_limit, money FROM codes")
        codes = {}
        for row in cursor.fetchall():
            # 獲取該代碼的使用者
            cursor.execute("SELECT user_id FROM code_usages WHERE code = ?", (row["code"],))
            users = [usage[0] for usage in cursor.fetchall()]
            
            codes[row["code"]] = {
                "use": row["use_limit"],
                "money": row["money"],
                "user": users
            }
        conn.close()
        return codes
    
    def add_code(self, code, use_limit, money):
        """新增代碼"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO codes (code, use_limit, money) VALUES (?, ?, ?)", 
                      (code, use_limit, money))
        conn.commit()
        conn.close()
        return {"use": use_limit, "money": money, "user": []}
    
    def delete_code(self, code):
        """刪除代碼"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM code_usages WHERE code = ?", (code,))
        cursor.execute("DELETE FROM codes WHERE code = ?", (code,))
        result = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return result
    
    def use_code(self, code, dc_id):
        """使用代碼"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 檢查代碼是否存在
        cursor.execute("SELECT use_limit, money FROM codes WHERE code = ?", (code,))
        code_info = cursor.fetchone()
        if not code_info:
            conn.close()
            return False, "代碼不存在"
        
        # 檢查用戶是否已經使用過該代碼
        cursor.execute("SELECT COUNT(*) FROM code_usages WHERE code = ? AND user_id = ?", (code, dc_id))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False, "你已經兌換過此代碼"
        
        # 檢查代碼是否已達使用上限
        cursor.execute("SELECT COUNT(*) FROM code_usages WHERE code = ?", (code,))
        if cursor.fetchone()[0] >= code_info["use_limit"]:
            conn.close()
            return False, "代碼已被使用完畢"
        
        # 使用代碼並增加用戶余額
        try:
            cursor.execute("INSERT INTO code_usages (code, user_id) VALUES (?, ?)", (code, dc_id))
            cursor.execute("UPDATE users SET money = money + ? WHERE dc_id = ?", (code_info["money"], dc_id))
            conn.commit()
            conn.close()
            return True, code_info["money"]
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

def get_db():
    """獲取資料庫實例"""
    return Database()
