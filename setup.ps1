# PowerShell 自动部署脚本
# Exercise Counter with YOLOv8 on NVIDIA Jetson

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "运动计数器 YOLOv8 自动部署脚本" -ForegroundColor Cyan
Write-Host "Exercise Counter with YOLOv8" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python是否已安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[信息] 检测到Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到Python！请先安装Python 3.8或更高版本" -ForegroundColor Red
    Write-Host "[错误] Python not found! Please install Python 3.8 or higher" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}

Write-Host ""

# 检查虚拟环境是否已存在
if (Test-Path "venv") {
    Write-Host "[警告] 虚拟环境已存在！" -ForegroundColor Yellow
    $choice = Read-Host "是否删除现有环境并重新创建？(Y/N)"
    if ($choice -eq "Y" -or $choice -eq "y") {
        Write-Host "[信息] 删除现有虚拟环境..." -ForegroundColor Yellow
        Remove-Item -Path "venv" -Recurse -Force
    } else {
        Write-Host "[信息] 使用现有虚拟环境" -ForegroundColor Green
        & "venv\Scripts\Activate.ps1"
        Write-Host ""
        goto SkipCreate
    }
}

# 创建虚拟环境
Write-Host "[信息] 正在创建虚拟环境..." -ForegroundColor Yellow
python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 虚拟环境创建失败！" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}
Write-Host "[成功] 虚拟环境创建完成" -ForegroundColor Green
Write-Host ""

:SkipCreate
# 激活虚拟环境
Write-Host "[信息] 激活虚拟环境..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 虚拟环境激活失败！" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}
Write-Host ""

# 升级pip
Write-Host "[信息] 升级pip到最新版本..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host ""

# 检查CUDA是否可用
Write-Host "[信息] 检测CUDA支持..." -ForegroundColor Yellow
python -c "import torch; print('CUDA可用' if torch.cuda.is_available() else 'CUDA不可用')" 2>$null
Write-Host ""

# 安装依赖
Write-Host "[信息] 安装项目依赖..." -ForegroundColor Yellow
Write-Host "[信息] 这可能需要几分钟时间，请耐心等待..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 依赖安装失败！" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}
Write-Host ""

# 验证关键依赖
Write-Host "[信息] 验证关键依赖安装..." -ForegroundColor Yellow
Write-Host ""

$dependencies = @(
    @{Name="PyTorch"; Import="torch"; Version="torch.__version__"},
    @{Name="OpenCV"; Import="cv2"; Version="cv2.__version__"},
    @{Name="NumPy"; Import="numpy"; Version="numpy.__version__"},
    @{Name="Ultralytics"; Import="ultralytics"; Version="ultralytics.__version__"}
)

foreach ($dep in $dependencies) {
    try {
        $version = python -c "import $($dep.Import); print($($dep.Version))" 2>&1
        Write-Host "✓ $($dep.Name)版本: $version" -ForegroundColor Green
    } catch {
        Write-Host "[错误] $($dep.Name)未正确安装" -ForegroundColor Red
        Read-Host "按Enter键退出"
        exit 1
    }
}

Write-Host ""

# 检查CUDA
Write-Host "[信息] CUDA检测：" -ForegroundColor Yellow
python -c "import torch; print('CUDA可用：', torch.cuda.is_available()); print('CUDA设备数量：', torch.cuda.device_count()) if torch.cuda.is_available() else None; print('CUDA版本：', torch.version.cuda) if torch.cuda.is_available() else None"
Write-Host ""

# 检查模型文件
Write-Host "[信息] 检查模型文件..." -ForegroundColor Yellow
if (Test-Path "for_detect\checkpoint\best_model.pt") {
    Write-Host "✓ 检测模型存在: for_detect\checkpoint\best_model.pt" -ForegroundColor Green
} else {
    Write-Host "[警告] 检测模型不存在: for_detect\checkpoint\best_model.pt" -ForegroundColor Yellow
    Write-Host "[提示] 请运行训练脚本生成模型或从其他地方获取" -ForegroundColor Yellow
}

if (Test-Path "yolov8s-pose.pt") {
    Write-Host "✓ YOLOv8姿态模型存在: yolov8s-pose.pt" -ForegroundColor Green
} else {
    Write-Host "[警告] YOLOv8姿态模型不存在: yolov8s-pose.pt" -ForegroundColor Yellow
    Write-Host "[提示] 首次运行时，Ultralytics会自动下载该模型" -ForegroundColor Yellow
}
Write-Host ""

# 完成
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[成功] 环境配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "使用说明：" -ForegroundColor Yellow
Write-Host "1. 激活虚拟环境: venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. 启动桌面程序: python app.py" -ForegroundColor White
Write-Host "3. 命令行演示: python demo.py --input 0" -ForegroundColor White
Write-Host "4. 完整版: python demo_pro.py --input your_video.mp4" -ForegroundColor White
Write-Host "5. 训练模型: python for_detect\train.py" -ForegroundColor White
Write-Host ""
Write-Host "注意：退出虚拟环境请输入 deactivate" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "按Enter键退出"

