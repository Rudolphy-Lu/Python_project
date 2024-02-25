# -*- coding: utf-8 -*-

# ★★★ 本檔案為「旅人 Traveler」專案主程式 ★★★
# 單機測試方式：由首頁 http://localhost:5000/ 網址進入
#%%---------------------------------------------------

from flask import Flask
from flask_mail import Mail # pip3 install Flask-Mail
from flask_session import Session # pip3 install Flask-Session

# 匯入自定義類別
from module.generic import Generic
from module.mambership import MembershipManager
from module.recommendation import SightsRecommendation
from module.tripPlanner import TripPlanner
from module.sharePlanner import SharePlanner

database="data/traveler.db"
# 建立各個自訂類別的實例
generic = Generic()
membership_manager = MembershipManager(database)
sights_recommend = SightsRecommendation(database)
trip_planner = TripPlanner(database)
share_planner = SharePlanner(database)

app = Flask(__name__)
app.config["SECRET_KEY"] = "xxxxxxxxxxxx" # 設置一個金鑰用於加密 session 資料
app.config["SESSION_TYPE"] = "filesystem"  # 將 Session 存儲在伺服器端的檔案系統中
app.config["MAIL_SERVER"] = "smtp.mail.yahoo.com"
app.config["MAIL_PORT"] = 587 # Yahoo Mail 使用的port
app.config["MAIL_USERNAME"] = "xxxxxx@yahoo.com"
app.config["MAIL_PASSWORD"] = "xxxxxxxxxxxxxxxxxxxxxxxxxxx" # 此參數為獨有的，不能隨意分享予他人
app.config["MAIL_USE_TLS"] = True # TLS與SSL的設置，在Gmail與Yahoo是相反的
app.config["MAIL_USE_SSL"] = False
mail = Mail(app)
Session(app)

#%% ============================================
# 首頁的route
@app.route("/")
def index():
    return generic.to_index()
    
#%% === 會員系統 ================================

# 註冊新會員的route
@app.route("/register", methods=["GET", "POST"])
def register():
    return membership_manager.register(mail)

# 進行登入的route
@app.route("/login", methods=["GET", "POST"])
def login():
    return membership_manager.login()

# 進行登出的route
@app.route("/logout")
def logout():
    return membership_manager.logout()

# 驗證成功或失敗的訊息頁面
@app.route("/verify/account=<account>&rdCode=<rdCode>", methods=["GET"])
def verify_result(account, rdCode):
    return membership_manager.verify_result(account, rdCode)

# 註銷尚未通過Email驗證的帳號
@app.route("/revoke/account=<account>&rdCode=<rdCode>", methods=["GET"])
def revoke_result(account, rdCode):
    return membership_manager.revoke_result(account, rdCode)

#%% === 景點展示與挑選系統 ============================

# 全臺景點展示
@app.route("/allrecommend",methods = ["POST", "GET"])
def allrecommend():
    return sights_recommend.allrecommend()

# 地區景點展示-縣市選單頁面
@app.route("/areapage",methods = ["POST", "GET"])
def areapage():
    return sights_recommend.areapage()

# 地區景點展示-特定縣市的頁面。<cName> 為中文縣市名稱
@app.route("/areapage/cName=<cName>", methods = ["POST","GET"])
def area_recommend(cName):
    return sights_recommend.area_recommend(cName)
    
# 景點展示頁面的+號按鈕新增方案
@app.route("/recommend_add_plan", methods=["POST"])
def recommend_add_plan():
    return sights_recommend.recommend_add_plan()

#%% === 旅程方案規劃系統 =========================

# 行程規劃頁面渲染
@app.route("/tripPlanning")
def tripPlanning():
    return trip_planner.tripPlanning()

# 新增方案
@app.route("/add_plan", methods=["POST"])
def add_plan():
    return trip_planner.add_plan()

# 重新命名方案
@app.route("/rename_plan", methods=["POST"])
def rename_plan():
    return trip_planner.rename_plan()

# 刪除方案
@app.route("/delete_plan", methods=["POST"])
def delete_plan():
    return trip_planner.delete_plan()

# 點選方案
@app.route("/select_plan", methods=["POST"])
def select_plan():
    return trip_planner.select_plan()

# 景點更新 (新增/刪除/調換順序)
@app.route("/update_box_order", methods=["POST"])
def update_box_order():
    return trip_planner.update_box_order()

# 行程方案與景點清單保存
@app.route("/confirm_save", methods=["POST"])
def confirm_save():
    return trip_planner.confirm_save()

#%% === 旅程方案分享系統 ==========================

# 分享自己的旅程方案供其他會員唯讀
@app.route("/share_planView", methods=["POST"])
def share_planView():
    return share_planner.share_planView()

# 檢視他人分享的頁面渲染
@app.route("/tripView")
def tripView():
    return share_planner.tripView()

# 點選他人分享的方案
@app.route("/select_planView", methods=["POST"])
def select_planView():
    return share_planner.select_planView()

# 刪除他人分享而來的方案
@app.route("/delete_planView", methods=["POST"])
def delete_planView():
    return share_planner.delete_planView()

#%% ===========================================
if __name__ == "__main__":
    app.run(debug=False)
    # 單機內測只打開上面那一行，線上部署則關閉上一行，開啟下方三行
    # import os
    # port = int(os.environ.get("PORT", 8000))
    # app.run(host="0.0.0.0", debug=False, port=port)