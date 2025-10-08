# 运动计数器 YOLOv8 - 完整指导文档

## 📋 目录
1. [系统要求](#系统要求)
2. [安装部署](#安装部署)
3. [使用指南](#使用指南)
4. [训练自定义模型](#训练自定义模型)
5. [参数详解](#参数详解)
6. [问题排查](#问题排查)
7. [性能优化](#性能优化)
8. [部署检查清单](#部署检查清单)

---

## 系统要求

### 硬件要求
- **CPU**: 现代多核处理器
- **内存**: 至少 8GB RAM（推荐 16GB）
- **GPU**: NVIDIA GPU（可选，用于加速）
  - 推荐: GTX 1060 或更高
  - 需要: CUDA 11.0+
- **磁盘空间**: 至少 5GB 可用空间

### 软件要求
- **操作系统**: 
  - Windows 10/11
  - Linux (Ubuntu 18.04+)
  - macOS (实验性支持)
- **Python**: 3.8 - 3.11（推荐 3.9）
- **CUDA**: 11.0+ （GPU用户）

### 主要依赖
- `torch>=2.0.0` - PyTorch深度学习框架
- `torchvision>=0.15.0` - PyTorch视觉库
- `ultralytics>=8.0.0` - YOLOv8实现
- `opencv-python>=4.8.0` - 计算机视觉库
- `numpy>=1.24.0` - 数值计算库

---

## 安装部署

### 方法一：自动安装（推荐）

#### Windows用户

**选项A - 批处理脚本（最简单）：**
双击运行 `setup.bat` 文件

**选项B - PowerShell脚本：**
```powershell
# 如果遇到执行策略限制
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 运行脚本
.\setup.ps1
```

#### Linux/macOS用户
```bash
# 添加执行权限
chmod +x setup.sh

# 运行脚本
./setup.sh
```

自动安装脚本会完成以下操作：
- ✅ 检测Python版本
- ✅ 创建虚拟环境
- ✅ 安装所有依赖
- ✅ 验证安装状态
- ✅ 检测CUDA支持
- ✅ 检查模型文件

### 方法二：手动安装

#### 1. 创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

#### 2. 升级pip
```bash
python -m pip install --upgrade pip
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 验证安装
```bash
python check_system.py
```

### GPU支持安装（可选）

#### 检查CUDA版本
```bash
nvidia-smi
```

#### 安装对应的PyTorch
访问 [PyTorch官网](https://pytorch.org/get-started/locally/) 选择合适版本。

例如，CUDA 11.8:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

CUDA 12.1:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

---

## 使用指南

### 1. 环境激活

每次使用前需要激活虚拟环境：

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 2. 基础版使用 (demo.py)

适用于单一运动类型的计数。

#### 基本语法
```bash
python demo.py --input <输入源> --sport <运动类型> [其他参数]
```

#### 使用示例

**摄像头实时计数：**
```bash
# 深蹲计数
python demo.py --input 0 --sport squat

# 俯卧撑计数
python demo.py --input 0 --sport pushup

# 仰卧起坐计数
python demo.py --input 0 --sport sit-up
```

**视频文件处理：**
```bash
# 处理视频文件
python demo.py --input video.mp4 --sport squat

# 保存处理结果
python demo.py --input video.mp4 --sport pushup --save_dir ./output
```

**使用不同模型：**
```bash
# 使用更小的模型（速度快）
python demo.py --input 0 --sport squat --model yolov8n-pose.pt

# 使用更大的模型（精度高）
python demo.py --input 0 --sport squat --model yolov8m-pose.pt
```

### 3. 完整版使用 (demo_pro.py)

自动识别运动类型并计数。

#### 基本语法
```bash
python demo_pro.py --input <输入源> [其他参数]
```

#### 使用示例

**自动识别运动类型：**
```bash
# 使用摄像头
python demo_pro.py --input 0

# 处理视频文件
python demo_pro.py --input workout.mp4

# 保存结果
python demo_pro.py --input video.mp4 --save_dir ./results
```

**自定义模型路径：**
```bash
python demo_pro.py \
    --input video.mp4 \
    --model yolov8m-pose.pt \
    --detector_model ./for_detect/checkpoint/
```

### 4. 操作控制

运行程序时：
- **Q键** - 退出程序
- **Ctrl+C** - 强制停止

### 5. 退出虚拟环境
```bash
deactivate
```

---

## 训练自定义模型

如果您想训练识别更多运动类型或提高识别准确度，可以训练自定义模型。

### 1. 数据准备

#### 从视频提取关键点数据
```bash
python for_detect/get_data_from_video.py
```

#### 数据组织结构
```
for_detect/data/
├── squat/
│   ├── 001.csv
│   ├── 002.csv
│   └── ...
├── pushup/
│   ├── 001.csv
│   └── ...
└── situp/
    ├── 001.csv
    └── ...
```

每个CSV文件包含5帧的17个关键点坐标数据。

### 2. 模型训练

#### 使用默认参数训练
```bash
python for_detect/train.py
```

#### 自定义训练参数
```bash
python for_detect/train.py \
    --data_path ./for_detect/data \
    --batch_size 8 \
    --epoch 200 \
    --device cuda:0 \
    --save_dir ./for_detect/checkpoint
```

#### 训练参数说明
- `--data_path`: 训练数据路径
- `--batch_size`: 批次大小（根据显存调整）
- `--epoch`: 训练轮数
- `--device`: 训练设备（cuda:0 或 cpu）
- `--save_dir`: 模型保存路径

### 3. 模型测试

```bash
python for_detect/Inference.py \
    --input test_video.mp4 \
    --checkpoint ./for_detect/checkpoint/
```

---

## 参数详解

### demo.py 完整参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--model` | str | yolov8s-pose.pt | YOLOv8姿态模型路径 |
| `--sport` | str | squat | 运动类型 (squat/pushup/sit-up) |
| `--input` | str | 0 | 输入源（0=摄像头，或视频文件路径） |
| `--save_dir` | str | None | 结果保存路径 |
| `--show` | bool | True | 是否显示实时画面 |

**运动类型参数值：**
- `squat` - 深蹲
- `pushup` - 俯卧撑
- `sit-up` - 仰卧起坐

**输入源参数：**
- `0` - 默认摄像头
- `1`, `2` - 其他摄像头
- `path/to/video.mp4` - 视频文件路径

### demo_pro.py 完整参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--model` | str | yolov8s-pose.pt | YOLOv8姿态模型路径 |
| `--detector_model` | str | ./for_detect/checkpoint/ | 运动检测模型路径 |
| `--sport` | list | [squat, situp, pushup] | 支持的运动类型列表 |
| `--input` | str | - | 输入源（必需参数） |
| `--save_dir` | str | None | 结果保存路径 |
| `--show` | bool | True | 是否显示实时画面 |

### train.py 完整参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--device` | str | cuda:0 | 训练设备 (cuda:0 或 cpu) |
| `--data_path` | str | ./data_without_resize | 训练数据路径 |
| `--batch_size` | int | 4 | 批次大小 |
| `--epoch` | int | 150 | 训练轮数 |
| `--save_dir` | str | ./checkpoint/without_resize | 模型保存路径 |

### YOLOv8模型选择

| 模型 | 大小 | 速度 | 精度 | 使用场景 |
|------|------|------|------|----------|
| yolov8n-pose.pt | 最小 | 最快 | 中等 | CPU或低端GPU |
| yolov8s-pose.pt | 小 | 快 | 良好 | 平衡性能（推荐） |
| yolov8m-pose.pt | 中 | 中等 | 很好 | 高端GPU |
| yolov8l-pose.pt | 大 | 慢 | 优秀 | 服务器部署 |
| yolov8x-pose.pt | 最大 | 最慢 | 最佳 | 离线处理 |

---

## 问题排查

### 安装问题

#### Q1: Python未找到
**错误信息：**
```
'python' 不是内部或外部命令
```

**解决方法：**
1. 重新安装Python，勾选"Add Python to PATH"
2. 或手动添加Python到系统环境变量
3. 重启命令行窗口

#### Q2: pip安装速度很慢
**解决方法：**
使用国内镜像源：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

其他镜像源：
```bash
# 阿里云
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 清华大学
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 中国科技大学
pip install -r requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple/
```

#### Q3: 虚拟环境激活失败（PowerShell）
**错误信息：**
```
无法加载文件 activate.ps1
```

**解决方法：**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Q4: OpenCV导入错误
**错误信息：**
```
ImportError: DLL load failed
```

**解决方法：**
```bash
pip uninstall opencv-python opencv-python-headless
pip install opencv-python
```

### CUDA/GPU问题

#### Q5: CUDA不可用
**检查方法：**
```bash
# 检查NVIDIA驱动
nvidia-smi

# 检查PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

**解决方法：**

1. **确认NVIDIA驱动已安装**
   ```bash
   nvidia-smi
   ```

2. **安装CUDA Toolkit**
   - 访问 [NVIDIA官网](https://developer.nvidia.com/cuda-downloads)
   - 下载对应版本的CUDA

3. **安装支持CUDA的PyTorch**
   ```bash
   # 先卸载CPU版本
   pip uninstall torch torchvision
   
   # 安装CUDA版本（根据您的CUDA版本选择）
   # CUDA 11.8
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   
   # CUDA 12.1
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   ```

#### Q6: GPU内存不足
**错误信息：**
```
CUDA out of memory
```

**解决方法：**
1. 使用更小的模型：`--model yolov8n-pose.pt`
2. 降低输入分辨率
3. 关闭其他占用GPU的程序

### 运行问题

#### Q7: 摄像头无法打开
**错误信息：**
```
Unable to open camera
```

**解决方法：**
1. 尝试不同的摄像头索引：
   ```bash
   python demo.py --input 1 --sport squat
   python demo.py --input 2 --sport squat
   ```

2. 检查摄像头是否被占用（关闭其他使用摄像头的程序）

3. Windows用户检查隐私设置：
   - 设置 → 隐私 → 相机 → 允许应用访问相机

#### Q8: 模型文件不存在
**错误信息：**
```
Model file not found
```

**解决方法：**

1. **YOLOv8模型**：首次运行时会自动下载
   
2. **检测模型**：需要训练生成
   ```bash
   python for_detect/train.py
   ```

3. 确保文件路径正确：
   ```
   for_detect/checkpoint/best_model.pt
   for_detect/checkpoint/idx_2_category.json
   ```

#### Q9: 计数不准确
**可能原因和解决方法：**

1. **身体不完整**：确保整个身体在画面中
2. **光照不足**：改善照明条件
3. **动作不标准**：调整运动姿势使其更加标准
4. **阈值不合适**：调整代码中的角度阈值
5. **模型需要重新训练**：使用更多数据重新训练

#### Q10: 程序运行很慢
**优化方法：**

1. **使用GPU加速**（最有效）
   ```bash
   # 安装CUDA版PyTorch
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

2. **使用更小的模型**
   ```bash
   python demo.py --input 0 --sport squat --model yolov8n-pose.pt
   ```

3. **降低输入分辨率**（修改代码中的resize参数）

4. **使用TensorRT优化**（高级）
   ```bash
   yolo export model=yolov8s-pose.pt format=engine device=0
   ```

### 依赖冲突问题

#### Q11: NumPy版本冲突
**解决方法：**
```bash
pip install numpy==1.24.0
```

#### Q12: PyTorch版本冲突
**解决方法：**
```bash
pip uninstall torch torchvision
pip install torch>=2.0.0 torchvision>=0.15.0
```

---

## 性能优化

### 性能基准

#### CPU模式（推荐配置）
| 模型 | FPS | 使用场景 |
|------|-----|----------|
| yolov8n-pose | 15-25 | 快速原型 |
| yolov8s-pose | 10-15 | 平衡性能 |
| yolov8m-pose | 5-10 | 高精度需求 |

#### GPU模式（GTX 1060）
| 模型 | FPS | 使用场景 |
|------|-----|----------|
| yolov8n-pose | 60-80 | 实时应用 |
| yolov8s-pose | 40-60 | 推荐配置 |
| yolov8m-pose | 25-35 | 高精度 |

#### GPU模式（RTX 3060）
| 模型 | FPS | 使用场景 |
|------|-----|----------|
| yolov8n-pose | 100+ | 多路视频 |
| yolov8s-pose | 80-100 | 高帧率 |
| yolov8m-pose | 50-70 | 最佳平衡 |

### 优化建议

#### 1. 模型选择
- **CPU用户**：使用 yolov8n-pose.pt
- **入门GPU**：使用 yolov8s-pose.pt
- **高端GPU**：使用 yolov8m-pose.pt

#### 2. 分辨率优化
在代码中调整resize参数：
```python
# demo_pro.py 第256行
pose_frame = cv2.resize(frame, (512, 512), interpolation=cv2.INTER_CUBIC)

# 可以调整为更小的分辨率以提高速度
pose_frame = cv2.resize(frame, (416, 416), interpolation=cv2.INTER_CUBIC)
```

#### 3. TensorRT加速（高级）
```bash
# 导出TensorRT模型（需要GPU）
yolo export model=yolov8s-pose.pt format=engine device=0

# FP16精度（速度更快）
yolo export model=yolov8s-pose.pt format=engine half=True device=0
```

---

## 部署检查清单

### ✅ 部署前检查

#### 系统要求
- [ ] Python 3.8+ 已安装
- [ ] Python 已添加到系统PATH
- [ ] 至少 5GB 可用磁盘空间
- [ ] 至少 8GB RAM

#### GPU要求（可选）
- [ ] NVIDIA GPU（GTX 1060或更高）
- [ ] CUDA 11.0+ 已安装
- [ ] NVIDIA驱动已正确安装

### ✅ 安装步骤检查

#### 1. 环境检查
```bash
python check_system.py
```
- [ ] Python版本检查通过（3.8+）
- [ ] 系统信息显示正确
- [ ] 磁盘空间充足

#### 2. 虚拟环境
- [ ] 虚拟环境 `venv/` 已创建
- [ ] 虚拟环境成功激活
- [ ] pip 已升级到最新版本

#### 3. 依赖安装
- [ ] PyTorch >= 2.0.0
- [ ] TorchVision >= 0.15.0
- [ ] Ultralytics >= 8.0.0
- [ ] OpenCV >= 4.8.0
- [ ] NumPy >= 1.24.0

验证命令：
```bash
pip list | findstr torch     # Windows
pip list | grep torch        # Linux/macOS
```

#### 4. GPU检查（可选）
```bash
python -c "import torch; print(torch.cuda.is_available())"
```
- [ ] CUDA可用状态为 True
- [ ] 显示GPU设备信息

#### 5. 模型文件
- [ ] `for_detect/checkpoint/best_model.pt` 存在
- [ ] `for_detect/checkpoint/idx_2_category.json` 存在
- [ ] YOLOv8模型存在或将自动下载

### ✅ 功能测试

#### 测试1: 基础导入
```bash
python -c "import torch, cv2, numpy, ultralytics; print('导入成功')"
```
- [ ] 所有模块导入成功

#### 测试2: 帮助信息
```bash
python demo.py --help
python demo_pro.py --help
```
- [ ] 帮助信息正确显示
- [ ] 无导入错误

#### 测试3: 实际运行
```bash
python demo.py --input 0 --sport squat
```
- [ ] 程序启动成功
- [ ] 姿态检测正常
- [ ] 计数功能正常
- [ ] 能正常退出（按q键）

### ✅ 部署成功标准

#### 必需项
- [x] Python环境正确安装
- [x] 虚拟环境创建成功
- [x] 所有依赖包安装完成
- [x] 程序能够正常启动

#### 功能项
- [ ] 摄像头/视频输入正常
- [ ] 姿态检测功能正常
- [ ] 计数功能正确
- [ ] 界面显示正常

#### 可选项（GPU用户）
- [ ] CUDA正确识别
- [ ] GPU加速启用
- [ ] 推理速度 >30 FPS

---

## 附录

### A. 运动检测原理

YOLOv8-Pose模型可以检测17个人体关键点：

```
0: 鼻子      9: 左手腕
1: 左眼      10: 右手腕
2: 右眼      11: 左髋
3: 左耳      12: 右髋
4: 右耳      13: 左膝
5: 左肩      14: 右膝
6: 右肩      15: 左踝
7: 左肘      16: 右踝
8: 右肘
```

通过计算关键点连线的角度来判断运动状态：
- **深蹲**：测量髋-膝-踝角度
- **俯卧撑**：测量肩-肘-腕角度
- **仰卧起坐**：测量肩-髋-膝角度

### B. 文件说明

#### 配置文件
- `requirements.txt` - Python依赖列表
- `for_detect/checkpoint/idx_2_category.json` - 运动类型映射

#### 脚本文件
- `check_system.py` - 系统环境检查
- `setup.bat` - Windows自动安装
- `setup.ps1` - PowerShell安装
- `setup.sh` - Linux/macOS安装

#### 程序文件
- `demo.py` - 基础版（单运动类型）
- `demo_pro.py` - 完整版（自动识别）
- `for_detect/train.py` - 模型训练
- `for_detect/Inference.py` - 推理测试
- `for_detect/get_data_from_video.py` - 数据提取

### C. 常用命令速查

```bash
# 环境管理
python check_system.py                    # 检查系统
setup.bat                                 # Windows安装
venv\Scripts\activate                     # 激活环境（Windows）
source venv/bin/activate                  # 激活环境（Linux）
deactivate                                # 退出环境

# 基础使用
python demo.py --input 0 --sport squat    # 摄像头深蹲
python demo.py --input video.mp4 --sport pushup  # 视频俯卧撑
python demo_pro.py --input 0              # 自动识别

# 模型训练
python for_detect/train.py                # 训练模型
python for_detect/Inference.py            # 测试模型

# 依赖管理
pip install -r requirements.txt           # 安装依赖
pip list                                  # 查看已安装
pip install --upgrade ultralytics         # 更新包
```

### D. 技术支持

如需更多帮助：

1. **运行系统检查**：`python check_system.py`
2. **查看错误日志**：注意错误堆栈信息
3. **查阅官方文档**：
   - [Ultralytics文档](https://docs.ultralytics.com/)
   - [PyTorch文档](https://pytorch.org/docs/)
4. **提交Issue**：访问项目GitHub仓库

---

**文档版本**: v1.0  
**最后更新**: 2024年

**祝您使用愉快！如有问题，欢迎反馈。** 🎉

