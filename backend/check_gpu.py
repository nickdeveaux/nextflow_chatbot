#!/usr/bin/env python3
"""Check if GPU (CUDA) is available and install appropriate requirements."""
import subprocess
import sys
import os

def has_cuda():
    """Check if CUDA is available on the system."""
    try:
        result = subprocess.run(
            ['nvidia-smi'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def has_cuda_in_python():
    """Check if CUDA is available via PyTorch (if already installed)."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

if __name__ == '__main__':
    # Check for GPU
    gpu_available = has_cuda() or has_cuda_in_python()
    
    if gpu_available:
        print("✓ GPU (CUDA) detected - will use GPU-accelerated packages")
        sys.exit(0)
    else:
        print("✓ CPU-only environment - will use CPU-optimized packages")
        sys.exit(1)

