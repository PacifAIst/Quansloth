#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "======================================================="
echo "   🚀 QUANSLOTH: TURBOQUANT LOCAL AI INSTALLER 🚀   "
echo "======================================================="

# Step 1: System Dependencies
echo -e "\n[1/4] Checking system dependencies (Git, Build Tools, CMake)..."
sudo apt-get update
sudo apt-get install -y build-essential cmake git

# Step 2: Clone and Build the C++ Engine
echo -e "\n[2/4] Fetching TheTom's TurboQuant Engine..."
cd ~

if [ -d "llama-cpp-turboquant" ]; then
    echo "Engine folder already exists. Pulling latest updates..."
    cd llama-cpp-turboquant
    git pull
else
    git clone https://github.com/TheTom/llama-cpp-turboquant.git
    cd llama-cpp-turboquant
fi

echo -e "\n⚙️ Compiling the V8 CUDA Engine..."
echo "Applying safe compile limit (-j 4) to prevent RAM overload..."
cmake -B build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4

# Step 3: Setup App Directory
echo -e "\n[3/4] Preparing the Quansloth environment..."
cd ~/quansloth-app

echo "📁 Creating 'models' directory for your GGUF files..."
mkdir -p models

# Step 4: Python Dependencies
echo -e "\n[4/4] Installing Python requirements..."
# Ensure pip is up to date, then install the required bridge packages
pip install --upgrade pip
pip install gradio openai PyPDF2

echo "======================================================="
echo " 🔥 INSTALLATION 100% COMPLETE! 🔥 "
echo "======================================================="
echo "Next Steps:"
echo "1. Put any .gguf model inside the 'models/' folder."
echo "2. Run: python quansloth_gui.py"
echo "======================================================="