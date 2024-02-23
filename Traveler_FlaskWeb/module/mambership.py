# -*- coding: utf-8 -*-

#%% === 會員系統 ============================

import re
import sqlite3
import pandas as pd
from flask_mail import Message # pip3 install Flask-Mail
from flask import render_template, request, redirect, url_for, session
from email.utils import formataddr

from .generic import Generic

# ※※※ 會員系統-路由呼叫用 ※※※
class MembershipManager:
    def __init__(self, database):
        self.database = database
        self.generic = Generic()
        self.membership_tools = MembershipTools(database=self.database)
    
    # 註冊新會員
    def register(self, mail):
        if request.method == "POST":
            account = request.form["account"]
            password = request.form["password"]
            confirmPassword = request.form["confirmPassword"]
            username = request.form["username"]
            email = request.form["email"]
            
            # ↓透過re檢查填寫的資料是否不符某些規定
            # 於前端表單也加入相同設置，可使伺服器減少接收一些不必要的request
            if not re.match(r"^[\w\u4e00-\u9fa5\u0800-\u4e00\u3040-\u30FF]{2,12}$", username) or not re.match(r".+@.+$", email) or not re.match(r"^[A-Za-z]\w{3,11}$", account) or not re.match(r"^(?=.*[A-Za-z])(?=.*\d)\w{6,12}$", password):
                # 註冊填寫的內容有問題時，需重新填寫，但自動填入上次已打好的資料於輸入框
                return render_template("register.html", rgs=2, error_msg="資料填寫方式有誤！請重新確認填寫規則。",
                                        account=account, password=password, confirmPassword=confirmPassword, username=username, email=email)

            if confirmPassword != password:
                # 密碼與確認密碼不一致。
                return render_template("register.html", rgs=2, error_msg="密碼與確認密碼不一致！",
                                        account=account, password=password, confirmPassword=confirmPassword, username=username, email=email)

            # ↓透過兩個自訂函式分別檢查帳號名稱或Email是否有被註冊過 (該兩項資料不允許重複)
            if self.membership_tools.is_overlap_taken(account):
                return render_template("register.html", rgs=2, error_msg="該帳號名稱已被註冊！",
                                        account=account, password=password, confirmPassword=confirmPassword, username=username, email=email)
            if self.membership_tools.is_overlap_taken(email):
                return render_template("register.html", rgs=2, error_msg="該Email已被用來註冊過！",
                                        account=account, password=password, confirmPassword=confirmPassword, username=username, email=email)
        
            # ↓先用自訂函式產生一組英數混合的8碼隨機驗證碼
            rdCode = self.generic.generate_random_string()
            # ↓用自訂函式寄送驗證信
            try:
                self.membership_tools.send_verify_email(username, account, email, rdCode, mail)
            except Exception: # 如果使用者輸入的是無效的Email或網路有問題，需進行此例外處理
                return render_template("register.html", rgs=2, error_msg="無效的Email！",
                                        account=account, password=password, confirmPassword=confirmPassword, username=username, email=email)

            # ↓以上檢查皆通過、Email也是有效地址，則開始寫入資料庫
            query = f"""
                    INSERT INTO membership (username, email, account, password, verify)
                    VALUES ('{username}', '{email}', '{account}', '{password}', '{rdCode}')
                    """
            with sqlite3.connect(self.database, check_same_thread=False) as conn:
                cs = conn.cursor()
                cs.execute(query)
                cs.close();

            return render_template("register.html", rgs=1,
                                    username="", email="", account="", password="")

        elif request.method == "GET":
            return render_template("register.html", rgs=0,
                                       username="", email="", account="", password="")
    
    # 進行登入
    def login(self):
        if request.method == "POST":
            account = request.form["account"]
            password = request.form["password"]
    
            # ↓以自訂函式檢查資料庫內是否有某條紀錄匹配該對帳號和密碼
            if self.membership_tools.is_correct_pair(account, password):
                # ↓匹配成功則繼續以自訂函式透過該帳號於資料庫找出對應的使用者名稱、email、驗證狀態
                username, email, verify = self.membership_tools.get_user_msg(account)
                
                # verify欄位的值並非 "ok"，代表該帳號尚未通過Email驗證，不予登入
                if verify != "ok":
                    return render_template("login.html", error_msg=f"您尚未驗證Email，請至 {email} 收取驗證信。",
                                           account=account, password=password)
                # ↓ 用session紀錄資訊，以及給「已登入狀態」打上自訂的標記
                session["account"] = account
                session["username"] = username
                session["login_status"] = "ok"
                
                # plans_pakg 是該會員擁有的旅程方案資訊，dict夾帶二維list形式
                plans_pakg = self.membership_tools.get_plans_pakg(account)
                plans = []
                for i in plans_pakg:
                    plans.append(plans_pakg[i][0])
                session["plans_pakg"] = plans_pakg
                session["plans"] = plans
                
                return redirect(url_for("index"))
            else: # 帳號或密碼錯誤時，需重新登入，但自動填入上次已打好的資料於輸入框
                return render_template("login.html", error_msg="帳號或密碼錯誤！請重新輸入。",
                                       account=account, password=password)
        elif request.method == "GET":
            if session.get("login_status") == "ok":
                return redirect(url_for("index")) #若已登入，重導向到首頁的路由函式
            else:
                # 剛進入時，所有輸入欄位都是清空狀態
                return render_template("login.html", error_msg=" ",
                                       username="", account="", password="")
    
    # 進行登出
    def logout(self):
        # 清除 session 裡面所有的資訊
        session.clear()
        return redirect(url_for("index"))
    
    # 驗證成功或失敗的訊息
    def verify_result(self, account, rdCode):
        # 將帳號名稱與驗證用的隨機碼與資料庫的紀錄進行比對
        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM membership WHERE account = ? AND verify = ?", (account, rdCode))
            result = cursor.fetchone()
        if result is None: # 比對失敗
            return render_template("verify_revoke.html", verify_check = 0)
        
        # 如果比對成功，要先修改資料庫裡 verify 欄位，原本是8個英數字元隨機碼，改成"ok"
        query = f"""
                UPDATE membership
                SET verify = 'ok'
                WHERE account = '{account}'
                """
        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            cs = conn.cursor()
            cs.execute(query)
            cs.close()
        return render_template("verify_revoke.html", verify_check = 1)
    
    # 註銷尚未通過Email驗證的帳號
    def revoke_result(self, account, rdCode):
        # 將帳號名稱與驗證用的隨機碼與資料庫的紀錄進行比對
        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM membership WHERE account = ? AND verify = ?", (account, rdCode))
            result = cursor.fetchone()
        if result is None: # 比對失敗
            return render_template("verify_revoke.html", verify_check = 0)
        
        # 如果比對成功，則刪除該筆帳號資料
        query = f"""
                DELETE FROM membership
                WHERE account = '{account}'
                """
        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            cs = conn.cursor()
            cs.execute(query)
            cs.close()
        return render_template("verify_revoke.html", verify_check = -1)

# ※※※ 會員系統-周邊工具 ※※※
class MembershipTools:
    def __init__(self, database):
        self.database = database
        self.generic = Generic()
    
    # 註冊時，以此用來比對帳號或Email是否已被註冊過
    def is_overlap_taken(self, colName):
        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            cursor = conn.cursor()
            if "@" in colName:
                cursor.execute("SELECT * FROM membership WHERE email = ?", (colName,))
            else:   
                cursor.execute("SELECT * FROM membership WHERE account = ?", (colName,))
            result = cursor.fetchone()
        return result is not None

    # 寄送驗證信
    def send_verify_email(self, username, account, email, rd_code, mail):
        msg = Message("【驗證信】感謝您註冊：旅人Traveler", recipients=[f"{email}"])
        msg.sender = formataddr(("旅人Traveler", "rudolphy1987@yahoo.com"))
        msg.html = render_template(r"email_verify.html", username=username, account=account, rdCode=rd_code)
        mail.send(msg)

    # 登入時，檢查輸入的帳號和密碼是否與資料庫中的某一筆記錄匹配
    def is_correct_pair(self, account, password):
        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM membership WHERE account = ? AND password = ?", (account, password))
            result = cursor.fetchone()
        return result is not None

    # 登入時，抓出與該帳號對應的會員基本資訊
    def get_user_msg(self, account):
        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM membership WHERE account = '{account}'")
            result = cursor.fetchone()
            cursor.close()
        return result[0], result[1], result[4] # 分別為username, email, verify
    
    # 登入時，抓出與該帳號對應的會員旅程方案資訊
    def get_plans_pakg(self, account):
        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            cs = conn.cursor()
            cs.execute(f"SELECT trip_ID, trip_Name, trip_Content FROM tripPlan WHERE account = '{account}'")
            result = cs.fetchall()
            cs.close()
        if result==[]: # 如果會員沒有任何方案，就強制生成一個無景點的預設方案
            rdCode = self.generic.generate_random_string()
            plans_pakg = {rdCode: ["預設方案", []]}
        else:
            plans_pakg = {}
            for i in result:
                if i[2] != "":
                    plans_pakg[i[0]] = [i[1], i[2].split("#,?")]
                elif i[2] == "":
                    plans_pakg[i[0]] = [i[1], []]
        return plans_pakg # 形式為一個 dict 夾帶二維list

    # 顯示自己的帳戶資料用：回傳一段以<table>包覆的HTML碼
    def get_self_membership(self, account):
        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            query = f"SELECT * FROM membership WHERE account = {account}"
            df_self = pd.read_sql_query(query, conn)
            table_self = df_self.to_html(index=False)
        return table_self

    # 顯示所有目前已註冊的帳戶資料用：回傳一段以<table>包覆的HTML碼
    def get_all_membership(self):
        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            query = "SELECT * FROM membership"
            df_all = pd.read_sql_query(query, conn)
            table_all = df_all.to_html(index=False)
        return table_all


