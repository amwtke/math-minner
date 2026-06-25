#!/usr/bin/env python3
"""方块数学矿工 — 本地多人服务器(Python 标准库,零第三方依赖)。

职责:
  1. 提供静态文件(index.html、fonts/*)。
  2. 提供按玩家名存档的 REST API。

运行:
    python3 server.py [端口]        # 默认 8000,绑 0.0.0.0,局域网可访问

存档:每个玩家一个 data/<名字>.json,写入用文件锁 + 原子替换防并发损坏。
"""
import io
import json
import os
import socket
import sys
import threading
import urllib.request
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))

# 请求体上限:存档是小 JSON,512KB 绰绰有余。超过即拒,防写满磁盘/吃内存。
MAX_BODY = 512 * 1024
# 静态文件只放行前端资源扩展名 —— 杜绝把 server.py / *.json 存档 / .md / 脚本等暴露给局域网。
ALLOWED_STATIC_EXT = {
    ".html", ".css", ".js", ".woff2", ".woff", ".ttf",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".m4a", ".mp3", ".aac", ".ogg", ".wav",   # 离线发音音频
}


class BodyTooLarge(Exception):
    """请求体超过 MAX_BODY。"""


def valid_name(name):
    """名字合法:字符串、长度 1–12、全部为字母/数字/中文(isalnum)。

    isalnum() 对中英文数字为真,对 '/'、'\\'、'.'、空白、控制字符、下划线、
    emoji 均为假 —— 因此从根上杜绝路径穿越(不可能出现 '..' 或分隔符)。
    """
    return isinstance(name, str) and 1 <= len(name) <= 12 and name.isalnum()


def save_path(data_dir, name):
    """已校验名字 -> data 目录内的 json 路径;再做一次越界防御。"""
    root = os.path.abspath(data_dir)
    p = os.path.abspath(os.path.join(root, name + ".json"))
    if os.path.commonpath([root, p]) != root:
        raise ValueError("path escapes data dir")
    return p


class Handler(BaseHTTPRequestHandler):
    server_version = "MathMiner/1.0"
    timeout = 30  # 闲置/慢速连接超时断开,避免工作线程被长期占住

    # —— 路由 ——————————————————————————————————————————————
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/players":
            return self._players()
        if path == "/api/save":
            return self._get_save(parsed)
        if path == "/api/audio/status":
            return self._audio_status()
        if path.startswith("/api/"):
            return self._send_json(404, {"ok": False, "error": "not found"})
        return self._serve_static(path)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/login":
            return self._login()
        if path == "/api/save":
            return self._post_save(parsed)
        if path == "/api/audio/fetch":
            return self._audio_fetch()
        return self._send_json(404, {"ok": False, "error": "not found"})

    # —— API 处理 ————————————————————————————————————————————
    def _login(self):
        try:
            body = self._read_body()
        except BodyTooLarge:
            return self._send_json(413, {"ok": False, "error": "请求体过大"})
        except ValueError:
            return self._send_json(400, {"ok": False, "error": "bad json"})
        name = body.get("name") if isinstance(body, dict) else None
        if not valid_name(name):
            return self._send_json(400, {"ok": False, "error": "名字只能用中英文和数字,1–12 位"})
        with self._lock_for(name):
            path = save_path(self.server.data_dir, name)
            if not os.path.exists(path):
                self._atomic_write(path, {})
            save = self._read_save(path)
        return self._send_json(200, {"ok": True, "name": name, "save": save})

    def _post_save(self, parsed):
        name = parse_qs(parsed.query).get("name", [None])[0]
        if not valid_name(name):
            return self._send_json(400, {"ok": False, "error": "invalid name"})
        try:
            body = self._read_body()
        except BodyTooLarge:
            return self._send_json(413, {"ok": False, "error": "存档过大"})
        except ValueError:
            return self._send_json(400, {"ok": False, "error": "bad json"})
        if not isinstance(body, dict):
            return self._send_json(400, {"ok": False, "error": "save must be an object"})
        with self._lock_for(name):
            self._atomic_write(save_path(self.server.data_dir, name), body)
        return self._send_json(200, {"ok": True})

    def _get_save(self, parsed):
        name = parse_qs(parsed.query).get("name", [None])[0]
        if not valid_name(name):
            return self._send_json(400, {"ok": False, "error": "invalid name"})
        path = save_path(self.server.data_dir, name)
        save = self._read_save(path) if os.path.exists(path) else {}
        return self._send_json(200, save)

    def _players(self):
        out = []
        try:
            files = os.listdir(self.server.data_dir)
        except OSError:
            files = []
        for fn in sorted(files):
            if not fn.endswith(".json"):
                continue
            name = fn[:-5]
            if not valid_name(name):
                continue
            obj = self._read_save(os.path.join(self.server.data_dir, fn))
            skin = obj.get("skin") if isinstance(obj, dict) else None
            out.append({"name": name, "skin": skin})
        return self._send_json(200, {"players": out})

    def _audio_have(self):
        try:
            return sum(1 for f in os.listdir(self.server.audio_dir)
                       if f.endswith(".mp3"))
        except OSError:
            return 0

    def _audio_status(self):
        ready = os.path.exists(self.server.ready_sentinel)
        return self._send_json(200, {"ok": True, "ready": ready,
                                      "have": self._audio_have()})

    def _audio_fetch(self):
        with self.server.audio_lock:                      # 串行，避免多设备并发重复下载
            if os.path.exists(self.server.ready_sentinel):
                return self._send_json(200, {"ok": True, "have": self._audio_have()})
            data, errors = None, []
            for url in AUDIO_ZIP_URLS:                     # 镜像优先,逐个尝试,任一成功即停
                try:
                    data = _download_zip(url)
                    break
                except Exception as e:                     # 记下失败源,全挂时一并报给前端
                    host = url.split("//", 2)[-1].split("/", 1)[0]
                    errors.append("%s(%s)" % (host, e))
            if data is None:                               # 全部源都失败：不写哨兵，可重试
                return self._send_json(502, {"ok": False, "error": "下载失败：" + "；".join(errors)})
            try:
                n = extract_pinyin_mp3(data, self.server.audio_dir)
            except Exception as e:                         # 解压失败：不写哨兵，可重试
                return self._send_json(502, {"ok": False, "error": "解压失败：" + str(e)})
            if n == 0:                                     # 解出 0 个 mp3：拒绝写哨兵，可重试
                return self._send_json(502, {"ok": False, "error": "下载内容为空，请重试"})
            with open(self.server.ready_sentinel, "w") as f:
                f.write("ok")
            return self._send_json(200, {"ok": True, "have": n})

    # —— 存储工具 ————————————————————————————————————————————
    def _lock_for(self, name):
        with self.server.locks_guard:
            lock = self.server.locks.get(name)
            if lock is None:
                lock = threading.Lock()
                self.server.locks[name] = lock
            return lock

    def _atomic_write(self, path, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

    def _read_save(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                txt = f.read()
            return json.loads(txt) if txt.strip() else {}
        except (OSError, ValueError):
            return {}

    # —— HTTP 工具 ————————————————————————————————————————————
    def _read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise BodyTooLarge()
        raw = self.rfile.read(length) if length > 0 else b""
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _serve_static(self, urlpath):
        rel = urlpath.lstrip("/") or "index.html"
        parts = [p for p in rel.replace("\\", "/").split("/") if p]
        # 拒绝任何以点开头的路径段(.git / .env / dotfiles),以及非前端资源扩展名
        if any(p.startswith(".") for p in parts):
            return self._send_json(404, {"ok": False, "error": "not found"})
        if os.path.splitext(rel)[1].lower() not in ALLOWED_STATIC_EXT:
            return self._send_json(404, {"ok": False, "error": "not found"})
        root = self.server.web_dir
        candidate = os.path.abspath(os.path.join(root, rel))
        try:
            inside = os.path.commonpath([root, candidate]) == root
        except ValueError:
            inside = False
        if not inside or not os.path.isfile(candidate):
            return self._send_json(404, {"ok": False, "error": "not found"})
        self._send_file(candidate)

    def _send_file(self, path):
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", _content_type(path))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):  # 静默,保持测试输出干净
        pass


# 发音整包(约 30MB)来源,按顺序尝试:先国内可达的镜像,失败再退回 GitHub 直连。
# GitHub 直连在国内常被限速到几十 KB/s,30MB 跑不完就会超时;镜像通常快得多。
# 镜像偶尔会挂,所以保留 GitHub 原址兜底——任一成功即停。
_GH_ZIP = ("codeload.github.com/davinfifield/"
           "mp3-chinese-pinyin-sound/zip/refs/heads/master")
AUDIO_ZIP_URLS = (
    "https://gh-proxy.com/https://" + _GH_ZIP,   # 镜像优先
    "https://" + _GH_ZIP,                        # GitHub 直连兜底
)


def extract_pinyin_mp3(zip_bytes, dest_dir):
    """把 zip 内所有 *.mp3 按 basename 拍平写入 dest_dir，返回写入数。
    basename 化天然挡住 zip-slip（不含分隔符），再加 commonpath 双保险。"""
    os.makedirs(dest_dir, exist_ok=True)
    root = os.path.abspath(dest_dir)
    n = 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for info in z.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".mp3"):
                continue
            base = os.path.basename(info.filename)
            if not base:
                continue
            target = os.path.abspath(os.path.join(dest_dir, base))
            if os.path.commonpath([root, target]) != root:
                continue
            with z.open(info) as src, open(target, "wb") as dst:
                dst.write(src.read())
            n += 1
    return n


def _download_zip(url, timeout=300):   # socket 超时:容忍慢速/偶发卡顿,不限制总时长
    req = urllib.request.Request(url, headers={"User-Agent": "MathMiner/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _content_type(path):
    for ext, ctype in (
        (".html", "text/html; charset=utf-8"),
        (".woff2", "font/woff2"),
        (".woff", "font/woff"),
        (".ttf", "font/ttf"),
        (".js", "text/javascript; charset=utf-8"),
        (".css", "text/css; charset=utf-8"),
        (".json", "application/json; charset=utf-8"),
        (".png", "image/png"),
        (".svg", "image/svg+xml"),
        (".ico", "image/x-icon"),
        (".mp3", "audio/mpeg"),
        (".m4a", "audio/mp4"),
        (".aac", "audio/aac"),
        (".ogg", "audio/ogg"),
        (".wav", "audio/wav"),
    ):
        if path.endswith(ext):
            return ctype
    return "application/octet-stream"


def make_server(host, port, data_dir, web_dir):
    srv = ThreadingHTTPServer((host, port), Handler)
    srv.daemon_threads = True
    srv.data_dir = os.path.abspath(data_dir)
    srv.web_dir = os.path.abspath(web_dir)
    srv.locks = {}
    srv.locks_guard = threading.Lock()
    srv.audio_dir = os.path.join(srv.web_dir, "audio", "pinyin")
    srv.ready_sentinel = os.path.join(srv.web_dir, "audio", ".ready")
    srv.audio_lock = threading.Lock()
    return srv


def _lan_ips():
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            # 排除回环与 169.254 链路本地(无路由时的自动地址)
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                ips.add(ip)
    except OSError:
        pass
    return sorted(ips)


def _sweep_tmp(data_dir):
    """清理上次异常退出残留的 *.json.tmp 孤儿文件。"""
    try:
        for fn in os.listdir(data_dir):
            if fn.endswith(".tmp"):
                try:
                    os.remove(os.path.join(data_dir, fn))
                except OSError:
                    pass
    except OSError:
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    data_dir = os.path.join(HERE, "data")
    os.makedirs(data_dir, exist_ok=True)
    _sweep_tmp(data_dir)
    srv = make_server("0.0.0.0", port, data_dir, HERE)
    print("⛏️  方块数学矿工 服务器已启动", flush=True)
    print(f"   本机:    http://localhost:{port}", flush=True)
    ips = _lan_ips()
    for ip in ips:
        print(f"   局域网:  http://{ip}:{port}    ← 手机/平板用这个", flush=True)
    if not ips:
        print("   局域网:  未自动探测到 IP —— 请在系统设置查看本机 WiFi 的 IP,", flush=True)
        print(f"            手机/平板访问 http://<那个IP>:{port}", flush=True)
    print("   ⚠ 已对同一 WiFi 下所有设备开放(无密码),公共网络慎用;", flush=True)
    print("      若系统弹出防火墙询问,请选「允许」,否则其他设备连不上。", flush=True)
    print("   按 Ctrl+C 停止", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n再见!存档已保存在 data/ 目录。")
    finally:
        srv.shutdown()
        srv.server_close()


if __name__ == "__main__":
    main()
