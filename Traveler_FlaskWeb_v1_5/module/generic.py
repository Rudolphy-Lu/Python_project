# -*- coding: utf-8 -*-

#%% === 通用區 ==============================

import string
import random
from flask import session, render_template

# 首頁與通用工具
class Generic:
    def __init__(self):
        self.characters = string.ascii_letters + string.digits
    
    # 首頁的路由
    def to_index(self):
        if session.get("login_status") == "ok": # 檢查 session 中的使用者登錄狀態
            username = session.get("username") # 從 session 中獲取使用者名稱資訊
            return render_template("index.html", login_code=1, username=username)
        else:
            return render_template("index.html")
    
    # 產生英數混合的隨機碼
    def generate_random_string(self, length=8):
        rd_code = "".join(random.choices(self.characters, k=length))
        return rd_code

