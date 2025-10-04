@echo off
title ShortsMaker Pro - Video Creator
color 0B
cls

echo.
echo  ========================================================
echo      _____ _                _       __  __       _             
echo     / ____^| ^|              ^| ^|     ^|  \/  ^|     ^| ^|            
echo    ^| (___ ^| ^|__   ___  _ __^| ^|_ ___^| \  / ^| __ _^| ^| _____ _ __ 
echo     \___ \^| '_ \ / _ \^| '__^| __/ __^| ^|\/^| ^|/ _` ^| ^|/ / _ \ '__^|
echo     ____) ^| ^| ^| ^| (_) ^| ^|  ^| ^|_\__ \ ^|  ^| ^| (_^| ^|   <  __/ ^|   
echo    ^|_____/^|_^| ^|_^|\___/^|_^|   \__^|___/_^|  ^|_^|\__,_^|_^|\_\___^|_^|   
echo                     __  __                                  
echo                    ^|  \/  ^|                                 
echo                    ^| \  / ^| __ _ _ __  __ _  __ _  ___ _ __ 
echo                    ^| ^|\/^| ^|/ _` ^| '_ \ / _` ^|/ _` ^|/ _ \ '__^|
echo                    ^| ^|  ^| ^| (_^| ^| ^| ^| ^| (_^| ^| (_^| ^|  __/ ^|   
echo                    ^|_^|  ^|_^|\__,_^|_^| ^|_^|\__,_^|\__, ^|\___^|_^|   
echo                                           __/ ^|          
echo                                          ^|___/           
echo  ========================================================
echo                    Professional Edition
echo  ========================================================
echo.
echo  [*] Checking Python installation...

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo  [X] ERROR: Python is not installed or not in PATH!
    echo.
    echo  Please install Python 3.10+ and try again.
    echo.
    pause
    exit
)

echo  [*] Python found!
echo  [*] Starting ShortsMaker Pro...
echo.
echo  ========================================================
echo.

python gui_app.py

if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo  ========================================================
    echo  [X] ERROR: Application failed to start!
    echo  ========================================================
    echo.
    echo  Common solutions:
    echo   1. Run: pip install -r requirements.txt
    echo   2. Check that all files are present
    echo   3. Make sure you're in the correct folder
    echo.
    echo  Press any key to exit...
    pause >nul
) else (
    echo.
    echo  Application closed normally.
)