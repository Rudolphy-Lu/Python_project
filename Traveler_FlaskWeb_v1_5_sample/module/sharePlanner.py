# -*- coding: utf-8 -*-

#%% === 旅程方案分享系統 =============================
 
import sqlite3
from flask import request, jsonify, session, render_template, render_template_string, redirect, url_for

from .generic import Generic

# 旅程方案分享系統
class SharePlanner:
    def __init__(self, database):
        self.database = database
        self.generic = Generic()
        
    # 分享自己的旅程方案供其他會員唯讀
    def share_planView(self):
        target_account = request.json.get("data")  # 要分享的目標帳號
        selected_plan = session.get("selected_plan")  # 當前選擇的方案
        account = session.get("account")  # 使用者帳號

        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            cs = conn.cursor()
            # 檢查目標帳戶是否存在
            cs.execute("SELECT account FROM membership WHERE account = ?", (target_account,))
            result = cs.fetchone()
            if result is None:
                return jsonify({"success": False})
            # 獲取 trip_ID
            cs.execute("SELECT trip_ID FROM tripPlan WHERE account = ? AND trip_Name = ?", (account, selected_plan,))
            trip_ID = cs.fetchone()[0]
            # 生成隨機碼
            rdCode = self.generic.generate_random_string()
            # 在 tripView 表中插入記錄
            query = """
                    INSERT INTO tripView (view_ID, trip_ID, account, provider)
                    VALUES (?, ?, ?, ?)
                    """
            cs.execute(query, (rdCode, trip_ID, target_account, account))

        return jsonify({"success": True})
    
    # 抓出與該帳號對應的可檢視旅程方案(由其他會員分享)的資訊
    def get_plans_view(self, account):
        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            cs = conn.cursor()
            cs.execute(f"SELECT view_ID, trip_ID, provider FROM tripView WHERE account = '{account}'")
            result = cs.fetchall()
            
            plansView_pakg = {}
            for i in result:
                cs.execute(f"SELECT trip_Name, trip_Content FROM tripPlan WHERE trip_ID = '{i[1]}'")
                result2 = cs.fetchone()
                plansView_pakg[i[1]] = [result2[0], result2[1].split("#,?")]
            cs.close()
        return plansView_pakg # 形式為一個 dict 夾帶二維list
    
    # 檢視他人分享的頁面渲染
    def tripView(self):
        if session.get("login_status") == "ok": # 檢查 session 中的使用者登錄狀態
            account = session.get("account") # 從 session 中獲取相關資訊
            username = session.get("username")
            plansView_pakg = self.get_plans_view(account)
            plansView = []
            for i in plansView_pakg:
                plansView.append(plansView_pakg[i][0])
            session["plansView_pakg"] = plansView_pakg
            session["plansView"] = plansView

            return render_template("tripView.html",
                                login_code=1, username=username,
                                plansView=plansView)
        else: # 要使用此頁面，就必須登入。尚未登入則導向登入頁面
            return redirect(url_for("login"))
        
    # 點選他人分享的方案
    def select_planView(self):
        plansView_pakg = session.get("plansView_pakg")
        selected_planView = request.form.get("planView")

        placeView = []
        for i, j in plansView_pakg.items():
            if j[0] == selected_planView:
                placeView = j[1] # 被選中的方案其相應的景點list
                break
        
        images = [] # 初始化：被選中的方案其相應的各景點縮圖
        if placeView != []:
            with sqlite3.connect(self.database, check_same_thread=False) as conn:
                cs = conn.cursor()
                for i in placeView:
                    if ("縣：" in i) or ("市：" in i):
                        i = i[4:]
                    cs.execute(f"SELECT sightIMGs FROM attractions WHERE sightName = '{i}';")
                    result = cs.fetchone()
                    if result != None: # 資料表內有對應的景點名稱，給予表內的URL字串
                        images.append(result[0])
                    else: # 資料表內沒有對應的景點名稱，給予固定的預設圖片
                        images.append("https://www.taiwan.net.tw/images/noPic.jpg")
        
        # 創建包含相關資訊的HTML片段
        place_html = render_template_string(
            """
            {% for title, image in items %}
                <div class="box">
                    <img src="{{ image }}" alt="{{ title }}">
                    <p class="sight_title">{{ title }}</p>
                    <div class="box-buttons">
                        <button class="map-btn">地圖</button>
                        <!-- <button class="delete-btn2">刪除</button> -->
                    </div>
                </div>
            {% endfor %}
            """,
            items=zip(placeView, images)
        )
        
        if len(placeView)==0:
            method, param = "place", "&q=臺灣"
        else:
            if len(placeView)==1:
                method, param = "place", f"&q={placeView[0]}"
            elif len(placeView)==2:
                method, param = "directions", f"&origin={placeView[0]}&destination={placeView[1]}"
            elif len(placeView)>=3:
                waypoints = "|".join(placeView[1:-1])
                method, param = "directions", f"&origin={placeView[0]}&destination={placeView[-1]}&waypoints={waypoints}"
                
        gmap_html = f'''
            <iframe
              width="100%"
              style="border:0; aspect-ratio: 6 / 5;"
              loading="lazy"
              allowfullscreen=""
              referrerpolicy="no-referrer-when-downgrade"
              src="https://www.google.com/maps/embed/v1/{method}?key=xxxxxxxx-xxxxxxx{param}"
            >
            </iframe>
        '''

        session["selected_planView"] = selected_planView
        return jsonify(success=True, selected_planView=selected_planView, place_html=place_html, gmap_html=gmap_html)
    
    # 刪除他人分享而來的方案
    def delete_planView(self):
        plansView = session.get("plansView")
        plansView_pakg = session.get("plansView_pakg")
        planView = request.form.get("planView")

        if planView in plansView:
            plansView.remove(planView)
            for i, j in plansView_pakg.items():
                if j[0] == planView:
                    del plansView_pakg[i] # 刪除dict的指定元素
                    with sqlite3.connect(self.database, check_same_thread=False) as conn:
                        cs = conn.cursor()
                        cs.execute(f"DELETE FROM tripView WHERE trip_ID = '{i}';")
                        conn.commit()
                    break

        session["plansView"] = plansView
        session["plansView_pakg"] = plansView_pakg
        return jsonify(success=True, plansView=plansView)


