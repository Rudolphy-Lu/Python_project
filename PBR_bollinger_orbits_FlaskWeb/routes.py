# -*- coding: utf-8 -*-

# 本淨比-布林軌道製圖程式 電腦網頁版

# ----------------------------------------------------------------
# 本程式提供投資人透過輸入台灣股市的股票代號，
# 取得長期本淨比之3/5/7年移動平均布林軌道圖。

# 本程式機制為透過靜態網路爬蟲，爬取 台灣股市資訊網 https://goodinfo.tw/ 之資料，
# 經過計算移動平均與軌道線之後，用Bokeh繪製互動式圖檔，透過Flask框架傳至網頁上。

# ----------------------------------------------------------------
from module import data_create, plot_create # 匯入自訂的模組
from flask import Flask, render_template, request

app = Flask(__name__)

# 主頁面的路由
@app.route("/PBR_orbit/", methods = ["POST","GET"])
def main():
    if request.method == "POST":
        # ↓ 抓取使用者在網頁輸入框內鍵入的股票代號
        stock_code = request.form["stock_code"]
        y_SMA = int(request.form["y_SMA"])
        # 非ETF的個股代碼規則為必須是4碼數字、且前2碼不得為"00"，
        # 已於前端透過正則表示式 "^[1-9]{2}\d{2}$" 檢查，避免對後端發送不必要的request。

        # 開始進行網路爬蟲擷取資料與製圖。
        try: # ↓ 將股票代號傳給爬蟲函式，獲取原始資料與股票中文名
            table_full, stockName = data_create.data_crawing(stock_code)
                # ↓ 抓取使用者在網頁選取的移動平均值計算年數，轉成整數型態。
            # y_SMA = int(request.form["y_SMA"])
                # ↓ 含爬取當下所屬月份往前回溯，至少需y_SMA年又1個月才可進行後續分析
            if len(table_full) < y_SMA*12+1: 
                return render_template(r"PBR_orbit.html",
                        error_code = 9, y_SMA = y_SMA,
                        stockName = stockName, stock_code = stock_code)
            else: # 選股滿足資料長度所需的條件，則依序繼續進行下列動作
            
                # ↓ DataFrame資料框架的建構
                dfPBR = data_create.dataframe_build(table_full)
                # ↓ 製圖所需數據的計算
                dfPBR = data_create.data_calculate(dfPBR, y_SMA, stock_code, stockName)
                
                source_df, p1, p2 = plot_create.plot_building(dfPBR, y_SMA, stock_code, stockName)
                # ↑Bokeh圖檔框架的建構
                p1, p2 = plot_create.plot_drawing(source_df, y_SMA, p1, p2)
                # ↑圖檔框架內繪製含有HoverTool互動功能的折線圖
                
                # ↓ 抓取由JavaScript偵測到的用戶端瀏覽器視窗尺寸，
                # 與1860的瀏覽器視窗寬度進行比對，傳入製圖函式以調整字體倍率。
                sc_ratio = int(request.form["screen_width"])/1860
                p1, p2 = plot_create.plot_setting(p1, p2, sc_ratio)
                # ↑調整圖檔框架的其餘參數細節 (代入視窗寬度比，來調整使用者看到的字體大小)

                html_Merge = plot_create.plot_merge(p1, p2, stock_code, stockName)
                # ↑透過Row layout將兩個子圖檔合併，將最終圖檔的html原始碼以str型態回傳
                
                return render_template(r"PBR_orbit.html",
                                        error_code = 0,
                                        stockName=stockName, stock_code=stock_code,
                                        html_Merge=html_Merge)
                # 讀取與本py檔同一層的templates資料夾內的 PBR_orbit.html，
                # 並將字串html_Merge代入給該網頁檔指定的{{html_Merge}}，
                # 這裡代入的字串內容其實是html網頁原始碼，使其在<iframe>內嵌頁面裡顯示
                
        except Exception:
            return render_template(r"PBR_orbit.html",
                    error_code = 1,
                    html_Merge=f"Connection Error!\
                                 查無該股票代號「{stock_code}」、或您的網路連線異常。")

    else:
        return render_template(r"PBR_orbit.html", error_code = -1)

# 說明頁面的路由
@app.route("/PBR_info/", methods = ["POST","GET"])
def info():
    return render_template(r"PBR_info.html")
    
# ----------------------------------------------------------------
if __name__=="__main__":
 	app.run()
    # 單機內測只打開上面那一行，線上部署則關閉上一行，開啟下方三行
    # import os
    # port = int(os.environ.get("PORT", 8000))
    # app.run(host="0.0.0.0", debug=False, port=port)