"""
运动计数器 GUI 应用程序
Exercise Counter GUI Application
集成所有功能的桌面程序
"""

import os
import sys
import cv2
import torch
import numpy as np
import math
import json
import datetime
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
try:
    from tkcalendar import Calendar
    HAS_TKCAL = True
except Exception:
    HAS_TKCAL = False
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, Colors
from copy import deepcopy

# 运动配置
SPORT_CONFIG = {
    'squat': {
        'name': '深蹲',
        'left_points_idx': [11, 13, 15],
        'right_points_idx': [12, 14, 16],
        'maintaining': 100,  # 更宽松：进入<100
        'relaxing': 160,    # 更宽松：退出>160
        'side_mode': 'avg',  # 可选: 'avg' | 'left' | 'right'
    },
    'pushup': {
        'name': '俯卧撑',
        'left_points_idx': [6, 8, 10],
        'right_points_idx': [5, 7, 9],
        'maintaining': 150,  # 更宽松：进入>150
        'relaxing': 120,     # 更宽松：退出<120
        'side_mode': 'avg',
    },
    'situp': {
        'name': '仰卧起坐',
        'left_points_idx': [6, 12, 14],
        'right_points_idx': [5, 11, 13],
        'maintaining': 120,  # 更宽松：进入<120
        'relaxing': 140,     # 更宽松：退出>140
        'side_mode': 'avg',
    }
}


class ExerciseCounterApp:
    """运动计数器主应用程序"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("健身检测系统 - Fitness Tracker")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # 应用变量
        self.is_running = False
        self.is_paused = False
        self.cap = None
        self.model = None
        self.detector_model = None
        self.counter = 0
        self.fps = 0
        self.current_sport = 'squat'
        self.auto_detect = False
        self.save_results = False
        self.save_dir = None
        self.video_writer = None

        # 性能参数
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.use_half = True if torch.cuda.is_available() else False
        # 在CPU上降低输入尺寸可显著提升FPS
        self.imgsz = 416 if not torch.cuda.is_available() else 640
        self.conf_thres = 0.5
        
        # 计数状态
        self.reaching = False
        self.reaching_last = False
        self.state_keep = False
        # 去抖/平滑相关
        self.prev_angle = None
        self.min_reach_frames = 3  # 至少连续N帧处于“到位”状态才计数
        self.reach_frames = 0
        self.show_angle = False
        self.current_angle = 0.0

        # 统计相关
        self.total_counts = {k: 0 for k in SPORT_CONFIG.keys()}
        self.stat_labels = {}
        self.session_start_time = None
        
        # 自动识别相关
        self.pose_key_point_frames = []
        self.idx_2_category = {}

        # 配置文件与统计默认（需在构建UI之前准备）
        self.config_path = os.path.join('config', 'thresholds.json')
        self.history_path = os.path.join('config', 'history.json')
        self.goals = {k: 20 for k in SPORT_CONFIG.keys()}  # 每日默认目标
        self.todays_counts = {k: 0 for k in SPORT_CONFIG.keys()}
        self.checked_in = False
        self.streak_days = 0
        self.date_str = datetime.date.today().isoformat()
        self.pb_by_sport = {}
        self.goal_label_by_sport = {}
        self.checkin_status_label = None
        # 先加载配置与历史，以便UI初始显示即为最新
        self.load_config(startup=True)
        self.load_history()

        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()

        # 加载模型
        self.load_models()
        
        # 绑定快捷键
        self.bind_shortcuts()
        
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置颜色
        style.configure('TButton', padding=10, font=('Arial', 10))
        style.configure('Start.TButton', foreground='green', font=('Arial', 12, 'bold'))
        style.configure('Pause.TButton', foreground='orange', font=('Arial', 12, 'bold'))
        style.configure('Stop.TButton', foreground='red', font=('Arial', 12, 'bold'))
        style.configure('TLabel', font=('Arial', 10))
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Counter.TLabel', font=('Arial', 48, 'bold'), foreground='blue')
        
    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        # 修正：应当为第0行赋权重，这样右侧视频区域可随窗口垂直扩展
        main_frame.rowconfigure(0, weight=1)
        
        # 左侧控制面板（带顶部导航：控制/设置）
        self.create_control_panel(main_frame)
        
        # 右侧视频显示区域
        self.create_video_panel(main_frame)
        
    def create_control_panel(self, parent):
        """创建左侧控制面板"""
        # 顶部导航
        nav = ttk.Notebook(parent)
        nav.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)

        control_frame = ttk.Frame(nav)
        settings_tab = ttk.Frame(nav)
        nav.add(control_frame, text="控制")
        nav.add(settings_tab, text="设置")
        
        row = 0
        
        # 标题
        title_label = ttk.Label(control_frame, text="运动计数器", style='Title.TLabel')
        title_label.grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        
        # 状态显示（提前到顶部，避免被底部挤压）
        status_frame = ttk.LabelFrame(control_frame, text="运动状态", padding="10")
        status_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        ttk.Label(status_frame, text="当前运动:").grid(row=0, column=0, sticky=tk.W)
        self.current_sport_label = ttk.Label(status_frame, text="未开始", foreground='gray')
        self.current_sport_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(status_frame, text="计数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.counter_label = ttk.Label(status_frame, text="0", style='Counter.TLabel')
        self.counter_label.grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Label(status_frame, text="FPS:").grid(row=2, column=0, sticky=tk.W)
        self.fps_label = ttk.Label(status_frame, text="0")
        self.fps_label.grid(row=2, column=1, sticky=tk.W, padx=5)
        row += 1

        # 输入源选择
        ttk.Label(control_frame, text="输入源:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5)
        row += 1
        
        self.input_var = tk.StringVar(value="camera")
        ttk.Radiobutton(control_frame, text="摄像头", variable=self.input_var, 
                       value="camera", command=self.on_input_change).grid(row=row, column=0, sticky=tk.W)
        row += 1
        
        ttk.Radiobutton(control_frame, text="视频文件", variable=self.input_var, 
                       value="file", command=self.on_input_change).grid(row=row, column=0, sticky=tk.W)
        row += 1
        
        # 摄像头选择
        self.camera_frame = ttk.Frame(control_frame)
        self.camera_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(self.camera_frame, text="摄像头:").pack(side=tk.LEFT)
        self.camera_var = tk.StringVar(value="0")
        camera_combo = ttk.Combobox(self.camera_frame, textvariable=self.camera_var, 
                                    values=["0", "1", "2"], width=5, state='readonly')
        camera_combo.pack(side=tk.LEFT, padx=5)
        row += 1
        
        # 文件选择
        self.file_frame = ttk.Frame(control_frame)
        self.file_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.file_path = tk.StringVar(value="")
        ttk.Entry(self.file_frame, textvariable=self.file_path, width=20, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self.file_frame, text="浏览", command=self.browse_file).pack(side=tk.LEFT, padx=5)
        self.file_frame.grid_remove()
        row += 1
        
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # 模式选择
        ttk.Label(control_frame, text="识别模式:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5)
        row += 1
        
        self.mode_var = tk.StringVar(value="manual")
        ttk.Radiobutton(control_frame, text="手动选择运动", variable=self.mode_var, 
                       value="manual", command=self.on_mode_change).grid(row=row, column=0, sticky=tk.W)
        row += 1
        
        ttk.Radiobutton(control_frame, text="自动识别运动", variable=self.mode_var, 
                       value="auto", command=self.on_mode_change).grid(row=row, column=0, sticky=tk.W)
        row += 1
        
        # 运动类型选择（手动模式）
        self.sport_frame = ttk.LabelFrame(control_frame, text="运动类型", padding="5")
        self.sport_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.sport_var = tk.StringVar(value="squat")
        for sport_id, config in SPORT_CONFIG.items():
            ttk.Radiobutton(self.sport_frame, text=config['name'], 
                          variable=self.sport_var, value=sport_id).pack(anchor=tk.W)
        row += 1
        
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # 保存选项
        self.save_var = tk.BooleanVar(value=False)
        save_check = ttk.Checkbutton(control_frame, text="保存处理结果", 
                                     variable=self.save_var, command=self.on_save_change)
        save_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        self.save_path_frame = ttk.Frame(control_frame)
        self.save_path_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.save_path_var = tk.StringVar(value="./output")
        ttk.Entry(self.save_path_frame, textvariable=self.save_path_var, width=15).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self.save_path_frame, text="选择", command=self.browse_save_dir).pack(side=tk.LEFT, padx=5)
        self.save_path_frame.grid_remove()
        row += 1
        
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # 控制按钮
        self.start_button = ttk.Button(control_frame, text="▶ 开始", 
                                       command=self.start_capture, style='Start.TButton')
        self.start_button.grid(row=row, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        row += 1
        
        self.pause_button = ttk.Button(control_frame, text="⏸ 暂停/继续", 
                                       command=self.toggle_pause, style='Pause.TButton', state='disabled')
        self.pause_button.grid(row=row, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        row += 1

        self.stop_button = ttk.Button(control_frame, text="⬛ 停止", 
                                      command=self.stop_capture, style='Stop.TButton', state='disabled')
        self.stop_button.grid(row=row, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        row += 1
        
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1

        # 检测设置（移动到“设置”页）
        settings_frame = ttk.LabelFrame(settings_tab, text="检测设置", padding="10")
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        ttk.Label(settings_frame, text="去抖帧数:").grid(row=0, column=0, sticky=tk.W)
        self.min_reach_frames_var = tk.IntVar(value=self.min_reach_frames)
        self.debounce_spin = tk.Spinbox(settings_frame, from_=1, to=10, width=4,
                                        textvariable=self.min_reach_frames_var,
                                        command=self.on_debounce_change)
        self.debounce_spin.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.show_angle_var = tk.BooleanVar(value=self.show_angle)
        ttk.Checkbutton(settings_frame, text="显示角度/阈值", variable=self.show_angle_var,
                        command=self.on_show_angle_change).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)

        # 动作选择 + 阈值快速调节（所有动作）
        ttk.Label(settings_frame, text="选择动作:").grid(row=2, column=0, sticky=tk.W, pady=(8, 2))
        self.config_sport_var = tk.StringVar(value=self.current_sport)
        ttk.Combobox(settings_frame, textvariable=self.config_sport_var, state='readonly', width=8,
                     values=list(SPORT_CONFIG.keys()),
                     postcommand=self.sync_threshold_fields).grid(row=2, column=1, sticky=tk.W, pady=(8, 2))

        self.enter_thr_var = tk.IntVar()
        self.exit_thr_var = tk.IntVar()
        self.side_mode_var = tk.StringVar()
        self.sync_threshold_fields()

        ttk.Label(settings_frame, text="进入:").grid(row=3, column=0, sticky=tk.E)
        ttk.Entry(settings_frame, textvariable=self.enter_thr_var, width=6).grid(row=3, column=1, sticky=tk.W)
        ttk.Label(settings_frame, text="退出:").grid(row=3, column=2, sticky=tk.E)
        ttk.Entry(settings_frame, textvariable=self.exit_thr_var, width=6).grid(row=3, column=3, sticky=tk.W)
        ttk.Button(settings_frame, text="应用阈值", command=self.apply_thresholds).grid(row=3, column=4, padx=6)

        # 侧别模式（对选中动作）
        ttk.Label(settings_frame, text="侧别:").grid(row=4, column=0, sticky=tk.E, pady=(6,0))
        ttk.Combobox(settings_frame, textvariable=self.side_mode_var, state='readonly', width=6,
                     values=['avg','left','right']).grid(row=4, column=1, sticky=tk.W, pady=(6,0))
        ttk.Button(settings_frame, text="应用侧别", command=self.apply_side_mode).grid(row=4, column=2, padx=6, pady=(6,0))

        # 统计看板（现代化：打卡/目标/进度）
        stats_frame = ttk.LabelFrame(settings_tab, text="健身统计与打卡", padding="10")
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        row_s = 0
        ttk.Button(stats_frame, text="清空统计", command=self.reset_stats).grid(row=row_s, column=0, sticky=tk.W)
        ttk.Button(stats_frame, text="保存配置", command=self.save_config).grid(row=row_s, column=1, sticky=tk.W, padx=6)
        ttk.Button(stats_frame, text="加载配置", command=lambda: self.load_config(startup=False)).grid(row=row_s, column=2, sticky=tk.W)
        ttk.Button(stats_frame, text="手动打卡", command=self.manual_checkin).grid(row=row_s, column=3, sticky=tk.W, padx=6)
        row_s += 1
        ttk.Label(stats_frame, text=f"日期: {self.date_str}").grid(row=row_s, column=0, sticky=tk.W, pady=(6,2))
        self.checkin_status_label = ttk.Label(stats_frame, text="未打卡", foreground='red')
        self.checkin_status_label.grid(row=row_s, column=1, sticky=tk.W)
        ttk.Label(stats_frame, text="连续打卡天数:").grid(row=row_s, column=2, sticky=tk.E)
        self.streak_label = ttk.Label(stats_frame, text="0")
        self.streak_label.grid(row=row_s, column=3, sticky=tk.W)
        row_s += 1
        ttk.Separator(stats_frame, orient='horizontal').grid(row=row_s, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=6)
        row_s += 1
        ttk.Label(stats_frame, text="项目").grid(row=row_s, column=0, sticky=tk.W)
        ttk.Label(stats_frame, text="今日/目标").grid(row=row_s, column=1, sticky=tk.W)
        ttk.Label(stats_frame, text="总计").grid(row=row_s, column=2, sticky=tk.W)
        ttk.Label(stats_frame, text="今日最佳").grid(row=row_s, column=3, sticky=tk.W)
        row_s += 1
        for sid, cfg in SPORT_CONFIG.items():
            ttk.Label(stats_frame, text=cfg['name']).grid(row=row_s, column=0, sticky=tk.W)
            pb = ttk.Progressbar(stats_frame, maximum=max(1, self.goals[sid]), length=120)
            pb.grid(row=row_s, column=1, sticky=tk.W, padx=4)
            self.pb_by_sport[sid] = pb
            total_lbl = ttk.Label(stats_frame, text="0")
            total_lbl.grid(row=row_s, column=2, sticky=tk.W, padx=4)
            self.stat_labels[sid] = total_lbl
            pb_lbl = ttk.Label(stats_frame, text="0")
            pb_lbl.grid(row=row_s, column=3, sticky=tk.W, padx=4)
            self.goal_label_by_sport[sid] = pb_lbl
            row_s += 1

        # 日历视图（可视化历史打卡）
        if HAS_TKCAL:
            cal_frame = ttk.LabelFrame(settings_tab, text="打卡日历", padding="10")
            cal_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
            self.calendar = Calendar(cal_frame, selectmode='day', date_pattern='yyyy-mm-dd')
            self.calendar.grid(row=0, column=0, sticky=(tk.W, tk.E))
            ttk.Button(cal_frame, text="跳转到今天", command=lambda: self.calendar.selection_set(self.date_str)).grid(row=1, column=0, sticky=tk.W, pady=6)
        # 结束控制页布局分隔
    def create_video_panel(self, parent):
        """创建右侧视频显示面板"""
        video_frame = ttk.LabelFrame(parent, text="视频显示", padding="10")
        video_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # 视频显示标签
        self.video_label = tk.Label(video_frame, bg='black', text='视频显示区域\n\n点击"开始"按钮启动',
                                    fg='white', font=('Arial', 16))
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
    def load_models(self):
        """加载AI模型"""
        try:
            # 加载更轻量的YOLOv8姿态检测模型（提升FPS）
            # 首选yolov8n-pose.pt；如未下载，Ultralytics会自动下载
            try:
                self.model = YOLO('yolov8n-pose.pt')
            except Exception:
                self.model = YOLO('yolov8s-pose.pt')

            # 设置运行设备
            try:
                # 新版Ultralytics推荐通过predict时传参device，这里保留以防兼容
                _ = self.model.to(self.device) if hasattr(self.model, 'to') else None
            except Exception:
                pass
            
            # 尝试加载运动识别模型
            try:
                from for_detect.Inference import LSTM
                checkpoint_path = './for_detect/checkpoint/'
                if os.path.exists(os.path.join(checkpoint_path, 'best_model.pt')):
                    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
                    self.detector_model = LSTM(17*2, 8, 2, 3, device)
                    model_weight = torch.load(os.path.join(checkpoint_path, 'best_model.pt'), 
                                             map_location=device)
                    self.detector_model.load_state_dict(model_weight)
                    
                    with open(os.path.join(checkpoint_path, 'idx_2_category.json'), 'r') as f:
                        self.idx_2_category = json.load(f)
                    print("✓ 运动识别模型加载成功")
            except Exception as e:
                print(f"⚠ 运动识别模型加载失败: {e}")
                print("  自动识别功能将不可用")
                
            print("✓ YOLOv8姿态模型加载成功")
            
        except Exception as e:
            messagebox.showerror("错误", f"模型加载失败：{str(e)}")
            
    def on_input_change(self):
        """输入源改变时的回调"""
        if self.input_var.get() == "camera":
            self.camera_frame.grid()
            self.file_frame.grid_remove()
        else:
            self.camera_frame.grid_remove()
            self.file_frame.grid()
            
    def on_mode_change(self):
        """识别模式改变时的回调"""
        if self.mode_var.get() == "manual":
            self.sport_frame.grid()
            self.auto_detect = False
        else:
            if self.detector_model is None:
                messagebox.showwarning("警告", "自动识别模型未加载，请先训练模型")
                self.mode_var.set("manual")
                return
            self.sport_frame.grid_remove()
            self.auto_detect = True
    
    def on_debounce_change(self):
        """去抖帧数修改"""
        try:
            self.min_reach_frames = int(self.min_reach_frames_var.get())
        except Exception:
            pass

    def on_show_angle_change(self):
        """切换角度显示"""
        self.show_angle = bool(self.show_angle_var.get())

    def apply_thresholds(self):
        """将阈值应用到选择的动作配置"""
        try:
            enter = int(self.enter_thr_var.get())
            exitv = int(self.exit_thr_var.get())
            sport = self.config_sport_var.get()
            SPORT_CONFIG[sport]['maintaining'] = enter
            SPORT_CONFIG[sport]['relaxing'] = exitv
        except Exception:
            pass

    def apply_side_mode(self):
        """应用侧别模式(avg/left/right)到选择的动作"""
        SPORT_CONFIG[self.config_sport_var.get()]['side_mode'] = self.side_mode_var.get()

    def sync_threshold_fields(self):
        """当切换要配置的动作时，同步该动作阈值/侧别到输入框"""
        s = self.config_sport_var.get() or self.current_sport
        cfg = SPORT_CONFIG[s]
        self.enter_thr_var.set(cfg['maintaining'])
        self.exit_thr_var.set(cfg['relaxing'])
        self.side_mode_var.set(cfg.get('side_mode', 'avg'))

    # ---------- 配置保存/加载与快捷键 ----------
    def get_current_config(self):
        return {
            'sports': {
                sid: {
                    'maintaining': cfg['maintaining'],
                    'relaxing': cfg['relaxing'],
                    'side_mode': cfg.get('side_mode', 'avg')
                } for sid, cfg in SPORT_CONFIG.items()
            },
            'min_reach_frames': self.min_reach_frames,
            'show_angle': self.show_angle
        }

    def save_config(self):
        try:
            data = self.get_current_config()
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # 同步保存今日历史
            self.save_history()
            messagebox.showinfo('提示', f'配置已保存到\n{self.config_path}')
        except Exception as e:
            messagebox.showerror('错误', f'配置保存失败：{e}')

    def load_config(self, startup=False):
        try:
            if not os.path.exists(self.config_path):
                return
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            sports = data.get('sports', {})
            for sid, cfg in sports.items():
                if sid in SPORT_CONFIG:
                    SPORT_CONFIG[sid]['maintaining'] = int(cfg.get('maintaining', SPORT_CONFIG[sid]['maintaining']))
                    SPORT_CONFIG[sid]['relaxing'] = int(cfg.get('relaxing', SPORT_CONFIG[sid]['relaxing']))
                    SPORT_CONFIG[sid]['side_mode'] = cfg.get('side_mode', SPORT_CONFIG[sid].get('side_mode', 'avg'))
            # 其它设置
            self.min_reach_frames = int(data.get('min_reach_frames', self.min_reach_frames))
            self.show_angle = bool(data.get('show_angle', self.show_angle))
            # 同步到UI
            if hasattr(self, 'min_reach_frames_var'):
                self.min_reach_frames_var.set(self.min_reach_frames)
            if hasattr(self, 'show_angle_var'):
                self.show_angle_var.set(self.show_angle)
            if hasattr(self, 'config_sport_var'):
                self.sync_threshold_fields()
            if not startup:
                messagebox.showinfo('提示', '配置已加载')
        except Exception as e:
            if not startup:
                messagebox.showerror('错误', f'配置加载失败：{e}')

    def save_history(self):
        try:
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            data = {}
            if os.path.exists(self.history_path):
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            data.setdefault('days', {})
            day = data['days'].get(self.date_str, {'counts': {}, 'checked_in': False})
            day['counts'] = self.todays_counts
            day['checked_in'] = self.checked_in
            data['days'][self.date_str] = day
            data['streak_days'] = self.streak_days
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_history(self):
        try:
            if not os.path.exists(self.history_path):
                return
            with open(self.history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.streak_days = int(data.get('streak_days', 0))
            day = data.get('days', {}).get(self.date_str)
            if day:
                self.todays_counts = day.get('counts', self.todays_counts)
                self.checked_in = bool(day.get('checked_in', False))
        except Exception:
            pass

    def manual_checkin(self):
        """手动打卡（达到任一目标即可自动打卡，也可手动）"""
        self.checked_in = True
        self.streak_days += 1
        self.save_history()

    def bind_shortcuts(self):
        try:
            self.root.bind('<space>', lambda e: self.toggle_pause())
            self.root.bind('<s>', lambda e: self.stop_capture())
            self.root.bind('<S>', lambda e: self.stop_capture())
            self.root.bind('<r>', lambda e: self.reset_stats())
            self.root.bind('<R>', lambda e: self.reset_stats())
            self.root.bind('<q>', lambda e: self.on_closing())
            self.root.bind('<Q>', lambda e: self.on_closing())
        except Exception:
            pass
            
    def on_save_change(self):
        """保存选项改变时的回调"""
        if self.save_var.get():
            self.save_path_frame.grid()
        else:
            self.save_path_frame.grid_remove()
            
    def browse_file(self):
        """浏览选择视频文件"""
        filename = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[("视频文件", "*.mp4 *.avi *.mov *.mkv"), ("所有文件", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
            
    def browse_save_dir(self):
        """浏览选择保存目录"""
        directory = filedialog.askdirectory(title="选择保存目录")
        if directory:
            self.save_path_var.set(directory)
            
    def start_capture(self):
        """开始视频捕获和处理"""
        if self.is_running:
            return
            
        # 获取输入源
        if self.input_var.get() == "camera":
            source = int(self.camera_var.get())
        else:
            source = self.file_path.get()
            if not source or not os.path.exists(source):
                messagebox.showerror("错误", "请选择有效的视频文件")
                return
                
        # 打开视频捕获
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            messagebox.showerror("错误", "无法打开视频源")
            return
            
        # 摄像头分辨率下调以提升性能（仅在CPU上设置）
        try:
            if isinstance(source, int) and not torch.cuda.is_available():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                # 一些摄像头使用MJPG编码更快
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        except Exception:
            pass

        # 设置保存
        if self.save_var.get():
            self.save_dir = os.path.join(self.save_path_var.get(), 
                                        datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
            os.makedirs(self.save_dir, exist_ok=True)
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.video_writer = cv2.VideoWriter(
                os.path.join(self.save_dir, 'result.mp4'),
                fourcc, fps, (width, height)
            )
            
        # 重置状态
        self.counter = 0
        self.reaching = False
        self.reaching_last = False
        self.state_keep = False
        self.pose_key_point_frames = []
        
        # 更新UI
        self.is_running = True
        self.start_button.config(state='disabled')
        self.pause_button.config(state='normal')
        self.stop_button.config(state='normal')
        
        # 获取当前运动类型
        self.current_sport = self.sport_var.get()
        self.current_sport_label.config(
            text=SPORT_CONFIG[self.current_sport]['name'],
            foreground='green'
        )
        # 重置去抖状态
        self.prev_angle = None
        self.reach_frames = 0
        self.reaching = False
        self.reaching_last = False
        
        # 启动处理线程
        self.process_thread = threading.Thread(target=self.process_video, daemon=True)
        self.process_thread.start()
        
    def stop_capture(self):
        """停止视频捕获"""
        self.is_running = False
        self.is_paused = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
            
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            
        self.start_button.config(state='normal')
        self.pause_button.config(state='disabled')
        self.stop_button.config(state='disabled')
        self.current_sport_label.config(text="已停止", foreground='gray')
        # 停止时持久化当日统计
        self.save_history()
        
        # 显示最终统计
        if self.counter > 0:
            messagebox.showinfo("统计结果", 
                              f"运动类型: {SPORT_CONFIG[self.current_sport]['name']}\n"
                              f"完成次数: {self.counter} 次\n" +
                              (f"结果已保存至: {self.save_dir}" if self.save_dir else ""))
        
    def draw_text_with_chinese(self, frame):
        """使用PIL在图像上绘制支持中文的文本"""
        # 转换为PIL格式
        frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(frame_pil)
        
        # 计算缩放比例
        plot_size_ratio = max(frame.shape[1] / 960, frame.shape[0] / 540)
        
        # 绘制背景矩形（使用OpenCV更高效）
        cv2.rectangle(frame, 
                     (int(20 * plot_size_ratio), int(20 * plot_size_ratio)),
                     (int(380 * plot_size_ratio), int(180 * plot_size_ratio)),
                     (55, 104, 0), -1)
        
        # 转换回PIL
        frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(frame_pil)
        
        # 尝试加载字体
        try:
            font_size = int(28 * plot_size_ratio)
            # Windows系统字体
            font = ImageFont.truetype("msyh.ttc", font_size)  # 微软雅黑
        except:
            try:
                font = ImageFont.truetype("SimHei.ttf", font_size)  # 黑体
            except:
                # 如果都失败，使用默认字体（只支持英文）
                font = ImageFont.load_default()
        
        # 获取运动类型（中英文）
        sport_name_cn = SPORT_CONFIG[self.current_sport]['name']
        sport_name_en = self.current_sport.capitalize()
        
        # 绘制文本
        y_offset = int(40 * plot_size_ratio)
        x_start = int(30 * plot_size_ratio)
        line_height = int(45 * plot_size_ratio)
        
        # 运动类型
        try:
            draw.text((x_start, y_offset), f'运动: {sport_name_cn}', 
                     font=font, fill=(255, 255, 255))
        except:
            draw.text((x_start, y_offset), f'Exercise: {sport_name_en}', 
                     font=font, fill=(255, 255, 255))
        
        # 计数
        y_offset += line_height
        try:
            draw.text((x_start, y_offset), f'计数: {self.counter}', 
                     font=font, fill=(255, 255, 255))
        except:
            draw.text((x_start, y_offset), f'Count: {self.counter}', 
                     font=font, fill=(255, 255, 255))
        
        # FPS
        y_offset += line_height
        draw.text((x_start, y_offset), f'FPS: {int(self.fps)}', 
                 font=font, fill=(255, 255, 255))
        
        # 转换回OpenCV格式
        frame_with_text = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
        return frame_with_text
    
    def calculate_angle(self, key_points, left_points_idx, right_points_idx):
        """计算关节角度"""
        def _calculate_angle(line1, line2):
            slope1 = math.atan2(line1[3] - line1[1], line1[2] - line1[0])
            slope2 = math.atan2(line2[3] - line2[1], line2[2] - line2[0])
            angle1 = math.degrees(slope1)
            angle2 = math.degrees(slope2)
            angle_diff = abs(angle1 - angle2)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            return angle_diff
        
        try:
            left_points = [[key_points.data[0][i][0], key_points.data[0][i][1]] for i in left_points_idx]
            right_points = [[key_points.data[0][i][0], key_points.data[0][i][1]] for i in right_points_idx]
            
            line1_left = [left_points[1][0].item(), left_points[1][1].item(),
                         left_points[0][0].item(), left_points[0][1].item()]
            line2_left = [left_points[1][0].item(), left_points[1][1].item(),
                         left_points[2][0].item(), left_points[2][1].item()]
            angle_left = _calculate_angle(line1_left, line2_left)
            
            line1_right = [right_points[1][0].item(), right_points[1][1].item(),
                          right_points[0][0].item(), right_points[0][1].item()]
            line2_right = [right_points[1][0].item(), right_points[1][1].item(),
                          right_points[2][0].item(), right_points[2][1].item()]
            angle_right = _calculate_angle(line1_right, line2_right)
            
            return (angle_left + angle_right) / 2
        except:
            return 0
            
    def process_video(self):
        """视频处理主循环"""
        while self.is_running and self.cap and self.cap.isOpened():
            if self.is_paused:
                time.sleep(0.05)
                continue
            ret, frame = self.cap.read()
            if not ret:
                break
                
            start_time = cv2.getTickCount()
            
            # 运行姿态检测（控制输入尺寸/设备/半精度/置信度以提升FPS）
            results = self.model.predict(
                frame,
                imgsz=self.imgsz,
                conf=self.conf_thres,
                device=self.device,
                half=self.use_half,
                verbose=False
            )
            
            if results[0].keypoints.shape[1] == 0:
                # 没有检测到人
                annotated_frame = frame
            else:
                # 自动识别运动类型（复用当前结果的关键点，避免二次推理）
                if self.auto_detect and self.detector_model:
                    try:
                        pose_data = results[0].keypoints.data[0, :, 0:2]
                        self.pose_key_point_frames.append(pose_data.tolist())
                    except Exception:
                        pass
                    
                    if len(self.pose_key_point_frames) == 5:
                        input_data = torch.tensor(self.pose_key_point_frames)
                        input_data = input_data.reshape(5, 17 * 2)
                        x_mean, x_std = torch.mean(input_data), torch.std(input_data)
                        input_data = (input_data - x_mean) / x_std
                        input_data = input_data.unsqueeze(dim=0)
                        input_data = input_data.to(self.detector_model.device)
                        rst_detector = self.detector_model(input_data)
                        idx = rst_detector.argmax().cpu().item()
                        detected_sport = self.idx_2_category[str(idx)]
                        if detected_sport in SPORT_CONFIG:
                            self.current_sport = detected_sport
                        del self.pose_key_point_frames[0]
                
                # 获取运动配置
                sport_config = SPORT_CONFIG[self.current_sport]
                
                # 计算角度
                # 根据侧别设置选择角度
                side_mode = sport_config.get('side_mode', 'avg')
                if side_mode == 'left':
                    angle = self.calculate_angle(
                        results[0].keypoints,
                        sport_config['left_points_idx'],
                        sport_config['left_points_idx']  # 只取左侧两段构线
                    )
                elif side_mode == 'right':
                    angle = self.calculate_angle(
                        results[0].keypoints,
                        sport_config['right_points_idx'],
                        sport_config['right_points_idx']
                    )
                else:
                    angle = self.calculate_angle(
                        results[0].keypoints,
                        sport_config['left_points_idx'],
                        sport_config['right_points_idx']
                    )
                
                # 角度平滑，降低抖动
                if self.prev_angle is None:
                    smooth_angle = angle
                else:
                    smooth_angle = 0.7 * self.prev_angle + 0.3 * angle
                self.prev_angle = smooth_angle

                # 使用阈值迟滞+方向自适配
                enter_thr = sport_config['maintaining']
                exit_thr = sport_config['relaxing']
                if enter_thr < exit_thr:
                    # 进入区：小于enter_thr；退出区：大于exit_thr（如深蹲/仰卧起坐）
                    if smooth_angle < enter_thr:
                        self.reaching = True
                    elif smooth_angle > exit_thr:
                        self.reaching = False
                else:
                    # 进入区：大于enter_thr；退出区：小于exit_thr（如俯卧撑）
                    if smooth_angle > enter_thr:
                        self.reaching = True
                    elif smooth_angle < exit_thr:
                        self.reaching = False

                # 去抖与计数逻辑
                if self.reaching:
                    self.reach_frames += 1
                else:
                    # 从到位状态退出且持续时间达标 -> 记一次
                    if self.reaching_last and self.reach_frames >= self.min_reach_frames:
                        self.counter += 1
                        # 累计到全局统计
                        sid = self.current_sport
                        self.total_counts[sid] = self.total_counts.get(sid, 0) + 1
                        self.todays_counts[sid] = self.todays_counts.get(sid, 0) + 1
                    self.reach_frames = 0

                self.reaching_last = self.reaching
                
                # 绘制结果（可选：降低绘制复杂度以提升FPS）
                try:
                    annotated_frame = results[0].plot()
                except Exception:
                    annotated_frame = frame
                
                # 可选：叠加角度/阈值辅助调参
                if self.show_angle:
                    plot_size_ratio = max(frame.shape[1] / 960, frame.shape[0] / 540)
                    txt = f"Angle: {smooth_angle:.1f}  Enter: {enter_thr}  Exit: {exit_thr}"
                    cv2.putText(annotated_frame, txt, (int(20 * plot_size_ratio), int(210 * plot_size_ratio)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6 * plot_size_ratio, (0, 255, 255),
                                thickness=int(2 * plot_size_ratio), lineType=cv2.LINE_AA)
                
            # 计算FPS（指数滑动平均，减少抖动）
            end_time = cv2.getTickCount()
            inst_fps = cv2.getTickFrequency() / (end_time - start_time)
            self.fps = inst_fps if self.fps == 0 else (0.9 * self.fps + 0.1 * inst_fps)

            # 添加信息文本（使用PIL支持中文）
            annotated_frame = self.draw_text_with_chinese(annotated_frame)
            
            # 保存视频
            if self.video_writer:
                self.video_writer.write(annotated_frame)
            
            # 更新显示
            self.update_video_display(annotated_frame)
            self.update_status_display()
            
        # 处理结束
        if self.is_running:
            self.root.after(0, self.stop_capture)
            
    def update_video_display(self, frame):
        """更新视频显示"""
        try:
            # 转换颜色空间
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 调整大小以适应显示区域
            label_width = self.video_label.winfo_width()
            label_height = self.video_label.winfo_height()
            
            if label_width > 1 and label_height > 1:
                h, w = frame_rgb.shape[:2]
                scale = min(label_width / w, label_height / h)
                new_w, new_h = int(w * scale), int(h * scale)
                frame_rgb = cv2.resize(frame_rgb, (new_w, new_h))
            
            # 转换为PIL Image
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(image=img)
            
            # 更新显示
            self.video_label.configure(image=img_tk, text='')
            self.video_label.image = img_tk
        except Exception as e:
            print(f"显示更新错误: {e}")
            
    def update_status_display(self):
        """更新状态显示"""
        try:
            self.counter_label.config(text=str(self.counter))
            self.fps_label.config(text=f"{int(self.fps)}")
            if self.auto_detect:
                sport_name = SPORT_CONFIG[self.current_sport]['name']
                self.current_sport_label.config(text=sport_name)
            # 更新统计面板
            for sid, lbl in self.stat_labels.items():
                lbl.config(text=str(self.total_counts.get(sid, 0)))
            # 今日进度与PB
            for sid, pb in self.pb_by_sport.items():
                pb['maximum'] = max(1, self.goals[sid])
                pb['value'] = min(self.goals[sid], self.todays_counts.get(sid, 0))
            for sid, lbl in self.goal_label_by_sport.items():
                lbl.config(text=str(self.todays_counts.get(sid, 0)))
            # 打卡与连击
            self.checkin_status_label.config(text=("已打卡" if self.checked_in else "未打卡"),
                                             foreground=('green' if self.checked_in else 'red'))
            self.streak_label.config(text=str(self.streak_days))
        except Exception as e:
            print(f"状态更新错误: {e}")
            
    def on_closing(self):
        """关闭窗口时的处理"""
        if self.is_running:
            self.stop_capture()
        # 退出时保存配置与历史
        try:
            self.save_history()
        except Exception:
            pass
        self.root.destroy()

    def reset_stats(self):
        """清空统计"""
        self.total_counts = {k: 0 for k in SPORT_CONFIG.keys()}
        self.counter = 0
        self.todays_counts = {k: 0 for k in SPORT_CONFIG.keys()}
        self.checked_in = False

    def toggle_pause(self):
        """暂停/继续"""
        if not self.is_running:
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.config(text="▶ 继续", style='Start.TButton')
        else:
            self.pause_button.config(text="⏸ 暂停/继续", style='Pause.TButton')


def main():
    """主函数"""
    root = tk.Tk()
    app = ExerciseCounterApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == '__main__':
    main()

