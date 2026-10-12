@echo off
title Khoi Dong He Thong Vietlott Mobile & Cloud
echo ========================================================
echo DANG KHOI DONG SERVER VIETLOTT & DUONG TRUYEN TOAN CAU...
echo ========================================================

cd /d D:\Thao\Vietlott

echo 1. Khoi dong Backend Python...
start "Vietlott Backend Server" /min cmd /c ".\venv\Scripts\python.exe -m uvicorn src.app:app --host 0.0.0.0 --port 8000"

timeout /t 2 /nobreak >nul

echo 2. Khoi dong Cloudflare Public Tunnel...
start "Vietlott Cloudflare Tunnel" cmd /k "cloudflared tunnel --url http://localhost:8000"

echo ========================================================
echo DA KHOI DONG THANH CONG!
echo Hay kiem tra cua so "Vietlott Cloudflare Tunnel" de lay link HTTPS.
echo ========================================================
pause
