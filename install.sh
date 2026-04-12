#!/bin/bash
set -e

echo "======================================================="
echo "   🚀 QUANSLOTH: TURBOQUANT LOCAL AI INSTALLER 🚀   "
echo "======================================================="

echo -e "\n[1/4] Checking system dependencies (Git, Build Tools, CMake, CUDA)..."
sudo apt-get update

# Base packages that everyone always needs
PACKAGES="build-essential cmake git"

# 🟢 NEW: Smart CUDA Detection!
if command -v nvcc &> /dev/null; then
    echo "✅ Existing CUDA Toolkit (nvcc) detected! Skipping redundant CUDA download to prevent bloat."
else
    echo "⚠️ No CUDA Toolkit found. Adding nvidia-cuda-toolkit to the download queue..."
    PACKAGES="$PACKAGES nvidia-cuda-toolkit"
fi

# Install the dynamically built list of packages
sudo apt-get install -y $PACKAGES

echo -e "\n[2/4] Fetching TheTom's TurboQuant Engine (Feature Branch)..."
cd ~

if [ -d "llama-cpp-turboquant" ]; then
    echo "Engine folder already exists. Pulling latest updates..."
    cd llama-cpp-turboquant
    git fetch origin
    git checkout feature/turboquant-kv-cache
    git pull origin feature/turboquant-kv-cache
else
    git clone -b feature/turboquant-kv-cache https://github.com/TheTom/llama-cpp-turboquant.git
    cd llama-cpp-turboquant
fi

echo -e "\n⚙️ Compiling the V8 CUDA Engine..."
echo "Applying safe compile limit (-j 4) to prevent RAM overload..."
cmake -B build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4

echo -e "\n[3/4] Preparing the Quansloth environment..."
cd ~/quansloth-app
mkdir -p models

echo -e "\n[4/4] Installing Python requirements..."
pip install --upgrade pip
# Now using your requirements file!
pip install -r requirements.txt

echo "======================================================="
echo " 🔥 INSTALLATION 100% COMPLETE! 🔥 "
echo "======================================================="
