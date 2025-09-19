# MapSearch：基于 Tkinter 的高德地图（AMap）POI 检索 GUI。

# 功能概览：
# - 按关键词在选定/全部城市检索
# - 多个 API Key 轮换与基础重试
# - 支持选择字段的实时 CSV 导出
# - 定时采集与倒计时显示
# - 设置项与已查询城市状态持久化


import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import os
import sys

def show_centered_message(title, message, message_type="info", parent_window=None):
    """显示居中的消息框"""
    try:
        if parent_window is None:
            # 如果没有提供父窗口，创建一个临时的根窗口
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            parent = root
        else:
            # 使用提供的父窗口
            parent = parent_window
            root = None
        
        # 创建简单的Toplevel窗口
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.resizable(False, False)
        dialog.transient(parent)  # 设置为主窗口的临时窗口
        dialog.grab_set()  # 模态窗口
        
        # 设置窗口样式
        dialog.configure(bg='#f8f9fa')
        
        # 创建主框架
        main_frame = tk.Frame(dialog, bg='#f8f9fa', relief='flat', bd=0)
        main_frame.pack(fill='both', expand=True, padx=25, pady=25)
        
        # 消息标签
        message_label = tk.Label(main_frame, text=message, 
                                font=('Microsoft YaHei UI', 11),
                                bg='#f8f9fa', fg='#2c3e50',
                                wraplength=280, justify='center')
        message_label.pack(pady=(0, 25))
        
        result = None
        
        def on_ok():
            nonlocal result
            result = True
            dialog.destroy()
        
        def on_cancel():
            nonlocal result
            result = False
            dialog.destroy()
        
        def on_yes():
            nonlocal result
            result = True
            dialog.destroy()
        
        def on_no():
            nonlocal result
            result = False
            dialog.destroy()
        
        # 按钮框架
        button_frame = tk.Frame(main_frame, bg='#f8f9fa')
        button_frame.pack()
        
        # 根据消息类型创建不同的按钮
        if message_type in ["yesno", "yesnocancel"]:
            yes_btn = tk.Button(button_frame, text="是", command=on_yes,
                               font=('Microsoft YaHei UI', 10), 
                               bg='#007bff', fg='white',
                               relief='flat', padx=20, pady=6,
                               cursor='hand2')
            yes_btn.pack(side='left', padx=6)
            
            no_btn = tk.Button(button_frame, text="否", command=on_no,
                              font=('Microsoft YaHei UI', 10),
                              bg='#6c757d', fg='white',
                              relief='flat', padx=20, pady=6,
                              cursor='hand2')
            no_btn.pack(side='left', padx=6)
            
            if message_type == "yesnocancel":
                cancel_btn = tk.Button(button_frame, text="取消", command=on_cancel,
                                      font=('Microsoft YaHei UI', 10),
                                      bg='#dc3545', fg='white',
                                      relief='flat', padx=20, pady=6,
                                      cursor='hand2')
                cancel_btn.pack(side='left', padx=6)
        else:
            ok_btn = tk.Button(button_frame, text="确定", command=on_ok,
                              font=('Microsoft YaHei UI', 10),
                              bg='#007bff', fg='white',
                              relief='flat', padx=25, pady=6,
                              cursor='hand2')
            ok_btn.pack()
        
        # 居中显示
        dialog.update_idletasks()
        
        if parent_window is not None:
            # 基于程序窗口居中显示
            parent_x = parent_window.winfo_x()
            parent_y = parent_window.winfo_y()
            parent_width = parent_window.winfo_width()
            parent_height = parent_window.winfo_height()
            
            x = parent_x + (parent_width // 2) - (dialog.winfo_width() // 2)
            y = parent_y + (parent_height // 2) - (dialog.winfo_height() // 2)
        else:
            # 基于屏幕居中显示
            screen_width = parent.winfo_screenwidth()
            screen_height = parent.winfo_screenheight()
            x = (screen_width // 2) - (dialog.winfo_width() // 2)
            y = (screen_height // 2) - (dialog.winfo_height() // 2)
        
        dialog.geometry(f"+{x}+{y}")
        
        # 等待窗口关闭
        dialog.wait_window()
        
        if root:
            root.destroy()
        
        return result
    except Exception as e:
        # 如果自定义窗口失败，使用默认的messagebox
        print(f"自定义窗口失败，使用默认messagebox: {e}")
        try:
            if parent_window is None:
                root = tk.Tk()
                root.withdraw()
                parent = root
            else:
                parent = parent_window
                root = None
            
            if message_type == "error":
                result = messagebox.showerror(title, message, parent=parent)
            elif message_type == "warning":
                result = messagebox.showwarning(title, message, parent=parent)
            elif message_type == "yesno":
                result = messagebox.askyesno(title, message, parent=parent)
            elif message_type == "yesnocancel":
                result = messagebox.askyesnocancel(title, message, parent=parent)
            else:  # info
                result = messagebox.showinfo(title, message, parent=parent)
            
            if root:
                root.destroy()
            return result
        except:
            # 最后的备用方案
            if message_type == "error":
                return messagebox.showerror(title, message)
            elif message_type == "warning":
                return messagebox.showwarning(title, message)
            elif message_type == "yesno":
                return messagebox.askyesno(title, message)
            elif message_type == "yesnocancel":
                return messagebox.askyesnocancel(title, message)
            else:  # info
                return messagebox.showinfo(title, message)
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
import configparser


class ConfigManager:
    """统一配置文件管理类"""
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self._load_default_config()
        self.load_config()
    
    def _load_default_config(self):
        """返回默认配置结构"""
        return {
            "metadata": {
                "version": "1.0",
                "created_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_provinces": 0,
                "total_cities": 0,
                "description": "MapSearch配置文件"
            },
            "user_settings": {
                "api_keys": "",
                "keywords": "",
                "all_provinces": False,
                "realtime_export": True,
                "realtime_export_path": "商家信息.csv",
                "auto_collect": False,
                "auto_collect_times": "6:00 18:00 24:00"
            },
            "field_settings": {
                "ID": False,
                "名称": True,
                "类型": False,
                "电话": True,
                "网址": False,
                "邮箱": False,
                "省份": True,
                "城市": True,
                "区域": True,
                "地址": True,
                "类型编码": False,
                "经纬度": False,
                "入口经纬度": False,
                "出口经纬度": False
            },
            "provinces": {}
        }
    
    def load_config(self):
        """从JSON文件加载配置，如果文件不存在则使用默认配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并配置，确保新字段不丢失
                    self._merge_config(loaded_config)
                print(f"已加载配置文件: {self.config_file}")
            else:
                print(f"配置文件不存在，使用默认配置: {self.config_file}")
        except Exception as e:
            print(f"加载配置文件失败: {e}，使用默认配置")
    
    def _merge_config(self, loaded_config):
        """合并加载的配置和默认配置"""
        for section, values in loaded_config.items():
            if section in self.config:
                if isinstance(values, dict):
                    self.config[section].update(values)
                else:
                    self.config[section] = values
    
    def save_config(self):
        """保存当前配置到JSON文件"""
        try:
            self.config["metadata"]["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"配置已保存到: {self.config_file}")
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get_user_settings(self):
        """获取用户设置"""
        return self.config.get("user_settings", {})
    
    def update_user_settings(self, settings):
        """更新用户设置"""
        self.config["user_settings"].update(settings)
    
    def get_field_settings(self):
        """获取字段设置"""
        return self.config.get("field_settings", {})
    # 
    def update_field_settings(self, fields):
        """更新字段设置"""
        self.config["field_settings"].update(fields)
    
    def get_provinces(self):
        """获取省份数据"""
        return self.config.get("provinces", {})
    
    def get_cities_by_province(self, province_name):
        """获取指定省份下的所有城市"""
        provinces = self.config.get("provinces", {})
        if province_name in provinces:
            return provinces[province_name].get("cities", {})
        return {}
    
    def get_all_cities(self):
        """获取所有城市数据（平铺结构）：返回 {city_name: city_code}。"""
        all_cities = {}
        provinces = self.config.get("provinces", {})
        for province_name, province in provinces.items():
            cities = province.get("cities", {})
            for city_name, city_data in cities.items():
                city_code = city_data.get("adcode")
                if city_name and city_code:
                    all_cities[city_name] = city_code
        return all_cities

    def iter_cities(self, province_name):
        """遍历指定省份下的城市，统一返回 (city_code, city_name)。
        根据当前配置文件结构：cities = { city_name: { adcode: city_code, ... } }
        """
        provinces = self.config.get("provinces", {})
        province = provinces.get(province_name, {})
        cities = province.get("cities", {})
        for city_name, city_data in cities.items():
            city_code = city_data.get("adcode")
            if city_name and city_code:
                yield city_code, city_name
    
    def update_provinces_data(self, province_to_cities, city_name_to_adcode):
        """更新省市数据到配置中，存储为：
        provinces = {
            province_name: {
                "name": province_name,
                "adcode": province_adcode,
                "cities": { city_name: { "name": city_name, "adcode": city_adcode, ... } }
            }
        }
        兼容传入的 city_pairs 为 (city_name, city_code) 或 (city_code, city_name)。
        """
        # 清空现有的省份数据
        self.config["provinces"] = {}

        for province_name, city_pairs in province_to_cities.items():
            # 推导省级 adcode（城市前两位 + 0000）
            province_adcode = ""
            if city_pairs:
                first_a, first_b = city_pairs[0]
                # 判断哪一个是 code
                candidate = first_a if (isinstance(first_a, str) and first_a.isdigit()) else first_b
                if isinstance(candidate, str) and len(candidate) >= 2 and candidate.isdigit():
                    province_adcode = candidate[:2] + "0000"

            self.config["provinces"][province_name] = {
                "name": province_name,
                "adcode": province_adcode,
                "cities": {}
            }

            for a, b in city_pairs:
                if isinstance(a, str) and a.isdigit():
                    city_code, city_name = a, b
                else:
                    city_name, city_code = a, b
                self.config["provinces"][province_name]["cities"][city_name] = {
                    "name": city_name,
                    "adcode": city_code,
                    "queried": False,
                    "last_query_time": None,
                    "query_count": 0
                }
        
        # 更新统计信息
        self._update_metadata_counts()
    
    def update_city_query_status(self, province_name, city_code, city_name, queried=True):
        """更新城市查询状态"""
        if "provinces" not in self.config:
            self.config["provinces"] = {}
        
        if province_name not in self.config["provinces"]:
            self.config["provinces"][province_name] = {"adcode": "", "cities": {}}
        
        if "cities" not in self.config["provinces"][province_name]:
            self.config["provinces"][province_name]["cities"] = {}
        
        # 以城市名为键进行存储，保持 adcode 字段
        cities = self.config["provinces"][province_name]["cities"]
        city_data = cities.get(city_name, {
            "name": city_name,
            "adcode": city_code,
            "queried": False,
            "last_query_time": None,
            "query_count": 0
        })
        
        if queried:
            city_data["queried"] = True
            city_data["last_query_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            city_data["query_count"] = city_data.get("query_count", 0) + 1
        else:
            city_data["queried"] = False
        self.config["provinces"][province_name]["cities"][city_name] = city_data
        
        # 立即持久化到文件
        try:
            self.save_config()
        except Exception:
            pass
    
    def get_queried_cities(self):
        """获取已查询城市列表"""
        queried_cities = []
        provinces = self.config.get("provinces", {})
        for province_name, province_data in provinces.items():
            cities = province_data.get("cities", {})
            for city_name, city_data in cities.items():
                if city_data.get("queried", False):
                    queried_cities.append(city_name)
        return queried_cities
    
    def reset_all_query_status(self):
        """重置所有城市的查询状态"""
        provinces = self.config.get("provinces", {})
        for province_name, province_data in provinces.items():
            cities = province_data.get("cities", {})
            for city_name, city_data in cities.items():
                city_data["queried"] = False
                city_data["last_query_time"] = None
                city_data["query_count"] = 0
    
    def find_province_by_city_code(self, city_code):
        """根据城市代码找到所属省份名；兼容不同 cities 结构。未找到返回空字符串。"""
        provinces = self.config.get("provinces", {})
        for province_name, province_data in provinces.items():
            cities = province_data.get("cities", {})
            # 兼容以代码为键
            if city_code in cities:
                return province_name
            # 兼容以名称为键，值里有 adcode
            for _, cdata in cities.items():
                if isinstance(cdata, dict) and cdata.get("adcode") == city_code:
                    return province_name
        return ""
    
    def _update_metadata_counts(self):
        """更新元数据中的统计信息"""
        provinces = self.config.get("provinces", {})
        total_provinces = len(provinces)
        total_cities = sum(len(p.get("cities", {})) for p in provinces.values())
        
        self.config["metadata"]["total_provinces"] = total_provinces
        self.config["metadata"]["total_cities"] = total_cities


class TriStateCheckbutton(tk.Checkbutton):
    """简单的三态复选框：支持选中、未选中、部分选中三种状态。"""
    def __init__(self, parent, text="", command=None, **kwargs):
        self._state = "unchecked"  # unchecked, checked, partial
        self._command = command
        # 使用 BooleanVar 来避免冲突
        self.var = tk.BooleanVar(value=False)
        super().__init__(parent, text=text, variable=self.var, 
                        command=self._on_click, **kwargs)
        self._update_appearance()
        
    def _on_click(self):
        """处理点击事件：用户点击仅在 checked 与 unchecked 间切换。
        部分选中（partial）仅用于程序根据城市勾选状态设置，不通过点击进入。
        """
        if self._state == "checked":
            self._state = "unchecked"
        else:
            # includes "unchecked" and "partial" → set to checked
            self._state = "checked"
        self._update_appearance()
        
        if self._command:
            self._command()
    
    def _update_appearance(self):
        """根据状态更新复选框外观。"""
        if self._state == "checked":
            self.var.set(True)
        elif self._state == "partial":
            self.var.set(True)
        else:  # unchecked
            self.var.set(False)
    
    def get_state(self):
        """获取当前状态。"""
        return self._state
    
    def set_state(self, state):
        """设置状态。"""
        if state in ["unchecked", "checked", "partial"]:
            self._state = state
            self._update_appearance()
            # 同步 variable（便于上层通过 .var.get() 判断）
            if state == "checked":
                self.var.set(True)
            else:
                # partial 与 unchecked 统一表现为未完全选中
                self.var.set(False)
    
    def is_checked(self):
        """是否完全选中。"""
        return self._state == "checked"
    
    def is_partial(self):
        """是否部分选中。"""
        return self._state == "partial"

class ProvinceCheckbutton(tk.Frame):
    """省份复选框：三态复选框 + 可点击省份名称。"""
    def __init__(self, parent, text="", province_name="", on_check_changed=None, on_click=None, canvas_ref=None, **kwargs):
        """初始化省份条目，绑定三态复选框与点击省名事件。"""
        super().__init__(parent, **kwargs)
        self.province_name = province_name
        self.on_check_changed = on_check_changed
        self.on_click = on_click
        self.canvas_ref = canvas_ref  # 直接保存画布引用
        
        # 三态复选框（checked/unchecked/partial）：用于呈现"全选/全不选/部分选中"的状态
        self.checkbox = TriStateCheckbutton(self, text="", command=self._on_check_changed,
                                            bg='#ffffff')
        self.checkbox.pack(side='left')
        
        # 省份名称标签
        self.base_text = text
        self.label = tk.Label(self, text=self.base_text, cursor='hand2', foreground='blue', bg='#ffffff')
        self.label.pack(side='left', padx=(5, 0))
        self.label.bind("<Button-1>", self._on_click)
        
        # 为省份名称标签绑定鼠标滚轮事件，确保鼠标在文字上也能滚动
        if self.canvas_ref:
            self.label.bind("<Enter>", self._on_label_enter)
            self.label.bind("<Leave>", self._on_label_leave)
        
        # 为整个省份复选框框架绑定滚轮事件，确保鼠标在复选框上也能滚动
        if self.canvas_ref:
            self.bind("<Enter>", self._on_frame_enter)
            self.bind("<Leave>", self._on_frame_leave)
        
    def _on_label_enter(self, event):
        """鼠标进入省份名称标签时，绑定滚轮事件到省份画布"""
        if self.canvas_ref:
            try:
                # 直接使用保存的画布引用
                self.canvas_ref.bind_all("<MouseWheel>", 
                    lambda ev: self.canvas_ref.yview_scroll(int(-1*(ev.delta/120)), "units"))
            except Exception as e:
                print(f"绑定省份滚轮事件失败: {e}")
    
    def _on_label_leave(self, event):
        """鼠标离开省份名称标签时，解绑滚轮事件"""
        if self.canvas_ref:
            try:
                # 直接使用保存的画布引用
                self.canvas_ref.unbind_all("<MouseWheel>")
            except Exception as e:
                print(f"解绑省份滚轮事件失败: {e}")
    
    def _on_frame_enter(self, event):
        """鼠标进入整个省份复选框框架时，绑定滚轮事件到省份画布"""
        if self.canvas_ref:
            try:
                # 直接使用保存的画布引用
                self.canvas_ref.bind_all("<MouseWheel>", 
                    lambda ev: self.canvas_ref.yview_scroll(int(-1*(ev.delta/120)), "units"))
            except Exception as e:
                print(f"绑定省份复选框滚轮事件失败: {e}")
    
    def _on_frame_leave(self, event):
        """鼠标离开整个省份复选框框架时，解绑滚轮事件"""
        if self.canvas_ref:
            try:
                # 直接使用保存的画布引用
                self.canvas_ref.unbind_all("<MouseWheel>")
            except Exception as e:
                print(f"解绑省份复选框滚轮事件失败: {e}")
    
    def _on_check_changed(self):
        """当省份三态变化时，将状态反馈给上层回调。"""
        if self.on_check_changed:
            self.on_check_changed(self.province_name, self.checkbox.get_state())
    
    def _on_click(self, event):
        """点击省份名称时触发，通知上层仅显示该省城市。"""
        if self.on_click:
            self.on_click(self.province_name)
    
    def get_state(self):
        """返回当前三态状态字符串。"""
        return self.checkbox.get_state()
    
    def set_state(self, state):
        """设置三态状态：unchecked/partial/checked。"""
        self.checkbox.set_state(state)
        self._update_label_for_state(state)

    def _update_label_for_state(self, state: str):
        """根据状态更新省份标签文案与颜色，突出"部分选择"。"""
        if state == "partial":
            self.label.config(text=f"{self.base_text}（部分）", foreground='#f59e0b')  # amber 提示色
        else:
            # checked/unchecked 恢复原文案与默认颜色
            self.label.config(text=self.base_text, foreground='blue')

class ScrollableFrame(tk.Frame):
    """可滚动容器：基于 Canvas + 垂直/水平滚动条。"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.container = container
        # 去除黑色边框：取消画布边框与高亮
        self.canvas = tk.Canvas(self, borderwidth=0, relief="flat", highlightthickness=0)
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

        # 绑定滚轮到画布和内部可滚动区域，确保鼠标在文字上也能滚动
        self.canvas.bind("<Enter>", lambda e: self._bind_to_mousewheel())
        self.canvas.bind("<Leave>", lambda e: self._unbind_from_mousewheel())
        self.scrollable_frame.bind("<Enter>", lambda e: self._bind_to_mousewheel())
        self.scrollable_frame.bind("<Leave>", lambda e: self._unbind_from_mousewheel())

    def _bind_to_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_from_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def get_frame(self):
        return self.scrollable_frame

    

class AMapGUI:
    """主界面：执行高德 POI 检索、定时任务与 CSV 导出。"""
    def __init__(self, root):
        """初始化主窗口、配置管理器、加载初始数据并构建 UI。"""
        self.root = root  # Tk 根窗口
        self.root.title("高德地图地点检索 - v1.2")
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 从 ConfigManager 加载城市数据（以配置为准）
        all_cities = self.config_manager.get_all_cities()  # {city_name: city_code}
        self.queried_city_names = set(self.config_manager.get_queried_cities())
        
        # 城市名 -> 复选框变量（用于将来扩展城市多选）
        self.checked_cities = {city_name: tk.BooleanVar(value=False) for city_name in all_cities.keys()}
        self.is_searching = False  # 标识是否正在检索（控制循环与终止）
        self.is_paused = False  # 标识是否处于暂停状态
        self.frames = []  # 右侧结果列的 frame 容器列表
        # 初始化复选框容器
        self.city_checkbuttons = {}
        self.province_checkbuttons = {}
        # 省/市数据加载防抖标志
        self.is_loading_province_city = False
        self.create_widgets()
        self.load_settings()  
        # 尝试从本地文件或ConfigManager加载省市数据
        if not self.load_province_city_data_from_config():
            print("本地省市数据文件不存在或为空，请点击'加载省/市'按钮从远程加载")
        self.update_clock()  # 启动定时器
        # 初始化进度显示为0
        self.update_progress(0)
        self.root.grid_columnconfigure(1, weight=1)  # 右侧列自适应
        for row_index in range(11):  # 行自适应，防止窗口拉伸错位（扩展以容纳城市文件控件）
            self.root.grid_rowconfigure(row_index, weight=1)


    def create_widgets(self):
        """构建窗口的控件、布局与样式（头部、配置、地区、操作、结果）。"""
        
        # 设置主窗口样式
        self.root.configure(bg='#ffffff')
        self.root.title("高德地图商家信息查询工具 - v1.2")
        self.root.geometry("1000x800")
        self.root.minsize(900, 600)
        
        # 设置样式
        self.setup_styles()
        
        # 主容器 - 减少边距，更紧凑
        main_container = tk.Frame(self.root, bg='#ffffff')
        main_container.pack(fill='both', expand=True, padx=12, pady=1)
        
        # 创建各个区域
        self.create_header(main_container)
        self.create_config_card(main_container)
        self.create_selection_card(main_container)
        self.create_action_card(main_container)
        self.create_results_card(main_container)
        # 进度显示已移动到操作面板内
        
    def create_header(self, parent):
        """创建顶部标题区域。"""
        header_frame = tk.Frame(parent, bg='#ffffff')
        header_frame.pack(fill='x', pady=(0, 4))
        
        # 主标题 - 简化设计
        # title_label = tk.Label(header_frame, text="高德地图商家信息查询工具", 
        #                       font=self.fonts['title'],
        #                       fg='#1f2937', bg='#ffffff')
        # title_label.pack(side='left')
        
        # 头部去除"加载省市数据"按钮，移至配置行与"实时导出"同一行
        
    def create_config_card(self, parent):
        """创建配置卡片。
        """
        # 配置区域 - 扁平化设计
        config_frame = tk.Frame(parent, bg='#ffffff', relief='flat', bd=1)
        config_frame.pack(fill='x', pady=(0, 0))
        
        # 标题
        title_frame = tk.Frame(config_frame, bg='#ffffff')
        title_frame.pack(fill='x', padx=12, pady=(6, 4))
        
        config_title = tk.Label(title_frame, text="基本配置", 
                               font=('Microsoft YaHei UI', 11, 'bold'),
                               fg='#374151', bg='#ffffff')
        config_title.pack(side='left')
        
        # 内容区域：API/关键词/导出路径/加载按钮 同一行
        # 说明：同一行能让用户按照"填 API → 填关键词 → 勾选导出 → 一键加载"顺序从左到右操作
        content_frame = tk.Frame(config_frame, bg='#ffffff')
        content_frame.pack(fill='x', padx=12, pady=(0, 4))
        # 让第1列(API输入框列)可伸缩
        content_frame.grid_columnconfigure(1, weight=1)

        # API
        tk.Label(content_frame, text="API Keys", font=('Microsoft YaHei UI', 9),
                fg='#6b7280', bg='#ffffff').grid(row=0, column=0, sticky='w')
        self.api_key_entry = tk.Entry(content_frame, font=('Consolas', 9),
                                     bg='white', fg='#374151', relief='solid', bd=1,
                                     highlightthickness=0, width=50)
        self.api_key_entry.grid(row=0, column=1, sticky='ew', padx=(6, 12))
        self.api_key_entry.insert(0, '05539bdacda89aa2b5341552259a6702')
        self.api_key_entry.bind("<FocusIn>", self.clear_placeholder)
        self.api_key_entry.bind("<FocusOut>", self.add_placeholder)

        # 关键词
        tk.Label(content_frame, text="关键词", font=('Microsoft YaHei UI', 9),
                fg='#6b7280', bg='#ffffff').grid(row=0, column=2, sticky='w')
        self.keyword_entry = tk.Entry(content_frame, font=('Microsoft YaHei UI', 9),
                                     bg='white', fg='#374151', relief='solid', bd=1,
                                     highlightthickness=0, width=16)
        self.keyword_entry.grid(row=0, column=3, sticky='w', padx=(6, 12))
        self.keyword_entry.insert(0, "水族馆")
        self.keyword_entry.bind("<FocusIn>", self.clear_placeholder)
        self.keyword_entry.bind("<FocusOut>", self.add_placeholder)

        # 导出
        self.realtime_export_var = tk.BooleanVar(value=True)
        self.realtime_export_check = tk.Checkbutton(content_frame, text="实时导出CSV",
                                                   variable=self.realtime_export_var,
                                                   font=('Microsoft YaHei UI', 9),
                                                   fg='#6b7280', bg='#ffffff', relief='flat')
        self.realtime_export_check.grid(row=0, column=4, sticky='w')
        self.realtime_export_path_entry = tk.Entry(content_frame, font=('Microsoft YaHei UI', 9),
                                                   bg='white', fg='#374151', relief='solid', bd=1,
                                                   highlightthickness=0, width=18)
        self.realtime_export_path_entry.grid(row=0, column=5, sticky='w', padx=(6, 12))
        self.realtime_export_path_entry.insert(0, "商家信息.csv")

        # 加载按钮
        # 说明：放在最右，完成配置后立即点击加载省/市数据
        self.load_area_button = self.create_button(content_frame, "加载省市数据",
                                         command=self.fetch_province_city_data,
                                         variant='primary', size='sm', padx=12, pady=4)
        self.load_area_button.grid(row=0, column=6, sticky='w')
        
    def create_selection_card(self, parent):
        """创建地区选择卡片：左侧省份三态，右侧城市列表与统计。"""
        # 地区选择区域
        selection_frame = tk.Frame(parent, bg='#ffffff', relief='flat', bd=1)
        selection_frame.pack(fill='both', expand=False, pady=(0, 0))
        
        # 标题
        title_frame = tk.Frame(selection_frame, bg='#ffffff')
        title_frame.pack(fill='x', padx=12, pady=(6, 4))
        
        selection_title = tk.Label(title_frame, text="地区选择", 
                                  font=('Microsoft YaHei UI', 11, 'bold'),
                                  fg='#374151', bg='#ffffff')
        selection_title.pack(side='left')
        
        # 内容区域
        content_frame = tk.Frame(selection_frame, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=12, pady=(0, 6))
        content_frame.grid_columnconfigure((0, 1), weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # 省份区域（左）- 顶部带"查询所有省份"按钮
        province_header = tk.Frame(content_frame, bg='#ffffff')
        province_header.grid(row=0, column=0, sticky='ew', pady=(0, 5), padx=(0, 10))
        province_header.grid_columnconfigure(0, weight=1)
        tk.Label(province_header, text="省份", font=('Microsoft YaHei UI', 10, 'bold'),
                 fg='#6b7280', bg='#ffffff').grid(row=0, column=0, sticky='w')
        # "选择所有省份"二态复选框：checked=全选，unchecked=全不选
        self.select_all_var = tk.BooleanVar(value=False)
        self.all_provinces_check = tk.Checkbutton(
            province_header,
            text="选择所有省份",
            variable=self.select_all_var,
            command=self.on_all_provinces_changed,
            bg='#ffffff',
            relief='flat'
        )
        self.all_provinces_check.grid(row=0, column=1, sticky='e')
        
        province_container = tk.Frame(content_frame, bg='white', relief='solid', bd=1)
        province_container.grid(row=1, column=0, sticky='nsew', padx=(0, 5))
        
        self.province_cb_canvas = tk.Canvas(province_container, bg='white', highlightthickness=0, height=140)
        self.province_cb_scroll = tk.Scrollbar(province_container, orient='vertical', 
                                              command=self.province_cb_canvas.yview)
        self.province_cb_frame = tk.Frame(self.province_cb_canvas, bg='white')
        
        self.province_cb_frame.bind("<Configure>", 
                                   lambda e: self.province_cb_canvas.configure(
                                       scrollregion=self.province_cb_canvas.bbox("all")))
        
        self.province_cb_canvas.create_window((0, 0), window=self.province_cb_frame, anchor='nw')
        self.province_cb_canvas.configure(yscrollcommand=self.province_cb_scroll.set)
        
        self.province_cb_canvas.pack(side='left', fill='both', expand=True)
        self.province_cb_scroll.pack(side='right', fill='y')
        
        # 城市区域（右）- 顶部带"选择所有市"二态复选框（仅作用于当前列表）
        city_header = tk.Frame(content_frame, bg='#ffffff')
        city_header.grid(row=0, column=1, sticky='ew', pady=(0, 5), padx=(5, 0))
        city_header.grid_columnconfigure(0, weight=1)
        tk.Label(city_header, text="城市", font=('Microsoft YaHei UI', 10, 'bold'),
                 fg='#6b7280', bg='#ffffff').grid(row=0, column=0, sticky='w')
        self.select_all_cities_var = tk.BooleanVar(value=False)
        self.select_all_cities_check = tk.Checkbutton(
            city_header,
            text="选择所有市",
            variable=self.select_all_cities_var,
            command=self.on_all_cities_changed,
            bg='#ffffff',
            relief='flat'
        )
        self.select_all_cities_check.grid(row=0, column=1, sticky='e')
        
        city_container = tk.Frame(content_frame, bg='white', relief='solid', bd=1)
        city_container.grid(row=1, column=1, sticky='nsew', padx=(5, 0))
        
        self.city_cb_canvas = tk.Canvas(city_container, bg='white', highlightthickness=0, height=140)
        self.city_cb_scroll = tk.Scrollbar(city_container, orient='vertical', 
                                          command=self.city_cb_canvas.yview)
        self.city_cb_frame = tk.Frame(self.city_cb_canvas, bg='white')
        
        self.city_cb_frame.bind("<Configure>", 
                               lambda e: self.city_cb_canvas.configure(
                                   scrollregion=self.city_cb_canvas.bbox("all")))
        
        self.city_cb_canvas.create_window((0, 0), window=self.city_cb_frame, anchor='nw')
        self.city_cb_canvas.configure(yscrollcommand=self.city_cb_scroll.set)
        
        self.city_cb_canvas.pack(side='left', fill='both', expand=True)
        self.city_cb_scroll.pack(side='right', fill='y')
        
        # 选择状态
        self.selected_provinces = set()
        self.selected_cities = set()
        self.province_vars = {}
        self.city_vars = {}
        
        # 统计信息
        stats_frame = tk.Frame(content_frame, bg='#ffffff')
        stats_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(4, 0))
        
        self.area_hint_label = tk.Label(stats_frame, text="未选择城市", 
                                       font=('Microsoft YaHei UI', 9),
                                       fg='#9ca3af', bg='#ffffff')
        self.area_hint_label.pack(side='left')
        
        # 省市数据结构
        self.province_to_cities = {}
        self.city_name_to_adcode = {}
        
        # 鼠标事件
        self._attach_mousewheel(self.province_cb_canvas, self.province_cb_canvas)
        self._attach_mousewheel(self.province_cb_frame, self.province_cb_canvas)
        self._attach_mousewheel(self.city_cb_canvas, self.city_cb_canvas)
        self._attach_mousewheel(self.city_cb_frame, self.city_cb_canvas)

        # 构建省份复选框列表
        self.build_provinces_ui()
        
    def create_action_card(self, parent):
        """创建操作卡片：查询、停止、导出与辅助操作及进度。"""
        # 操作区域
        action_frame = tk.Frame(parent, bg='#ffffff', relief='flat', bd=1)
        action_frame.pack(fill='x', pady=(0, 0))
        
        # 标题
        title_frame = tk.Frame(action_frame, bg='#ffffff')
        title_frame.pack(fill='x', padx=12, pady=(4, 2))
        
        action_title = tk.Label(title_frame, text="操作面板", 
                               font=('Microsoft YaHei UI', 11, 'bold'),
                               fg='#374151', bg='#ffffff')
        action_title.pack(side='left')
        
        # 内容区域
        content_frame = tk.Frame(action_frame, bg='#ffffff')
        content_frame.pack(fill='x', padx=12, pady=(0, 2))
        
        # 操作按钮行（统一样式，单行排列）
        actions_row = tk.Frame(content_frame, bg='#ffffff')
        actions_row.pack(fill='x', pady=(0, 4))

        # 统一按钮样式：size=sm，统一间距；保留语义颜色
        self.start_button = self.create_button(actions_row, "开始查询",
                                     command=self.start_search, variant='success', size='sm', padx=12, pady=6)
        self.start_button.pack(side='left', padx=(0, 8))

        # 新增 暂停/继续 按钮（位于"停止"左侧）
        self.pause_button = self.create_button(actions_row, "暂停",
                                     command=self.toggle_pause, variant='warning', size='sm', padx=12, pady=6)
        self.pause_button.pack(side='left', padx=(0, 8))
        self.pause_button.configure(state='disabled')

        self.stop_button = self.create_button(actions_row, "停止",
                                    command=self.stop_search, variant='danger', size='sm', padx=12, pady=6)
        self.stop_button.pack(side='left', padx=(0, 8))

        self.export_button = self.create_button(actions_row, "导出 CSV",
                                      command=self.export_csv, variant='primary', size='sm', padx=12, pady=6)
        self.export_button.pack(side='left', padx=(0, 8))

        # 辅助操作（同一行继续追加）
        aux_buttons = [
            ("重置状态", self.reset_cities_status),
            ("保存设置", self.save_settings),
            ("重新加载配置", self.refresh_config),
            ("打开文件夹", self.open_csv_folder),
            ("清除输出", self.clear_output)
        ]
        for text, command in aux_buttons:
            btn = self.create_button(actions_row, text, command=command,
                           variant='secondary', size='sm', padx=12, pady=6)
            btn.pack(side='left', padx=(0, 8))
            
        # 查询进度区域（放在操作面板内，更显眼）
        progress_section = tk.Frame(content_frame, bg='#ffffff', relief='solid', bd=1)
        progress_section.pack(fill='x', pady=(4, 0))
        
        # 进度标题
        progress_title = tk.Frame(progress_section, bg='#ffffff')
        progress_title.pack(fill='x', padx=10, pady=(6, 3))
        
        tk.Label(progress_title, text="🔍 查询进度", 
                font=('Microsoft YaHei UI', 9, 'bold'),
                fg='#1e40af', bg='#ffffff').pack(side='left')
        
        # 进度内容
        progress_content = tk.Frame(progress_section, bg='#ffffff')
        progress_content.pack(fill='x', padx=10, pady=(0, 6))
        
        # 左侧状态信息
        left_status = tk.Frame(progress_content, bg='#ffffff')
        left_status.pack(side='left')
        
        self.queried_cities_label = tk.Label(left_status, text="已查询: 0", 
                                            font=('Microsoft YaHei UI', 9),
                                            fg='#374151', bg='#ffffff')
        self.queried_cities_label.pack(side='left', padx=(0, 15))
        
        self.total_cities_label = tk.Label(left_status, text=f"总计: {sum(len(p.get('cities', {})) for p in self.config_manager.get_provinces().values())}", 
                                          font=('Microsoft YaHei UI', 9),
                                          fg='#374151', bg='#ffffff')
        self.total_cities_label.pack(side='left', padx=(0, 15))
        
        # 中间进度条区域
        progress_bar_frame = tk.Frame(progress_content, bg='#ffffff')
        progress_bar_frame.pack(side='left', fill='x', expand=True, padx=(0, 15))
        
        # 进度条容器（黑框）
        progress_container = tk.Frame(progress_bar_frame, bg='#ffffff', height=18, relief='solid', bd=1)
        progress_container.pack(fill='x')
        progress_container.pack_propagate(False)

        # 内轨道：在黑框内预留左右/上下内边距，确保绿色条不会压线
        self.progress_track = tk.Frame(progress_container, bg='#ffffff', height=14)
        self.progress_track.pack(fill='x', padx=2, pady=2)
        self.progress_track.pack_propagate(False)

        # 进度条本体（放在轨道内，从左向右增长）
        self.progress_bar = tk.Frame(self.progress_track, bg='#10b981', height=14, relief='flat')
        self.progress_bar.place(x=0, y=0, relwidth=0, height=14)  # 初始宽度为0
        
        # 右侧进度百分比
        self.progress_label = tk.Label(progress_content, text="0.0%", 
                                      font=('Microsoft YaHei UI', 9, 'bold'),
                                      fg='#10b981', bg='#ffffff')
        self.progress_label.pack(side='right')
        
        # 高级功能切换按钮 - 直接在操作面板内
        self.create_advanced_toggle(content_frame)
            
    def create_advanced_toggle(self, parent):
        """在操作面板内创建高级功能切换按钮与内容区域。"""
        # 高级功能切换区域
        toggle_section = tk.Frame(parent, bg='#ffffff')
        toggle_section.pack(fill='x', pady=(4, 0))
        
        # 分隔线
        # separator = tk.Frame(toggle_section, bg='#ffffff', height=1)
        # separator.pack(fill='x', pady=(0, 8))
        
        # 高级功能切换按钮
        self.show_advanced = tk.BooleanVar(value=False)
        self.advanced_toggle = self.create_button(toggle_section, "▼ 高级功能",
                                        command=self.toggle_advanced_features,
                                        variant='ghost', size='sm', padx=15, pady=5)
        self.advanced_toggle.pack()
        
        # 高级功能区域（初始隐藏）
        self.advanced_card = tk.Frame(parent, bg='#ffffff', relief='solid', bd=1)
        
        # 高级功能标题
        adv_title_frame = tk.Frame(self.advanced_card, bg='#ffffff')
        adv_title_frame.pack(fill='x', padx=10, pady=(6, 4))
        
        adv_title = tk.Label(adv_title_frame, text="🔧 高级功能", 
                            font=('Microsoft YaHei UI', 10, 'bold'),
                            fg='#374151', bg='#ffffff')
        adv_title.pack(side='left')
        
        # 高级功能内容
        adv_content = tk.Frame(self.advanced_card, bg='#ffffff')
        adv_content.pack(fill='x', padx=10, pady=(0, 6))
        adv_content.grid_columnconfigure(1, weight=1)
        
        # （已移除）城市文件选择功能
        
        # 定时采集
        tk.Label(adv_content, text="⏰ 定时采集", font=('Microsoft YaHei UI', 9),
                fg='#6b7280', bg='#ffffff').grid(row=1, column=0, sticky='w', pady=(0, 8))
        
        auto_frame = tk.Frame(adv_content, bg='#ffffff')
        auto_frame.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=(0, 8))
        
        self.auto_collect_var = tk.BooleanVar(value=False)
        self.auto_collect_check = tk.Checkbutton(auto_frame, text="启用定时采集", 
                                                variable=self.auto_collect_var,
                                                font=('Microsoft YaHei UI', 8),
                                                fg='#6b7280', bg='#ffffff',
                                                relief='flat')
        self.auto_collect_check.pack(side='left')
        
        self.auto_collect_times_entry = tk.Entry(auto_frame, font=('Microsoft YaHei UI', 8),
                                                bg='white', fg='#374151', relief='solid', bd=1,
                                                highlightthickness=0, width=25)
        self.auto_collect_times_entry.pack(side='left', padx=(8, 0))
        self.auto_collect_times_entry.insert(0, "6:00 18:00 24:00")
        
        # 倒计时显示
        self.remaining_time_label = tk.Label(self.advanced_card, 
                                            text="⏱️ 距离下次采集: 00:00:00", 
                                            font=('Microsoft YaHei UI', 8),
                                            fg='#9ca3af', bg='#ffffff')
        self.remaining_time_label.pack(padx=12, pady=(0, 8))
        
    def toggle_advanced_features(self):
        """切换高级功能显示/隐藏，并更新按钮文案。"""
        if self.show_advanced.get():
            # 隐藏高级功能
            self.advanced_card.pack_forget()
            self.advanced_toggle.config(text="▼ 高级功能")
            self.show_advanced.set(False)
        else:
            # 显示高级功能
            self.advanced_card.pack(fill='x', pady=(8, 0))
            self.advanced_toggle.config(text="▲ 收起高级功能")
            self.show_advanced.set(True)
            
    def create_results_card(self, parent):
        """创建结果显示卡片：日志、POI 数据与导出字段选择。"""
        # 结果区域 - 固定高度，为状态栏留出空间
        results_frame = tk.Frame(parent, bg='#ffffff', relief='flat', bd=1)
        results_frame.pack(fill='x', pady=(0, 4))
        results_frame.configure(height=240)
        results_frame.pack_propagate(False)
        
        # 标题
        title_frame = tk.Frame(results_frame, bg='#ffffff')
        title_frame.pack(fill='x', padx=12, pady=(6, 4))
        
        results_title = tk.Label(title_frame, text="查询结果", 
                                font=('Microsoft YaHei UI', 11, 'bold'),
                                fg='#374151', bg='#ffffff')
        results_title.pack(side='left')
        
        # 内容区域 - 设置固定高度
        content_frame = tk.Frame(results_frame, bg='#ffffff')
        content_frame.pack(fill='x', padx=12, pady=(0, 6))
        content_frame.configure(height=200)  # 再压缩高度，为底部高级功能留空间
        content_frame.pack_propagate(False)  # 禁止子控件改变父容器大小
        content_frame.grid_columnconfigure((0, 1, 2), weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # 日志区域
        log_label = tk.Label(content_frame, text="查询日志", 
                            font=('Microsoft YaHei UI', 9, 'bold'),
                            fg='#6b7280', bg='#ffffff')
        log_label.grid(row=0, column=0, sticky='w', pady=(0, 5), padx=(0, 5))
        
        # 外容器：给查询日志增加边框
        log_container = tk.Frame(content_frame, relief='solid', bd=1, highlightthickness=0)
        log_container.grid(row=1, column=0, sticky='nsew', padx=(0, 5))
        
        # 统一日志背景为淡灰色
        LOG_BG = '#f3f4f6'
        
        self.message_frame = ScrollableFrame(log_container)
        self.message_frame.pack(fill='both', expand=True)
        try:
            self.message_frame.canvas.configure(bg=LOG_BG)
            self.message_frame.scrollable_frame.configure(bg=LOG_BG)
        except Exception:
            pass
        
        # POI数据区域
        data_label = tk.Label(content_frame, text="商家信息数据", 
                             font=('Microsoft YaHei UI', 9, 'bold'),
                             fg='#6b7280', bg='#ffffff')
        data_label.grid(row=0, column=1, sticky='w', pady=(0, 5), padx=(5, 5))
        
        data_container = tk.Frame(content_frame, bg='white', relief='solid', bd=1, highlightthickness=0)
        data_container.grid(row=1, column=1, sticky='nsew', padx=(5, 5))
        
        self.table_frame = ScrollableFrame(data_container)
        self.table_frame.pack(fill='both', expand=True)
        
        # 导出字段区域
        fields_label = tk.Label(content_frame, text="导出字段", 
                               font=('Microsoft YaHei UI', 9, 'bold'),
                               fg='#6b7280', bg='#ffffff')
        fields_label.grid(row=0, column=2, sticky='w', pady=(0, 5), padx=(5, 0))
        
        fields_container = tk.Frame(content_frame, bg='white', relief='solid', bd=1)
        fields_container.grid(row=1, column=2, sticky='nsew', padx=(5, 0))
        
        self.checkbox_canvas = tk.Canvas(fields_container, bg='white', highlightthickness=0)
        self.checkbox_scrollbar = tk.Scrollbar(fields_container, orient="vertical", 
                                              command=self.checkbox_canvas.yview)
        self.checkbox_scrollable_frame = tk.Frame(self.checkbox_canvas, bg='white')
        
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
        
        # 启用鼠标滚轮在导出字段框内滚动
        self._attach_mousewheel(self.checkbox_canvas, self.checkbox_canvas)
        self._attach_mousewheel(self.checkbox_scrollable_frame, self.checkbox_canvas)
        
        # 创建数据框架
        self.frame1 = self.create_frame(self.message_frame.get_frame())
        self.frame2 = self.create_frame(self.table_frame.get_frame())
        self.frame3 = self.create_frame(self.table_frame.get_frame())
        
        # 字段映射
        self.fields = {
            "ID": ("id", tk.BooleanVar(value=False)),
            "名称": ("name", tk.BooleanVar(value=True)),
            "类型": ("type", tk.BooleanVar(value=False)),
            "类型编码": ("typecode", tk.BooleanVar(value=False)),
            "地址": ("address", tk.BooleanVar(value=True)),
            "经纬度": ("location", tk.BooleanVar(value=False)),
            "电话": ("tel", tk.BooleanVar(value=True)),
            "网址": ("website", tk.BooleanVar(value=False)),
            "邮箱": ("email", tk.BooleanVar(value=False)),
            "省份": ("pname", tk.BooleanVar(value=False)),
            "城市": ("cityname", tk.BooleanVar(value=False)),
            "区域": ("adname", tk.BooleanVar(value=False)),
            "入口经纬度": ("entr_location", tk.BooleanVar(value=False)),
            "出口经纬度": ("exit_location", tk.BooleanVar(value=False)),
        }
        
        for field in self.fields:
            cb = tk.Checkbutton(self.checkbox_scrollable_frame, text=field, 
                               variable=self.fields[field][1],
                               font=('Microsoft YaHei UI', 8),
                               fg='#374151', bg='white', relief='flat')
            cb.pack(anchor="w", padx=8, pady=2)
            # 悬停在文字/复选框上时也能滚动
            self._attach_mousewheel(cb, self.checkbox_canvas)
            
    def update_progress(self, total_count):
        """更新进度显示（以配置为准统计已查询城市）。"""
        try:
            provinces = self.config_manager.get_provinces()
            queried_count = 0
            for province in provinces.values():
                for city in province.get('cities', {}).values():
                    if city.get('queried'):
                        queried_count += 1

            if total_count <= 0:
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.place(x=0, y=0, relwidth=0, height=14)
                if hasattr(self, 'progress_label'):
                    self.progress_label.config(text="0.0%", fg='#6b7280')
                if hasattr(self, 'queried_cities_label'):
                    self.queried_cities_label.config(text="已查询: 0")
                if hasattr(self, 'total_cities_label'):
                    self.total_cities_label.config(text=f"总计: {total_count}")
                return

            progress_percent = (queried_count / total_count) * 100

            if hasattr(self, 'progress_bar'):
                self.progress_bar.place(x=0, y=0, relwidth=progress_percent/100, height=14)
            if hasattr(self, 'progress_label'):
                self.progress_label.config(text=f"{progress_percent:.1f}%", fg='#10b981')
            if hasattr(self, 'queried_cities_label'):
                self.queried_cities_label.config(text=f"已查询: {queried_count}")
            if hasattr(self, 'total_cities_label'):
                self.total_cities_label.config(text=f"总计: {total_count}")
        except Exception as e:
            print(f"更新进度失败: {e}")

    def mark_city_completed(self, city_name: str):
        """将城市标记为本轮运行已完成。"""
        if not hasattr(self, 'completed_run_cities'):
            self.completed_run_cities = set()
        self.completed_run_cities.add(city_name)

    def update_progress_run(self):
        """按当前运行的城市集合更新进度条和计数。"""
        try:
            total = len(getattr(self, 'current_run_cities', set()))
            done = len(getattr(self, 'completed_run_cities', set()))
            percent = (done / total) if total > 0 else 0

            def _apply():
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.place(x=0, y=0, relwidth=percent, height=14)
                if hasattr(self, 'progress_label'):
                    self.progress_label.config(text=f"{percent*100:.1f}%")
                if hasattr(self, 'queried_cities_label'):
                    self.queried_cities_label.config(text=f"已查询: {done}")
                if hasattr(self, 'total_cities_label'):
                    self.total_cities_label.config(text=f"总计: {total}")

            # 确保在主线程更新 UI
            if hasattr(self, 'root'):
                self.root.after(0, _apply)
            else:
                _apply()
        except Exception:
            pass

    def finalize_progress_run(self):
        """将本轮进度强制更新为 100%。"""
        try:
            if hasattr(self, 'current_run_cities'):
                self.completed_run_cities = set(self.current_run_cities)
            self.update_progress_run()
        except Exception:
            pass
        
    def setup_styles(self):
        """设置统一的界面样式、颜色与字体，并配置基础 ttk 主题。"""
        # 颜色与字体基调（尽量与现有配色保持一致并细化 hover）
        self.colors = {
            'bg': '#ffffff',
            'text': '#374151',
            'muted': '#6b7280',
            'border': '#e5e7eb',
            'primary': '#3b82f6',   # 蓝色
            'primary_hover': '#2563eb',
            'success': '#10b981',   # 绿色
            'success_hover': '#059669',
            'danger': '#ef4444',    # 红色
            'danger_hover': '#dc2626',
            'warning': '#f59e0b',   # 黄色
            'warning_hover': '#d97706',
            'ghost_hover': '#f3f4f6'
        }

        self.fonts = {
            'title': ('Microsoft YaHei UI', 18, 'bold'),
            'h1': ('Microsoft YaHei UI', 11, 'bold'),
            'body': ('Microsoft YaHei UI', 9),
            'btn': ('Microsoft YaHei UI', 10, 'bold'),
            'btn_sm': ('Microsoft YaHei UI', 9)
        }

        # 通用 Entry 边框与背景（保持轻量）
        style = ttk.Style()
        try:
            style.theme_use(style.theme_use())
        except Exception:
            pass

        # 统一 Label 颜色
        self.root.option_add('*Label.background', self.colors['bg'])
        self.root.option_add('*Label.foreground', self.colors['text'])

    def create_button(self, parent, text, command=None, variant='primary', size='md', padx=15, pady=6):
        """创建带有 hover 效果的按钮。
        variant: primary | success | danger | ghost
        size: md | sm
        """
        palette = self.colors
        if variant == 'primary':
            bg, fg, hover = palette['primary'], '#ffffff', palette['primary_hover']
        elif variant == 'success':
            bg, fg, hover = palette['success'], '#ffffff', palette['success_hover']
        elif variant == 'danger':
            bg, fg, hover = palette['danger'], '#ffffff', palette['danger_hover']
        elif variant == 'warning':
            bg, fg, hover = palette['warning'], '#ffffff', palette['warning_hover']
        elif variant == 'secondary':
            bg, fg, hover = palette.get('ghost_hover', '#f3f4f6'), palette['text'], palette.get('border', '#e5e7eb')
        else:  # ghost
            bg, fg, hover = palette['bg'], palette['text'], palette['ghost_hover']

        font = self.fonts['btn'] if size == 'md' else self.fonts['btn_sm']

        # 边框风格：实心按钮无边框，ghost 有细边
        relief = 'flat'
        bd = 1 if variant in ('ghost', 'secondary') else 0

        btn = tk.Button(parent, text=text, command=command,
                        font=font, bg=bg, fg=fg, activeforeground=fg,
                        activebackground=hover, relief=relief, bd=bd,
                        highlightthickness=0, cursor='hand2', padx=padx, pady=pady,
                        disabledforeground='#ffffff')

        # hover 效果
        def _enter(_):
            if btn['state'] != 'disabled':
                btn.configure(bg=hover)
        def _leave(_):
            if btn['state'] != 'disabled':
                btn.configure(bg=bg)
        btn.bind('<Enter>', _enter)
        btn.bind('<Leave>', _leave)
        
        # 保存原始颜色，用于状态恢复
        btn._original_bg = bg
        btn._original_fg = fg
        
        return btn
    
    def create_frame(self, container):
        """在给定容器中创建一个可扩展的列 frame。"""
        frame = tk.Frame(container)
        frame.pack(side="left", fill="both", expand=True)
        return frame
        
    def _attach_mousewheel(self, widget, target_canvas):
        """将鼠标滚轮事件绑定到指定 canvas，实现悬停滚动。"""
        def _on_enter(e):
            widget.bind_all("<MouseWheel>", lambda ev: target_canvas.yview_scroll(int(-1*(ev.delta/120)), "units"))
        def _on_leave(e):
            widget.unbind_all("<MouseWheel>")
        widget.bind("<Enter>", _on_enter)
        widget.bind("<Leave>", _on_leave)

    def clear_output(self):
        """清空右侧输出区域和查询日志中的所有条目。"""
        # 清空 POI 数据区域
        for frame in getattr(self, 'frames', []):
            for widget in frame.winfo_children():
                widget.destroy()
        # 清空 查询日志 区域
        try:
            log_inner = self.message_frame.get_frame()
            for widget in log_inner.winfo_children():
                widget.destroy()
            # 重置滚动位置
            self.message_frame.canvas.yview_moveto(0)
        except Exception:
            pass

    def clear_placeholder(self, event):
        """当输入框获得焦点时，清除占位提示文字并恢复正常颜色。"""
        widget = event.widget
        if widget == self.keyword_entry and self.keyword_entry.get() == "查询完成后，先点击恢复状态，再进行新查询":
            self.keyword_entry.delete(0, tk.END)
            self.keyword_entry.config(foreground='black')
        elif widget == self.api_key_entry and self.api_key_entry.get() == "可输入多个key，每个key用空格隔开":
            self.api_key_entry.delete(0, tk.END)
            self.api_key_entry.config(foreground='black')

    def save_settings(self):
        """保存当前设置到配置文件（用户设置与字段设置）。"""
        try:
            # 更新用户设置
            user_settings = {
                'api_keys': self.api_key_entry.get(),
                'keywords': self.keyword_entry.get(),
                'all_provinces': self.select_all_var.get(),
                'realtime_export': self.realtime_export_var.get(),
                'realtime_export_path': self.realtime_export_path_entry.get(),
                'auto_collect': getattr(self, 'auto_collect_var', tk.BooleanVar()).get(),
                'auto_collect_times': self.auto_collect_times_entry.get() if hasattr(self, 'auto_collect_times_entry') and self.auto_collect_times_entry else '',
            }
            self.config_manager.update_user_settings(user_settings)
            
            # 更新字段设置
            field_settings = {field: var.get() for field, (english, var) in self.fields.items()}
            self.config_manager.update_field_settings(field_settings)
            
            # 保存到文件
            if self.config_manager.save_config():
                show_centered_message("提示", "成功保存参数", "info", self.root)
            else:
                show_centered_message("错误", "保存配置失败", "error", self.root)
                
        except Exception as e:
            show_centered_message("错误", f"保存设置失败：{str(e)}", "error", self.root)
        
    def load_settings(self):
        """从配置文件加载设置并恢复界面状态。"""
        try:
            # 获取用户设置
            user_settings = self.config_manager.get_user_settings()
            
            # 设置API Keys
            self.api_key_entry.delete(0, tk.END)
            self.api_key_entry.insert(0, user_settings.get('api_keys', ''))
            
            # 设置关键词
            self.keyword_entry.delete(0, tk.END)
            self.keyword_entry.insert(0, user_settings.get('keywords', ''))
            
            # 设置"查询所有省份"二态复选框状态
            all_provinces_checked = user_settings.get('all_provinces', False)
            self.select_all_var.set(bool(all_provinces_checked))
            
            # 设置实时导出
            self.realtime_export_var.set(user_settings.get('realtime_export', True))
            self.realtime_export_path_entry.delete(0, tk.END)
            self.realtime_export_path_entry.insert(0, user_settings.get('realtime_export_path', ''))
            
            # 设置定时采集
            if hasattr(self, 'auto_collect_var'):
                self.auto_collect_var.set(user_settings.get('auto_collect', False))
            if hasattr(self, 'auto_collect_times_entry'):
                self.auto_collect_times_entry.delete(0, tk.END)
                self.auto_collect_times_entry.insert(0, user_settings.get('auto_collect_times', ''))
            
            # 获取字段设置
            field_settings = self.config_manager.get_field_settings()
            for field, (english, var) in self.fields.items():
                var.set(field_settings.get(field, var.get()))
                
        except Exception as e:
            print(f"加载设置失败：{e}")
    
    def refresh_config(self):
        """刷新配置：重新从配置文件加载设置并弹提示。"""
        try:
            # 重新加载配置文件
            self.config_manager.load_config()
            # 重新应用设置到界面
            self.load_settings()
            # 显示成功提示
            show_centered_message("提示", "配置已刷新", "info", self.root)
        except Exception as e:
            show_centered_message("错误", f"刷新配置失败：{str(e)}", "error", self.root)
            return

    def add_placeholder(self, event):
        """当输入框失去焦点且为空时，恢复占位提示文字与灰色。"""
        widget = event.widget
        if widget == self.keyword_entry and self.keyword_entry.get() == "":
            self.keyword_entry.config(foreground='grey')
            self.keyword_entry.insert(0, "查询完成后，先点击恢复状态，再进行新查询")
        elif widget == self.api_key_entry and self.api_key_entry.get() == "":
            self.api_key_entry.config(foreground='grey')
            self.api_key_entry.insert(0, "可输入多个key，每个key用空格隔开")   
            
    def update_clock(self):
        """每秒更新倒计时标签，并在到时触发定时采集。"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        # 检查是否存在定时采集变量（避免初始化先后问题）
        if hasattr(self, 'auto_collect_var') and self.auto_collect_var.get():
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
                if hasattr(self, 'remaining_time_label'):
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


    def on_all_provinces_changed(self):
        """查询所有省份：二态逻辑，作用于左侧省份列表全部条目。
        - checked: 将所有省份设为选中（同时联动选中其城市）
        - unchecked: 将所有省份设为未选中（同时联动取消其城市）
        """
        state = 'checked' if self.select_all_var.get() else 'unchecked'

        # 保障结构存在
        if not hasattr(self, 'province_checkbuttons'):
            self.province_checkbuttons = {}

        # 遍历省份条目，设置三态并联动城市选择
        for province_name, province_cb in list(self.province_checkbuttons.items()):
            try:
                province_cb.set_state(state)
            except Exception:
                pass
            # 调用原有联动逻辑，批量勾选/取消该省所有城市
            self.on_province_check_changed(province_name, state)

        # 统计信息与头部二态无需特别处理，on_province_check_changed 会更新城市集合
        # 但为防止状态竞态，这里再统一刷新一次
        self.update_province_check_states()
        self.update_all_provinces_check_state()




    def on_all_cities_changed(self):
        """选择所有市：二态逻辑，仅作用于当前右侧城市列表中"可见"的城市。
        - checked: 勾选当前列表中所有城市
        - unchecked: 取消勾选当前列表中所有城市
        """
        check_all = bool(self.select_all_cities_var.get())

        if not hasattr(self, 'city_checkbuttons'):
            self.city_checkbuttons = {}
        if not hasattr(self, 'city_vars'):
            self.city_vars = {}

        # 若当前城市列表框未显示任何城市，则该操作无效，复选框恢复为未选中
        if not self.city_checkbuttons:
            self.select_all_cities_var.set(False)
            return

        for city_name in list(self.city_checkbuttons.keys()):
            if city_name not in self.city_vars:
                self.city_vars[city_name] = tk.BooleanVar()
            try:
                self.city_vars[city_name].set(check_all)
            except tk.TclError:
                continue

        # 同步下游：更新选中集合、三态与统计
        self.on_city_checks_changed()


    def start_search(self):
        """校验输入，确定目标地区，并启动检索线程。"""
        # 若已有查询在进行，直接忽略以避免重复日志/并发线程
        if getattr(self, 'is_searching', False):
            show_centered_message("提示", "已有查询在进行中，请先停止或等待完成", "info", self.root)
            return
        # 获取 API Keys 列表（空格分隔，多 key 轮换）
        self.api_keys = [key for key in self.api_key_entry.get().strip().split() if key != '可输入多个key，每个key用空格隔开' and key]
        self.current_key_index = 0  # 当前使用的 key 下标

        keyword = self.keyword_entry.get().strip()  # 检索关键词

        if not self.api_keys or not self.api_keys[0] or not keyword or keyword == "查询完成后，先点击恢复状态，再进行新查询":
            show_centered_message("警告", "API Key 和 关键词 都不能为空", "warning", self.root)
            return

        # 初始化第一个 API Key（不输出日志，避免重复）
        if self.api_keys:
            self.api_key = self.api_keys[0]
            self.current_key_index = 1
            print(f"当前正在使用第 1 个 key: {self.api_key}")

        # 仅使用 UI 中的省市选择，不再从文件导入
        if self.select_all_var.get():
            # 全选：从配置聚合所有城市名称
            regions = []
            provinces = self.config_manager.get_provinces()
            for p in provinces.values():
                for city_name, city_data in p.get('cities', {}).items():
                    if city_name:
                        regions.append(city_name)
        else:
            regions = list(self.selected_cities)
            print(f"调试：选中的城市列表：{regions}")
            if not regions:
                show_centered_message("警告", "请先在右侧城市列表中选择至少一个城市", "warning", self.root)
                return

        # 检查是否选择了过多城市，建议分批处理
        if len(regions) > 50 and not getattr(self, 'batch_mode', False):
            # 对于askyesnocancel，我们需要特殊处理
            root = tk.Tk()
            root.withdraw()
            result = messagebox.askyesnocancel(
                "批量查询警告", 
                f"您选择了 {len(regions)} 个城市，建议分批处理以避免程序崩溃。\n\n" +
                "• 点击'是'：启用批量处理模式（推荐）\n" +
                "• 点击'否'：一次性查询所有城市（可能崩溃）\n" +
                "• 点击'取消'：取消本次查询",
                parent=root
            )
            # 居中显示
            root.update_idletasks()
            x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
            y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
            root.geometry(f"+{x}+{y}")
            root.destroy()
            
            if result is None:  # 取消
                return
            elif result:  # 是 - 启用批量处理
                self.batch_mode = True
                self.batch_size = min(10, max(5, len(regions) // 10))  # 动态计算批次大小
                show_centered_message("批量处理", f"将以每批 {self.batch_size} 个城市的方式处理，预计需要 {len(regions) // self.batch_size + 1} 个批次。", "info", self.root)
            else:  # 否 - 一次性查询
                self.batch_mode = False
        else:
            self.batch_mode = False

        # 记录本次运行的目标与完成进度
        self.current_run_cities = set(regions)
        self.completed_run_cities = set()

        # 初始化进度显示（本次运行总数）
        try:
            if hasattr(self, 'total_cities_label'):
                self.total_cities_label.config(text=f"总计: {len(self.current_run_cities)}")
            if hasattr(self, 'queried_cities_label'):
                self.queried_cities_label.config(text=f"已查询: 0")
            if hasattr(self, 'progress_bar'):
                self.progress_bar.place(x=2, y=2, relwidth=0, height=21)
            if hasattr(self, 'progress_label'):
                self.progress_label.config(text="0.0%")
        except Exception:
            pass

        self.is_searching = True  # 置为检索中
        self.is_paused = False
        # 启用暂停按钮
        if hasattr(self, 'pause_button'):
            self.pause_button.configure(state='normal', text='暂停')
        
        if self.batch_mode:
            # 批量处理模式
            threading.Thread(target=self.search_pois_batch, args=(keyword, regions), daemon=True).start()
        else:
            # 传统模式
            threading.Thread(target=self.search_pois, args=(keyword, regions), daemon=True).start()  # 后台线程执行，避免卡住 UI

        
    
    def use_next_api_key(self):
        """切换到下一个 API Key；全部用尽则停止。"""
        if self.current_key_index < len(self.api_keys):
            self.api_key = self.api_keys[self.current_key_index]
            self.current_key_index += 1
            print(f"切换到第 {self.current_key_index} 个 key: {self.api_key}")
        else:
            print("所有 key 都用完，程序结束。")
            self.insert_text(self.frame1, "所有 key 都用完，程序结束。\n")
            self.is_searching = False


    def insert_text(self, frame, text):
        """向指定面板追加一条文本记录（左对齐，自动换行）。确保在主线程更新UI。"""
        if not hasattr(self, 'frames'):
            self.frames = []

        # 去除尾部换行，避免额外间距；空行直接忽略
        text = (text or '').rstrip('\n')
        if text.strip() == '':
            return

        # 在主线程执行实际的UI更新，避免后台线程直接操作Tk
        def _do_update():
            # 检查窗口是否还存在
            try:
                if not self.is_searching or not hasattr(self, 'root') or not self.root.winfo_exists():
                    return
            except Exception:
                return

            # 与日志区域统一的淡灰背景（放在主线程读取）
            try:
                bg_local = self.message_frame.scrollable_frame.cget('bg')
            except Exception:
                bg_local = None
            if not bg_local:
                bg_local = '#f3f4f6'

            try:
                label = tk.Label(frame, text=text, anchor='w', bg=bg_local)
                label.pack(fill='x', padx=0, pady=0, ipady=0)
            except Exception:
                return

            # 自动滚动到最底部（日志与POI区域）
            try:
                self.root.update_idletasks()
            except Exception:
                pass
            try:
                if hasattr(self, 'message_frame') and hasattr(self.message_frame, 'canvas'):
                    self.message_frame.canvas.yview_moveto(1)
            except Exception:
                pass
            try:
                if hasattr(self, 'table_frame') and hasattr(self.table_frame, 'canvas'):
                    self.table_frame.canvas.yview_moveto(1)
            except Exception:
                pass

        try:
            # 将UI更新安排到主线程
            self.root.after(0, _do_update)
        except Exception:
            # 如果无法调度，直接忽略该条
            pass

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
            # 暂停控制：若暂停，保持空转等待恢复
            while self.is_paused and self.is_searching:
                time.sleep(0.2)
            region = regions.pop(0)
            # 从配置中查找城市代码（用于查询和状态更新）
            region_code_list = []
            provinces = self.config_manager.get_provinces()
            for province_name, province_data in provinces.items():
                cities = province_data.get('cities', {})
                for city_name, city_data in cities.items():
                    if city_name == region:
                        region_code_list = [city_data.get('adcode')]
                        break
                if region_code_list:
                    break
            print(f"正在查询 {region}...代码：{region_code_list}")
            if not region_code_list:
                self.insert_text(self.frame1, f"找不到城市代码：{region}\n")
                continue

            region_code = region_code_list[0]
            page_num = 1
            pois = []

            # 合并"开始查询"和首次状态为一行输出
            start_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            status_logged = False  # 仅记录一次状态行
            status_printed = False  # 控制台仅打印一次状态码
            while self.is_searching:
                # 暂停控制
                while self.is_paused and self.is_searching:
                    time.sleep(0.2)
                # 构建请求参数（每页 20 条）
                params = {
                    "key": self.api_key,
                    "keywords": keyword,
                    "city": region_code,  # 使用 adcode 值进行查询
                    "offset": 20,
                    "output": "json",
                    "page": page_num,
                }
                response = session.get(url, params=params)
                data = response.json()

                status_code = response.status_code
                status_value = data.get('status')
                status_info = data.get('info')
                if not status_printed:
                    print(f"状态码: {status_code}, 返回状态值: {status_value}, 返回状态说明: {status_info}")
                    status_printed = True
                if not status_logged:
                    self.insert_text(self.frame1, f"{start_time} | {region} — 状态码: {status_code}, 状态: {status_info}\n")
                    status_logged = True

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
            
            # 更新城市查询状态到配置文件
            # 从配置中查找城市代码和省份名
            city_code = '000000'
            province_name = ''
            provinces = self.config_manager.get_provinces()
            for p_name, p_data in provinces.items():
                cities = p_data.get('cities', {})
                for city_name, city_data in cities.items():
                    if city_name == region:
                        city_code = city_data.get('adcode', '000000')
                        province_name = p_name
                        break
                if province_name:
                    break
            
            self.config_manager.update_city_query_status(
                province_name, city_code, region, True
            )
            
            # 本次运行进度更新
            self.mark_city_completed(region)
            self.update_progress_run()

        self.insert_text(self.frame1, "查询结束.\n\n")
        self.insert_text(self.frames[0], "\n")
        self.insert_text(self.frames[1], "\n")
        self.table_frame.canvas.yview_moveto(1)
        self.pois_data = all_pois
        # 结束时将进度置为100%
        self.finalize_progress_run()
        # 标记完成，允许再次发起查询
        self.is_searching = False
        self.is_paused = False
        if hasattr(self, 'pause_button'):
            try:
                self.pause_button.configure(state='disabled', text='暂停')
            except Exception:
                pass
        
    def search_pois_batch(self, keyword, regions):
        """批量处理城市查询，防止程序崩溃。"""
        self.clear_frames()
        
        selected_fields = [(chinese, english) for chinese, (english, var) in self.fields.items() if var.get()]
        
        self.frames = []
        for idx in range(len(selected_fields)):
            frame = self.create_frame(self.table_frame.get_frame())
            self.frames.append(frame)
        
        total_regions = len(regions)
        batch_size = getattr(self, 'batch_size', 5)  # 默认每批 5 个城市
        all_pois = []
        batch_count = 0
        
        self.insert_text(self.frame1, f"开始批量处理 {total_regions} 个城市，每批 {batch_size} 个...\n")
        
        while regions and self.is_searching:
            # 取一批城市
            current_batch = regions[:batch_size]
            regions = regions[batch_size:]
            batch_count += 1
            
            self.insert_text(self.frame1, f"\n─── 正在处理第 {batch_count} 批（{len(current_batch)} 个城市） ───\n")
            
            # 处理当前批次
            batch_pois = self._process_batch(keyword, current_batch, selected_fields)
            all_pois.extend(batch_pois)
            
            # 更新进度
            processed_count = (batch_count * batch_size) - len(regions)
            progress_percent = (processed_count / total_regions) * 100
            self.insert_text(self.frame1, f"已处理 {processed_count}/{total_regions} 个城市 ({progress_percent:.1f}%)\n")
            
            # 批次间隔，防止API限流
            if regions and self.is_searching:  # 还有更多批次
                self.insert_text(self.frame1, "批次处理间隔 5 秒，防止API限流...\n")
                time.sleep(5)  # 批次间隔
        
        if self.is_searching:
            self.insert_text(self.frame1, f"\n✅ 批量处理完成！共处理 {batch_count} 个批次，获取 {len(all_pois)} 条POI数据\n")
        else:
            self.insert_text(self.frame1, "\n⚠️ 批量处理已停止\n")
            
        self.table_frame.canvas.yview_moveto(1)
        self.pois_data = all_pois
        # 结束时将进度置为100%
        self.finalize_progress_run()
        # 标记完成，允许再次发起查询
        self.is_searching = False
        self.is_paused = False
        if hasattr(self, 'pause_button'):
            try:
                self.pause_button.configure(state='disabled', text='暂停')
            except Exception:
                pass
        
    def _process_batch(self, keyword, city_batch, selected_fields):
        """处理一个批次的城市查询。"""
        batch_pois = []
        url = "https://restapi.amap.com/v3/place/text"
        session = requests.Session()
        
        # 设置超时和重试
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        
        for region in city_batch:
            # 暂停控制
            while self.is_paused and self.is_searching:
                time.sleep(0.2)
            if not self.is_searching:
                break
                
            try:
                # 从配置中查找城市代码
                region_code_list = []
                provinces = self.config_manager.get_provinces()
                for province_name, province_data in provinces.items():
                    cities = province_data.get('cities', {})
                    for city_name, city_data in cities.items():
                        if city_name == region:
                            region_code_list = [city_data.get('adcode')]
                            break
                    if region_code_list:
                        break
                
                if not region_code_list:
                    self.insert_text(self.frame1, f"⚠️ 找不到城市代码：{region}\n")
                    continue
                
                region_code = region_code_list[0]
                self.insert_text(self.frame1, f"🔍 查询 {region} ({region_code})...")
                
                # 单个城市查询
                city_pois = self._query_single_city(session, url, keyword, region, region_code, selected_fields)
                batch_pois.extend(city_pois)
                
                # 更新查询状态
                self._update_city_query_status(region, region_code)
                self.mark_city_completed(region)
                self.update_progress_run()
                
                self.insert_text(self.frame1, f" ✅ 完成，获取 {len(city_pois)} 条数据\n")
                
                # 城市间隔，防止过快请求
                time.sleep(0.5)
                
            except Exception as e:
                self.insert_text(self.frame1, f" ❌ 失败：{str(e)}\n")
                continue
        
        return batch_pois
        
    def _query_single_city(self, session, url, keyword, region, region_code, selected_fields):
        """查询单个城市的POI数据（含多页翻页与实时导出）。"""
        city_pois = []
        page_num = 1
        max_pages = 10  # 限制每个城市最多查询页数，防止无限循环
        
        while page_num <= max_pages and self.is_searching:
            # 暂停控制
            while self.is_paused and self.is_searching:
                time.sleep(0.2)
            try:
                params = {
                    "key": self.api_key,
                    "keywords": keyword,
                    "city": region_code,  # 使用 adcode 值进行查询
                    "offset": 20,
                    "output": "json",
                    "page": page_num,
                }
                
                response = session.get(url, params=params, timeout=10)
                data = response.json()
                
                if response.status_code != 200:
                    break
                    
                if data.get("status") == "0":
                    # API错误，尝试切换key
                    self.use_next_api_key()
                    if not self.is_searching:
                        break
                    continue
                
                if data.get("status") == "1" and int(data.get("count", 0)) > 0:
                    new_pois = data.get("pois", [])
                    city_pois.extend(new_pois)
                    
                    # 显示POI数据
                    for poi in new_pois:
                        display_texts = [f"{chinese}: {poi.get(english, '无数据')}" for chinese, english in selected_fields if english in poi]
                        for idx, text in enumerate(display_texts):
                            if idx < len(self.frames):
                                self.insert_text(self.frames[idx], text)
                    
                    # 实时导出
                    if self.realtime_export_var.get():
                        self.export_to_csv_realtime(new_pois)
                    
                    # 小于一页，说明已到末页
                    if len(new_pois) < 20:
                        break
                    page_num += 1
                    
                else:
                    # 无数据或其他情况
                    break
                    
            except requests.RequestException as e:
                # 网络错误，跳过该页
                break
            except Exception as e:
                # 其他错误，跳过该页
                break
        
        return city_pois
        
    def _update_city_query_status(self, region, region_code):
        """更新城市查询状态到配置，供后续进度统计使用。"""
        try:
            # 从配置中查找省份名
            province_name = ''
            provinces = self.config_manager.get_provinces()
            for p_name, p_data in provinces.items():
                cities = p_data.get('cities', {})
                for city_name, city_data in cities.items():
                    if city_name == region:
                        province_name = p_name
                        break
                if province_name:
                    break
            
            self.config_manager.update_city_query_status(province_name, region_code, region, True)
            
            # 不再维护 queried_cities 内存副本，统一以配置为准
            
        except Exception as e:
            print(f"更新查询状态失败: {e}")
        
    def clear_frames(self):
        """销毁结果面板中的所有 frame，便于新一轮查询重建。"""
        if hasattr(self, 'frames'):
            for frame in self.frames:
                frame.destroy()
            self.frames = []


    def fetch_province_city_data(self):
        """通过高德行政区划接口加载省/市列表，并填充多选框。
        
        使用说明：
        - 需已填写有效 Web 服务 Key（GENERAL.api_keys 的第一个）。
        - 先拉取省级，再按省遍历拉取市级，构建 self.province_to_cities 与 self.city_name_to_adcode。
        """
        # 防抖：若正在加载，则提示并返回
        if getattr(self, 'is_loading_province_city', False):
            show_centered_message("提示", "正在从远程加载省/市数据，请稍候…", "info", self.root)
            return

        api_keys_text = self.api_key_entry.get().strip()
        if not api_keys_text:
            show_centered_message("警告", "请先填写 API Key 再加载省/市。", "warning", self.root)
            return
        api_key = api_keys_text.split()[0]

        # 清空 UI（在主线程执行）
        self.province_to_cities = {}
        self.city_name_to_adcode = {}
        self.selected_provinces.clear()
        self.selected_cities.clear()
        self.province_vars.clear()
        self.city_vars.clear()
        for child in self.province_cb_frame.winfo_children():
            child.destroy()
        for child in self.city_cb_frame.winfo_children():
            child.destroy()
        self.area_hint_label.config(text="正在加载省/市，请稍候...")

        # 设置加载中状态与按钮禁用
        self.is_loading_province_city = True
        try:
            if hasattr(self, 'load_area_button') and self.load_area_button:
                self.load_area_button.config(state='disabled', text='加载中…')
        except Exception:
            pass

        def _load():
            try:
                # 1) 拉取省级
                url = "https://restapi.amap.com/v3/config/district"
                
                # 支持多个API Key
                api_keys = [key.strip() for key in api_key.split() if key.strip()]
                current_key_index = 0
                
                def get_next_api_key():
                    nonlocal current_key_index
                    key = api_keys[current_key_index]
                    current_key_index = (current_key_index + 1) % len(api_keys)
                    return key
                
                params = {
                    "key": get_next_api_key(),
                    "keywords": "中国",
                    "subdistrict": 1,
                    "extensions": "base",
                }
                resp = requests.get(url, params=params)
                data = resp.json()
                if data.get("status") != "1":
                    raise RuntimeError(f"加载省份失败: {data.get('info')}")
                provinces = data.get("districts", [])[0].get("districts", [])
                # 在后台线程中构建数据，稍后切回主线程更新 UI
                province_to_cities: dict[str, list[tuple[str, str]]] = {}
                city_name_to_adcode: dict[str, str] = {}
                
                total_provinces = len(provinces)
                current_province = 0
                
                for p in provinces:
                    pname = p.get("name")
                    pcode = p.get("adcode")
                    print(f"正在加载 {pname} ({pcode}) 的城市数据...")
                    
                    # 添加延迟避免API限制
                    import time
                    # 可以从配置中读取延迟时间，默认为0.5秒
                    delay = 0.5
                    time.sleep(delay)  # 每次请求间隔
                    
                    params = {
                        "key": get_next_api_key(),
                        "keywords": pcode,
                        "subdistrict": 1,
                        "extensions": "base",
                    }
                    
                    # 添加重试机制
                    max_retries = 3
                    for retry in range(max_retries):
                        try:
                            r2 = requests.get(url, params=params, timeout=10)
                            d2 = r2.json()
                            if d2.get("status") == "1":
                                break
                            elif d2.get("info") == "CUQPS_HAS_EXCEEDED_THE_LIMIT":
                                if retry < max_retries - 1:
                                    print(f"API限制，等待重试... ({retry + 1}/{max_retries})")
                                    time.sleep(2 * (retry + 1))  # 递增等待时间
                                    continue
                            else:
                                break
                        except Exception as e:
                            if retry < max_retries - 1:
                                print(f"请求失败，重试中... ({retry + 1}/{max_retries})")
                                time.sleep(1)
                                continue
                            else:
                                print(f"请求失败: {e}")
                                break
                    
                    if d2.get("status") != "1":
                        print(f"警告：加载 {pname} 的城市数据失败，状态：{d2.get('status')}，信息：{d2.get('info')}")
                        continue
                    cities = d2.get("districts", [])[0].get("districts", [])
                    city_pairs = []
                    for c in cities:
                        cname = c.get("name")
                        ccode = c.get("adcode")
                        if not cname or not ccode:
                            continue
                        city_pairs.append((cname, ccode))
                        city_name_to_adcode[cname] = ccode
                    province_to_cities[pname] = city_pairs
                    current_province += 1
                    print(f"成功加载 {pname} 的 {len(city_pairs)} 个城市 ({current_province}/{total_provinces})")

                # 手动添加可能缺失的直辖市数据
                self._add_missing_municipalities(province_to_cities, city_name_to_adcode)

            
                def _populate_on_main_thread():
                    # 先写入配置文件
                    try:
                        self.config_manager.update_provinces_data(province_to_cities, city_name_to_adcode)
                        self.config_manager.save_config()
                    except Exception as e:
                        print(f"保存省市数据到配置失败: {e}")

                    # 再从配置读取并填充界面（确保以配置为唯一数据源）
                    try:
                        # 重建省份 UI，等待用户点击省份再展示城市
                        self.build_provinces_ui()
                        provinces = self.config_manager.get_provinces()
                        count = sum(len(p.get('cities', {})) for p in provinces.values())
                        self.area_hint_label.config(text=f"已从配置加载{count}个城市数据，请先选择左侧省份。")
                    except Exception as e:
                        show_centered_message("错误", f"从配置加载省/市失败：{e}", "error", self.root)

                    # 复位加载状态与按钮
                    self.is_loading_province_city = False
                    try:
                        if hasattr(self, 'load_area_button') and self.load_area_button:
                            self.load_area_button.config(state='normal', text='加载省市数据')
                    except Exception:
                        pass

                self.root.after(0, _populate_on_main_thread)
            except Exception as e:
                def _on_error():
                    show_centered_message("错误", f"加载省/市失败：{e}", "error", self.root)
                    self.area_hint_label.config(text="加载失败，请检查网络或 Key。")
                    # 复位加载状态与按钮
                    self.is_loading_province_city = False
                    try:
                        if hasattr(self, 'load_area_button') and self.load_area_button:
                            self.load_area_button.config(state='normal', text='加载省市数据')
                    except Exception:
                        pass
                self.root.after(0, _on_error)

        threading.Thread(target=_load, daemon=True).start()

    def _add_missing_municipalities(self, province_to_cities, city_name_to_adcode):
        """手动添加可能缺失的直辖市与台湾省数据，规范化市级展示。

        目的：
        - 高德行政区划接口对直辖市返回区县列表，UI 期望“城市”层级；
        - 某些环境下台湾省可能无法返回，需要手动补充；
        - 将直辖市在本工具内统一作为一个“城市”选项，便于检索。
        """
        # 规范化直辖市：将其城市列表设置为仅包含自身（市级 adcode）
        municipalities = {
            "北京市": "110000",
            "天津市": "120000",
            "上海市": "310000",
            "重庆市": "500000",
        }
        for muni_name, muni_code in municipalities.items():
            # 如果未包含该直辖市，或其城市列表为区县等非市级，统一覆盖为自身
            need_override = False
            if muni_name not in province_to_cities:
                need_override = True
            else:
                existing_city_pairs = province_to_cities.get(muni_name) or []
                # 若已存在但不是仅包含自身，则改为仅自身
                if not (len(existing_city_pairs) == 1 and existing_city_pairs[0][0] == muni_name):
                    need_override = True
            if need_override:
                province_to_cities[muni_name] = [(muni_name, muni_code)]
            # 同步城市名称到编码映射
            city_name_to_adcode[muni_name] = muni_code

        # 添加台湾省数据（因为API可能无法获取）
        taiwan_data = {
            "台湾省": {
                "adcode": "710000",
                "cities": [
                    ("台北市", "710000"),
                    ("新北市", "710100"),
                    ("桃园市", "710200"),
                    ("台中市", "710300"),
                    ("台南市", "710400"),
                    ("高雄市", "710500"),
                    ("基隆市", "710600"),
                    ("新竹市", "710700"),
                    ("新竹县", "710800"),
                    ("苗栗县", "710900"),
                    ("彰化县", "711000"),
                    ("南投县", "711100"),
                    ("云林县", "711200"),
                    ("嘉义市", "711300"),
                    ("嘉义县", "711400"),
                    ("屏东县", "711500"),
                    ("宜兰县", "711600"),
                    ("花莲县", "711700"),
                    ("台东县", "711800"),
                    ("澎湖县", "711900"),
                    ("金门县", "712000"),
                    ("连江县", "712100")
                ]
            }
        }
        
        for province_name, data in taiwan_data.items():
            needs_fill = False
            if province_name not in province_to_cities:
                needs_fill = True
            else:
                existing = province_to_cities.get(province_name) or []
                if len(existing) == 0:
                    needs_fill = True
            if needs_fill:
                print(f"手动填充台湾省城市数据：{province_name}")
                city_pairs = []
                for city_name, city_code in data["cities"]:
                    city_pairs.append((city_name, city_code))
                    city_name_to_adcode[city_name] = city_code
                province_to_cities[province_name] = city_pairs
                print(f"台湾省城市数：{len(data['cities'])}")

    def show_all_cities(self):
        """显示所有城市在城市选择区域（默认视图）。"""
        # 清空城市复选框区域
        for child in self.city_cb_frame.winfo_children():
            child.destroy()
        self.city_checkbuttons.clear()
        
        # 从配置中获取所有城市
        all_cities = self.config_manager.get_all_cities()
        
        # 为所有城市创建复选框
        for city_name in sorted(all_cities.keys()):
            if city_name not in self.city_vars:
                self.city_vars[city_name] = tk.BooleanVar()
            var = self.city_vars[city_name]
            cb = tk.Checkbutton(self.city_cb_frame, text=city_name, variable=var, command=self.on_city_checks_changed,
                               bg='#ffffff', fg='#374151', relief='flat')
            cb.pack(anchor='w')
            self.city_checkbuttons[city_name] = cb
            
        # 更新统计信息
        self.area_hint_label.config(text=f"可选择{len(all_cities)}个城市")

    def build_provinces_ui(self):
        """根据配置构建省份复选框列表。
        数据来源：ConfigManager.provinces，优先使用已缓存数据；
        行为：省份名称可点击（右侧仅显示该省城市），勾选省份同步城市选择。
        """
        # 清空
        for child in self.province_cb_frame.winfo_children():
            child.destroy()
        self.province_checkbuttons.clear()
        self.province_vars = {}

        provinces = self.config_manager.get_provinces()
        for province_name in sorted(provinces.keys()):
            row = ProvinceCheckbutton(
                self.province_cb_frame,
                text=province_name,
                province_name=province_name,
                on_check_changed=self.on_province_check_changed,
                on_click=self.on_province_clicked,
                canvas_ref=self.province_cb_canvas,
                bg='#ffffff'
            )
            row.pack(anchor='w')
            self.province_checkbuttons[province_name] = row

        # 初次进入：不平铺所有城市，保持右侧为空并给出提示
        for child in self.city_cb_frame.winfo_children():
            child.destroy()
        self.city_checkbuttons.clear()
        self.current_province_name = None
        self.area_hint_label.config(text="请选择左侧省份")
        
        # 从现有配置中填充 province_to_cities 字典，确保城市数据立即可用
        self._populate_province_to_cities_from_config()

    def _populate_province_to_cities_from_config(self):
        """从现有配置中填充 province_to_cities 字典，确保城市数据立即可用"""
        try:
            provinces = self.config_manager.get_provinces()
            for province_name, province_data in provinces.items():
                cities = province_data.get("cities", {})
                if cities:
                    city_pairs = []
                    for city_name, city_data in cities.items():
                        city_code = city_data.get("adcode")
                        if city_name and city_code:
                            city_pairs.append((city_name, city_code))
                            self.city_name_to_adcode[city_name] = city_code
                    if city_pairs:
                        self.province_to_cities[province_name] = city_pairs
                        print(f"从配置加载 {province_name} 的 {len(city_pairs)} 个城市")
        except Exception as e:
            print(f"从配置填充省市数据失败：{e}")

    def on_province_clicked(self, province_name):
        """点击省份名称 -> 右侧仅显示该省城市。
        注：不改变已选状态，仅改变展示范围，统计与三态保持同步。
        """
        province_cities = self.province_to_cities.get(province_name)
        if not province_cities:
            # 若未填充 province_to_cities，则根据配置构造（统一转换）
            city_pairs = []
            for code, name in self.config_manager.iter_cities(province_name):
                city_pairs.append((name, code))
            province_cities = city_pairs
            self.province_to_cities[province_name] = city_pairs

        # 清空并填充该省城市
        for child in self.city_cb_frame.winfo_children():
            child.destroy()
        self.city_checkbuttons.clear()

        for city_name, city_code in province_cities:
            if city_name not in self.city_vars:
                self.city_vars[city_name] = tk.BooleanVar()
            var = self.city_vars[city_name]
            cb = tk.Checkbutton(self.city_cb_frame, text=city_name, variable=var, command=self.on_city_checks_changed,
                               bg='#ffffff', fg='#374151', relief='flat')
            cb.pack(anchor='w')
            self.city_checkbuttons[city_name] = cb

        self.current_province_name = province_name
        # 计算当前省的"可选择"与"已选择"数量
        total_in_province = len(province_cities)
        selected_in_province = sum(1 for city_name, _ in province_cities if city_name in self.city_vars and self.city_vars[city_name].get())
        # 计算全局已选数量
        provinces = self.config_manager.get_provinces()
        total_selected_global = 0
        for p in provinces.values():
            for city_name, city_data in p.get('cities', {}).items():
                if city_name and city_name in self.city_vars and self.city_vars[city_name].get():
                    total_selected_global += 1
        self.area_hint_label.config(text=f"{province_name}：可选择{total_in_province}个城市 / 已选择{total_selected_global}市")
        # 切换省份后，同步右上角"查询所有市"二态勾选状态
        if hasattr(self, 'select_all_cities_var'):
            self.update_all_cities_check_state()

    def on_province_check_changed(self, province_name, state):
        """省份复选框变化：
        - checked: 全选该省所有城市
        - unchecked: 取消选择该省所有城市
        - partial: 维持现状（由城市勾选推动）
        """
        province_cities = self.province_to_cities.get(province_name)
        if not province_cities:
            # 同步填充（统一转换）
            city_pairs = []
            for code, name in self.config_manager.iter_cities(province_name):
                city_pairs.append((name, code))
            province_cities = city_pairs
            self.province_to_cities[province_name] = city_pairs

        if state == 'checked':
            for city_name, _ in province_cities:
                if city_name not in self.city_vars:
                    self.city_vars[city_name] = tk.BooleanVar()
                self.city_vars[city_name].set(True)
        elif state == 'unchecked':
            for city_name, _ in province_cities:
                if city_name not in self.city_vars:
                    self.city_vars[city_name] = tk.BooleanVar()
                self.city_vars[city_name].set(False)
        # partial 交由城市选择驱动

        # 若当前右侧显示的是该省城市，需要刷新勾选状态
        for city_name in list(self.city_checkbuttons.keys()):
            if city_name in [n for n, _ in province_cities]:
                try:
                    # 直接设置 BooleanVar 的值来更新复选框状态
                    if city_name in self.city_vars:
                        self.city_vars[city_name].set(self.city_vars[city_name].get())
                except tk.TclError:
                    pass

        # 触发下游同步
        self.on_city_checks_changed()
        # 省份操作后，强制刷新"选择所有省份"的状态，避免失效
        self.update_all_provinces_check_state()

    def show_province_cities(self, province_name):
        """显示指定省份的所有城市（备用接口，目前使用 on_province_clicked）。"""
        province_cities = self.province_to_cities.get(province_name, [])
        if not province_cities:
            return
            
        # 清空城市复选框区域
        for child in self.city_cb_frame.winfo_children():
            child.destroy()
        
        # 创建该省的所有城市复选框
        for city_name, city_code in province_cities:
            if city_name not in self.city_vars:
                self.city_vars[city_name] = tk.BooleanVar()
            var = self.city_vars[city_name]
            cb = tk.Checkbutton(self.city_cb_frame, text=city_name, variable=var, command=self.on_city_checks_changed,
                               bg='#ffffff', fg='#374151', relief='flat')
            cb.pack(anchor='w')
            self.city_checkbuttons[city_name] = cb



    def on_city_checks_changed(self):
        """当城市勾选变化时，更新选择集合并刷新省份三态与全选三态。"""
        # 确保城市复选框已创建
        if not hasattr(self, 'city_checkbuttons'):
            self.city_checkbuttons = {}
            
        # 更新选中的城市
        self.selected_cities = {name for name, var in self.city_vars.items() if var.get()}
        
        # 更新各省份三态
        self.update_province_check_states()

        # 更新左侧"选择所有省份"与右侧"查询所有市"复选框的状态
        self.update_all_provinces_check_state()
        if hasattr(self, 'select_all_cities_var'):
            self.update_all_cities_check_state()
        
        # 更新状态文案：显示当前省可选择数量 + 全局已选数量
        provinces = self.config_manager.get_provinces()
        total_selected_global = 0
        for p in provinces.values():
            for city_name, city_data in p.get('cities', {}).items():
                if city_name and city_name in self.city_vars and self.city_vars[city_name].get():
                    total_selected_global += 1
        # 当前省可选择数量（若未选中某省，则显示全部城市数）
        if getattr(self, 'current_province_name', None):
            province_cities = self.province_to_cities.get(self.current_province_name)
            if not province_cities:
                city_pairs = []
                for code, name in self.config_manager.iter_cities(self.current_province_name):
                    city_pairs.append((name, code))
                province_cities = city_pairs
            total_in_province = len(province_cities)
            prefix = f"{self.current_province_name}：可选择{total_in_province}个城市"
        else:
            total_all = sum(len(p.get('cities', {})) for p in provinces.values())
            prefix = f"全部：可选择{total_all}个城市"
        self.area_hint_label.config(text=f"{prefix} / 已选择{total_selected_global}市")

    def update_province_check_states(self):
        """根据城市选择状态更新省份复选框的状态。
        算法：统计该省下城市的勾选数，0 -> unchecked，=总数 -> checked，其余 -> partial。
        """
        if not hasattr(self, 'province_checkbuttons') or not self.province_checkbuttons:
            return
            
        # 确保城市复选框已创建
        if not hasattr(self, 'city_checkbuttons'):
            self.city_checkbuttons = {}
            
        for province_name, province_cb in self.province_checkbuttons.items():
            # 获取该省份下的所有城市
            province_cities = self.province_to_cities.get(province_name, [])
            if not province_cities:
                # 若未缓存，则从配置构造并回填，确保三态可计算
                city_pairs = []
                for code, name in self.config_manager.iter_cities(province_name):
                    city_pairs.append((name, code))
                province_cities = city_pairs
                if not hasattr(self, 'province_to_cities'):
                    self.province_to_cities = {}
                self.province_to_cities[province_name] = city_pairs
                
            # 统计该省份下城市的选择状态
            total_cities = len(province_cities)
            checked_cities = 0
            
            for city_name, _ in province_cities:
                if city_name in self.city_vars and self.city_vars[city_name].get():
                    checked_cities += 1
            
            # 根据城市选择状态设置省份复选框状态
            if checked_cities == 0:
                province_cb.set_state("unchecked")
            elif checked_cities == total_cities:
                province_cb.set_state("checked")
            else:
                # 部分选中状态，保持当前状态不变
                province_cb.set_state("partial")
                
        # 更新统计信息（以全局省市为准，而非仅右侧可见城市）
        provinces = self.config_manager.get_provinces()
        total_selected_global = 0
        for p in provinces.values():
            for city_name, city_data in p.get('cities', {}).items():
                if city_name and city_name in self.city_vars and self.city_vars[city_name].get():
                    total_selected_global += 1
        self.area_hint_label.config(text=f"已选{total_selected_global}市")

    def update_all_provinces_check_state(self):
        """根据全局城市选择状态更新"选择所有省份"的二态复选框。
        逻辑：遍历配置中的所有城市，若全部被选中则勾上，否则取消。
        与右侧可见城市无关，保证在操作省份时也能实时准确。
        """
        provinces = self.config_manager.get_provinces()
        total = 0
        checked = 0
        for p in provinces.values():
            for city_name, city_data in p.get('cities', {}).items():
                if not city_name:
                    continue
                total += 1
                if city_name in self.city_vars and self.city_vars[city_name].get():
                    checked += 1
        self.select_all_var.set(total > 0 and checked == total)

    def update_all_cities_check_state(self):
        """根据当前右侧可见城市的勾选情况，实时更新"查询所有市"的二态勾选。"""
        if not hasattr(self, 'city_checkbuttons') or not self.city_checkbuttons:
            self.select_all_cities_var.set(False)
            return
        total = len(self.city_checkbuttons)
        checked = 0
        for name in self.city_checkbuttons.keys():
            if name in self.city_vars and self.city_vars[name].get():
                checked += 1
        self.select_all_cities_var.set(total > 0 and checked == total)

    def save_province_city_data_to_file(self):
        """将加载的省市数据保存到ConfigManager（便于下次直接读取）。"""
        try:
            # 将数据保存到 ConfigManager 而不是文件
            if hasattr(self, 'province_to_cities') and hasattr(self, 'city_name_to_adcode'):
                # 更新 ConfigManager 中的省市数据
                self.config_manager.update_provinces_data(self.province_to_cities, self.city_name_to_adcode)
                
                # 保存配置
                if self.config_manager.save_config():
                    print(f"省市数据已保存到配置文件")
                    self.insert_text(self.frame1, f"省市数据已保存到配置文件: config.json\n")
                else:
                    print(f"保存省市数据失败")
                    self.insert_text(self.frame1, f"保存省市数据失败\n")
            else:
                print(f"没有省市数据可保存")
                self.insert_text(self.frame1, f"没有省市数据可保存\n")
                
        except Exception as e:
            print(f"保存省市数据失败: {e}")
            self.insert_text(self.frame1, f"保存省市数据失败: {e}\n")

    def load_province_city_data_from_config(self):
        """从 ConfigManager 加载省市数据并填充到界面。
        行为调整：仅重建省份列表，右侧等待点击后展示该省城市。
        """
        try:
            # 从 ConfigManager 获取数据
            all_cities = self.config_manager.get_all_cities()
            if not all_cities:
                return False
            
            # 重建省份 UI
            self.build_provinces_ui()
            provinces = self.config_manager.get_provinces()
            count = sum(len(p.get('cities', {})) for p in provinces.values())
            self.area_hint_label.config(text=f"已从配置加载{count}个城市数据，请先选择左侧省份。")
            return True
            
        except Exception as e:
            print(f"从配置加载省市数据失败: {e}")
            return False

    
    

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
                    # 若所有选中字段均为空列表或等价于空，则整行不写入
                    raw_values = []
                    for _, english in selected_fields:
                        v = poi.get(english, '')
                        raw_values.append(v)
                    all_empty = True
                    for v in raw_values:
                        if v not in (None, '', '[]'):
                            # 处理真正的空列表类型
                            if isinstance(v, list) and len(v) == 0:
                                pass
                            else:
                                all_empty = False
                                break
                    if all_empty:
                        continue

                    row = []
                    for _, english in selected_fields:
                        value = poi.get(english, '')
                        # 将空列表表现形式置空
                        if value == "[]" or (isinstance(value, list) and len(value) == 0):
                            row.append('')
                        else:
                            row.append(value)
                    writer.writerow(row)
        except PermissionError as e:
            print(f"文件 '{realtime_export_path}' 被占用或没有写权限: {str(e)}")
            show_centered_message("警告", f"无法写入文件 '{realtime_export_path}'，请检查文件是否已被占用或没有写权限。", "warning", self.root)
    
    def stop_search(self):
        """优雅停止当前检索，并在输出中插入分隔。"""
        self.is_searching = False
        self.is_paused = False
        if hasattr(self, 'pause_button'):
            self.pause_button.configure(state='disabled', text='暂停')
        self.insert_text(self.frame1, "用户主动终止查询.\n")
        self.insert_text(self.frame2, "\n")
        self.insert_text(self.frame3, "\n")
        
        # 更新进度显示为已查询的城市数量
        try:
            # 直接调用现有的进度更新方法
            self.update_progress_run()
        except Exception as e:
            print(f"更新进度显示失败: {e}")

    def toggle_pause(self):
        """切换暂停/继续状态，影响搜索循环与分页循环。"""
        if not self.is_searching:
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.configure(text='继续')
            self.insert_text(self.frame1, "已暂停查询\n")
        else:
            self.pause_button.configure(text='暂停')
            self.insert_text(self.frame1, "已继续查询\n")
        
    def get_next_unqueried_city(self):
        """返回下一个未查询城市名称（基于配置）；若全部查询过则返回 None。"""
        provinces = self.config_manager.get_provinces()
        for p in provinces.values():
            for code, c in p.get('cities', {}).items():
                city_name = c.get('name')
                if city_name and not c.get('queried'):
                    return city_name
        return None

    def save_queried_cities(self):
        """将内存中的已查询城市同步写入配置文件（兼容旧流程，当前无实际写入）。"""
        # 在这里不需要具体实现，因为查询状态在search_pois中实时更新
        # 保留这个方法以兼容现有调用
        pass

    def export_csv(self):
        """通过"另存为"导出汇总 POI，使用用户勾选的字段设置。"""
        if not hasattr(self, 'pois_data'):
            show_centered_message("警告", "没有数据可导出，请先进行查询。", "warning", self.root)
            return
        
        # 获取用户选择的字段，与实时导出保持一致
        selected_fields = [(chinese, english) for chinese, (english, var) in self.fields.items() if var.get()]
        
        if not selected_fields:
            show_centered_message("警告", "请至少选择一个字段进行导出。", "warning", self.root)
            return
        
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filepath:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                # 写入表头，使用用户选择的中文字段名
                header = [chinese for chinese, _ in selected_fields]
                writer.writerow(header)
                
                # 写入数据，使用用户选择的英文字段名
                for poi in self.pois_data:
                    # 若所有选中字段均为空列表或等价于空，则整行不写入
                    raw_values = []
                    for _, english in selected_fields:
                        v = poi.get(english, '')
                        raw_values.append(v)
                    all_empty = True
                    for v in raw_values:
                        if v not in (None, '', '[]'):
                            if isinstance(v, list) and len(v) == 0:
                                pass
                            else:
                                all_empty = False
                                break
                    if all_empty:
                        continue

                    row = []
                    for _, english in selected_fields:
                        value = poi.get(english, '')
                        if value == "[]" or (isinstance(value, list) and len(value) == 0):
                            row.append('')
                        else:
                            row.append(value)
                    writer.writerow(row)
            show_centered_message("提示", "导出完成", "info", self.root)

    def reset_cities_status(self):
        """清空已查询城市记录与标记，并刷新界面列表。"""
        try:
            # 使用ConfigManager重置所有查询状态
            self.config_manager.reset_all_query_status()
                        
            # 保存更新后的配置
            self.config_manager.save_config()
            
            # 更新进度显示
            total = sum(len(p.get('cities', {})) for p in self.config_manager.get_provinces().values())
            self.update_progress(total)
            
            show_centered_message("提示", "所有城市状态已恢复为未查询", "info", self.root)
            
        except Exception as e:
            show_centered_message("错误", f"重置状态失败：{str(e)}", "error", self.root)



if __name__ == "__main__":
    root = tk.Tk()
    # 设置窗口/任务栏图标，兼容 PyInstaller 单文件
    def _resource_path(relative_path: str) -> str:
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    try:
        icon_path = None
        for name in ("app.ico"):
            p = _resource_path(name)
            if os.path.exists(p):
                icon_path = p
                break
        if icon_path:
            root.iconbitmap(icon_path)
    except Exception:
        pass
    app = AMapGUI(root)

    style = ttk.Style()
    style.configure('TButton', font=('Arial', 12), foreground='blue', padding=10)
    style.configure('TLabel', font=('Arial', 12))
    style.configure('TEntry', font=('Arial', 12))

    root.mainloop()