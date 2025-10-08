"""
系统环境检查脚本
System Environment Check Script
检查当前系统是否满足项目运行要求
"""

import sys
import platform
import subprocess
import os

# 设置UTF-8编码（Windows兼容性）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    # 设置控制台代码页为UTF-8
    os.system('chcp 65001 > nul')


def print_separator(title=""):
    """打印分隔线"""
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def check_python_version():
    """检查Python版本"""
    print_separator("Python版本检查")
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("[X] Python版本过低！需要Python 3.8或更高版本")
        return False
    else:
        print("[OK] Python版本符合要求")
        return True


def check_system_info():
    """检查系统信息"""
    print_separator("系统信息")
    print(f"操作系统: {platform.system()}")
    print(f"系统版本: {platform.release()}")
    print(f"处理器: {platform.processor()}")
    print(f"架构: {platform.machine()}")


def check_package(package_name, import_name=None):
    """检查单个包是否已安装"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', '未知版本')
        print(f"[OK] {package_name}: {version}")
        return True
    except ImportError:
        print(f"[X] {package_name}: 未安装")
        return False


def check_dependencies():
    """检查依赖包"""
    print_separator("依赖包检查")
    
    packages = [
        ("PyTorch", "torch"),
        ("TorchVision", "torchvision"),
        ("NumPy", "numpy"),
        ("OpenCV", "cv2"),
        ("Ultralytics", "ultralytics"),
        ("Pillow", "PIL"),
        ("Matplotlib", "matplotlib"),
        ("SciPy", "scipy"),
        ("tkcalendar", "tkcalendar"),
    ]
    
    all_installed = True
    for pkg_name, import_name in packages:
        if not check_package(pkg_name, import_name):
            all_installed = False
    
    return all_installed


def check_cuda():
    """检查CUDA支持"""
    print_separator("GPU/CUDA检查")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            print(f"[OK] CUDA可用")
            print(f"  CUDA版本: {torch.version.cuda}")
            print(f"  cuDNN版本: {torch.backends.cudnn.version()}")
            print(f"  GPU数量: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                print(f"\n  GPU {i}: {props.name}")
                print(f"    显存: {props.total_memory / 1024**3:.2f} GB")
                print(f"    计算能力: {props.major}.{props.minor}")
        else:
            print("[!] CUDA不可用，将使用CPU运行")
            print("  如需GPU加速，请安装支持CUDA的PyTorch版本")
    except ImportError:
        print("[X] PyTorch未安装，无法检测CUDA")


def check_models():
    """检查模型文件"""
    print_separator("模型文件检查")
    
    import os
    
    models = [
        "yolov8s-pose.pt",
        "for_detect/checkpoint/best_model.pt",
        "for_detect/checkpoint/idx_2_category.json"
    ]
    
    for model_path in models:
        if os.path.exists(model_path):
            size = os.path.getsize(model_path) / (1024 * 1024)
            print(f"[OK] {model_path} ({size:.2f} MB)")
        else:
            print(f"[X] {model_path} (不存在)")


def check_disk_space():
    """检查磁盘空间"""
    print_separator("磁盘空间检查")
    
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        
        print(f"总空间: {total / (1024**3):.2f} GB")
        print(f"已使用: {used / (1024**3):.2f} GB")
        print(f"可用空间: {free / (1024**3):.2f} GB")
        
        if free < 5 * 1024**3:  # 少于5GB
            print("[!] 警告：可用磁盘空间不足5GB")
        else:
            print("[OK] 磁盘空间充足")
    except Exception as e:
        print(f"[X] 无法检查磁盘空间: {e}")


def test_imports():
    """测试关键模块导入"""
    print_separator("模块导入测试")
    
    try:
        print("测试导入主要模块...")
        import torch
        import cv2
        import numpy as np
        from ultralytics import YOLO
        
        print("[OK] 所有关键模块导入成功")
        
        # 测试简单操作
        print("\n测试基本操作...")
        arr = np.array([1, 2, 3])
        tensor = torch.tensor([1, 2, 3])
        print(f"[OK] NumPy数组创建成功: {arr}")
        print(f"[OK] PyTorch张量创建成功: {tensor}")
        
        return True
    except Exception as e:
        print(f"[X] 模块导入失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  运动计数器 YOLOv8 - 系统环境检查")
    print("  Exercise Counter with YOLOv8 - System Check")
    print("=" * 60)
    
    # 执行各项检查
    python_ok = check_python_version()
    check_system_info()
    deps_ok = check_dependencies()
    check_cuda()
    check_models()
    check_disk_space()
    imports_ok = test_imports()
    
    # 总结
    print_separator("检查总结")
    
    if python_ok and deps_ok and imports_ok:
        print("[OK] 系统环境检查通过！")
        print("  您可以开始运行项目了")
    else:
        print("[X] 系统环境检查未通过")
        print("  请先运行 setup.bat 或 setup.ps1 安装依赖")
    
    print("\n建议命令：")
    print("  安装依赖: setup.bat 或 ./setup.ps1")
    print("  运行演示: python demo.py --input 0")
    print("  完整功能: python demo_pro.py --input video.mp4")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

