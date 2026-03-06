"""
GPU Setup Checker for TexQL Local Training
Run this before training to verify your system is ready
"""

import sys

def check_python():
    """Check Python version"""
    print("🐍 Checking Python...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (need 3.8+)")
        return False

def check_pytorch():
    """Check PyTorch installation"""
    print("\n🔥 Checking PyTorch...")
    try:
        import torch
        print(f"   ✅ PyTorch {torch.__version__}")
        return True, torch
    except ImportError:
        print("   ❌ PyTorch not installed")
        print("   Install with: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        return False, None

def check_cuda(torch_module):
    """Check CUDA availability"""
    print("\n🎮 Checking GPU (CUDA)...")
    
    if not torch_module.cuda.is_available():
        print("   ❌ CUDA not available")
        print("   Training will use CPU (very slow)")
        print("\n   Solutions:")
        print("   1. Install CUDA-enabled PyTorch")
        print("   2. Update NVIDIA drivers")
        print("   3. Use Google Colab instead")
        return False
    
    # GPU details
    gpu_count = torch_module.cuda.device_count()
    gpu_name = torch_module.cuda.get_device_name(0)
    gpu_capability = torch_module.cuda.get_device_capability(0)
    
    # Memory info
    total_memory = torch_module.cuda.get_device_properties(0).total_memory / (1024**3)
    
    print(f"   ✅ CUDA available")
    print(f"   GPU Count: {gpu_count}")
    print(f"   GPU Name: {gpu_name}")
    print(f"   GPU Memory: {total_memory:.2f} GB")
    print(f"   CUDA Version: {torch_module.version.cuda}")
    print(f"   Compute Capability: {gpu_capability[0]}.{gpu_capability[1]}")
    
    # Check if memory is sufficient
    if total_memory < 2.5:
        print(f"\n   ⚠️  Warning: Only {total_memory:.1f}GB VRAM")
        print("   This might be tight. Consider:")
        print("   - Using batch_size=1")
        print("   - Using t5-small model")
        print("   - Closing other GPU applications")
    elif total_memory < 4:
        print(f"\n   ✅ {total_memory:.1f}GB VRAM is adequate")
        print("   Recommended settings:")
        print("   - batch_size=2 (default)")
        print("   - model=google/flan-t5-small (default)")
    else:
        print(f"\n   🎉 {total_memory:.1f}GB VRAM is excellent!")
        print("   You can use larger models or batch sizes")
    
    return True

def check_memory():
    """Check system memory"""
    print("\n💾 Checking System RAM...")
    try:
        import psutil
        total_ram = psutil.virtual_memory().total / (1024**3)
        available_ram = psutil.virtual_memory().available / (1024**3)
        
        print(f"   Total RAM: {total_ram:.1f} GB")
        print(f"   Available RAM: {available_ram:.1f} GB")
        
        if available_ram < 4:
            print("   ⚠️  Low available RAM")
            print("   Close other applications before training")
        else:
            print("   ✅ Sufficient RAM")
        
        return True
    except ImportError:
        print("   ⚠️  psutil not installed (optional)")
        return True

def check_disk_space():
    """Check available disk space"""
    print("\n💿 Checking Disk Space...")
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_gb = free / (1024**3)
        
        print(f"   Free space: {free_gb:.1f} GB")
        
        if free_gb < 5:
            print("   ⚠️  Low disk space")
            print("   Need at least 5GB for models and checkpoints")
            return False
        else:
            print("   ✅ Sufficient disk space")
        
        return True
    except Exception as e:
        print(f"   ⚠️  Could not check disk space: {e}")
        return True

def check_dependencies():
    """Check required packages"""
    print("\n📦 Checking Dependencies...")
    
    required = [
        'transformers',
        'datasets',
        'pandas',
        'numpy',
        'tqdm',
        'accelerate'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n   Install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True

def check_data():
    """Check if training data exists"""
    print("\n📊 Checking Training Data...")
    
    import os
    
    required_files = [
        'data/train.csv',
        'data/val.csv',
        'data/test.csv'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
            all_exist = False
    
    if not all_exist:
        print("\n   Generate data first:")
        print("   python data_generation.py")
        return False
    
    return True

def test_gpu_training():
    """Test actual GPU training with a small sample"""
    print("\n🧪 Testing GPU Training...")
    
    try:
        import torch
        import torch.nn as nn
        
        if not torch.cuda.is_available():
            print("   ⚠️  Skipping (no GPU)")
            return True
        
        # Create small test
        device = torch.device("cuda")
        model = nn.Linear(100, 10).to(device)
        optimizer = torch.optim.Adam(model.parameters())
        
        # Training step
        for _ in range(5):
            x = torch.randn(32, 100).to(device)
            y = torch.randn(32, 10).to(device)
            
            output = model(x)
            loss = nn.MSELoss()(output, y)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        print("   ✅ GPU training test passed")
        print(f"   GPU Memory Used: {torch.cuda.memory_allocated() / 1024**2:.1f} MB")
        
        # Clear cache
        torch.cuda.empty_cache()
        
        return True
        
    except Exception as e:
        print(f"   ❌ GPU training test failed: {e}")
        return False

def print_recommendations(gpu_memory_gb):
    """Print training recommendations based on hardware"""
    print("\n" + "="*60)
    print("💡 Recommended Training Settings")
    print("="*60)
    
    if gpu_memory_gb >= 8:
        print("\n✨ Your GPU is powerful! You can use:")
        print("   Model: google/flan-t5-base")
        print("   Batch size: 4-8")
        print("   Command: python train_local.py --target sql --batch-size 4")
    elif gpu_memory_gb >= 4:
        print("\n✅ Your GPU is good! Recommended settings:")
        print("   Model: google/flan-t5-small")
        print("   Batch size: 2-4")
        print("   Command: python train_local.py --target sql --batch-size 2")
    elif gpu_memory_gb >= 2.5:
        print("\n⚠️  Your GPU has limited memory. Use:")
        print("   Model: t5-small or google/flan-t5-small")
        print("   Batch size: 1-2")
        print("   Command: python train_local.py --target sql --batch-size 1")
    else:
        print("\n⚠️  Your GPU has very limited memory!")
        print("   Consider using Google Colab instead")
        print("   Or use CPU (slow): python train_local.py --target sql")
    
    print("\n📚 More info: See LOCAL_TRAINING.md")

def main():
    """Run all checks"""
    print("="*60)
    print("TexQL GPU Setup Checker")
    print("="*60)
    
    all_passed = True
    gpu_memory = 0
    
    # Run checks
    all_passed &= check_python()
    
    pytorch_ok, torch_module = check_pytorch()
    all_passed &= pytorch_ok
    
    if pytorch_ok and torch_module:
        cuda_ok = check_cuda(torch_module)
        all_passed &= cuda_ok
        
        if cuda_ok:
            gpu_memory = torch_module.cuda.get_device_properties(0).total_memory / (1024**3)
            test_gpu_training()
    
    all_passed &= check_memory()
    all_passed &= check_disk_space()
    all_passed &= check_dependencies()
    all_passed &= check_data()
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    if all_passed:
        print("\n✅ All checks passed! You're ready to train.")
        if gpu_memory > 0:
            print_recommendations(gpu_memory)
        print("\n🚀 Start training:")
        print("   python train_local.py --target sql")
        print("   OR: Run train.bat for interactive mode")
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        print("\n📖 For help, see:")
        print("   - LOCAL_TRAINING.md")
        print("   - README.md")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
