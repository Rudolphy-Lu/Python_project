# -*- coding: utf-8 -*-

# 本檔案為「時空超越者」SMR計算器的數據計算模組檔，

# 主程式位於同路徑下的 main.py。

# -----------------------------------------------------------------
# from datetime import datetime
# from random import randint
import pandas as pd
import threading
    
    # 使用多執行緒的做法時，參數要多一個空串列 df_SMR_list
def smr_calculate(df_SMR_list, i, conn, cs, pp_age_rangeSUM, dist_ts_sql, dist_g_sql, df_dth_rate, Death_Cause_sql, gender_sql, min_agegroup, max_agegroup):
    
    # ↓ 先從人口總檔資料表(pp1971to2011_ref2011)裡面，依據使用者指定的篩選條件，
    # 把人口數資料依性別年齡各自加總之後以「年」為單位區分出來並轉成DataFrame
    query = f"""
            SELECT year, {pp_age_rangeSUM}
            FROM pp1971to2011_ref2011
            WHERE (district in ({dist_ts_sql})) or (district_g {dist_g_sql})
            GROUP BY year
            ORDER BY year;
            """
    df_SMR = pd.read_sql_query(query, conn)
    
    # ↓ 將前面存放篩選後人口檔的所有內容(原本是人數)按性別與年齡，
    # 各自乘以死亡率(除了第1欄的"year"，其餘欄位名稱與索引值皆相同，可以直接相乘)，
    # 如此將所有數字都轉換為「預期死亡人數」，最後再進行列的加總(每列都是一個年份)。
    df_SMR.iloc[:, 1:] *= df_dth_rate
    df_SMR[f"DthNum_exp_{i+1}"] = df_SMR.iloc[:, 1:].sum(axis=1)
    # df_SMR[f"DthNum_exp_{i+1}"] = df_SMR.drop("year", axis=1).sum(axis=1)
    # df_SMR[f"DthNum_exp_{i+1}"] = df_SMR.drop(columns=["year"], axis=1).sum(axis=1)
    # ↑上面被註解的這兩行在此例當中也是等效的，可以只指定排除一個欄位並將其餘進行加總，
    # 如果要排除多個不連續但已知名稱的欄位，則可以照此範例使用串列方式代入。
    
    
    # ↓ 從死亡總檔資料表(death1971to2011)內，根據所選條件篩選出每一年的實際死亡人數，
    # 並將整個篩選結果直接併入已有的DataFrame
    count_name = f"DthNum_obs_{i+1}" # ← 動態生成實際死亡數的欄位名稱，代入下方SQL語法
    query = f"""
            SELECT COUNT(*) AS {count_name}
            FROM death1971to2011
            WHERE (1 IN ({Death_Cause_sql}))
                and (gender {gender_sql})
                and (agegroup between {min_agegroup} and {max_agegroup})
                and ((district in ({dist_ts_sql})) or (district_g {dist_g_sql}))
            GROUP BY deathyr
            ORDER BY deathyr;
            """
    df_SMR = pd.concat([df_SMR, pd.read_sql_query(query, conn)], axis=1)
    
    # ↓ 最後，將實際死亡人數(dth_num_obs)除以預期死亡人數(dth_num_exp)，
    # 就得到每年SMR的值
    df_SMR[f"SMR_{i+1}"] = df_SMR[f"DthNum_obs_{i+1}"] / df_SMR[f"DthNum_exp_{i+1}"]
    
    # ↓ 計算SMR的3年移動平均。這裡設定最後一年數字不變，
    # 第一年為前二年的平均
    # 其餘的值為本身再加上前後各一年計算出的平均值
    df_SMR.loc[0, f"SMR3ma_{i+1}"] = df_SMR.loc[0:1, f"SMR_{i+1}"].mean()
    df_SMR.loc[len(df_SMR)-1, f"SMR3ma_{i+1}"] = df_SMR.loc[len(df_SMR)-1, f"SMR_{i+1}"]
    for j in range(len(df_SMR)-2):
        df_SMR.loc[j+1, f"SMR3ma_{i+1}"] = df_SMR.loc[j:j+2, f"SMR_{i+1}"].mean()
    
    # ↓ 整個外部迴圈所有輪次皆要保留計算出的最後4個欄位，
    #   依序是：預期死亡人數、實際死亡人數、SMR原始值、SMR三年移動平均值。
    # ↓ 但只有第一輪(i為0)需要多留下"year"這個欄位
    # ↓ 原本用return的方式是單執行緒的做法。多執行緒改用加入list來後續處理。
    
    df_SMR_list.append(df_SMR.iloc[: , -4:])
    # if i == 0:
    #     return df_SMR.iloc[: ,[0, -4, -3, -2, -1]] #含西元年份
    # else:
    #     return df_SMR.iloc[: , -4:] #不含西元年份


def start_subthread(threads):
    for th in threads:
        th.start()
    for th in threads:
        th.join() # 等待所有子執行緒結束