# 健身检测系统 Fitness Tracker (YOLOv8)

![演示](https://github.com/yuyoujiang/exercise-counting-with-YOLOv8/assets/76863444/d592ff9b-6bc2-4017-8731-cf408052f0dd)

基于YOLOv8-Pose的实时运动计数应用，支持深蹲、俯卧撑、仰卧起坐等运动类型的自动识别和计数。

## ✨ 功能特点

- 🖥️ **全新GUI桌面程序** - 图形界面操作，简单直观
- 🎯 实时姿态检测与运动计数
- 🏋️ 支持多种运动类型（深蹲/俯卧撑/仰卧起坐）
- 🤖 智能自动识别运动类型
- 🎥 支持摄像头和视频文件输入
- 🚀 可选GPU加速支持
- 💾 实时预览和结果保存功能

## 🚀 快速开始

### 方式一：GUI桌面程序（推荐）⭐

1. **环境检查**
```bash
python check_system.py
```

2. **自动安装**
```bash
setup.bat          # Windows
./setup.sh         # Linux/macOS
```

3. **启动桌面程序**
```bash
# 激活虚拟环境
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/macOS

# 运行GUI桌面程序
python app.py
```

### 方式二：命令行程序

```bash
# 使用摄像头进行深蹲计数
python demo.py --input 0 --sport squat

# 自动识别运动类型（完整版）
python demo_pro.py --input 0
```

## 📖 使用示例

### 基础版（单一运动类型）
```bash
# 深蹲计数
python demo.py --input 0 --sport squat

# 俯卧撑计数（使用视频）
python demo.py --input video.mp4 --sport pushup

# 仰卧起坐计数并保存结果
python demo.py --input 0 --sport sit-up --save_dir ./output
```

### 完整版（自动识别运动类型）
```bash
# 摄像头自动识别
python demo_pro.py --input 0

# 处理视频文件
python demo_pro.py --input video.mp4 --save_dir ./results
```

## 📊 支持的运动类型

| 运动类型 | 参数名 | 说明 |
|---------|--------|------|
| 深蹲 | `squat` | Squats |
| 俯卧撑 | `pushup` | Push-ups |
| 仰卧起坐 | `sit-up` | Sit-ups |

## 💻 系统要求

- Python 3.8+
- 8GB RAM（推荐16GB）
- 5GB 磁盘空间
- NVIDIA GPU（可选，用于加速）

## 📚 文档

- **快速上手**: 参考上方"快速开始"部分
- **详细指南**: 查看 [Guidance.md](Guidance.md)
- **自动化脚本**: `setup.bat` / `setup.sh` / `check_system.py`

## 🔧 主要参数

### demo.py
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--input` | 0 | 输入源（0=摄像头，或视频路径） |
| `--sport` | squat | 运动类型 |
| `--model` | yolov8s-pose.pt | 模型路径 |
| `--save_dir` | None | 结果保存路径 |

### demo_pro.py
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--input` | 0 | 输入源 |
| `--model` | yolov8s-pose.pt | YOLOv8模型路径 |
| `--detector_model` | ./for_detect/checkpoint/ | 检测模型路径 |
| `--save_dir` | None | 结果保存路径 |

## 🛠️ 项目结构

```
├── app.py                    # 🆕 GUI桌面程序（推荐）
├── demo.py                   # 命令行基础版
├── demo_pro.py               # 命令行完整版
├── check_system.py           # 系统检查脚本
├── setup.bat                 # Windows安装脚本
├── setup.sh                  # Linux/macOS安装脚本
├── requirements.txt          # 依赖列表
├── Guidance.md               # 详细指导文档
└── for_detect/               # 运动检测模块
    ├── train.py              # 训练脚本
    ├── Inference.py          # 推理脚本
    └── checkpoint/           # 模型文件
```

## ❓ 常见问题

**Q: 摄像头无法打开？**  
A: 尝试修改 `--input 1` 或 `--input 2`，检查摄像头是否被占用

**Q: 程序运行很慢？**  
A: 安装CUDA版PyTorch，或使用更小的模型 `yolov8n-pose.pt`

**Q: CUDA不可用？**  
A: 安装对应版本的PyTorch：
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

更多问题请查看 [Guidance.md](Guidance.md)

## 📄 许可证

本项目采用 MIT 许可证

## 🙏 参考项目

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [Seeed Studio Wiki](https://wiki.seeedstudio.com/YOLOv8-DeepStream-TRT-Jetson/)

## 🎉 开始使用

```bash
# 1. 检查环境
python check_system.py

# 2. 运行安装
setup.bat  # Windows

# 3. 激活环境
venv\Scripts\activate

# 4. 开始计数
python demo.py --input 0 --sport squat
```

**详细文档请查看 [Guidance.md](Guidance.md)** 📖
