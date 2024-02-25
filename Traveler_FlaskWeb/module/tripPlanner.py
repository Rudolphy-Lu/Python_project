# -*- coding: utf-8 -*-

#%% === 旅程方案規劃系統 =============================

import sqlite3
import pandas as pd
from flask import session, render_template, redirect, url_for, request, jsonify, render_template_string

from .generic import Generic

# 旅程方案規劃系統
class TripPlanner:
    def __init__(self, database):
        self.database = database
        self.generic = Generic()
        
    # 行程規劃頁面渲染
    def tripPlanning(self):
        if session.get("login_status") == "ok": # 檢查 session 中的使用者登錄狀態
            username = session.get("username") # 從 session 中獲取相關資訊
            plans = session.get("plans")
            return render_template("tripPlanning.html",
                                login_code=1, username=username,
                                plans=plans)
        else: # 要使用此頁面，就必須登入。尚未登入則導向登入頁面
            return redirect(url_for("login"))
        
    # 新增方案
    def add_plan(self):
        plans = session.get("plans")
        plans_pakg = session.get("plans_pakg")
        plan = request.form.get("plan")
        if plan:
            if plan in plans: # 已存在同名的方案名稱
                return jsonify(success=False, plans=plans)
            rdCode = self.generic.generate_random_string()
            plans.append(plan)
            plans_pakg[rdCode] = [plan, []]

        session["plans"] = plans
        session["plans_pakg"] = plans_pakg
        return jsonify(success=True, plans=plans)
    
    # 重新命名方案
    def rename_plan(self):
        plans = session.get("plans")
        plans_pakg = session.get("plans_pakg")
        old_plan = request.form.get("old_plan")
        new_plan = request.form.get("new_plan")
        if old_plan in plans:
            if new_plan in plans: # 已存在同名的方案名稱
                return jsonify(success=False, plans=plans)
            index = plans.index(old_plan)
            plans[index] = new_plan
            for i, j in plans_pakg.items(): # 修改dict的內容
                if j[0] == old_plan:
                    plans_pakg[i] = [new_plan, j[1]]
                    break

        session["plans"] = plans
        session["plans_pakg"] = plans_pakg
        return jsonify(success=True, plans=plans)
    
    # 刪除方案
    def delete_plan(self):
        plans = session.get("plans")
        plans_pakg = session.get("plans_pakg")
        plan = request.form.get("plan")
        if plan in plans:
            plans.remove(plan)
            for i, j in plans_pakg.items():
                if j[0] == plan:
                    del plans_pakg[i] # 刪除dict的指定元素
                    break
        
        if plans == []: # 如果會員把方案都刪光，就強制生成一個無景點的預設方案
            rdCode = self.generic.generate_random_string()
            plans = ["預設方案"]
            plans_pakg = {rdCode: ["預設方案", []]}

        session["plans"] = plans
        session["plans_pakg"] = plans_pakg
        return jsonify(success=True, plans=plans)
    
    # 點選方案
    def select_plan(self):
        plans_pakg = session.get("plans_pakg")
        selected_plan = request.form.get("plan")
        
        place = [] # 初始化：被選中的方案其相應的景點list -方案被點擊時動態生成
        for i, j in plans_pakg.items():
            if j[0] == selected_plan:
                place = j[1]
                break
        
        images = [] # 初始化：被選中的方案其相應的各景點縮圖
        if place != []:
            with sqlite3.connect(self.database, check_same_thread=False) as conn:
                cs = conn.cursor()
                for i in place:
                    if ("縣：" in i) or ("市：" in i):
                        i = i[4:]
                    cs.execute(f"SELECT sightIMGs FROM attractions WHERE sightName = '{i}';")
                    result = cs.fetchone()
                    if result != None: # 資料表內有對應的景點名稱，給予表內的圖片URL
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
                        <button class="delete-btn2">刪除</button>
                    </div>
                </div>
            {% endfor %}
            """,
            items=zip(place, images)
        )
        
        if len(place)==0:
            method, param = "place", "&q=臺灣"
        else:
            if len(place)==1:
                method, param = "place", f"&q={place[0]}"
            elif len(place)==2:
                method, param = "directions", f"&origin={place[0]}&destination={place[1]}"
            elif len(place)>=3:
                waypoints = "|".join(place[1:-1])
                method, param = "directions", f"&origin={place[0]}&destination={place[-1]}&waypoints={waypoints}"
                
        gmap_html = f'''
            <iframe
              width="100%"
              style="border:0; aspect-ratio: 6 / 5;"
              loading="lazy"
              allowfullscreen=""
              referrerpolicy="no-referrer-when-downgrade"
              src="https://www.google.com/maps/embed/v1/{method}?key=xxxxx-xxxxxx{param}"
            >
            </iframe>
        '''

        session["selected_plan"] = selected_plan
        return jsonify(success=True, selected_plan=selected_plan, place_html=place_html, gmap_html=gmap_html)
    
    # 景點更新 (新增/刪除/調換順序)
    def update_box_order(self):
        plans_pakg = session.get("plans_pakg")
        selected_plan = session.get("selected_plan")
        data = request.json
        place = data.get("order", [])
        
        for i, j in plans_pakg.items():
            if j[0] == selected_plan:
                plans_pakg[i] = [selected_plan, place]
                break
        
        if len(place)==0:
            gmap_html = "<iframe></iframe>"
        else:
            if len(place)==1:
                method, param = "place", f"&q={place[0]}"
            elif len(place)==2:
                method, param = "directions", f"&origin={place[0]}&destination={place[1]}"
            elif len(place)>=3:
                waypoints = "|".join(place[1:-1])
                method, param = "directions", f"&origin={place[0]}&destination={place[-1]}&waypoints={waypoints}"
                
            gmap_html = f'''
                <iframe
                  width="100%"
                  style="border:0; aspect-ratio: 6 / 5;"
                  loading="lazy"
                  allowfullscreen=""
                  referrerpolicy="no-referrer-when-downgrade"
                  src="https://www.google.com/maps/embed/v1/{method}?key=xxxxx-xxxxxx{param}"
                >
                </iframe>
            '''
            
        session["plans_pakg"] = plans_pakg
        return jsonify({"status": "success", "gmap_html": gmap_html})
    
    # 行程方案與景點清單保存
    def confirm_save(self):
        try:
            account = session.get("account")
            plans_pakg = session.get("plans_pakg")
            trip_id_list, temp = [], []
            for i, j in plans_pakg.items():
                trip_id_list.append(i)
                temp.append([i, j[0], "#,?".join(j[1]), account])
            df = pd.DataFrame(data=temp, columns=["trip_ID", "trip_Name", "trip_Content", "account"])    
            print(trip_id_list)
            
            with sqlite3.connect(self.database, check_same_thread=False) as conn:
                cs = conn.cursor()
                cs.execute(f"DELETE FROM tripPlan WHERE account = '{account}';")
                conn.commit()
                df.to_sql("tripPlan", conn, if_exists="append", index=False)
                
                params = ','.join('?' * len(trip_id_list))
                
                cs.execute(f"DELETE FROM tripView WHERE provider = '{account}' AND trip_ID NOT IN ({params})", tuple(trip_id_list))
                conn.commit()

            return jsonify(success=True, message="保存成功！")
        
        except Exception:
            return jsonify(success=False, message="保存失敗！")


