# -*- coding: utf-8 -*-

# 「時空超越者」SMR計算器 電腦網頁版_Flask框架版本
# -----------------------------------------------------------------
# 本檔案 (routes.py) 為「主程式」，
# 所需的資料庫檔案為 data資料夾內的SMR.db

# 本程式提供公共衛生/流行病學研究者，透過輸入要比較的行政區代碼，及篩選研究背景，
# 全自動製作標準化死亡比 (SMR) 互動式圖表。
# -----------------------------------------------------------------

from flask import Flask, render_template, request, flash, redirect, url_for, send_file
import os
import sqlite3
import pandas as pd
import threading

    # 以下三行匯入的是與本程式放在同一個路徑下的自定義模組
from module.smr_preprocessing import foolproof, chinese_name
from module.smr_maker import smr_calculate, start_subthread
from module.smr_plotly import smr_figure

app = Flask(__name__)
app.secret_key = "ebryey54nn64bbw5vb5" # 隨意打，加密用

# 主函式的路由
@app.route("/SMR/", methods = ["POST","GET"])
def main():
    if request.method == "POST":
        error_code = 0 # 用做偵測是否有錯誤來決定程式是否繼續執行的開關
        
        #%%===== 資料庫檔案存在與否的檢查 =========================================
        
        # ↓ 用os.getcwd()獲取python執行檔的路徑，
        # 並偵測data資料夾內的 SMR.db 檔是否有存在，
        # 若存在，才與 SMR.db 進行連線 (且避免創建非必要的空資料檔)
        if os.path.isfile(os.getcwd()+"/data/SMR.db"):
            db_path = os.path.join(os.getcwd(), "data/SMR.db")
                # 使用 check_same_thread=False 參數開啟多執行緒支援
            conn = sqlite3.connect(db_path, check_same_thread=False)
            cs = conn.cursor()
        else:
            error_code = 1
            html_msg = "伺服器的資料庫正在進行維護，目前暫停查詢。"
            flash(html_msg)
            return redirect(url_for("main"))
        #%%===== 行政區代碼輸入框的檢查與資料準備 ==================================
        
        # ↓ 首先對行政區代碼輸入框、性別年齡、死因等資訊分別進行接收與初檢
        if error_code == 0:
            # ↓ 分別接收使用者在網頁的五個輸入框內鍵入的行政區代碼
            dist_ori_1 = request.form.get("dist_ori_1").upper()
            dist_ori_2 = request.form.get("dist_ori_2").upper()
            dist_ori_3 = request.form.get("dist_ori_3").upper()
            dist_ori_4 = request.form.get("dist_ori_4").upper()
            dist_ori_5 = request.form.get("dist_ori_5").upper()

            # ↓ 初步辨識有幾個輸入框內存在資訊，這在之後用來判斷要在折線圖裡畫出幾條SMR線
            dist_ori_pre = [dist_ori_1, dist_ori_2, dist_ori_3, dist_ori_4, dist_ori_5]
            dist_ori_all = [i for i in dist_ori_pre if (i not in ("",",") and i.isspace()==False)]
            del dist_ori_pre
            if dist_ori_all == []:
                error_code = 1
                flash("您尚未輸入任何行政區代碼！")
            
            # ↓ 分別接收使用者在網頁上選定的性別、年齡範圍
            gender_sql = request.form["gender_sql"] # "is not Null"為兩性、"= 2"為女性、"= 1"為男性
            min_agegroup = int(request.form.get("min_agegroup"))
            max_agegroup = int(request.form.get("max_agegroup"))
            if min_agegroup > max_agegroup:
                error_code = 1
                flash("最大年齡必須大於或等於最小年齡！")
                
            # ↓ 接收使用者在網頁勾選的死因，由於是複選，抓取型態為list
            Death_Cause = request.form.getlist("dth_cause")
            if Death_Cause == []:
                error_code = 1
                flash("請勾選至少一項死因！")
            else: # ↓ 轉成特定格式編排的字串，將在後面塞入某段SQL語法內。
                for i in range(len(Death_Cause)):
                    Death_Cause[i] = f"'{Death_Cause[i]}'"
                Death_Cause_sql = ",".join(Death_Cause)
            
            if error_code == 1:
                cs.close(); conn.close()
                # return redirect(url_for("main"))
                return render_template(r"SMR.html", error_code = 1)

        # ↓ 將行政區代碼與行政區中文名稱的對照檔資料表直接拉進DataFrame裡 (僅1欄)
        if error_code == 0:  
            df_Dcode2011 = pd.read_sql_query("SELECT * FROM DistrictCode_2011", conn)    
            
        # ↓ 行政區代碼的進一步防呆檢查與整併
        if error_code == 0:
            dist_ts_all, dist_g_all = [], []
            for i in range(len(dist_ori_all)):
                if error_code == 0:
                    dist_ts, dist_g, error_code, html_msg = foolproof(dist_ori_all[i], df_Dcode2011, error_code)
                    dist_ts_all.append(dist_ts)
                    dist_g_all.append(dist_g)
                    
            if error_code == 1:
                flash(html_msg)
                cs.close(); conn.close()
                # return redirect(url_for("main"))
                return render_template(r"SMR.html", error_code = 1)

        #%%===== 共通資訊的資料準備 (性別、年齡範圍、死因) =====================
        
        if error_code == 0:    
            # ↓ 傳給preprocessing模組的chinese_name函式，找出有效代碼分別對應的行政區中文名，
            # ↓ 以及將前面整併好的代碼轉為特製的字串編排方式，方便後續塞入SQL語法內
            dist_name_all, dist_ts_allsql, dist_g_allsql = [], [], []
            for i in range(len(dist_ori_all)):
                dist_name, dist_ts_sql, dist_g_sql = chinese_name(dist_ts_all[i], dist_g_all[i], df_Dcode2011)
                dist_name_all.append(dist_name)
                dist_ts_allsql.append(dist_ts_sql)
                dist_g_allsql.append(dist_g_sql)
        
            # ↓ 自製「字串產生器」，會根據使用者選擇的性別與年齡範圍，
            # 而動態產生不同的字串，這些產生出的字串將在之後被塞入SQL語法裡。
            pp_age_rangeSUM_m, pp_age_rangeSUM_f = "", ""
            
            for i in range(min_agegroup, max_agegroup+1):
                
                if gender_sql == "is not Null":
                    pp_age_rangeSUM_m += f"SUM(page{i}m),"
                    pp_age_rangeSUM_f += f"SUM(page{i}f),"
                elif gender_sql == "= 2":
                    pp_age_rangeSUM_f += f"SUM(page{i}f),"
                else:
                    pp_age_rangeSUM_m += f"SUM(page{i}m),"
           
            pp_age_rangeSUM = (pp_age_rangeSUM_m + pp_age_rangeSUM_f).rstrip(",")
            del pp_age_rangeSUM_m, pp_age_rangeSUM_f
            
            # ↓ 字串 gender_ch 代表性別的中文內容，將在之後被塞入Plotly繪圖的函式，顯示給使用者看到。
            if gender_sql == "is not Null":
                gender_ch = "兩性"
            elif gender_sql == "= 2":
                gender_ch = "女性"
            else:
                gender_ch = "男性"
            # ↓ 字串 age_text 代表年齡範圍的中文內容，將在之後被塞入Plotly繪圖的函式，顯示給使用者看到。
            if min_agegroup == 1 and max_agegroup == 19:
                age_text = "全年齡"
            elif max_agegroup == 19:
                if min_agegroup == 2:
                    age_text = "1歲以上"
                else:
                    age_text = f"{(min_agegroup-2)*5}歲以上"
            elif min_agegroup == 1:
                if max_agegroup == 1:
                    age_text = "未滿1歲(嬰兒)"
                else:
                    age_text = f"未滿{(max_agegroup-1)*5}歲"
            elif min_agegroup == 2:
                age_text = f"1至{(max_agegroup-1)*5-1}歲"
            else:
                age_text = f"{(min_agegroup-2)*5}至{(max_agegroup-1)*5-1}歲"
            
            # ↓ 撈取死亡率資料表(deathrate_2011)裡，特定死因之死亡率總和(有分年齡與性別)，
            # 由於一律使用全臺灣2011年為基準來進行標準化，撈出來的原始樣式只會有一列。
            query = f"""
                    SELECT {pp_age_rangeSUM}
                    FROM deathrate_2011
                    WHERE deathcause IN ({Death_Cause_sql});
                    """
            df_dth_rate = pd.read_sql_query(query, conn)
            # ↓ 將撈出僅一列的死亡率資料複製成若干列，準備在之後丟進自製函式執行後續任務
            df_dth_rate = pd.concat([df_dth_rate]*(2011-1971+1), ignore_index=True)
            
            # ↓ 將用來轉譯死因中文名詞死因代碼對照檔資料表直接拉進DataFrame裡 (僅1欄)
            df_CauseName = pd.read_sql_query("SELECT * FROM death_cause_name", conn)
            
            # ↓ 利用原本為串列形式的死因種類清單進行死因名詞對照 (後續要顯示至使用者介面)，
            # 隨後將其進行另一種字串編排的轉換，它將被塞入後續其他函式的SQL語法內
            CauseName_str = ""
            for i in range(len(Death_Cause)):
                Death_Cause[i] = Death_Cause[i].strip("'")
                for j in range(len(df_CauseName)):
                    if Death_Cause[i] == df_CauseName.loc[j,'death_cause']:
                        CauseName_str += f"{df_CauseName.loc[j,'name_cht']}、"
            
            # ↓ 字串 CauseName_str 代表死因種類的中文內容，將在之後被塞入Plotly繪圖的函式，顯示給使用者看到。
            CauseName_str = CauseName_str.rstrip("、")
            # ↓ 這個將被塞入下一段函式內的SQL語法
            Death_Cause_sql = ",".join(Death_Cause)
        
        #%%===== 從資料庫撈取人口數與死亡數的資料，正式計算SMR =======================
            
            # ====== 以下為多執行緒的做法：===========================
            
            threads = [] #放置多個挾帶任務的子執行緒物件
            df_SMR_list = []  #設一空串列放置各組SMR計算結果的DataFrame
            # ↓ 先把年份加入，確保之後DataFrame的第一個欄位會是西元年份
            df_SMR_list.append(pd.DataFrame(data=range(1971,2011+1),columns=["year"]))
            
            # ↓ 建立多個挾帶任務的子執行緒保存在一個list裡面
            for i in range(len(dist_ori_all)):
                threads.append(threading.Thread(target=smr_calculate, args=(df_SMR_list, i, conn, cs, pp_age_rangeSUM, dist_ts_allsql[i], dist_g_allsql[i], df_dth_rate, Death_Cause_sql, gender_sql, min_agegroup, max_agegroup)))
            
            # ↓ 呼叫自製函式啟動所有子執行緒的工作任務，且等待所有子執行緒任務結束才會執行下一步    
            start_subthread(threads)
            # ↓ 橫向合併所有組別的DaraFrame
            df_SMR_all = pd.concat(df_SMR_list, axis=1)
        
            # ====== 以下為原本單執行緒的做法：===========================
            
            # # ↓ 先建立一個要依序合併多組SMR計算結果的空表格    
            # df_SMR_all = pd.DataFrame()
            # # ↓ 透過迴圈，將所需的參數代入自製函式計算，接著將得到的各組資料橫向合併為一個DataFrame
            # for i in range(len(dist_ori_all)):
            #     df_SMR = smr_calculate(i, conn, cs, pp_age_rangeSUM, dist_ts_allsql[i], dist_g_allsql[i], df_dth_rate, Death_Cause_sql, gender_sql, min_agegroup, max_agegroup)
            #     df_SMR_all = pd.concat([df_SMR_all, df_SMR], axis=1)
        
        #%%===== 將裝載著數據結果的DataFrame導入Plotly套件框架，進行製圖與回傳前端=====
            
            # ↓ 抓取由JavaScript偵測到的用戶端瀏覽器視窗尺寸，
            # 與1860的瀏覽器視窗寬度進行比對，傳入製圖函式以調整字體倍率。
            sc_ratio = int(request.form.get("screen_width"))/1860
            plot_html = smr_figure(df_SMR_all, dist_ori_all, dist_name_all, gender_ch, age_text, CauseName_str, sc_ratio)
            
            # 將要準備輸出到前端顯示的表格欄位名稱改成中文
            df_SMR_all = df_SMR_all.rename(columns={"year": "年份"})
            for i in range(len(dist_ori_all)):
                df_SMR_all = df_SMR_all.rename(columns={f"DthNum_exp_{i+1}": f"預期死亡人數_組別{i+1}",
                                                        f"DthNum_obs_{i+1}": f"實際死亡人數_組別{i+1}",
                                                        f"SMR_{i+1}": f"SMR原始值_組別{i+1}",
                                                        f"SMR3ma_{i+1}": f"SMR三年移動平均_組別{i+1}"
                                                        })
            # ↓ 將DataFrame轉換為HTML表格排版，並去除索引值。
            #   它的形式是以<table></table>包覆的長字串，
            #   最後會將其塞入 render_template() 使其於網頁上顯示
            table_html = df_SMR_all.to_html(index=False)
            
            # ↓ 將圖表等相關資訊回傳給前端
            cs.close(); conn.close()
            return render_template(r"SMR.html",
                                   error_code = 0, # 自定義的條件判斷碼
                                   plot_html = plot_html, # 圖
                                   table_html = table_html # 表
                                   )
            
    else:
        return render_template(r"SMR.html", error_code = 1)

# 簡介的路由
@app.route("/SMR/info/", methods = ["POST","GET"])
def info():
    return render_template(r"SMR_info.html")

# 行政區代碼對照表的路由
@app.route("/SMR/district_code/")
def dist_code():
    return send_file("templates/DistrictCode_2011.html", as_attachment=False)

# ----------------------------------------------------------------
if __name__ == "__main__":
	app.run()