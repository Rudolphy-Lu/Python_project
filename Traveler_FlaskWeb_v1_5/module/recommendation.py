# -*- coding: utf-8 -*-

#%% === 景點展示系統 ============================

import threading
import sqlite3
import random
import pandas as pd
from flask import render_template, session, request, jsonify

# 景點展示系統
class SightsRecommendation:
    def __init__(self, database):
        self.database = database
        
    # 全臺景點隨機展示
    def allrecommend(self):
        unique_cNames = ("臺北市","新北市","基隆市","宜蘭縣","桃園市",
                         "新竹縣","新竹市","苗栗縣","臺中市","彰化縣",
                         "南投縣","雲林縣","嘉義縣","嘉義市","臺南市",
                         "高雄市","屏東縣","花蓮縣","臺東縣")
        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            # 從上面指定的地區名稱中隨機選取12個 (此名單不含離島縣市)
            random_cNames = random.sample(unique_cNames, 12)

            # 使用 multi-thread 搭配迴圈，從每個隨機選取的地區中隨機選擇一條資料
            df_temp_list = []
            def random_sight(num):
                for cName in random_cNames[num:num+3]:
                    query = """
                        SELECT * 
                        FROM attractions
                        WHERE cName = ?
                        ORDER BY RANDOM()
                        LIMIT 1;
                    """
                    df_temp_list.append(pd.read_sql_query(query, conn, params=(cName,)))
            threads = [threading.Thread(target=random_sight, args=(num,)) for num in range(0,10,3)]
            for th in threads:
                th.start()
                th.join()
            df_attractions = pd.concat([i for i in df_temp_list], ignore_index=True)
        area_attractions = df_attractions.to_dict("records")

        if session.get("login_status") == "ok": # 檢查 session 中的使用者登錄狀態
            username = session.get("username") # 從 session 中獲取需要的資訊
            plans = session.get("plans")
            
            return render_template("recommend.html",
                                   login_code=1, username=username, cName="隨機挑選",
                                   plans=plans, area_attractions=area_attractions
                                   )
        else: # 未登入狀態
            return render_template("recommend.html", cName="為您隨機挑選",
                                   area_attractions=area_attractions)
        
    # 地區景點展示-縣市選單頁面
    def areapage(self):
        # 地區頁面
        cNames = {"north": ("臺北市","新北市","基隆市","宜蘭縣","桃園市","新竹縣","新竹市"),
                  "central": ("苗栗縣","臺中市","彰化縣","南投縣","雲林縣"),
                  "south": ("嘉義縣","嘉義市","臺南市","高雄市","屏東縣"),
                  "east": ("花蓮縣","臺東縣")
                  }

        if session.get("login_status") == "ok": # 檢查 session 中的使用者登錄狀態
            username = session.get("username") # 從 session 中獲取使用者暱稱資訊
            return render_template("areapage.html", cNames=cNames,
                                   login_code=1, username=username
                                   )
        else: # 未登入狀態
            return render_template("areapage.html", cNames=cNames)
        
    # 地區景點展示-特定縣市的頁面。<cName> 為中文縣市名稱
    def area_recommend(self, cName):
        # 地區景點展示
        with sqlite3.connect(self.database, check_same_thread=False) as conn:
            query = f"""
                    SELECT * 
                    FROM attractions
                    WHERE cName = '{cName}';
                    """
            df_attractions = pd.read_sql_query(query, conn)
        area_attractions = df_attractions.to_dict("records")

        if session.get("login_status") == "ok": # 檢查 session 中的使用者登錄狀態
            username = session.get("username")
            plans = session.get("plans")
            return render_template("recommend.html",
                                   login_code=1, username=username, cName=cName,
                                   plans=plans, area_attractions=area_attractions)
        else:
            return render_template("recommend.html",
                                   cName=cName, area_attractions=area_attractions)
    
    # 景點展示頁面的+號按鈕新增方案
    def recommend_add_plan(self):
        # 新增計劃
        try:
            plans_pakg = session.get("plans_pakg")
            data = request.json
            selected_plan = data.get('selectedPlan')
            sight_name = data.get('sightName')
            city_name = data.get('cityName')

            for i, j in plans_pakg.items():
                if j[0] == selected_plan:
                    if city_name != "隨機挑選":
                        j[1].append(city_name+"："+sight_name)
                    else:
                        with sqlite3.connect(self.database, check_same_thread=False) as conn:
                            cs = conn.cursor()
                            cs.execute(f"SELECT cName FROM attractions WHERE sightName = '{sight_name}';")
                            result = cs.fetchone()
                        j[1].append(result[0]+"："+sight_name)
                    plans_pakg[i] = [selected_plan, j[1]]
                    break

            session["plans_pakg"] = plans_pakg
            return jsonify(success=True, message="景點新增成功！")
        except Exception:
            return jsonify(success=False, message="景點新增失敗！")


