@echo off
echo =======================================================
echo Booting Quansloth Local Matrix...
echo Please wait while the CUDA engine initializes.
echo =======================================================
wsl -d Ubuntu -e bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda activate quansloth && cd ~/quansloth-app && python quansloth_gui.py"
pause
