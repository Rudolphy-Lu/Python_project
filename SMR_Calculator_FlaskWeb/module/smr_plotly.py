# -*- coding: utf-8 -*-

# 本檔案為「時空超越者」SMR計算器的資料視覺化(繪圖)模組檔。
# 主程式位於同路徑下的 main.py。
# ----------------------------------------------------------

import plotly.graph_objs as go
# from plotly.offline import plot
# import plotly.io as pio # 單機版使用，

def smr_figure(df_SMR_all, dist_ori_all, dist_name_all, gender_ch, age_text, CauseName_str, sc_ratio):
    
    line_list = [] # 創立一個準備用來裝載複數線條資料物件的空list
    line_color = ["blue", "red", "green", "orange", "purple"] # 備妥線條顏色清單
    
    # ↓ 利用 locals() 函式，動態創建變數名稱，製造複數個線條資料物件
    for i in range(len(dist_ori_all)):
        locals()[f"trace_{i+1}"] = go.Scatter(x=df_SMR_all['year'], y=df_SMR_all[f"SMR3ma_{i+1}"],
                                              mode='lines', name=f"{dist_name_all[i]}",
                                              line=dict(color=line_color[i], width=4),
                                              hovertemplate='SMR=%{y}', showlegend=True)
        line_list.append(locals()[f"trace_{i+1}"]) # ← 合併線條資料物件至list
    
    # ↓ Plotly套件允許藉由HTML及CSS語法來自定義標題字體形式
    title_str = '<span style="font-size: 2.8vmax; color: black;"><b>SMR三年移動平均圖</b></span> ' \
                '<span style="font-size: 1.4vmax; color: black;">(1971-2011)</span><br><br>'\
                f'<span style="font-size: 1.3vmax; color: black;">性別與年齡：{gender_ch}，{age_text}</span><br><br>'\
                f'<span style="font-size: 1.3vmax; color: black;">死因：{CauseName_str}</span>'
    
    # ↓ 創建圖形的布局架構，並將上方的標題字串代入此架構的title項目
    layout_smr = go.Layout(title=dict(text = title_str, x=0.10, y=0.93),
                       # title='Interactive Line Chart',
                       # title_font=dict(size=24, color='black'),  # 設定標題字體大小與顏色
                       height = 900*sc_ratio,
                       xaxis=dict(title='Year', title_font=dict(size=28*sc_ratio, color='black'), tickangle=-90),  # 設定X軸標題和文字大小與顏色
                       yaxis=dict(title='SMR 3-year moving average', title_font=dict(size=28*sc_ratio, color='black'), tickformat=".2f"),  # 設定Y軸標題和文字大小與顏色
                       xaxis_tickfont=dict(size=20*sc_ratio, color='black'),  # 設定X軸刻度文字大小與顏色
                       yaxis_tickfont=dict(size=20*sc_ratio, color='black'),  # 設定Y軸刻度文字大小與顏色
                       legend_font=dict(size=24*sc_ratio, color='black'),  # 設定圖例字體大小與顏色
                       legend=dict(x=0.50, y=1.32), # 設定圖例框的相對位置
                       hoverlabel=dict(font=dict(size=24*sc_ratio)), # 設定動態懸停文字的字體大小
                       hovermode='x', #當滑鼠游標移動到x軸上，顯示該x軸對應的所有點位
                       margin=dict(t=220*sc_ratio, b=30*sc_ratio, l=150*sc_ratio), # 設定圖檔與四邊(l, r, t, b)的距離
                       plot_bgcolor='#F0F0F0', # 使用16進制表示法設定圖形內部的背景顏色
                       paper_bgcolor='#FFFFFF', # 使用16進制表示法設定圖形外圍的背景顏色
                       dragmode=False, # 此行開始是鎖住某些功能(例如防止使用者拖曳圖型)，避免使用者不慎破壞圖形
                       legend_itemclick=False,
                       legend_itemdoubleclick=False,
                       modebar_remove =["zoom","zoomin", "zoomout","pan"]
                       )

    # ↓ 將線條資料物件與圖形架構進行組裝
    fig = go.Figure(data = line_list, layout = layout_smr)
    
    # fig.update_yaxes(scaleanchor="x", scaleratio=0.8)
     
    # ↓ 若為單機版使用，設定輸出的HTML檔案名稱 (可包含絕對路徑，使檔案儲存於指定的路徑內)
    # plot_filename = r"D:/SMR.html"

    # ↓ 儲存離線非互動式圖為HTML檔案，並且以瀏覽器自動開啟。此功能可在單機版使用。
    # plot(fig, filename=plot_filename, auto_open=True)

    # ↓ 儲存離線互動式圖為HTML檔案，並且以瀏覽器自動開啟。此功能可在單機版使用。
    # pio.write_html(fig, file=plot_filename, auto_open=True)
    
    # ↓ 將圖形的html片段傳給前端的<iframe>，在裡面顯示圖形
    plot_html = fig.to_html(full_html=True)
    # plot_html = pio.to_html(fig, include_plotlyjs=True)
    return plot_html
    