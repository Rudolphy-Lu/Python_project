# -*- coding: utf-8 -*-

# 本淨比-布林軌道製圖程式 電腦網頁版
# 此為Bokeh資料視覺化的模組檔，非主程式 (主程式請見同資料夾內的 main.py)
# ----------------------------------------------------

# 使用之Bokeh套件版本為第3版，部分語法與舊版稍有不同。
# from bokeh.plotting import figure, show, output_file
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.models import HoverTool,ColumnDataSource, NumeralTickFormatter, LinearAxis, Range1d
from bokeh.layouts import column
from datetime import datetime

# Bokeh圖檔框架的建構
def plot_building(dfPBR, y_SMA, stock_code, stockName):
          
    dfPBR = dfPBR.iloc[::-1] # 先將DataFrame內容上下顛倒，使其時間由遠至近
    source_df = ColumnDataSource(dfPBR)
    
    # 以下，p1為本淨比的圖，p2為根據本淨比各軌道線換算之股價圖 
    p1 = figure(
        x_range = list(dfPBR.index),
        width = 1600, height = 1100,
        margin=(15, 0, 0, 0),
        title=f"{stockName}({stock_code})\n本淨比：{y_SMA}年移動均線與布林軌道", 
        x_axis_label= "時間範圍："+dfPBR.index[0][:4]+"年"+dfPBR.index[0][5:]+"月"+"至"+
                                dfPBR.index[-1][:4]+"年"+dfPBR.index[-1][5:]+"月",
        y_axis_label="本淨比",
        toolbar_location=None, tools='' # 刪除默認的工具欄，以及禁止工具顯示，包含拖動
        )
    
    p2 = figure(
        x_range = list(dfPBR.index),
        width = 1600, height = 1200,
        margin=(15, 0, 0, 0),
        title=f"{stockName}({stock_code})\n上圖各軌道線換算之股價", 
        x_axis_label= "時間範圍："+dfPBR.index[0][:4]+"年"+dfPBR.index[0][5:]+"月"+"至"+
                                dfPBR.index[-1][:4]+"年"+dfPBR.index[-1][5:]+"月",
        y_axis_label="股價(元)",
        toolbar_location=None, tools="" # 刪除默認的工具欄，以及禁止工具顯示，包含拖動
        )
    
    return source_df, p1, p2

# 圖檔框架內繪製含有HoverTool互動功能的折線圖
def plot_drawing(source_df, y_SMA, p1, p2):
    plot1 = p1.line("index", "mPBR", color="black", line_width=3, source=source_df, legend_label="當月實際本淨比")
    p1.add_tools(HoverTool(renderers=[plot1], tooltips=[("年月份", "@index"), ("本淨比", "@mPBR{0.2f}")],
                          mode='vline', attachment = 'left'))
    plot2 = p1.line("index", "u", color="green", line_width=2, source=source_df, legend_label=f"u ({y_SMA}年移動平均)")
    p1.add_tools(HoverTool(renderers=[plot2], tooltips=[("μ", "@u{0.2f}")],
                          mode='vline', attachment = 'right'))
    plot3 = p1.line("index", "u1H", color="orange", line_width=2, source=source_df)
    p1.add_tools(HoverTool(renderers=[plot3], tooltips=[("μ+σ", "@u1H{0.2f}")],
                          mode='vline', attachment = 'right'))
    plot4 = p1.line("index", "u1L", color="orange", line_width=2, source=source_df)
    p1.add_tools(HoverTool(renderers=[plot4], tooltips=[("μ-σ", "@u1L{0.2f}")],
                          mode='vline', attachment = 'right'))
    plot5 = p1.line("index", "u2H", color="red", line_width=2, source=source_df)
    p1.add_tools(HoverTool(renderers=[plot5], tooltips=[("μ+2σ", "@u2H{0.2f}")],
                          mode='vline', attachment = 'right'))
    plot6 = p1.line("index", "u2L", color="red", line_width=2, source=source_df)
    p1.add_tools(HoverTool(renderers=[plot6], tooltips=[("μ-2σ", "@u2L{0.2f}")],
                          mode='vline', attachment = 'right'))
    p1.line("index", "fake_1", color="orange", line_width=2, source=source_df, legend_label="μ ± σ")
    p1.line("index", "fake_2", color="red", line_width=2, source=source_df, legend_label="μ ± 2σ")
    
    # ---------------------------------------------------
    plot7 = p2.line("index", "mPrice", color="black", line_width=3, source=source_df, legend_label="當月實際收盤價")
    p2.add_tools(HoverTool(renderers=[plot7], tooltips=[("年月份", "@index"), ("收盤價", "@mPrice{0.2f}")],
                          mode='vline', attachment = 'left'))
    plot8 = p2.line("index", "M", color="green", line_width=2, source=source_df, legend_label=f"M ({y_SMA}年移動平均)")
    p2.add_tools(HoverTool(renderers=[plot8], tooltips=[("M", "@M{0.2f}")],
                          mode='vline', attachment = 'right'))
    plot9 = p2.line("index", "M1H", color="orange", line_width=2, source=source_df)
    p2.add_tools(HoverTool(renderers=[plot9], tooltips=[("M+σ", "@M1H{0.2f}")],
                          mode='vline', attachment = 'right'))
    plotA = p2.line("index", "M1L", color="orange", line_width=2, source=source_df)
    p2.add_tools(HoverTool(renderers=[plotA], tooltips=[("M-σ", "@M1L{0.2f}")],
                          mode='vline', attachment = 'right'))
    plotB = p2.line("index", "M2H", color="red", line_width=2, source=source_df)
    p2.add_tools(HoverTool(renderers=[plotB], tooltips=[("M+2σ", "@M2H{0.2f}")],
                          mode='vline', attachment = 'right'))
    plotC = p2.line("index", "M2L", color="red", line_width=2, source=source_df)
    p2.add_tools(HoverTool(renderers=[plotC], tooltips=[("M-2σ", "@M2L{0.2f}")],
                          mode='vline', attachment = 'right'))
    p2.line("index", "fake_1", color="orange", line_width=2, source=source_df, legend_label="M ± σ")
    p2.line("index", "fake_2", color="red", line_width=2, source=source_df, legend_label="M ± 2σ")
    
    return p1, p2

# 調整圖檔框架的其餘參數
def plot_setting(p1, p2, sc_ratio):
    p1.title.align = "center"
    p1.title.text_font_size = str(3.3*sc_ratio)+"em"
    p1.xaxis.axis_label_text_font_size = str(2.3*sc_ratio)+"em"
    p1.xaxis.major_label_text_font_size = "0em"
    # p1.xaxis.major_label_orientation = pi/2
    p1.xgrid.grid_line_color = None
    p1.yaxis.axis_label_text_font_size = str(2.8*sc_ratio)+"em"
    p1.yaxis.formatter = NumeralTickFormatter(format="0.0")
    p1.yaxis.major_label_text_font_size = str(2.2*sc_ratio)+"em"
    p1.legend.location = "bottom_left"
    p1.legend.label_text_font_size = str(1.7*sc_ratio)+"em"
    p1.extra_y_ranges = {"empty": Range1d(start=0, end=1)}
    p1.add_layout(LinearAxis(y_range_name="empty",
                  axis_label=" ", axis_label_text_font_size = str(5*sc_ratio)+"em",
                  major_tick_line_color=None, minor_tick_line_color=None,
                  major_label_text_color=None), "right")
    
    p2.title.align = "center"
    p2.title.text_font_size = str(3.3*sc_ratio)+"em"
    p2.xaxis.axis_label_text_font_size = str(2.3*sc_ratio)+"em"
    p2.xaxis.major_label_text_font_size = "0em"
    # p2.xaxis.major_label_orientation = pi/2
    p2.xgrid.grid_line_color = None
    p2.yaxis.axis_label_text_font_size = str(2.8*sc_ratio)+"em"
    # p2.yaxis.formatter = NumeralTickFormatter(format="0.0")
    p2.yaxis.major_label_text_font_size = str(2.2*sc_ratio)+"em"
    p2.legend.location = "bottom_left"
    p2.legend.label_text_font_size = str(1.7*sc_ratio)+"em"
    p2.extra_y_ranges = {"empty": Range1d(start=0, end=1)}
    p2.add_layout(LinearAxis(y_range_name="empty",
                  axis_label=" ", axis_label_text_font_size = str(5*sc_ratio)+"em",
                  major_tick_line_color=None, minor_tick_line_color=None,
                  major_label_text_color=None), "right")
    return p1, p2

# 透過Row layout將兩個子圖檔合併，將最終圖檔的html原始碼以str型態回傳
def plot_merge(p1, p2, stock_code, stockName):
    
    nowTime = datetime.now()
    web_title = f"{stock_code}{stockName}"+"_estPrice_"+f"{nowTime:%Y%m%d_%H%M%S}"
    p_merge = column(p1,p2) # 將p1與p2以上下排列形式進行合併
    
    p_merge.sizing_mode = "scale_both" # 使動態圖檔允許隨視窗大小縮放(不包含字體)
    p_merge.aspect_ratio = 2.15
    html_Merge = file_html(p_merge, CDN, web_title)
    # ↑變數 html_Merge 的型態為str，內容是bokeh繪出之圖形的html原始碼組成的「超長字串」
    # column(p1,p2) 意為透過bokeh.layouts的column功能，將p1與p2以上下排列方式合併
    
    return html_Merge