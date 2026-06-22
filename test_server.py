"""Math Miner 服务器测试 (Python 标准库 unittest)。

覆盖:名字校验、登录建档、存读一致、玩家列表、路径穿越防护、
并发写不损坏、静态文件、未知路径 404。
运行: python3 test_server.py
"""
import json
import os
import tempfile
import threading
import unittest
import http.client
from urllib.parse import quote

import server


def _enc(path):
    # 把非 ASCII(中文名字)百分号编码,保留 URL 结构与已有的 %xx
    return quote(path, safe="/?=&%")


def _post(port, path, obj):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    body = json.dumps(obj).encode("utf-8")
    c.request("POST", _enc(path), body, {"Content-Type": "application/json"})
    r = c.getresponse()
    data = r.read()
    c.close()
    return r.status, data


def _get(port, path):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    c.request("GET", _enc(path))
    r = c.getresponse()
    data = r.read()
    status = r.status
    c.close()
    return status, data


class NameValidationTests(unittest.TestCase):
    def test_accepts_chinese_english_digits(self):
        self.assertTrue(server.valid_name("小明"))
        self.assertTrue(server.valid_name("Leo"))
        self.assertTrue(server.valid_name("乐乐2"))
        self.assertTrue(server.valid_name("a"))
        self.assertTrue(server.valid_name("a" * 12))  # 边界:12 个字符
        self.assertTrue(server.valid_name("汉" * 12))  # 12 个中文字符

    def test_rejects_empty_and_too_long(self):
        self.assertFalse(server.valid_name(""))
        self.assertFalse(server.valid_name("a" * 13))  # 13 个字符
        self.assertFalse(server.valid_name("汉" * 13))  # 13 个中文字符

    def test_rejects_path_and_special_chars(self):
        for bad in ["../x", "a/b", "a\\b", "a.b", "..", ".", " ", "a b", "a\tb", "a\n", "😀", "_x"]:
            self.assertFalse(server.valid_name(bad), f"should reject {bad!r}")

    def test_rejects_non_str(self):
        self.assertFalse(server.valid_name(None))
        self.assertFalse(server.valid_name(123))


class ServerHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = os.path.join(self.tmp.name, "data")
        self.web_dir = os.path.join(self.tmp.name, "web")
        os.makedirs(self.data_dir)
        os.makedirs(os.path.join(self.web_dir, "fonts"))
        with open(os.path.join(self.web_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write("<!-- MATH MINER INDEX -->")
        with open(os.path.join(self.web_dir, "fonts", "PressStart2P.woff2"), "wb") as f:
            f.write(b"wOF2fake")
        self.srv = server.make_server("127.0.0.1", 0, self.data_dir, self.web_dir)
        self.port = self.srv.server_address[1]
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    def test_login_new_player_creates_empty_save(self):
        status, data = _post(self.port, "/api/login", {"name": "小明"})
        self.assertEqual(status, 200)
        j = json.loads(data)
        self.assertTrue(j["ok"])
        self.assertEqual(j["name"], "小明")
        self.assertEqual(j["save"], {})
        self.assertTrue(os.path.exists(os.path.join(self.data_dir, "小明.json")))

    def test_login_existing_returns_saved_data(self):
        _post(self.port, "/api/login", {"name": "乐乐"})
        payload = {"stars": 42, "tool": 3, "res": {"wood": 5}}
        status, _ = _post(self.port, "/api/save?name=乐乐", payload)
        self.assertEqual(status, 200)
        status, data = _post(self.port, "/api/login", {"name": "乐乐"})
        j = json.loads(data)
        self.assertEqual(j["save"]["stars"], 42)
        self.assertEqual(j["save"]["tool"], 3)
        self.assertEqual(j["save"]["res"], {"wood": 5})

    def test_save_then_get_roundtrip(self):
        _post(self.port, "/api/login", {"name": "Leo"})
        payload = {"stars": 7, "stage": {"1": 2}}
        _post(self.port, "/api/save?name=Leo", payload)
        status, data = _get(self.port, "/api/save?name=Leo")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data), payload)

    def test_get_save_unknown_player_returns_empty(self):
        status, data = _get(self.port, "/api/save?name=Nobody")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data), {})

    def test_players_list_includes_skin(self):
        _post(self.port, "/api/login", {"name": "小明"})
        _post(self.port, "/api/save?name=小明", {"skin": "alex", "stars": 1})
        _post(self.port, "/api/login", {"name": "Leo"})
        status, data = _get(self.port, "/api/players")
        self.assertEqual(status, 200)
        players = json.loads(data)["players"]
        names = {p["name"]: p.get("skin") for p in players}
        self.assertIn("小明", names)
        self.assertIn("Leo", names)
        self.assertEqual(names["小明"], "alex")

    def test_login_rejects_invalid_name(self):
        status, data = _post(self.port, "/api/login", {"name": "../evil"})
        self.assertEqual(status, 400)
        self.assertFalse(json.loads(data)["ok"])

    def test_save_rejects_invalid_name(self):
        status, _ = _post(self.port, "/api/save?name=../../evil", {"x": 1})
        self.assertEqual(status, 400)

    def test_path_traversal_writes_nothing_outside_data(self):
        outside = os.path.join(self.tmp.name, "evil.json")
        _post(self.port, "/api/save?name=" + "..%2F..%2Fevil", {"x": 1})
        _post(self.port, "/api/save?name=../../evil", {"x": 1})
        self.assertFalse(os.path.exists(outside))
        # data dir holds only validly-named files
        for fn in os.listdir(self.data_dir):
            self.assertTrue(fn.endswith(".json"))
            self.assertTrue(server.valid_name(fn[:-5]))

    def test_concurrent_saves_keep_valid_json(self):
        _post(self.port, "/api/login", {"name": "Race"})
        errors = []

        def worker(n):
            try:
                _post(self.port, "/api/save?name=Race", {"stars": n, "big": list(range(200))})
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        with open(os.path.join(self.data_dir, "Race.json"), encoding="utf-8") as f:
            obj = json.load(f)  # must parse — not corrupted
        self.assertIn("stars", obj)

    def test_serves_index_html(self):
        status, data = _get(self.port, "/")
        self.assertEqual(status, 200)
        self.assertIn(b"MATH MINER INDEX", data)

    def test_serves_font_file(self):
        status, data = _get(self.port, "/fonts/PressStart2P.woff2")
        self.assertEqual(status, 200)
        self.assertEqual(data, b"wOF2fake")

    def test_unknown_path_404(self):
        status, _ = _get(self.port, "/api/does-not-exist")
        self.assertEqual(status, 404)

    def test_static_path_traversal_blocked(self):
        status, _ = _get(self.port, "/../server.py")
        self.assertIn(status, (400, 403, 404))

    def test_blocks_source_dotfiles_and_data(self):
        # web_dir 里放诱饵:源码 / json / dotfile / .git/config
        with open(os.path.join(self.web_dir, "server.py"), "w") as f:
            f.write("SECRET_SOURCE")
        with open(os.path.join(self.web_dir, "config.json"), "w") as f:
            f.write("SECRET_JSON")
        with open(os.path.join(self.web_dir, ".secret"), "w") as f:
            f.write("DOT_SECRET")
        os.makedirs(os.path.join(self.web_dir, ".git"))
        with open(os.path.join(self.web_dir, ".git", "config"), "w") as f:
            f.write("GIT_CONFIG")
        for path, marker in [
            ("/server.py", b"SECRET_SOURCE"),
            ("/config.json", b"SECRET_JSON"),
            ("/.secret", b"DOT_SECRET"),
            ("/.git/config", b"GIT_CONFIG"),
        ]:
            status, data = _get(self.port, path)
            self.assertIn(status, (403, 404), f"{path} 应被拦截,得到 {status}")
            self.assertNotIn(marker, data, f"{path} 泄露了内容")

    def test_still_serves_whitelisted_assets(self):
        self.assertEqual(_get(self.port, "/")[0], 200)
        self.assertEqual(_get(self.port, "/index.html")[0], 200)
        self.assertEqual(_get(self.port, "/fonts/PressStart2P.woff2")[0], 200)

    def test_rejects_oversized_body(self):
        _post(self.port, "/api/login", {"name": "Big"})
        big = {"blob": "x" * (600 * 1024)}  # > 512KB 上限
        status, _ = _post(self.port, "/api/save?name=Big", big)
        self.assertEqual(status, 413)

    def test_get_save_rejects_invalid_name(self):
        status, _ = _get(self.port, "/api/save?name=../../evil")
        self.assertEqual(status, 400)

    def test_players_robust_to_bad_files(self):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(os.path.join(self.data_dir, "Good.json"), "w", encoding="utf-8") as f:
            f.write('{"skin":"red"}')
        with open(os.path.join(self.data_dir, "broken.json"), "w") as f:
            f.write("not json")
        open(os.path.join(self.data_dir, "empty.json"), "w").close()
        with open(os.path.join(self.data_dir, "Race.json.tmp"), "w") as f:
            f.write("{}")
        status, data = _get(self.port, "/api/players")
        self.assertEqual(status, 200)
        players = json.loads(data)["players"]
        names = {p["name"] for p in players}
        self.assertIn("Good", names)
        self.assertNotIn("Race.json", names)   # .tmp 残留不算玩家
        self.assertNotIn("Race", names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
