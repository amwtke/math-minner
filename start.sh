#!/usr/bin/env bash
# 方块数学矿工 — 一键启动本地多人服务器 (Mac / Linux)
# 用法: ./start.sh [端口]   端口默认 8000
cd "$(dirname "$0")" || exit 1
PORT="${1:-8000}"
exec python3 server.py "$PORT"
