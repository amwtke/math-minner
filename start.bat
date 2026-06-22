@echo off
REM 方块数学矿工 — 一键启动本地多人服务器 (Windows)
REM 用法: start.bat [端口]   端口默认 8000
cd /d "%~dp0"
set PORT=%1
if "%PORT%"=="" set PORT=8000
where py >nul 2>nul && (py -3 server.py %PORT%) || (python server.py %PORT%)
pause
