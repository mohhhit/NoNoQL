"""
Setup script for TexQL project
Checks dependencies and creates necessary directories
"""

import sys
import subprocess
import os

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro}")
        print("   Required: Python 3.8 or higher")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\nChecking dependencies...")
    
    required_packages = [
        'pandas',
        'numpy',
        'faker',
        'transformers',
        'torch',
        'datasets',
        'streamlit',
        'tqdm'
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    return missing

def install_dependencies():
    """Install missing dependencies"""
    print("\nInstalling dependencies from requirements.txt...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    
    directories = ['data', 'models', 'data_sample']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ {directory}/")
    
    return True

def check_cuda():
    """Check CUDA availability"""
    print("\nChecking CUDA availability...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA available")
            print(f"   Device: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA version: {torch.version.cuda}")
            return True
        else:
            print("⚠️  CUDA not available (CPU mode)")
            print("   Training will be slower on CPU")
            print("   Consider using Google Colab with GPU")
            return False
    except ImportError:
        print("❌ PyTorch not installed")
        return False

def verify_files():
    """Verify all required files exist"""
    print("\nVerifying project files...")
    
    required_files = [
        'data_generation.py',
        'training_colab.ipynb',
        'app.py',
        'inference.py',
        'requirements.txt',
        'README.md',
        'QUICKSTART.md'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            all_exist = False
    
    return all_exist

def main():
    """Run setup checks"""
    print("="*60)
    print("TexQL Setup Script")
    print("="*60)
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Setup failed: Incompatible Python version")
        return False
    
    # Create directories
    create_directories()
    
    # Verify files
    if not verify_files():
        print("\n⚠️  Some project files are missing")
    
    # Check dependencies
    missing = check_dependencies()
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        response = input("\nInstall missing dependencies? (y/n): ")
        
        if response.lower() == 'y':
            if not install_dependencies():
                print("\n❌ Setup failed: Could not install dependencies")
                return False
        else:
            print("\nSkipping dependency installation")
            print("Install manually with: pip install -r requirements.txt")
    
    # Check CUDA
    check_cuda()
    
    # Summary
    print("\n" + "="*60)
    print("Setup Summary")
    print("="*60)
    print("\n✅ Setup completed!")
    print("\nNext steps:")
    print("1. Run demo: python demo.py")
    print("2. Generate data: python data_generation.py")
    print("3. Train models: Open training_colab.ipynb in Google Colab")
    print("4. Run app: streamlit run app.py")
    print("\nFor detailed instructions, see:")
    print("  - QUICKSTART.md (quick guide)")
    print("  - README.md (full documentation)")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
