@echo off
chcp 65001
echo ========================================
echo 运动计数器 YOLOv8 自动部署脚本
echo Exercise Counter with YOLOv8
echo ========================================
echo.

:: 检查Python是否已安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python！请先安装Python 3.8或更高版本
    echo [错误] Python not found! Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo [信息] 检测到Python版本：
python --version
echo.

:: 检查虚拟环境是否已存在
if exist "venv\" (
    echo [警告] 虚拟环境已存在！
    set /p choice="是否删除现有环境并重新创建？(Y/N): "
    if /i "%choice%"=="Y" (
        echo [信息] 删除现有虚拟环境...
        rmdir /s /q venv
    ) else (
        echo [信息] 使用现有虚拟环境
        goto :activate_venv
    )
)

:: 创建虚拟环境
echo [信息] 正在创建虚拟环境...
python -m venv venv
if %errorlevel% neq 0 (
    echo [错误] 虚拟环境创建失败！
    pause
    exit /b 1
)
echo [成功] 虚拟环境创建完成
echo.

:activate_venv
:: 激活虚拟环境
echo [信息] 激活虚拟环境...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [错误] 虚拟环境激活失败！
    pause
    exit /b 1
)
echo.

:: 升级pip
echo [信息] 升级pip到最新版本...
python -m pip install --upgrade pip
echo.

:: 检查CUDA是否可用
echo [信息] 检测CUDA支持...
python -c "import torch; print('CUDA可用' if torch.cuda.is_available() else 'CUDA不可用')" 2>nul
if %errorlevel% neq 0 (
    echo [信息] PyTorch未安装，将在下一步安装
)
echo.

:: 安装依赖
echo [信息] 安装项目依赖...
echo [信息] 这可能需要几分钟时间，请耐心等待...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败！
    pause
    exit /b 1
)
echo.

:: 验证关键依赖
echo [信息] 验证关键依赖安装...
echo.

python -c "import torch; print('✓ PyTorch版本:', torch.__version__)"
if %errorlevel% neq 0 (
    echo [错误] PyTorch未正确安装
    pause
    exit /b 1
)

python -c "import cv2; print('✓ OpenCV版本:', cv2.__version__)"
if %errorlevel% neq 0 (
    echo [错误] OpenCV未正确安装
    pause
    exit /b 1
)

python -c "import numpy; print('✓ NumPy版本:', numpy.__version__)"
if %errorlevel% neq 0 (
    echo [错误] NumPy未正确安装
    pause
    exit /b 1
)

python -c "import ultralytics; print('✓ Ultralytics版本:', ultralytics.__version__)"
if %errorlevel% neq 0 (
    echo [错误] Ultralytics未正确安装
    pause
    exit /b 1
)
echo.

:: 检查CUDA
echo [信息] CUDA检测：
python -c "import torch; print('CUDA可用：', torch.cuda.is_available()); print('CUDA设备数量：', torch.cuda.device_count()) if torch.cuda.is_available() else None; print('CUDA版本：', torch.version.cuda) if torch.cuda.is_available() else None"
echo.

:: 检查模型文件
echo [信息] 检查模型文件...
if exist "for_detect\checkpoint\best_model.pt" (
    echo ✓ 检测模型存在: for_detect\checkpoint\best_model.pt
) else (
    echo [警告] 检测模型不存在: for_detect\checkpoint\best_model.pt
    echo [提示] 请运行训练脚本生成模型或从其他地方获取
)

if exist "yolov8s-pose.pt" (
    echo ✓ YOLOv8姿态模型存在: yolov8s-pose.pt
) else (
    echo [警告] YOLOv8姿态模型不存在: yolov8s-pose.pt
    echo [提示] 首次运行时，Ultralytics会自动下载该模型
)
echo.

:: 完成
echo ========================================
echo [成功] 环境配置完成！
echo ========================================
echo.
echo 使用说明：
echo 1. 激活虚拟环境: venv\Scripts\activate
echo 2. 启动桌面程序: python app.py
echo 3. 命令行演示: python demo.py --input 0
echo 4. 完整版: python demo_pro.py --input your_video.mp4
echo 5. 训练模型: python for_detect\train.py
echo.
echo 注意：退出虚拟环境请输入 deactivate
echo ========================================
pause

