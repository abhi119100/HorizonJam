#!/usr/bin/env python3
# setup_moshika.py
"""
Setup script for local Moshi-ka TTS implementation.
Installs required dependencies and checks system compatibility.
"""

import subprocess
import sys
import torch

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
        print(f"✓ Successfully installed {package}")
    except subprocess.CalledProcessError:
        print(f"✗ Failed to install {package}")
        return False
    return True

def check_cuda():
    """Check CUDA availability"""
    if torch.cuda.is_available():
        print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
        print(f"✓ CUDA version: {torch.version.cuda}")
        return True
    else:
        print("⚠ CUDA not available - will use CPU (slower)")
        return False

def main():
    print("Setting up Local Moshi-ka TTS...")
    print("=" * 40)
    
    # Required packages
    packages = [
        "torch",
        "transformers", 
        "soundfile",
        "fastapi",
        "uvicorn",
        "aiohttp",
        "pydantic"
    ]
    
    # Install packages
    print("\n1. Installing required packages...")
    for package in packages:
        if not install_package(package):
            print(f"Setup failed at {package}")
            return False
    
    # Check CUDA
    print("\n2. Checking CUDA availability...")
    has_cuda = check_cuda()
    
    # GPU-specific PyTorch installation
    if has_cuda:
        print("\n3. Installing GPU-optimized PyTorch...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "torch", "--index-url", "https://download.pytorch.org/whl/cu118"
            ])
            print("✓ GPU PyTorch installed")
        except subprocess.CalledProcessError:
            print("⚠ GPU PyTorch installation failed, using default")
    
    print("\n" + "=" * 40)
    print("Setup complete!")
    print("\nNext steps:")
    print("1. Test the model: python test_moshi.py")
    print("2. Start TTS server: uvicorn tts_server:app --host 0.0.0.0 --port 5000")
    print("3. Start WebSocket relay: uvicorn ws_relay:app --port 8000")
    print("4. Open test_client.html in your browser")
    
    return True

if __name__ == "__main__":
    main()