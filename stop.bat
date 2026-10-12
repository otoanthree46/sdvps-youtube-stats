@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*http.server 8765*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo Server stopped.
timeout /t 2 >nul
