@echo off
cd /d "%~dp0"
rem 最新データを取得(オフライン/競合時は無視)→ 簡易サーバーを非表示で起動 → ブラウザを開く
git pull --ff-only >nul 2>&1
start "" /min powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "python -m http.server 8765 --bind 127.0.0.1 --directory docs"
timeout /t 2 /nobreak >nul
start "" "http://localhost:8765/"
