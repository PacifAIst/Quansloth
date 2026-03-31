____                         _       _   _     
  / __ \                       | |     | | | |    
 | |  | |_   _  __ _ _ __   ___| | ___ | |_| |__  
 | |  | | | | |/ _` | '_ \ / __| |/ _ \| __| '_ \ 
 | |__| | |_| | (_| | | | |\__ \ | (_) | |_| | | |
  \___\_\\__,_|\__,_|_| |_||___/_|\___/ \__|_| |_|
         [ POWERED BY TURBOQUANT+ | NVIDIA CUDA ]

# 🦥 Quansloth: TurboQuant Local AI Server

![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)
![Platform: Linux | WSL2](https://img.shields.io/badge/Platform-Linux%20%7C%20WSL2-orange.svg)
![Backend: CUDA](https://img.shields.io/badge/Backend-NVIDIA%20CUDA-green.svg)

Quansloth is a fully private, air-gapped AI server that runs massive context models natively on consumer hardware (like an RTX 3060). By bridging a custom Gradio Python frontend with a highly optimized `llama.cpp` CUDA backend, Quansloth achieves extreme memory compression, saving up to **75% of your VRAM**.

---

## ✨ Features

* **TurboQuant Cache Compression:** Run 8,192+ token contexts natively on 6GB GPUs without Out-Of-Memory (OOM) crashes.
* **Live Hardware Analytics:** The UI physically intercepts the C++ engine logs to report your exact VRAM allocation and savings in real-time.
* **Context Injector:** Upload long documents (PDF, TXT, CSV, MD) directly into the chat stream to test the AI's memory limits.
* **Dual-Routing:** Auto-scan your local `models/` folder, or input custom absolute paths to load any `.gguf` file.
* **Cyberpunk UI:** A sleek, fully responsive dark-mode dashboard built for power users.

---

## 🛠️ Prerequisites

Before installing, ensure your system meets these requirements:
1. Windows 11 with **WSL2 (Ubuntu)** installed (or a native Linux machine).
2. An **NVIDIA GPU** with updated Studio or Game Ready Drivers.
3. **Miniconda** (or Anaconda) installed inside your WSL/Linux environment.

---

## 🚀 Installation

**1. Prepare your Python Environment**
Open your WSL Ubuntu terminal and create a fresh Conda environment:
```bash
conda create -n quansloth python=3.10 -y
conda activate quansloth
```

**2. Clone this Repository**
```bash
git clone https://github.com/PacifAIst/Quansloth.git
cd Quansloth
```

**3. Run the Automated Installer**
We have included a bash script that will automatically download the required C++ engine, compile it safely for your GPU (using 4 CPU cores to prevent RAM crashes), and install all Python dependencies.

```bash
chmod +x install.sh
./install.sh
```

---

## 🎮 Usage

**Adding Models:**
Download any .gguf AI model (e.g., Llama 3) from HuggingFace and place it inside the models/ directory.

**Starting the Server (Linux/WSL):**
```bash
conda activate quansloth
python quansloth_gui.py
```

**Starting the Server (Windows 1-Click):**
If you created the Launch_Quansloth.bat file from our setup guide, simply double-click it on your Windows desktop. It will automatically boot the WSL matrix and launch the app in the background.

**Connecting:**
Open your web browser and navigate to:
👉 http://127.0.0.1:7860

---

## 🎛️ Pro Tips for the UI

- **Symmetric (Turbo3):** Best overall compression for standard models.
- **Asymmetric (Q8/Turbo4):** Use this if you are running Q4_K_M quantized models to balance speed and memory.
- **Watch the Math:** When you hit Launch, keep an eye on the "Hardware Stats" box to see exactly how many Megabytes of VRAM the TurboQuant engine just saved you.

---

Please see ACKNOWLEDGEMENTS.md for credits regarding the C++ backend that powers this interface.
