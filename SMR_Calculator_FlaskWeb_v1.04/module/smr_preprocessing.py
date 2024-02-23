# -*- coding: utf-8 -*-

# 本檔案為「時空超越者」SMR計算器的資料預處理模組檔，包含了：
# 自定義函式 foolproof：行政區代碼的各種格式排錯、檢查、重覆區域整併...等，一系列的防呆措施。
# 自定義函式 chinese_name：透過對照表將行政區代碼另存為中文詞條，
#                         以及順勢將行政區代碼轉為特製的字串編排方式，方便後續塞入SQL語法內。

# 主程式位於同路徑下的 main.py。
# ----------------------------------------------------------------

# 行政區代碼的各種格式排錯、檢查、重覆區域整併...等，一系列的防呆措施。
def foolproof(dist_ori, df_Dcode2011, error_code):
    dist_ori = dist_ori.strip().strip(",").split(",")
    dist_ts = [] # 初始化一個用來裝使用者輸入的4碼「鄉鎮市區」的串列
    dist_g = [] # 初始化一個用來裝使用者輸入的2碼「縣」或「直轄市」的串列
    html_msg = "" #用來裝載文字提示訊息
    
    for j in range(len(dist_ori)): # 處理二維串列所有子元素的內容
        dist_ori[j] = dist_ori[j].strip()
    dist_ori = sorted(list(set(dist_ori)))
    for j in range(len(dist_ori)):
        if dist_ori[j] == "" or dist_ori[j].isspace():
            error_code = 1
            html_msg += "輸入框內的開頭、結尾似乎有多餘的逗號或空格！"
            break
        elif (len(dist_ori[j]) not in (2,4)) or (not dist_ori[j].isdigit()) and (dist_ori[j] != "TW"):
            error_code = 1
            html_msg += f"您輸入的代碼 {dist_ori[j]} 格式錯誤！"
        elif dist_ori[j] not in df_Dcode2011["district_code"].values:
            error_code = 1
            html_msg += f"您輸入的代碼 {dist_ori[j]} 並無對應的行政區！"
        else:
            dist_ori[j] = f"'{dist_ori[j]}'" # 在每個行政區代碼的兩側加上單引號，之後要塞入SQL語法
            if len(dist_ori[j]) == 6:
                dist_ts.append(dist_ori[j])
            elif len(dist_ori[j]) == 4:
                dist_g.append(dist_ori[j])
            else:
                error_code = 1
                html_msg += "發生非預期的錯誤！"
        
    dist_gtemp = [g[:3] for g in dist_g]
    dist_ts = [ts for ts in dist_ts if ts[:3] not in dist_gtemp]
    
    return dist_ts, dist_g, error_code, html_msg

# 透過對照表將行政區代碼另存為中文詞條，並將行政區代碼轉為特製的字串編排方式，方便後續塞入SQL語法內。
def chinese_name(dist_ts, dist_g, df_Dcode2011):
    dist_tsn = "" # 初始化一個用來裝使用者輸入的4碼「鄉鎮市區」中文名稱的字串
    dist_gn = "" # 初始化一個用來裝使用者輸入的2碼「縣」或「直轄市」中文名稱的字串
    for item in dist_ts:
        for k in range(len(df_Dcode2011)):
            if item[1:5] == df_Dcode2011.loc[k,'district_code']:
                dist_tsn += f"{df_Dcode2011.loc[k,'district_name']}、"
    for item in dist_g:
        for k in range(len(df_Dcode2011)):
            if item[1:3] == df_Dcode2011.loc[k,'district_code']:
                dist_gn += f"{df_Dcode2011.loc[k,'district_name']}、"
    
    # ↓ 行政區中文名稱合併，後續要將其塞入對使用者顯示文字的位置
    dist_name = (dist_tsn + dist_gn).rstrip("、")
    
    # ↓ 將行政區代碼轉為特製的字串編排方式，方便後續塞入SQL語法內
    dist_ts_sql = ",".join(dist_ts)
    
    if dist_g == ["'TW'"]:
        dist_g_sql = "is not Null"
    else:
        dist_g_sql = "in (" + ",".join(dist_g) + ")"
    
    return dist_name, dist_ts_sql, dist_g_sql