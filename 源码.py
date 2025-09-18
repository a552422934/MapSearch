"""MapSearch：基于 Tkinter 的高德地图（AMap）POI 检索 GUI。

功能概览：
- 按关键词在选定/全部城市检索 POI
- 多个 API Key 轮换与基础重试
- 支持选择字段的实时 CSV 导出
- 定时采集与倒计时显示
- 设置项与已查询城市状态持久化
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import requests
import threading
import csv
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import webbrowser
import json
from datetime import datetime, timedelta  # 日期时间与时间间隔处理

# 省份及城市的行政区划代码列表（左侧为区号/城市代码，右侧为中文城市名）
province_adcode_list=[
'010,北京市',
'022,天津市',
'0311,石家庄市',
'0315,唐山市',
'0335,秦皇岛市',
'0310,邯郸市',
'0319,邢台市',
'0312,保定市',
'0313,张家口市',
'0314,承德市',
'0317,沧州市',
'0316,廊坊市',
'0318,衡水市',
'0351,太原市',
'0352,大同市',
'0353,阳泉市',
'0355,长治市',
'0356,晋城市',
'0349,朔州市',
'0354,晋中市',
'0359,运城市',
'0350,忻州市',
'0357,临汾市',
'0358,吕梁市',
'0471,呼和浩特市',
'0472,包头市',
'0473,乌海市',
'0476,赤峰市',
'0475,通辽市',
'0477,鄂尔多斯市',
'0470,呼伦贝尔市',
'0478,巴彦淖尔市',
'0474,乌兰察布市',
'0482,兴安盟',
'0479,锡林郭勒盟',
'0483,阿拉善盟',
'024,沈阳市',
'0411,大连市',
'0412,鞍山市',
'0413,抚顺市',
'0414,本溪市',
'0415,丹东市',
'0416,锦州市',
'0417,营口市',
'0418,阜新市',
'0419,辽阳市',
'0427,盘锦市',
'0410,铁岭市',
'0421,朝阳市',
'0429,葫芦岛市',
'0431,长春市',
'0432,吉林市',
'0434,四平市',
'0437,辽源市',
'0435,通化市',
'0439,白山市',
'0438,松原市',
'0436,白城市',
'1433,延边朝鲜族自治州',
'0451,哈尔滨市',
'0452,齐齐哈尔市',
'0467,鸡西市',
'0468,鹤岗市',
'0469,双鸭山市',
'0459,大庆市',
'0458,伊春市',
'0454,佳木斯市',
'0464,七台河市',
'0453,牡丹江市',
'0456,黑河市',
'0455,绥化市',
'0457,大兴安岭地区',
'021,上海市',
'025,南京市',
'0510,无锡市',
'0516,徐州市',
'0519,常州市',
'0512,苏州市',
'0513,南通市',
'0518,连云港市',
'0517,淮安市',
'0515,盐城市',
'0514,扬州市',
'0511,镇江市',
'0523,泰州市',
'0527,宿迁市',
'0571,杭州市',
'0574,宁波市',
'0577,温州市',
'0573,嘉兴市',
'0572,湖州市',
'0575,绍兴市',
'0579,金华市',
'0570,衢州市',
'0580,舟山市',
'0576,台州市',
'0578,丽水市',
'0551,合肥市',
'0553,芜湖市',
'0552,蚌埠市',
'0554,淮南市',
'0555,马鞍山市',
'0561,淮北市',
'0562,铜陵市',
'0556,安庆市',
'0559,黄山市',
'0550,滁州市',
'1558,阜阳市',
'0557,宿州市',
'0564,六安市',
'0558,亳州市',
'0566,池州市',
'0563,宣城市',
'0591,福州市',
'0592,厦门市',
'0594,莆田市',
'0598,三明市',
'0595,泉州市',
'0596,漳州市',
'0599,南平市',
'0597,龙岩市',
'0593,宁德市',
'0791,南昌市',
'0798,景德镇市',
'0799,萍乡市',
'0792,九江市',
'0790,新余市',
'0701,鹰潭市',
'0797,赣州市',
'0796,吉安市',
'0795,宜春市',
'0794,抚州市',
'0793,上饶市',
'0531,济南市',
'0532,青岛市',
'0533,淄博市',
'0632,枣庄市',
'0546,东营市',
'0535,烟台市',
'0536,潍坊市',
'0537,济宁市',
'0538,泰安市',
'0631,威海市',
'0633,日照市',
'0539,临沂市',
'0534,德州市',
'0635,聊城市',
'0543,滨州市',
'0530,菏泽市',
'0371,郑州市',
'0378,开封市',
'0379,洛阳市',
'0375,平顶山市',
'0372,安阳市',
'0392,鹤壁市',
'0373,新乡市',
'0391,焦作市',
'0393,濮阳市',
'0374,许昌市',
'0395,漯河市',
'0398,三门峡市',
'0377,南阳市',
'0370,商丘市',
'0376,信阳市',
'0394,周口市',
'0396,驻马店市',
'1391,济源市',
'027,武汉市',
'0714,黄石市',
'0719,十堰市',
'0717,宜昌市',
'0710,襄阳市',
'0711,鄂州市',
'0724,荆门市',
'0712,孝感市',
'0716,荆州市',
'0713,黄冈市',
'0715,咸宁市',
'0722,随州市',
'0718,恩施土家族苗族自治州',
'0728,仙桃市',
'2728,潜江市',
'1728,天门市',
'1719,神农架林区',
'0731,长沙市',
'0733,株洲市',
'0732,湘潭市',
'0734,衡阳市',
'0739,邵阳市',
'0730,岳阳市',
'0736,常德市',
'0744,张家界市',
'0737,益阳市',
'0735,郴州市',
'0746,永州市',
'0745,怀化市',
'0738,娄底市',
'0743,湘西土家族苗族自治州',
'020,广州市',
'0751,韶关市',
'0755,深圳市',
'0756,珠海市',
'0754,汕头市',
'0757,佛山市',
'0750,江门市',
'0759,湛江市',
'0668,茂名市',
'0758,肇庆市',
'0752,惠州市',
'0753,梅州市',
'0660,汕尾市',
'0762,河源市',
'0662,阳江市',
'0763,清远市',
'0769,东莞市',
'0760,中山市',
'0768,潮州市',
'0663,揭阳市',
'0766,云浮市',
'0771,南宁市',
'0772,柳州市',
'0773,桂林市',
'0774,梧州市',
'0779,北海市',
'0770,防城港市',
'0777,钦州市',
'1755,贵港市',
'0775,玉林市',
'0776,百色市',
'1774,贺州市',
'0778,河池市',
'1772,来宾市',
'1771,崇左市',
'0898,海口市',
'0899,三亚市',
'2898,三沙市',
'0805,儋州市',
'1897,五指山市',
'1894,琼海市',
'1893,文昌市',
'1898,万宁市',
'0807,东方市',
'0806,定安县',
'1892,屯昌县',
'0804,澄迈县',
'1896,临高县',
'0802,白沙黎族自治县',
'0803,昌江黎族自治县',
'2802,乐东黎族自治县',
'0809,陵水黎族自治县',
'0801,保亭黎族苗族自治县',
'1899,琼中黎族苗族自治县',
'023,重庆市',
'028,成都市',
'0813,自贡市',
'0812,攀枝花市',
'0830,泸州市',
'0838,德阳市',
'0816,绵阳市',
'0839,广元市',
'0825,遂宁市',
'1832,内江市',
'0833,乐山市',
'0817,南充市',
'1833,眉山市',
'0831,宜宾市',
'0826,广安市',
'0818,达州市',
'0835,雅安市',
'0827,巴中市',
'0832,资阳市',
'0837,阿坝藏族羌族自治州',
'0836,甘孜藏族自治州',
'0834,凉山彝族自治州',
'0851,贵阳市',
'0858,六盘水市',
'0852,遵义市',
'0853,安顺市',
'0857,毕节市',
'0856,铜仁市',
'0859,黔西南布依族苗族自治州',
'0855,黔东南苗族侗族自治州',
'0854,黔南布依族苗族自治州',
'0871,昆明市',
'0874,曲靖市',
'0877,玉溪市',
'0875,保山市',
'0870,昭通市',
'0888,丽江市',
'0879,普洱市',
'0883,临沧市',
'0878,楚雄彝族自治州',
'0873,红河哈尼族彝族自治州',
'0876,文山壮族苗族自治州',
'0691,西双版纳傣族自治州',
'0872,大理白族自治州',
'0692,德宏傣族景颇族自治州',
'0886,怒江傈僳族自治州',
'0887,迪庆藏族自治州',
'0891,拉萨市',
'0892,日喀则市',
'0895,昌都市',
'0894,林芝市',
'0893,山南市',
'0896,那曲市',
'0897,阿里地区',
'029,西安市',
'0919,铜川市',
'0917,宝鸡市',
'0910,咸阳市',
'0913,渭南市',
'0911,延安市',
'0916,汉中市',
'0912,榆林市',
'0915,安康市',
'0914,商洛市',
'0931,兰州市',
'1937,嘉峪关市',
'0935,金昌市',
'0943,白银市',
'0938,天水市',
'1935,武威市',
'0936,张掖市',
'0933,平凉市',
'0937,酒泉市',
'0934,庆阳市',
'0932,定西市',
'2935,陇南市',
'0930,临夏回族自治州',
'0941,甘南藏族自治州',
'0971,西宁市',
'0972,海东市',
'0970,海北藏族自治州',
'0973,黄南藏族自治州',
'0974,海南藏族自治州',
'0975,果洛藏族自治州',
'0976,玉树藏族自治州',
'0977,海西蒙古族藏族自治州',
'0951,银川市',
'0952,石嘴山市',
'0953,吴忠市',
'0954,固原市',
'1953,中卫市',
'0991,乌鲁木齐市',
'0990,克拉玛依市',
'0995,吐鲁番市',
'0992,胡杨河市',
'0902,哈密市',
'0994,昌吉回族自治州',
'0909,博尔塔拉蒙古自治州',
'0996,巴音郭楞蒙古自治州',
'0997,阿克苏地区',
'0908,克孜勒苏柯尔克孜自治州',
'0998,喀什地区',
'0903,和田地区',
'0999,伊犁哈萨克自治州',
'0901,塔城地区',
'0906,阿勒泰地区',
'0993,石河子市',
'1997,阿拉尔市',
'1998,图木舒克市',
'1994,五家渠市',
'1906,北屯市',
'1996,铁门关市',
'1909,双河市',
'1999,可克达拉市',
'1903,昆玉市',
'1886,台湾省',
'1852,香港特别行政区',
'1853,澳门特别行政区',
]

# 已查询城市持久化文件路径
queried_cities_file = 'queried_cities.txt'

if not os.path.exists(queried_cities_file):
    # 初始化文件，确保后续读写不报错
    with open(queried_cities_file, 'w', encoding='utf-8') as file:
        file.write('')

if os.path.exists(queried_cities_file):
    # queried_cities：内存中的已查询城市列表（包含纯名称与带✔️标记的重复项）
    with open(queried_cities_file, 'r', encoding='utf-8') as file:
        queried_cities = file.read().splitlines()
else:
    queried_cities = []  # 若文件不存在，初始化为空

class ScrollableFrame(tk.Frame):
    """可滚动容器：基于 Canvas + 垂直/水平滚动条。"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.container = container
        self.canvas = tk.Canvas(self, borderwidth=2, relief="solid") 
        self.v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview) 
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")  

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def get_frame(self):
        return self.scrollable_frame

class AMapGUI:
    """主界面：执行高德 POI 检索、定时任务与 CSV 导出。"""
    def __init__(self, root):
        self.root = root  # Tk 根窗口
        self.root.title("高德地图POI检索 - v1.1")
        # 城市名 -> 复选框变量（用于将来扩展城市多选）
        self.checked_cities = {city.split(',')[1]: tk.BooleanVar(value=False) for city in province_adcode_list}
        self.is_searching = False  # 标识是否正在检索（控制循环与终止）
        self.frames = []  # 右侧结果列的 frame 容器列表
        self.create_widgets()
        self.load_settings()  
        self.update_province_status()
        self.update_clock()  # 启动定时器
        self.update_progress(len(province_adcode_list))  # 初始化进度
        self.root.grid_columnconfigure(1, weight=1)  # 右侧列自适应
        for row_index in range(9):  # 行自适应，防止窗口拉伸错位
            self.root.grid_rowconfigure(row_index, weight=1)


    def create_widgets(self):
        """构建窗口的控件、布局与样式。"""
        ttk.Label(self.root, text="API Keys:(可输入多个key，每个key用空格隔开)", font=('Arial', 11, 'bold')).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.api_key_entry = ttk.Entry(self.root, font=('Arial', 11), foreground='gray')
        self.api_key_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')  # API Key 输入框
        self.api_key_entry.insert(0, '05539bdacda89aa2b5341552259a6702') # 默认api
        self.api_key_entry.config(foreground='black')
        self.api_key_entry.bind("<FocusIn>", self.clear_placeholder)
        self.api_key_entry.bind("<FocusOut>", self.add_placeholder)
        
        ttk.Label(self.root, text="关键词（可输入多个关键词，每个关键词用空格隔开）", font=('Arial', 11, 'bold')).grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.keyword_entry = ttk.Entry(self.root, width=10, font=('Arial', 11), foreground='grey')  # 关键词输入框
        self.keyword_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        # 设置关键词
        self.keyword_entry.insert(0, "水族")
        self.keyword_entry.config(foreground='black')
        self.keyword_entry.bind("<FocusIn>", self.clear_placeholder)
        self.keyword_entry.bind("<FocusOut>", self.add_placeholder)

        self.all_provinces_var = tk.BooleanVar()  # 是否查询所有城市
        self.all_provinces_check = ttk.Checkbutton(self.root, text="查询所有城市（输入框实时显示正在查询的城市，并且自动选择未查询城市）", variable=self.all_provinces_var, command=self.toggle_province_entry)
        self.all_provinces_check.grid(row=2, column=0, padx=5, pady=5, sticky='w')

        self.province_entry_var = tk.StringVar()  # 当前选中的城市名称
        self.province_entry = ttk.Combobox(self.root, textvariable=self.province_entry_var, width=47, font=('Arial', 11), foreground='grey')  # 城市选择下拉
        self.province_entry.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        self.province_entry.bind('<KeyRelease>', self.update_province_list)
        self.province_entry.insert(0, "按下↓键可快速选择，✔代表已查询查询全部时会跳过")
        self.province_entry.bind("<FocusIn>", self.clear_placeholder)
        self.province_entry.bind("<FocusOut>", self.add_placeholder)

        self.button_frame = ttk.Frame(self.root)  # 顶部按钮区容器
        self.button_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
        self.button_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.start_button = ttk.Button(self.button_frame, text="启动查询", command=self.start_search, style='TButton')  # 启动查询按钮
        self.start_button.grid(row=0, column=0, padx=5)
        self.export_button = ttk.Button(self.button_frame, text="导出CSV", command=self.export_csv, style='TButton')  # 手动导出按钮
        self.export_button.grid(row=0, column=1, padx=5)
        self.reset_button = ttk.Button(self.button_frame, text="恢复城市状态", command=self.reset_cities_status, style='TButton')  # 恢复状态按钮
        self.reset_button.grid(row=0, column=2, padx=5)
        self.stop_button = ttk.Button(self.button_frame, text="停止当前查询", command=self.stop_search, style='TButton')  # 停止查询按钮
        self.stop_button.grid(row=0, column=3, padx=5)
        self.open_folder_button = ttk.Button(self.button_frame, text="打开CSV文件夹", command=self.open_csv_folder, style='TButton')  # 打开导出目录按钮
        self.open_folder_button.grid(row=0, column=4, padx=5)
        self.save_settings_button = ttk.Button(self.button_frame, text="保存当前信息", command=self.save_settings, style='TButton')  # 保存设置按钮
        self.save_settings_button.grid(row=0, column=5, padx=5)
        self.clear_output_button = ttk.Button(self.button_frame, text="清除输出", command=self.clear_output, style='TButton')  # 清空输出按钮
        self.clear_output_button.grid(row=0, column=6, padx=5)


        
        self.realtime_export_var = tk.BooleanVar(value=True)  # 是否开启实时导出
        self.realtime_export_check = ttk.Checkbutton(self.root, text="实时导出CSV，建议开启（若输入已有的文件名，则在已有列表后追加）", variable=self.realtime_export_var)
        self.realtime_export_check.grid(row=3, column=0, padx=5, pady=5, sticky='w')
        
        self.realtime_export_path_entry = ttk.Entry(self.root, width=50, font=('Arial', 11))  # 实时导出 CSV 路径
        self.realtime_export_path_entry.grid(row=3, column=1, padx=5, pady=5, sticky='nsew')
        self.realtime_export_path_entry.insert(0, "商家信息.csv")
        
        self.auto_collect_var = tk.BooleanVar(value=False)  # 是否开启定时采集
        self.auto_collect_check = ttk.Checkbutton(self.root, text="开启定时采集功能（可输入多个时间，用空格隔开）", variable=self.auto_collect_var)
        self.auto_collect_check.grid(row=7, column=0, padx=5, pady=5, sticky='w')

        self.auto_collect_times_entry = ttk.Entry(self.root, width=50, font=('Arial', 11))  # 定时采集时间点（多值空格分隔）
        self.auto_collect_times_entry.grid(row=7, column=1, padx=5, pady=5, sticky='w')
        self.auto_collect_times_entry.insert(0, "6:00 18:00 24:00")

        self.remaining_time_label = ttk.Label(self.root, text="距离下次采集还剩：00:00:00", font=('Arial', 11, 'bold'))  # 倒计时显示
        self.remaining_time_label.grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky='w')

        # 创建左侧消息滚动框架
        self.message_frame = ScrollableFrame(self.root)  # 左侧消息滚动区
        self.message_frame.grid(row=5, column=0, padx=5, pady=5, sticky='nsew')

        # 创建右侧表格滚动框架
        self.table_frame = ScrollableFrame(self.root)  # 右侧表格滚动区
        self.table_frame.grid(row=5, column=1, padx=5, pady=5, sticky='nsew')

        # 列布局
        self.frame1 = self.create_frame(self.message_frame.get_frame())  # 消息列 1
        self.frame2 = self.create_frame(self.table_frame.get_frame())  # 数据列 1
        self.frame3 = self.create_frame(self.table_frame.get_frame())  # 数据列 2
        
        self.checkbox_frame = tk.Frame(self.root)  # 右侧字段选择容器
        self.checkbox_frame.grid(row=5, column=2, padx=5, pady=5, sticky='nsew')


        self.checkbox_canvas = tk.Canvas(self.checkbox_frame, borderwidth=2, relief="solid")  # 字段区域：画布（带边框）
        self.checkbox_scrollbar = ttk.Scrollbar(self.checkbox_frame, orient="vertical", command=self.checkbox_canvas.yview)  # 字段区域：垂直滚动条
        self.checkbox_scrollable_frame = ttk.Frame(self.checkbox_canvas)  # 字段区域：实际承载复选框的 frame


        self.checkbox_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.checkbox_canvas.configure(
                scrollregion=self.checkbox_canvas.bbox("all"),
                width=self.checkbox_scrollable_frame.winfo_reqwidth()
            )
        )

        self.checkbox_canvas.create_window((0, 0), window=self.checkbox_scrollable_frame, anchor="nw")
        self.checkbox_canvas.configure(yscrollcommand=self.checkbox_scrollbar.set)

        self.checkbox_canvas.pack(side="left", fill="both", expand=True)
        self.checkbox_scrollbar.pack(side="right", fill="y")

        # 字段映射：中文显示名 -> (AMap 字段英文名, 是否选中变量)
        self.fields = {
            "ID": ("id", tk.BooleanVar(value=False)),
            # "父POI的ID": ("parent", tk.BooleanVar(value=False)),
            "名称": ("name", tk.BooleanVar(value=True)),  # 默认选择名称
            "类型": ("type", tk.BooleanVar(value=False)),
            "类型编码": ("typecode", tk.BooleanVar(value=False)),
            # "行业类型": ("biz_type", tk.BooleanVar(value=False)),
            "地址": ("address", tk.BooleanVar(value=True)),  # 默认选择地址
            "经纬度": ("location", tk.BooleanVar(value=False)),
            # "离中心点距离": ("distance", tk.BooleanVar(value=False)),
            "电话": ("tel", tk.BooleanVar(value=True)),  # 默认选择电话
            # "邮编": ("postcode", tk.BooleanVar(value=False)),
            "网址": ("website", tk.BooleanVar(value=False)),
            "邮箱": ("email", tk.BooleanVar(value=False)),
            # "省份编码": ("pcode", tk.BooleanVar(value=False)),
            "省份": ("pname", tk.BooleanVar(value=False)),
            # "城市编码": ("citycode", tk.BooleanVar(value=False)),
            "城市": ("cityname", tk.BooleanVar(value=False)),
            # "区域编码": ("adcode", tk.BooleanVar(value=False)),
            "区域": ("adname", tk.BooleanVar(value=False)),
            "入口经纬度": ("entr_location", tk.BooleanVar(value=False)),
            "出口经纬度": ("exit_location", tk.BooleanVar(value=False)),
            # "POI导航id": ("navi_poiid", tk.BooleanVar(value=False)),
            # "地理格ID": ("gridcode", tk.BooleanVar(value=False)),
            # "别名": ("alias", tk.BooleanVar(value=False)),
            # "停车场类型": ("parking_type", tk.BooleanVar(value=False)),
            # "特色内容": ("tag", tk.BooleanVar(value=False)),
            # "是否有室内地图": ("indoor_map", tk.BooleanVar(value=False)),
            # "父级POI": ("cpid", tk.BooleanVar(value=False))
        }

        for field in self.fields:
            ttk.Checkbutton(self.checkbox_scrollable_frame, text=field, variable=self.fields[field][1]).pack(anchor="w")

        self.style = ttk.Style()  # 统一样式配置
        self.style.configure('TButton', font=('Arial', 12), foreground='blue')
        self.style.configure('TLabel', font=('Arial', 12))
        self.style.configure('TEntry', font=('Arial', 12))
        
        self.info_frame = ttk.Frame(self.root)  # 进度信息区域
        self.info_frame.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky='ew')

        self.queried_cities_label = ttk.Label(self.info_frame, text="已查询城市：0", font=('Arial', 11, 'bold'))
        self.queried_cities_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        self.total_cities_label = ttk.Label(self.info_frame, text=f"总城市：{len(province_adcode_list)}", font=('Arial', 11, 'bold'))
        self.total_cities_label.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        self.progress = ttk.Progressbar(self.info_frame, orient='horizontal', length=200, mode='determinate')  # 进度条
        self.progress.grid(row=0, column=2, padx=5, pady=5, sticky='ew')
        self.progress_label = ttk.Label(self.info_frame, text="进度：0.00%", font=('Arial', 11))
        self.progress_label.grid(row=0, column=3, padx=5, pady=5, sticky='w')
        self.data_too_large_label = ttk.Label(self.info_frame, text="输出表空白时数据量太大，请及时清除", font=('Arial', 11, 'bold'))
        self.data_too_large_label.grid(row=0, column=4, padx=5, pady=5, sticky='w')

        
    def clear_output(self):
        """清空右侧输出区域中的所有条目。"""
        for frame in self.frames:
            for widget in frame.winfo_children():
                widget.destroy()

    def clear_placeholder(self, event):
        """当输入框获得焦点时，清除占位提示文字并恢复正常颜色。"""
        widget = event.widget
        if widget == self.province_entry and self.province_entry.get() == "按下↓键可快速选择，✔代表已查询查询全部时会跳过":
            self.province_entry.delete(0, tk.END)
            self.province_entry.config(foreground='black')
        elif widget == self.keyword_entry and self.keyword_entry.get() == "查询完成后，先点击恢复状态，再进行新查询":
            self.keyword_entry.delete(0, tk.END)
            self.keyword_entry.config(foreground='black')
        elif widget == self.api_key_entry and self.api_key_entry.get() == "可输入多个key，每个key用空格隔开":
            self.api_key_entry.delete(0, tk.END)
            self.api_key_entry.config(foreground='black')

    def save_settings(self):
        """保存当前输入与字段选择到 settings.int（JSON）。"""
        settings = {
            "api_keys": self.api_key_entry.get(),
            "keywords": self.keyword_entry.get(),
            "all_provinces": self.all_provinces_var.get(),
            "province": self.province_entry_var.get(),
            "realtime_export": self.realtime_export_var.get(),
            "realtime_export_path": self.realtime_export_path_entry.get(),
            "auto_collect": self.auto_collect_var.get(),
            "auto_collect_times": self.auto_collect_times_entry.get(),
            "selected_fields": {field: var.get() for field, (english, var) in self.fields.items()}  
        }
        with open("settings.int", "w", encoding="utf-8") as file:
            json.dump(settings, file)

        
        popup = tk.Toplevel(self.root)
        popup.title("提示")
        label = ttk.Label(popup, text="成功保存参数")
        label.pack(pady=10, padx=10)
        popup.after(2000, popup.destroy)
        
    def load_settings(self):
        """加载已保存的设置（如存在）并恢复界面状态。"""
        try:
            with open("settings.int", "r", encoding="utf-8") as file:
                settings = json.load(file)
                self.api_key_entry.delete(0, tk.END)
                self.api_key_entry.insert(0, settings.get("api_keys", ""))
                self.keyword_entry.delete(0, tk.END)
                self.keyword_entry.insert(0, settings.get("keywords", ""))
                self.all_provinces_var.set(settings.get("all_provinces", False))
                self.province_entry_var.set(settings.get("province", ""))
                self.realtime_export_var.set(settings.get("realtime_export", True))
                self.realtime_export_path_entry.delete(0, tk.END)
                self.realtime_export_path_entry.insert(0, settings.get("realtime_export_path", ""))
                self.auto_collect_var.set(settings.get("auto_collect", False))
                self.auto_collect_times_entry.delete(0, tk.END)
                self.auto_collect_times_entry.insert(0, settings.get("auto_collect_times", ""))
                
                
                selected_fields = settings.get("selected_fields", {})
                for field, var in self.fields.items():
                    if field in selected_fields:
                        var[1].set(selected_fields[field])
        except FileNotFoundError:
            pass

    def add_placeholder(self, event):
        """当输入框失去焦点且为空时，恢复占位提示文字与灰色。"""
        widget = event.widget
        if widget == self.province_entry and self.province_entry.get() == "":
            self.province_entry.config(foreground='grey')
            self.province_entry.insert(0, "按下↓键可快速选择，✔代表已查询查询全部时会跳过")
        elif widget == self.keyword_entry and self.keyword_entry.get() == "":
            self.keyword_entry.config(foreground='grey')
            self.keyword_entry.insert(0, "查询完成后，先点击恢复状态，再进行新查询")
        elif widget == self.api_key_entry and self.api_key_entry.get() == "":
            self.api_key_entry.config(foreground='grey')
            self.api_key_entry.insert(0, "可输入多个key，每个key用空格隔开")   
            
    def update_clock(self):
        """每秒更新倒计时标签，并在到时触发定时采集。"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        if self.auto_collect_var.get():
            collect_times = self.auto_collect_times_entry.get().split()
            if current_time in collect_times:
                if not hasattr(self, 'last_collect_time') or self.last_collect_time != current_time:
                    self.start_search()
                    self.last_collect_time = current_time

            next_time = self.get_next_collect_time(now, collect_times)
            if next_time:
                remaining_time = next_time - now
                if remaining_time < timedelta(0):
                    remaining_time += timedelta(days=1)
                self.remaining_time_label.config(text=f"距离下次采集还剩：{str(remaining_time).split('.')[0]}")

        self.root.after(1000, self.update_clock)

    def get_next_collect_time(self, now, collect_times):
        """计算下一次采集时间；若今日已过则滚动到次日。"""
        today = now.date()
        time_points = [datetime.strptime(t.replace("24",'00'), "%H:%M").time() for t in collect_times]
        datetime_points = [datetime.combine(today, tp) for tp in time_points]

        future_times = [dt for dt in datetime_points if dt > now]
        if future_times:
            return min(future_times)
        else:
            return min(datetime_points) + timedelta(days=1)


    
    def open_csv_folder(self):
        """在系统文件管理器中打开当前实时导出路径所在文件夹。"""
        folder_path = os.path.dirname(os.path.abspath(self.realtime_export_path_entry.get().strip()))

        folder_path = folder_path if folder_path else '.'
        webbrowser.open(folder_path)


    def toggle_province_entry(self):
        """切换“查询所有城市”时的交互：禁用下拉框并自动填充下一未查询城市。"""
        if self.all_provinces_var.get():
            self.province_entry.config(state='disabled')
            self.update_province_entry()
            next_region = self.get_next_unqueried_city()
            if next_region:
                self.province_entry_var.set(next_region)
        else:
            self.province_entry.config(state='normal')

    def update_province_entry(self):
        """将下拉框设为第一个未查询过的城市，便于连续检索。"""
        for item in province_adcode_list:
            city = item.split(',')[1]
            if city not in queried_cities:
                self.province_entry_var.set(city)
                break

    def update_province_status(self):
        """刷新城市 ✔️/❌ 标记并更新下拉列表值。"""
        for i, item in enumerate(province_adcode_list):
            code, city = item.split(',')
            city = city.replace(' ✔️', '').replace(' ❌', '')
            if city in queried_cities:
                province_adcode_list[i] = f'{code},{city} ✔️'
            else:
                province_adcode_list[i] = f'{code},{city} ❌'
        self.province_entry['values'] = [item.split(',')[1] for item in province_adcode_list]

    def update_province_list(self, event):
        """根据输入的子串动态过滤下拉候选列表。

        参数：
        - event: Tk 事件对象（此处未直接使用，仅满足回调签名）。
        """
        current_text = self.province_entry_var.get()
        values = [item.split(',')[1] for item in province_adcode_list if current_text in item.split(',')[1]]
        self.province_entry['values'] = values

    def start_search(self):
        """校验输入，确定目标地区，并启动检索线程。"""
        # 获取 API Keys 列表（空格分隔，多 key 轮换）
        self.api_keys = [key for key in self.api_key_entry.get().strip().split() if key != '可输入多个key，每个key用空格隔开' and key]
        self.current_key_index = 0  # 当前使用的 key 下标

        keyword = self.keyword_entry.get().strip()  # 检索关键词

        if not self.api_keys or not self.api_keys[0] or not keyword or keyword == "查询完成后，先点击恢复状态，再进行新查询":
            messagebox.showwarning("警告", "API Key 和 关键词 都不能为空")
            return

        self.use_next_api_key()

        if self.all_provinces_var.get():
            regions = [item.split(',')[1].replace(' ✔️', '').replace(' ❌', '') for item in province_adcode_list if '✔️' not in item.split(',')[1]]
            if regions:
                self.province_entry_var.set(regions[0])
        else:
            region = self.province_entry_var.get().replace(' ✔️', '').replace(' ❌', '')
            if not region:
                messagebox.showwarning("警告", "请选择一个省份")
                return
            regions = [region]

        self.is_searching = True  # 置为检索中
        threading.Thread(target=self.search_pois, args=(keyword, regions)).start()  # 后台线程执行，避免卡住 UI

        
    
    def use_next_api_key(self):
        """切换到下一个 API Key；全部用尽则停止。"""
        if self.current_key_index < len(self.api_keys):
            self.api_key = self.api_keys[self.current_key_index]
            self.current_key_index += 1
            print(f"当前正在使用第 {self.current_key_index} 个 key: {self.api_key}")
            self.insert_text(self.frame1, f"开始查询...当前正在使用第 {self.current_key_index} 个 key\n")
        else:
            print("所有 key 都用完，程序结束。")
            self.insert_text(self.frame1, "所有 key 都用完，程序结束。\n")
            self.is_searching = False


    def insert_text(self, frame, text):
        """向指定面板追加一条文本记录（左对齐，自动换行）。"""
        if not hasattr(self, 'frames'):
            self.frames = []
        label = tk.Label(frame, text=text, anchor='w')
        label.pack(fill='x')

    def search_pois(self, keyword, regions):
        """分页请求高德文本检索接口，持续更新界面并按需导出。"""
        self.clear_frames()

        selected_fields = [(chinese, english) for chinese, (english, var) in self.fields.items() if var.get()]

        self.frames = []
        for idx in range(len(selected_fields)):
            frame = self.create_frame(self.table_frame.get_frame())
            self.frames.append(frame)

        url = "https://restapi.amap.com/v3/place/text"  # 文本检索接口
        session = requests.Session()
        # 基础重试策略：429/5xx 时退避重试
        retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        all_pois = []
        total_regions = len(regions)

        while regions and self.is_searching:
            region = regions.pop(0)
            self.province_entry_var.set(region)
            region_code_list = [item.split(',')[0] for item in province_adcode_list if region in item.split(',')[1]]
            print(f"正在查询 {region}...代码：{region_code_list}")
            if not region_code_list:
                self.insert_text(self.frame1, f"找不到省份代码：{region}\n")
                continue

            region_code = region_code_list[0]
            page_num = 1
            pois = []

            self.insert_text(self.frame1, f"开始查询 {region} 于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...\n")

            while self.is_searching:
                # 构建请求参数（每页 20 条）
                params = {
                    "key": self.api_key,
                    "keywords": keyword,
                    "city": region_code,
                    "offset": 20,
                    "output": "json",
                    "page": page_num,
                }
                response = session.get(url, params=params)
                data = response.json()

                status_code = response.status_code
                status_value = data.get('status')
                status_info = data.get('info')
                print(f"状态码: {status_code}, 返回状态值: {status_value}, 返回状态说明: {status_info}")
                self.insert_text(self.frame1, f"正在查询 {region}...状态码: {status_code}, 返回状态值: {status_value}, 返回状态说明: {status_info}\n")

                if status_code == 200 and status_value == '0':
                    # 高德返回状态为 0：通常为限额或 key 问题
                    if status_info == 'USER_DAILY_QUERY_OVER_LIMIT':
                        print("查询已超出每日限制，切换到下一个 key。")
                        self.insert_text(self.frame1, "查询已超出每日限制，切换到下一个 key。\n")
                    elif status_info == 'INVALID_USER_KEY':
                        print("无效的用户密钥，切换到下一个 key。")
                        self.insert_text(self.frame1, "无效的用户密钥，切换到下一个 key。\n")
                    self.use_next_api_key()
                    if not self.is_searching:
                        return
                    continue

                if data["status"] == "1" and int(data["count"]) > 0:
                    # 有结果：累加、显示，并按需实时写入 CSV
                    new_pois = data["pois"]
                    pois.extend(new_pois)
                    for poi in new_pois:
                        display_texts = [f"{chinese}: {poi[english]}" for chinese, english in selected_fields if english in poi]
                        for idx, text in enumerate(display_texts):
                            self.insert_text(self.frames[idx], text)

                        self.table_frame.canvas.yview_moveto(1)

                    if self.realtime_export_var.get():
                        self.export_to_csv_realtime(new_pois)

                    # 小于一页，说明已到末页
                    if len(new_pois) < 20:
                        break
                    page_num += 1
                    time.sleep(1.1)  # 轻微限速，避免过快触发风控
                else:
                    # 无更多数据或状态异常，结束本城市循环
                    break

            all_pois.extend(pois)
            queried_cities.append(region)
            queried_cities.append(region + " ✔️")
            self.save_queried_cities()
            self.update_progress(total_regions)

        self.insert_text(self.frame1, "查询结束.\n\n")
        self.insert_text(self.frames[0], "\n")
        self.insert_text(self.frames[1], "\n")
        self.table_frame.canvas.yview_moveto(1)
        self.pois_data = all_pois
        
    def clear_frames(self):
        """销毁结果面板中的所有 frame，便于新一轮查询重建。"""
        if hasattr(self, 'frames'):
            for frame in self.frames:
                frame.destroy()
            self.frames = []
    
    def update_progress(self, total_regions):
        """根据已查询城市数更新进度条与计数标签。"""
        queried_count = int(len(queried_cities)/2)  # 因为有两个状态，所以除以2
    
        self.queried_cities_label.config(text=f"已查询城市：{queried_count}")
        self.progress['value'] = (queried_count / total_regions) * 100
        self.progress_label.config(text=f"进度：{self.progress['value']:.2f}%")


    def export_to_csv_realtime(self, pois):
        """按所选字段实时追加写入 CSV（UTF-8 BOM）。"""
        realtime_export_path = self.realtime_export_path_entry.get().strip()
        if not realtime_export_path:
            realtime_export_path = "realtime_export.csv" 
        
        # 获取用户选择的字段
        selected_fields = [(chinese, english) for chinese, (english, var) in self.fields.items() if var.get()]

        # 判断文件是否被占用或没有权限
        try:
            with open(realtime_export_path, 'a', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                if os.path.getsize(realtime_export_path) == 0: 
                    header = [chinese for chinese, _ in selected_fields]
                    writer.writerow(header)
                for poi in pois:
                    row = [poi.get(english, '无数据') for _, english in selected_fields]
                    writer.writerow(row)
        except PermissionError as e:
            print(f"文件 '{realtime_export_path}' 被占用或没有写权限: {str(e)}")
            messagebox.showwarning("警告", f"无法写入文件 '{realtime_export_path}'，请检查文件是否已被占用或没有写权限。")
    
    def stop_search(self):
        """优雅停止当前检索，并在输出中插入分隔。"""
        self.is_searching = False
        self.insert_text(self.frame1, "用户主动终止查询.\n")
        self.insert_text(self.frame2, "\n")
        self.insert_text(self.frame3, "\n")
        
    def get_next_unqueried_city(self):
        """返回下一个未查询城市名称；若全部查询过则返回 None。"""
        for item in province_adcode_list:
            city = item.split(',')[1]
            if city not in queried_cities:
                return city
        return None

    def save_queried_cities(self):
        """将内存中的已查询城市同步写入文件，并刷新 UI 标记。"""
        with open(queried_cities_file, 'r', encoding='utf-8') as file:
            existing_cities = file.read().splitlines()

        for city in queried_cities:
            city_name = city.replace(' ✔️', '').replace(' ❌', '')
            if city_name not in existing_cities:
                existing_cities.append(city_name)
                existing_cities.append(city_name + " ✔️")

        with open(queried_cities_file, 'w', encoding='utf-8') as file:
            for city in existing_cities:
                file.write(city + "\n")

        self.update_province_status()

    def export_csv(self):
        """通过“另存为”导出汇总 POI（名称/地址/电话）。"""
        if not hasattr(self, 'pois_data'):
            messagebox.showwarning("警告", "没有数据可导出，请先进行查询。")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filepath:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["POI名称", "详细地址", "联系电话"])
                for poi in self.pois_data:
                    writer.writerow([poi['name'], poi['address'], poi.get('tel', '无电话')])
            messagebox.showinfo("提示", "导出完成")

    def reset_cities_status(self):
        """清空已查询城市记录与标记，并刷新界面列表。"""
        global queried_cities
        queried_cities = []
        for i, item in enumerate(province_adcode_list):
            code, city = item.split(',')
            city = city.replace(' ✔️', '').replace(' ❌', '')
            province_adcode_list[i] = f'{code},{city} ❌'
        self.province_entry['values'] = [item.split(',')[1] for item in province_adcode_list]

        with open(queried_cities_file, 'w', encoding='utf-8') as file:
            file.truncate()
        
        messagebox.showinfo("提示", "所有城市状态已恢复为未查询")

    def create_frame(self, container):
        """在给定容器中创建一个可扩展的列 frame。"""
        frame = tk.Frame(container)
        frame.pack(side="left", fill="both", expand=True)
        return frame

if __name__ == "__main__":
    root = tk.Tk()
    app = AMapGUI(root)

    style = ttk.Style()
    style.configure('TButton', font=('Arial', 12), foreground='blue', padding=10)
    style.configure('TLabel', font=('Arial', 12))
    style.configure('TEntry', font=('Arial', 12))

    root.mainloop()