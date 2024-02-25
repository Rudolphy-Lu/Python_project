# -*- coding: utf-8 -*-
# 本淨比-布林軌道製圖程式 電腦網頁版
# 此為爬蟲與數據分析的模組檔，非主程式擋
# ----------------------------------------------------
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 將股票代號傳給此爬蟲函式，獲取原始資料與股票中文名
def data_crawing(stock_code):
    headers_w = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"}
    url = "https://goodinfo.tw/tw/ShowK_ChartFlow.asp?RPT_CAT=PBR&STOCK_ID="+stock_code+"&CHT_CAT=MONTH&PERIOD=7300"
            # ↑原為下拉式選單，透過觀察XHR並測試後找出含二十年資料的真正網址
    r = requests.get(url, headers = headers_w)
    
    if r.status_code == 200:
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        stockName = soup.find("table",class_="b0 p6_0").find("td",align="center").find_all("nobr")[1].text
        table_full = soup.find("div", id="divDetail").find_all("tr", align="center")
        # ↑獲取的table_full是一整個可迭代的原始二維表格
        # ↑由於該表格中間有一堆標頭，用pandas的read_html()效率並不好
        return (table_full, stockName)

# DataFrame資料框架的建構
def dataframe_build(table_full):
    dfPBR = pd.DataFrame(
        columns = ["mPrice","mPBR",
                   "u2L","u1L","u","u1H","u2H",
                   "M2L","M1L","M","M1H","M2H","fake_1","fake_2"])
    # ↑先宣告一個含特定欄位名稱、但尚無資料的DataFrame
    
    for i in table_full:
        rowT = i.find_all("td") # 每個row都是該月份的所有原始資料
        dfPBR.loc["20"+rowT[0].text.replace("M","-")] = [float(rowT[1].text), float(rowT[5].text)]+[None]*12
        # ↑觀察<td>標籤的排序，[0]是年月份，[1]是月收盤價，[5]是月本淨比，
        # ↑以年月份為索引值，將所需的資料寫入前面已準備好的DataFrame內
    return dfPBR

# 製圖所需數據的計算
def data_calculate(dfPBR, y_SMA, stock_code, stockName):
    # 以下根據月收盤價及mPBR，進行數據計算並將結果分別寫入其餘欄位    
    for j in range(len(dfPBR)-y_SMA*12): #最早的y_SMA*12個月不予計算「y_SMA*12+1月移動平均」
    
        # ↓u (N-month moving average of PBR), u61±σ, u61±2σ
        dfPBR.iloc[j, 2] = dfPBR.iloc[j:j+y_SMA*12+1,1].mean() - dfPBR.iloc[j:j+y_SMA*12+1,1].std()*2
        dfPBR.iloc[j, 3] = dfPBR.iloc[j:j+y_SMA*12+1,1].mean() - dfPBR.iloc[j:j+y_SMA*12+1,1].std()
        dfPBR.iloc[j, 4] = dfPBR.iloc[j:j+y_SMA*12+1,1].mean()
        dfPBR.iloc[j, 5] = dfPBR.iloc[j:j+y_SMA*12+1,1].mean() + dfPBR.iloc[j:j+y_SMA*12+1,1].std()
        dfPBR.iloc[j, 6] = dfPBR.iloc[j:j+y_SMA*12+1,1].mean() + dfPBR.iloc[j:j+y_SMA*12+1,1].std()*2
        # ↓M (Converted price by PBR), M±σ, M±2σ
        dfPBR.iloc[j, 7] = dfPBR.iloc[j,0] / dfPBR.iloc[j,1] * dfPBR.iloc[j, 2]
        dfPBR.iloc[j, 8] = dfPBR.iloc[j,0] / dfPBR.iloc[j,1] * dfPBR.iloc[j, 3]
        dfPBR.iloc[j, 9] = dfPBR.iloc[j,0] / dfPBR.iloc[j,1] * dfPBR.iloc[j, 4]
        dfPBR.iloc[j,10] = dfPBR.iloc[j,0] / dfPBR.iloc[j,1] * dfPBR.iloc[j, 5]
        dfPBR.iloc[j,11] = dfPBR.iloc[j,0] / dfPBR.iloc[j,1] * dfPBR.iloc[j, 6]
        
    return dfPBR
