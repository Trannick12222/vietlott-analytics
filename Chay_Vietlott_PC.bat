@echo off
chcp 65001 >nul
title Vietlott Analytics - Desktop PC
cd /d "%~dp0"

echo ========================================================
echo       VIETLOTT ANALYTICS & PREDICTION - DESKTOP PC
echo ========================================================
echo Đang khởi động ứng dụng trên máy tính...
echo.

if exist ".\venv\Scripts\python.exe" (
    ".\venv\Scripts\python.exe" desktop_app.py
) else (
    echo [LỖI] Không tìm thấy môi trường ảo venv. Đang thử bằng Python hệ thống...
    python desktop_app.py
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo [LỖI] Đã xảy ra lỗi khi khởi chạy ứng dụng.
    pause
)
