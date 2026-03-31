@echo off
title Quansloth AI Server
color 0B

echo ==========================================
echo       WAKING UP QUANSLOTH AI SERVER...
echo ==========================================
echo.
echo Please wait while the WSL Matrix boots up...
echo (Keep this window open to keep the server running)
echo.

:: This command reaches into Linux, activates Conda, and runs your app
wsl -e bash -ic "conda activate quansloth && cd ~/quansloth-app && python quansloth_gui.py"

pause