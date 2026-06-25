# 语文·拼音矿工 一期 实现计划（拼音配对挖矿闭环）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在「方块数学矿工」里加入「语文」学科与第一个玩法「🔤拼音配对挖矿」，跑通 登录→选学科→选世界→汉字配拼音挖矿→升镐/皮肤 的完整闭环，发音由服务器运行时按需拉取。

**Architecture:** 复用现有配对引擎 `G.*`，通过 `S.subject` 把世界表/题库/字体在「数学/语文」间分流（泛化而非另写）。新增 `#subjects` 选学科屏与 `#audioFetch` 下载屏。内容由构建期 `tools/gen_data.py`（pypinyin）生成静态 `pinyin-data.js`（入 git）。音频由 `server.py` 用标准库 `urllib`+`zipfile` 从 davinfifield 仓库按需下载到 `audio/`（不入 git）。

**Tech Stack:** 纯 HTML/CSS/JS 单文件前端（无构建、无框架、无 node）；Python 3 标准库服务器；构建期工具 pypinyin（仅开发机）。

## Global Constraints

逐条来自设计文档 `docs/superpowers/specs/2026-06-25-pinyin-game-design.md`，每个任务都隐含遵守：

- **运行时零第三方依赖**：前端只有静态文件；`server.py` 只用标准库；pypinyin 仅构建期用，绝不进运行时。
- **离线**：数学玩法与所有游玩设备始终 100% 离线；唯一例外是语文发音首次需**服务器**联网一次拉取。
- **共享经济不动**：矿石 `S.res`、星星 `S.stars`、镐子 `S.tool`、皮肤 `S.skin`、技能跨学科共享，不新增、不分叉。
- **像素风复用**：复用现有 `.tile`/`.world`/HUD/overlay/`beep()` 视觉与音效。
- **音频文件名全 ASCII**：davinfifield 命名 `<拼音字母+调号数字>.mp3`，ü 写作 `uu`（lü→`luu3`、nǚ→`nuu3`、lüe→`luue`），ju/qu/xu/yu 不变；轻声 `5` 或省略。
- **davinfifield 仓库事实**（已联网核实，The Unlicense/公共领域）：默认分支 `master`；mp3 在 `mp3/` 子目录；zip 直链 `https://codeload.github.com/davinfifield/mp3-chinese-pinyin-sound/zip/refs/heads/master`；解压顶层目录 `mp3-chinese-pinyin-sound-master/`。
- **iOS 音频**：`.m4a` MIME 必须是 `audio/mp4`；首次播放须在用户手势内解锁。
- **音频不入 git**：`.gitignore` 加 `audio/`；`pinyin-data.js` 入 git（小文本）。
- **存档兼容**：新字段在 `applySave` 用 `Object.assign` 兜底，防旧档「第 NaN 关」。

## 测试策略（贴合本仓库现状）

本仓库只有 Python 服务器测试（`test_server.py`，标准库 `unittest`），前端无测试框架且刻意零依赖、无构建。故：

- **Python 部分（`tools/gen_data.py` 的纯函数、`server.py` 的音频端点与解压逻辑）走真 TDD**：先写失败测试 → 跑红 → 实现 → 跑绿。
- **前端部分（`index.html`）走「脚本化手动验收」**：每个前端任务末尾给出明确的「打开哪个页面、点什么、应看到什么」清单，而不是含糊的「测试一下」。不引入 JS 测试框架（与项目零依赖/无构建一致）。

**测试运行器**：本仓库用标准库 `unittest`（**未装 pytest**）。跑全部：`python3 test_server.py`、`cd tools && python3 test_gen_data.py`；跑单个：`python3 -m unittest test_server.ExtractAudioTest -v`。**构建期 pypinyin** 装在仓库根的 `.venv-tools/`（已建好，经清华镜像安装；`files.pythonhosted.org` 在本机 TLS 不通，故用国内镜像）；运行 `gen_data.py` 用 `.venv-tools/bin/python3`。`unittest` 测试用系统 `python3` 即可（纯标准库）。

## File Structure

| 文件 | 责任 | 本期动作 |
|---|---|---|
| `tools/gen_data.py` | 构建期：汉字→拼音/声调/音频码，生成 `pinyin-data.js` | 新建 |
| `tools/test_gen_data.py` | `gen_data.py` 纯函数单测 | 新建 |
| `pinyin-data.js` | 运行时静态数据：`PINYIN_DATA`、`PINYIN_WORLDS` | 新建（构建产物，入 git） |
| `server.py` | 静态服务 + 存档 API + **音频拉取 API** | 改：静态白名单/MIME；加 `/api/audio/status`、`/api/audio/fetch`；可测的 `extract_pinyin_mp3` | 
| `test_server.py` | 服务器单测 | 改：加音频端点与解压测试 |
| `index.html` | 前端本体 | 改：`#subjects`/`#audioFetch` 屏、导航分流、配对引擎泛化、`playPy`、引用 `pinyin-data.js` |
| `.gitignore` | 忽略规则 | 改：加 `audio/` |
| `README.md` | 文档 | 改：语文玩法与音频说明 |

---

## Task 0: 工程脚手架（.gitignore + tools 目录 + 数据引用占位）

**Files:**
- Modify: `.gitignore`
- Create: `tools/` (目录)

**Interfaces:**
- Produces: `audio/` 被 git 忽略；`tools/` 目录存在。

- [ ] **Step 1: 把 audio/ 加入 .gitignore**

读现有 `.gitignore`，在末尾追加（若已忽略 `data/` 则照同样风格）：

```gitignore
# 运行时由服务器拉取的发音音频，不入 git
audio/
# 构建期 pypinyin 的虚拟环境，不入 git
.venv-tools/
```

- [ ] **Step 2: 建 tools 目录占位**

```bash
mkdir -p tools
```

- [ ] **Step 3: 验证**

Run: `git check-ignore audio/x.mp3 && ls -d tools`
Expected: 输出 `audio/x.mp3` 和 `tools`（说明已忽略、目录存在）。

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: 忽略 audio/，建 tools/ 目录（语文一期脚手架）"
```

---

## Task 1: 构建期数据生成器 `tools/gen_data.py`

把汉字词库经 pypinyin 转成运行时静态 `pinyin-data.js`。核心可测点是**音频码归一化**（pypinyin 串→davinfifield 文件码），纯字符串逻辑，不依赖 pypinyin，可真 TDD。

**Files:**
- Create: `tools/gen_data.py`
- Test: `tools/test_gen_data.py`
- Produces (运行后): `pinyin-data.js`

**Interfaces:**
- Produces:
  - `normalize_code(tone3: str) -> str`：`'ma3'→'ma3'`、`'lv4'→'luu4'`、`'lü4'→'luu4'`、`'lve4'→'luue4'`、`'ju1'→'ju1'`、`'nv3'→'nuu3'`。
  - `WORLDS`：`list[dict]`，每项 `{"id":int,"name":str,"icon":str,"words":list[str]}`（仅汉字）。
  - 生成的 `pinyin-data.js` 暴露全局 `window.PINYIN_DATA`（`{汉字: {py, code}}`）与 `window.PINYIN_WORLDS`（`[{id,name,icon,words:[汉字...]}]`）。

- [ ] **Step 1: 写失败测试 `tools/test_gen_data.py`**

```python
import unittest
from gen_data import normalize_code


class NormalizeCodeTest(unittest.TestCase):
    def test_plain_syllable_unchanged(self):
        self.assertEqual(normalize_code("ma3"), "ma3")
        self.assertEqual(normalize_code("hao3"), "hao3")

    def test_v_form_to_uu(self):
        # pypinyin 默认 ü 输出为 v
        self.assertEqual(normalize_code("lv4"), "luu4")
        self.assertEqual(normalize_code("nv3"), "nuu3")

    def test_u_umlaut_to_uu(self):
        # 若 pypinyin 配置成输出 ü 字符也要兜住
        self.assertEqual(normalize_code("lü4"), "luu4")

    def test_compound_v(self):
        self.assertEqual(normalize_code("lve4"), "luue4")
        self.assertEqual(normalize_code("nve2"), "nuue2")

    def test_jqxy_u_not_touched(self):
        # ju/qu/xu/yu 里的 u 不是 ü，保持不变
        self.assertEqual(normalize_code("ju1"), "ju1")
        self.assertEqual(normalize_code("qu4"), "qu4")
        self.assertEqual(normalize_code("yu2"), "yu2")

    def test_neutral_tone_five(self):
        self.assertEqual(normalize_code("ma5"), "ma5")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd tools && python3 -m unittest test_gen_data -v` （或 `python3 test_gen_data.py`）
Expected: FAIL —— `ImportError`/`ModuleNotFoundError: gen_data` 或 `normalize_code` 未定义。

- [ ] **Step 3: 写 `tools/gen_data.py`（先让 normalize_code 通过）**

```python
#!/usr/bin/env python3
"""构建期：汉字词库 -> pinyin-data.js（运行时纯静态、零依赖）。
仅在开发机运行；产物 pinyin-data.js 入 git。需要 pypinyin: pip install pypinyin。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "pinyin-data.js")


def normalize_code(tone3):
    """pypinyin TONE3 串 -> davinfifield 文件码：ü/v -> uu。

    davinfifield 命名：普通 'ma3'，ü 写 'uu'（'lv4'->'luu4'、'lü4'->'luu4'、
    'lve4'->'luue4'），ju/qu/xu/yu 不含 ü 保持不变。轻声用末尾 5 或省略。
    拼音里不存在真正的字母 v（v 只是 ü 的替写），故直接全局替换安全。
    """
    return tone3.replace("ü", "uu").replace("v", "uu")


# 词库：仅列汉字，按一期「拼音配对挖矿」世界分组（主题+难度）。
# 取自设计文档 §5 的分级分主题字词，先用单字撑起三个世界。
WORLDS = [
    {"id": 1, "name": "启蒙草原", "icon": "var(--grass)", "words": [
        "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
        "爸", "妈", "人", "口", "手", "目", "日", "月", "水", "火",
        "山", "石", "大", "小", "上", "下"]},
    {"id": 2, "name": "万物洞穴", "icon": "var(--stone)", "words": [
        "牛", "羊", "马", "鸟", "鱼", "猫", "狗", "鸡",
        "木", "禾", "花", "草", "果", "瓜", "米", "豆",
        "红", "黄", "蓝", "绿", "白", "黑",
        "走", "跑", "看", "听", "吃", "笑"]},
    {"id": 3, "name": "词语矿井", "icon": "var(--dirt)", "words": [
        "爸爸", "妈妈", "太阳", "月亮", "星星", "小鸟",
        "老虎", "熊猫", "苹果", "学校", "老师", "朋友",
        "你好", "谢谢", "再见", "唱歌"]},
]


def build():
    try:
        from pypinyin import pinyin, Style
    except ImportError:
        sys.exit("需要 pypinyin（仅构建期）：pip install pypinyin")

    def disp(hz):
        # 整词消歧：用 pinyin(word) 让词典按上下文选音；空格分隔多字
        return " ".join(s[0] for s in pinyin(hz, style=Style.TONE))

    def codes(hz):
        # 每个字一个 davinfifield 音频码（顺序播放多字词）
        t3 = pinyin(hz, style=Style.TONE3, neutral_tone_with_five=True)
        return [normalize_code(s[0]) for s in t3]

    data = {}
    poly = []  # 多音字人工复核清单
    seen_multi = set()
    for w in WORLDS:
        for hz in w["words"]:
            if hz in data:
                continue
            ms = pinyin(hz, heteronym=True)
            if any(len(s) > 1 for s in ms) and hz not in seen_multi:
                poly.append(f"{hz}\t{ms}")
                seen_multi.add(hz)
            data[hz] = {"py": disp(hz), "code": codes(hz)}

    worlds = [{"id": w["id"], "name": w["name"], "icon": w["icon"], "words": w["words"]}
              for w in WORLDS]

    js = (
        "/* 自动生成，勿手改。源：tools/gen_data.py（pypinyin）。 */\n"
        "window.PINYIN_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"
        "window.PINYIN_WORLDS = " + json.dumps(worlds, ensure_ascii=False) + ";\n"
    )
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(js)
    with open(os.path.join(HERE, "polyphone_review.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(poly))
    print(f"已写 {OUT}：{len(data)} 字/词，{len(worlds)} 世界；多音字待复核 {len(poly)} 条。")


if __name__ == "__main__":
    build()
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd tools && python3 -m unittest test_gen_data -v`
Expected: PASS（全部 6 个用例绿）。

- [ ] **Step 5: 真跑生成器，核对 pypinyin 实际输出**

```bash
# venv 已建好并装了 pypinyin（清华镜像）。如需重建：
#   python3 -m venv .venv-tools
#   .venv-tools/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pypinyin
.venv-tools/bin/python3 tools/gen_data.py
```
Expected: 打印「已写 …/pinyin-data.js：NN 字/词，3 世界…」。
然后抽查产物，确认 ü 字映射正确（pypinyin 输出 `绿`→`lv4`、`女`→`nv3`，归一化后应为 `luu4`/`nuu3`）：

Run: `grep -o '"绿":{[^}]*}' pinyin-data.js`
Expected: 形如 `"绿":{"py":"lǜ","code":["luu4"]}`（**`luu4`**，已实测 pypinyin 0.55 输出 `lv4`，`normalize_code` 转 `luu4`）。

- [ ] **Step 6: Commit**

```bash
git add tools/gen_data.py tools/test_gen_data.py pinyin-data.js tools/polyphone_review.txt
git commit -m "feat: gen_data.py 构建期生成 pinyin-data.js（pypinyin，ü->uu 对齐 davinfifield）"
```

---

## Task 2: 服务器放行音频静态文件（扩展名 + MIME）

让 `audio/*.mp3` 能被现有静态服务托管（当前会 404）。

**Files:**
- Modify: `server.py:26-29`（`ALLOWED_STATIC_EXT`）, `server.py:214-229`（`_content_type`）
- Test: `test_server.py`

**Interfaces:**
- Produces: GET `/audio/<x>.mp3` 命中真实文件时返回 200 + `Content-Type: audio/mpeg`。

- [ ] **Step 1: 写失败测试（加到 `test_server.py`）**

`test_server.py` 已有 `ServerHTTPTests`（`setUp` 起临时服务器，提供 `self.web_dir`/`self.port`）。在该类里加一个方法（需要读 header，故用已 import 的 `http.client` 内联请求，而非只返回 `(status,data)` 的模块级 `_get`）：

```python
    def test_serves_mp3_with_audio_mime(self):
        audio_dir = os.path.join(self.web_dir, "audio", "pinyin")
        os.makedirs(audio_dir, exist_ok=True)
        with open(os.path.join(audio_dir, "ma3.mp3"), "wb") as f:
            f.write(b"ID3fake")
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request("GET", "/audio/pinyin/ma3.mp3")
        r = c.getresponse(); body = r.read()
        self.assertEqual(r.status, 200)
        self.assertEqual(r.getheader("Content-Type"), "audio/mpeg")
        self.assertEqual(body, b"ID3fake")
        c.close()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest test_server.ServerHTTPTests.test_serves_mp3_with_audio_mime -v`
Expected: FAIL —— 状态码 404（扩展名未放行）。

- [ ] **Step 3: 改 `server.py` 两处**

`ALLOWED_STATIC_EXT`（26-29 行）追加音频后缀：

```python
ALLOWED_STATIC_EXT = {
    ".html", ".css", ".js", ".woff2", ".woff", ".ttf",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".m4a", ".mp3", ".aac", ".ogg", ".wav",   # 离线发音音频
}
```

`_content_type`（214-229 行）的元组里补音频 MIME（`.m4a` 必须 `audio/mp4`，iOS 才肯播）：

```python
        (".mp3", "audio/mpeg"),
        (".m4a", "audio/mp4"),
        (".aac", "audio/aac"),
        (".ogg", "audio/ogg"),
        (".wav", "audio/wav"),
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m unittest test_server.ServerHTTPTests.test_serves_mp3_with_audio_mime -v`
Expected: PASS。

- [ ] **Step 5: 回归全部服务器测试**

Run: `python3 test_server.py`
Expected: 全绿（未破坏既有用例）。

- [ ] **Step 6: Commit**

```bash
git add server.py test_server.py
git commit -m "feat(server): 放行 audio/*.mp3 静态托管 + 正确 MIME"
```

---

## Task 3: 服务器音频拉取端点 `/api/audio/status` 与 `/api/audio/fetch`

服务器用标准库下载 davinfifield zip 并解压到 `audio/pinyin/`。把「解压」抽成可测纯函数 `extract_pinyin_mp3`，对它做真 TDD（含 zip-slip 防御），真实 `urllib` 下载作薄封装手动验证。

**Files:**
- Modify: `server.py`（加模块函数 `extract_pinyin_mp3`、`_download_zip`；`make_server` 加 `audio_dir`/`audio_lock`；`do_GET`/`do_POST` 路由；两个处理函数）
- Test: `test_server.py`

**Interfaces:**
- Consumes: Task 2 的静态托管（拉下来的文件随后由 `/audio/...` 提供）。
- Produces:
  - `extract_pinyin_mp3(zip_bytes: bytes, dest_dir: str) -> int`：把 zip 里所有 `*.mp3` **按 basename 拍平**写进 `dest_dir`，返回写入数；对越界条目（zip-slip）跳过不写。
  - `GET /api/audio/status` → `{"ok":true,"ready":bool,"have":int}`。
  - `POST /api/audio/fetch` → 成功 `{"ok":true,"have":int}`；失败 `{"ok":false,"error":str}` + 5xx。

- [ ] **Step 1: 写失败测试（加到 `test_server.py`）—— 解压与 zip-slip**

在 `test_server.py` 顶部 import 区补 `import io` 和 `import zipfile`（`tempfile`/`os`/`json`/`unittest` 已有）。新增独立测试类（用 `server.extract_pinyin_mp3`，与文件内 `server.valid_name` 同风格）：

```python
class ExtractAudioTest(unittest.TestCase):
    def _zip(self, names):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for n in names:
                z.writestr(n, b"ID3" + n.encode("utf-8", "ignore"))
        return buf.getvalue()

    def test_flattens_mp3_by_basename(self):
        d = tempfile.mkdtemp()
        zb = self._zip([
            "mp3-chinese-pinyin-sound-master/mp3/ma3.mp3",
            "mp3-chinese-pinyin-sound-master/mp3/luu4.mp3",
            "mp3-chinese-pinyin-sound-master/README.md",   # 非 mp3 跳过
        ])
        n = server.extract_pinyin_mp3(zb, d)
        self.assertEqual(n, 2)
        self.assertTrue(os.path.exists(os.path.join(d, "ma3.mp3")))
        self.assertTrue(os.path.exists(os.path.join(d, "luu4.mp3")))
        self.assertFalse(os.path.exists(os.path.join(d, "README.md")))

    def test_rejects_zip_slip(self):
        d = tempfile.mkdtemp()
        zb = self._zip(["../../evil.mp3", "ok/ma1.mp3"])
        server.extract_pinyin_mp3(zb, d)
        # 恶意条目被 basename 拍平成 d/evil.mp3，留在 dest 内，绝不逃逸到上级目录
        self.assertTrue(os.path.exists(os.path.join(d, "ma1.mp3")))
        self.assertFalse(os.path.exists(os.path.abspath(os.path.join(d, "..", "..", "evil.mp3"))))
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest test_server.ExtractAudioTest -v`
Expected: FAIL —— `ImportError: cannot import name 'extract_pinyin_mp3'`。

- [ ] **Step 3: 在 `server.py` 顶部加导入与解压/下载函数**

在 import 区补 `import io, zipfile, urllib.request`，并加模块级函数（放在 `_content_type` 附近）：

```python
AUDIO_ZIP_URL = ("https://codeload.github.com/davinfifield/"
                 "mp3-chinese-pinyin-sound/zip/refs/heads/master")


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


def _download_zip(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "MathMiner/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()
```

- [ ] **Step 4: 跑解压测试确认通过**

Run: `python3 -m unittest test_server.ExtractAudioTest -v`
Expected: PASS（2 用例绿）。

- [ ] **Step 5: `make_server` 挂上 audio_dir / audio_lock**

在 `make_server`（232-239 行）`return srv` 前加：

```python
    srv.audio_dir = os.path.join(srv.web_dir, "audio", "pinyin")
    srv.ready_sentinel = os.path.join(srv.web_dir, "audio", ".ready")
    srv.audio_lock = threading.Lock()
```

- [ ] **Step 6: 加路由与处理函数**

`do_GET`（59-68 行）在 `/api/save` 分支旁加：

```python
        if path == "/api/audio/status":
            return self._audio_status()
```

`do_POST`（70-77 行）加：

```python
        if path == "/api/audio/fetch":
            return self._audio_fetch()
```

在「API 处理」区加两个方法：

```python
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
            try:
                data = _download_zip(AUDIO_ZIP_URL)
                n = extract_pinyin_mp3(data, self.server.audio_dir)
            except Exception as e:                         # 网络/解压失败：不写哨兵，可重试
                return self._send_json(502, {"ok": False, "error": "下载失败：" + str(e)})
            with open(self.server.ready_sentinel, "w") as f:
                f.write("ok")
            return self._send_json(200, {"ok": True, "have": n})
```

- [ ] **Step 7: 写并跑 status 端点测试**

在 `ServerHTTPTests` 类里加（用模块级 `_get(self.port, path)`，返回 `(status, data)`）：

```python
    def test_audio_status_not_ready_initially(self):
        status, data = _get(self.port, "/api/audio/status")
        self.assertEqual(status, 200)
        j = json.loads(data)
        self.assertFalse(j["ready"])
        self.assertEqual(j["have"], 0)
```

Run: `python3 -m unittest test_server.ExtractAudioTest test_server.ServerHTTPTests.test_audio_status_not_ready_initially test_server.ServerHTTPTests.test_serves_mp3_with_audio_mime -v`
Expected: PASS。

- [ ] **Step 8: 回归全部服务器测试 + 真实下载冒烟（需联网）**

Run: `python3 test_server.py`
Expected: 全绿。

可选联网冒烟（确认真链接可用）：
```bash
python3 -c "import server; d=server._download_zip(server.AUDIO_ZIP_URL); print(len(d), 'bytes'); print(server.extract_pinyin_mp3(d, 'audio/pinyin'), 'mp3')"
ls audio/pinyin/ma3.mp3 audio/pinyin/luu3.mp3
```
Expected: 打印若干 MB、~1000 mp3；两个抽样文件存在。（跑完可删 `audio/` 让前端走首次下载流程。）

- [ ] **Step 9: Commit**

```bash
git add server.py test_server.py
git commit -m "feat(server): /api/audio/status + /api/audio/fetch（urllib+zipfile，含 zip-slip 防御与并发锁）"
```

---

## Task 4: 前端「选学科」导航（`#subjects` 屏 + 分流）

在标题与玩法之间插入学科选择层，并把 `G.goModes` 改成按学科渲染玩法卡。

**Files:**
- Modify: `index.html`（`#title` 按钮 :210；`#modes` 段 :230-246；`G.goModes` 覆盖定义 :991；`G` 对象加方法）

**Interfaces:**
- Consumes: 现有 `show(id)`、`.world` 卡样式、`G.goWorlds`、`M.start`。
- Produces: `G.goSubjects()`、`G.goModes(subj)`、`renderModes(subj)`；`S.subject` 被设置为 `'math'|'cn'`。

- [ ] **Step 1: 加 `#subjects` 屏**

在 `#title` 段（204-212 行）之后、`#modes` 段之前插入：

```html
  <!-- SUBJECT SELECT -->
  <section id="subjects" class="screen">
    <div class="userBar"><span id="subjBadge"></span>
      <button class="btn gray" style="font-size:11px;padding:6px 10px" onclick="show('title')">↩ 标题</button></div>
    <div class="logo pix" style="font-size:20px">选择学科</div>
    <div style="display:grid;gap:14px;margin-top:22px">
      <div class="world" style="background:linear-gradient(135deg,var(--cyan),rgba(0,0,0,.25))" onclick="G.goModes('math')">
        <div class="wicon" style="background:var(--cyan)"></div>
        <div><h3>➗ 数学</h3><p>挖方块 · 学加减 · 凑十法</p></div>
      </div>
      <div class="world" style="background:linear-gradient(135deg,var(--grass),rgba(0,0,0,.25))" onclick="G.goModes('cn')">
        <div class="wicon" style="background:var(--grass)"></div>
        <div><h3>📖 语文拼音</h3><p>汉字配拼音 · 挖方块学拼音</p></div>
      </div>
    </div>
    <p class="tip" style="margin-top:20px">矿石、镐子、皮肤、星星 两科共享 · 进度自动存档</p>
  </section>
```

- [ ] **Step 2: 标题按钮改为进学科选择**

`index.html:210`，把 `onclick="G.goModes()"` 改为 `onclick="G.goSubjects()"`。

- [ ] **Step 3: `#modes` 段改为动态容器**

把 `#modes` 段（230-246 行）内写死的两张数学卡所在容器，替换为一个空容器 `id="modeList"`，并保留底部「清空进度」按钮：

```html
  <!-- MODE SELECT -->
  <section id="modes" class="screen">
    <div class="logo pix" style="font-size:20px" id="modeTitle">选择玩法</div>
    <div style="display:grid;gap:14px;margin-top:22px" id="modeList"></div>
    <p class="tip" style="margin-top:20px" id="modeTip">矿石、镐子、皮肤共享 · 进度自动存档</p>
    <div style="text-align:center;margin-top:12px">
      <button class="btn gray" style="font-size:12px;padding:8px 16px" onclick="if(confirm('确定清空所有存档进度吗？')) resetSave()">🗑️ 清空进度</button>
    </div>
  </section>
```

- [ ] **Step 4: 实现 `goSubjects` / `goModes` / `renderModes`**

把 `index.html:991` 的 `G.goModes = function(){ show('modes'); };` 替换为：

```javascript
G.goSubjects = function(){ const b=$('subjBadge'); if(b) b.textContent='👤 '+(Auth.user||''); show('subjects'); };
G.goModes = function(subj){ S.subject = subj||S.subject||'math'; renderModes(S.subject); show('modes'); };
function renderModes(subj){
  const list=$('modeList');
  $('modeTitle').textContent = subj==='cn' ? '语文 · 选择玩法' : '数学 · 选择玩法';
  if(subj==='cn'){
    list.innerHTML = `
      <div class="world" style="background:linear-gradient(135deg,var(--grass),rgba(0,0,0,.25))" onclick="PG.start()">
        <div class="wicon" style="background:var(--grass)"></div>
        <div><h3>🔤 拼音配对挖矿</h3><p>汉字配拼音，挖方块学认读</p></div>
      </div>`;
  } else {
    list.innerHTML = `
      <div class="world" style="background:linear-gradient(135deg,var(--grass),rgba(0,0,0,.25))" onclick="G.goWorlds()">
        <div class="wicon" style="background:var(--grass)"></div>
        <div><h3>⛏️ 配对挖矿</h3><p>题目配答案，挖方块学加减</p></div>
      </div>
      <div class="world" style="background:linear-gradient(135deg,var(--cyan),rgba(0,0,0,.25))" onclick="M.start()">
        <div class="wicon" style="background:var(--cyan)"></div>
        <div><h3>💥 数字消消乐</h3><p>连成一串凑出目标数字</p></div>
      </div>`;
  }
}
```

> 说明：`PG.start` 在 Task 6 定义；本步先让数学路径完整工作，语文卡点击暂时报未定义（下一任务补）。

- [ ] **Step 5: 手动验收（数学路径不破）**

```bash
python3 server.py
```
打开 `http://localhost:8000`，登录任意玩家：
- 点「开始游戏」→ 应进**新的「选择学科」屏**，有 ➗数学 / 📖语文 两卡。
- 点「➗数学」→ 进玩法屏，显示**配对挖矿 + 数字消消乐**两卡，标题为「数学 · 选择玩法」。
- 玩一把配对挖矿与消消乐，确认与改版前一致（世界、挖矿、升镐、皮肤都正常）。
- 「🏠 玩法」「↩ 标题」返回键工作。
- 点「📖语文」→ 玩法屏显示「拼音配对挖矿」一卡（点它此刻控制台报 `PG is not defined`，预期，下个任务补）。

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(ui): 新增选学科屏，玩法列表按学科分流（数学路径不变）"
```

---

## Task 5: 前端接入拼音数据与语文状态/存档字段

引入 `pinyin-data.js`，加 `S.subject`/`S.pyMatchStage`，并纳入存档（带兜底）。

**Files:**
- Modify: `index.html`（`<head>`/脚本前引入数据；`freshState` :418-424；`SAVE_FIELDS` :446；`applySave` :496-502）

**Interfaces:**
- Consumes: `window.PINYIN_DATA`、`window.PINYIN_WORLDS`（Task 1 产物）。
- Produces: `S.subject`、`S.pyMatchStage`（`{1:0,2:0,3:0}`，按拼音世界 id 记进度）；二者随存档持久化。

- [ ] **Step 1: 引入数据脚本**

在主 `<script>`（367 行那段）**之前**加一行外链（放在 `</head>`/首个 `<script>` 之前即可，确保 `window.PINYIN_DATA` 先就绪）：

```html
<script src="/pinyin-data.js"></script>
```

- [ ] **Step 2: `freshState` 加字段**

`freshState`（418-424 行）的返回对象里追加：

```javascript
    subject:'math',
    pyMatchStage:{1:0,2:0,3:0},
```

- [ ] **Step 3: `SAVE_FIELDS` 追加**

`index.html:446` 改为：

```javascript
const SAVE_FIELDS=['res','tool','skinsOwned','skin','stage','crushStage','stars','totalCleared','pyMatchStage'];
```

> `subject` 是会话内导航态，不必入档（每次从学科屏选）；只持久化进度 `pyMatchStage`。

- [ ] **Step 4: `applySave` 兜底**

在 `applySave`（496-502 行）里、`S.stage = Object.assign(...)` 那行旁加：

```javascript
  S.pyMatchStage = Object.assign({1:0,2:0,3:0}, S.pyMatchStage||{});
```

- [ ] **Step 5: 手动验收（数据已加载、旧档不崩）**

`python3 server.py`，打开页面，开浏览器控制台：
- 输入 `Object.keys(PINYIN_DATA).length` → 应为 Task 1 生成的字/词数（>0）。
- 输入 `PINYIN_DATA['妈']` → 应为 `{py:'mā', code:['ma1']}`。
- 输入 `PINYIN_WORLDS.length` → `3`。
- 用一个**老存档**玩家登录（或先清空再玩数学存一次），确认控制台无报错、`S.pyMatchStage` 为 `{1:0,2:0,3:0}`。

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(ui): 引入 pinyin-data.js，加 subject/pyMatchStage 状态与存档兜底"
```

---

## Task 6: 拼音配对挖矿引擎（泛化配对引擎 `G`）

新增 `PG` 入口，复用 `G` 的世界/难度/挖矿/技能/HUD，仅替换世界表、题库与 tile 字体。

**Files:**
- Modify: `index.html`（`diffFor` :390-398；`G.renderWorlds` :539-553；`G.startWorld` :555-566；`G.buildBoard` :568-594；`G.renderBoard` :596-611；`G.success` :658-670；`G.win`/`nextLevel` :753-767；样式区加 `.tile.cn`）。新增 `PG` 对象。

**Interfaces:**
- Consumes: `PINYIN_WORLDS`、`PINYIN_DATA`、`S.subject`、`S.pyMatchStage`、现有 `G.*`/`shuffle`/`rand`。
- Produces: `PG.start()`（进语文配对世界选择）；`G` 各方法在 `S.subject==='cn'` 下走拼音分支。

- [ ] **Step 1: 加中文 tile 字体样式**

在 `.tile .val{...}`（105 行）附近加：

```css
  .tile.cn .val{font-family:var(--cn);font-size:20px;font-weight:700;}
  .tile.cn{justify-content:center;}
```

- [ ] **Step 2: `diffFor` 支持拼音世界**

把 `diffFor`（390-398 行）改为按学科取世界表，并对拼音关闭点阵：

```javascript
function diffFor(world, stage){
  const cn = S.subject==='cn';
  const list = cn ? PINYIN_WORLDS : WORLDS;
  const w = list[world-1];
  if(cn){
    const pairs = Math.min(4 + Math.floor(stage/1), 8);   // 4→8 对随关卡上升
    return {pairs, dots:false, cn:true, dl:Math.min(4,stage)};
  }
  const maxN = Math.min(w.max + stage*w.step, w.cap);
  const pairs = Math.min(w.pairs + Math.floor(stage/2), 8);
  const dots = w.op==='add' && maxN<=20;
  const span = (w.cap - w.max) || 1;
  const dl = Math.max(0, Math.min(4, Math.round((maxN - w.max)/span*4)));
  return {maxN, minN:w.min, pairs, dots, op:w.op, dl};
}
```

- [ ] **Step 3: 加 `PG` 入口 + 拼音世界选择**

在 `M` 对象定义之后（990 行附近）加：

```javascript
const PG = {
  start(){ S.subject='cn'; this.goWorlds(); },
  goWorlds(){ this.renderWorlds(); show('worlds'); },
  renderWorlds(){
    G.renderRes('resBarW');
    $('worldList').innerHTML = PINYIN_WORLDS.map(w=>{
      const st=S.pyMatchStage[w.id]||0;
      return `
      <div class="world" style="background:linear-gradient(135deg,${w.icon},rgba(0,0,0,.25))" onclick="PG.startWorld(${w.id})">
        <div class="wicon" style="background:${w.icon}"></div>
        <div style="flex:1"><h3>${w.id}. ${w.name} <span style="font-size:12px;color:var(--gold)">第${st+1}关</span></h3>
          <p>汉字配拼音 · 共 ${w.words.length} 字</p></div>
      </div>`;
    }).join('');
  },
  startWorld(id){
    S.subject='cn'; S.world=id; S.curStage=S.pyMatchStage[id]||0;
    S.diff=diffFor(id, S.curStage);
    S.maxHearts = S.tool>=2?6:5; if(S.tool>=4) S.maxHearts=7;
    S.hearts=S.maxHearts; S.skillUses={}; S.shield=false;
    SKILLS.forEach(s=>{ if(S.tool>=s.tier) S.skillUses[s.key]=s.uses; });
    G.buildBoard(); show('game');
  },
};
```

- [ ] **Step 4: `G.buildBoard` 分流题库**

在 `buildBoard`（568 行）开头、`const d=S.diff;` 之后加拼音分支（数学逻辑保持原样，包到 else 里或提前 return）：

```javascript
  buildBoard(){
    const d = S.diff;
    if(S.subject==='cn'){ return this.buildPinyinBoard(d); }
    // …(原数学生成逻辑不变)…
```

并在 `G` 里新增方法：

```javascript
  buildPinyinBoard(d){
    const w = PINYIN_WORLDS[S.world-1];
    const pool = shuffle(w.words.slice()).slice(0, d.pairs);
    const pairs = pool.map(hz=>({txt:hz, ans:(PINYIN_DATA[hz]||{}).py||hz, code:(PINYIN_DATA[hz]||{}).code||[]}));
    let tiles=[];
    pairs.forEach((p,i)=>{
      tiles.push({k:'q',pid:i,txt:p.txt,done:false});
      tiles.push({k:'a',pid:i,ans:p.ans,code:p.code,done:false});
    });
    shuffle(tiles);
    S.board=tiles; S.sel=null; S.busy=false;
    this.renderHUD(); this.renderBoard(); this.renderSkills();
    $('worldName').innerHTML = `${w.name} · 第${S.curStage+1}关`;
  },
```

- [ ] **Step 5: `G.renderBoard` 给拼音 tile 上中文字体、关点阵**

`renderBoard`（596-611 行）里给 q/a tile 的 class 按学科加 `cn`，并保持 `dots` 受 `d.dots` 控制（拼音已为 false）。最小改动：把两处 `class="tile q ..."`/`class="tile a ..."` 改成带条件类：

```javascript
      const cnc = S.subject==='cn' ? ' cn' : '';
      if(t.k==='q'){
        return `<button class="tile q${cnc} ${S.sel===i?'sel':''}" data-i="${i}">
          <span class="tag pix">${S.subject==='cn'?'汉字':'题目'}</span><span class="val">${t.txt}</span></button>`;
      }else{
        let dd='';
        if(dots){ let s=''; for(let n=0;n<Math.min(t.ans,20);n++) s+=`<span class="dot"></span>`; dd=`<div class="dots">${s}</div>`; }
        return `<button class="tile a${cnc} ${S.sel===i?'sel':''}" data-i="${i}">
          <span class="tag pix">${S.subject==='cn'?'拼音':'答案'}</span><span class="val">${t.ans}</span>${dd}</button>`;
      }
```

- [ ] **Step 6: `G.success` 配对成功播音（占位，Task 7 接真音频）**

`success`（658-670 行）在 `beep('good');` 后加（`playPy` 在 Task 7 定义；先用可选链避免未定义报错）：

```javascript
    if(S.subject==='cn' && typeof playPy==='function'){
      const codes=(S.board[i].code||S.board[j].code||[]);
      playPy(codes);
    }
```

- [ ] **Step 7: `win`/`nextLevel` 按学科记进度**

`nextLevel`（767 行）现为 `S.stage[S.world]++`。改为按学科：

```javascript
  nextLevel(){ this.close('winOv');
    if(S.subject==='cn') S.pyMatchStage[S.world]=(S.pyMatchStage[S.world]||0)+1;
    else S.stage[S.world]++;
    toast('🔥 难度提升！'); (S.subject==='cn'?PG:this).startWorld(S.world); },
```

`win`（753-766 行）里宝箱矿石 `const k=[...][Math.min(S.world,4)-1]` 对拼音世界（id 1-3）仍取得到合法矿石，无需特改；如需更稳，cn 时固定 `k='stone'`。`retry`（768 行）对 cn 调 `PG.startWorld`：

```javascript
  retry(){ this.close('loseOv'); (S.subject==='cn'?PG:this).startWorld(S.world); },
```

- [ ] **Step 8: 「🏠 地图」返回键按学科**

`#game` 段（296-300 行）的「🏠 地图」`onclick="G.goWorlds()"` 改为 `onclick="(S.subject==='cn'?PG:G).goWorlds()"`。

- [ ] **Step 9: 手动验收（完整拼音配对闭环）**

`python3 server.py`，登录：
- 选「📖语文」→「🔤拼音配对挖矿」→ 进世界选择，3 个拼音世界。
- 进「启蒙草原」：棋盘出现**汉字 tile（妈/八…）与拼音 tile（mā/bā…）**，中文清晰不乱码、无点阵。
- 点「妈」再点「mā」→ 配对成功消除、挖到矿、加星、连击；点错扣心。
- 通关 → 弹「通关」→「再来一关」难度上升（对数增多）；血量耗尽→重试。
- 「🏠 地图」回到拼音世界；进度 `S.pyMatchStage` 记到对应世界。
- 切回「➗数学」玩一把，确认数学世界/难度/挖矿仍全部正常（泛化未伤数学）。

- [ ] **Step 10: Commit**

```bash
git add index.html
git commit -m "feat(ui): 拼音配对挖矿（泛化配对引擎 PG，复用挖矿/技能/HUD/存档）"
```

---

## Task 7: 运行时发音（`playPy` + iOS 解锁 + `#audioFetch` 下载屏）

进入语文时确保音频就绪（缺则自动下载），配对成功与点拼音 tile 时发音。

**Files:**
- Modify: `index.html`（`beep()` :430 旁加 `playPy`/解锁；`G.goModes('cn')` 入口接下载检查；加 `#audioFetch` 屏）

**Interfaces:**
- Consumes: `/api/audio/status`、`/api/audio/fetch`（Task 3）；`S.board[].code`（Task 6）。
- Produces: 全局 `playPy(codes)`；`Audio.ensureReady()` 流程；`#audioFetch` 屏。

- [ ] **Step 1: 加 `#audioFetch` 下载屏**

在 `#subjects` 段后插入：

```html
  <!-- AUDIO FETCH -->
  <section id="audioFetch" class="screen" style="text-align:center;padding-top:40px">
    <div class="logo pix" style="font-size:18px">📥 准备发音</div>
    <p class="tip" id="afMsg" style="margin-top:18px">首次进入语文，正在下载发音资源…</p>
    <div class="tip" style="font-size:28px;margin-top:18px">⏳</div>
    <div class="closeRow" id="afActions" style="margin-top:22px;display:none">
      <button class="btn green" onclick="Audio2.retry()">重试 🔄</button>
      <button class="btn gray" onclick="Audio2.skip()">继续（暂无发音）</button>
    </div>
  </section>
```

- [ ] **Step 2: 加 `playPy` 与 iOS 解锁（`beep()` 旁，430 行附近）**

```javascript
const _pyPool = new Map();
let _audioUnlocked = false;
// 极小静音 WAV（44 字节、0 采样），仅用于在用户手势内解锁 iOS 的 HTML5 Audio。
const _SILENT_WAV = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA=';
function _unlockAudio(){
  if(_audioUnlocked) return; _audioUnlocked = true;
  try{ const a=new Audio(_SILENT_WAV); a.volume=0; a.play().catch(()=>{}); }catch(e){}
  // 兜底：真正的发音都从点击回调(success/tap)内触发，本身就在手势链里。
}
function playPy(codes){
  const list = Array.isArray(codes) ? codes : [codes];
  let i=0;
  const step=()=>{
    if(i>=list.length) return;
    const code=list[i++]; if(!code){ return step(); }
    let a=_pyPool.get(code);
    if(!a){ a=new Audio('/audio/pinyin/'+code+'.mp3'); _pyPool.set(code,a); }
    a.currentTime=0;
    a.onended=()=>setTimeout(step,120);   // 多字词顺序播，间隔 120ms
    a.play().catch(()=>{});
  };
  step();
}
```

- [ ] **Step 3: 加 `Audio2` 就绪流程，并在进语文时拦截**

```javascript
const Audio2 = {
  ready:false,
  async ensure(){           // 返回 true=可继续进语文
    if(this.ready) return true;
    try{
      const r=await fetch('/api/audio/status'); const j=await r.json();
      if(j.ready){ this.ready=true; return true; }
    }catch(e){}
    return false;
  },
  async gate(){             // 进语文前调用：就绪直接放行，否则进下载屏
    if(await this.ensure()) return true;
    show('audioFetch'); $('afActions').style.display='none';
    $('afMsg').textContent='首次进入语文，正在下载发音资源…';
    try{
      const r=await fetch('/api/audio/fetch',{method:'POST'}); const j=await r.json();
      if(j.ok){ this.ready=true; return true; }
      throw new Error(j.error||'下载失败');
    }catch(e){
      $('afMsg').textContent='发音下载失败（服务器可能没联网）。可重试，或先无发音游玩。';
      $('afActions').style.display='flex';
      return false;          // 等用户在下载屏点重试/跳过
    }
  },
  retry(){ this.ready=false; G.enterCn(); },
  skip(){ this.ready=false; G.goModes('cn'); },   // 降级：无发音继续
};
```

- [ ] **Step 4: 让「📖语文」先过音频闸**

把 `#subjects` 里 `onclick="G.goModes('cn')"` 改为 `onclick="_unlockAudio();G.enterCn()"`，并在 `G` 加：

```javascript
G.enterCn = async function(){
  _unlockAudio();
  const ok = await Audio2.gate();
  if(ok) G.goModes('cn');     // 失败时停在 #audioFetch，由用户选重试/跳过
};
```

> 数学卡保持 `onclick="G.goModes('math')"` 不变（数学不需要音频）。

- [ ] **Step 5: 点拼音 tile 也发音（可选增强）**

`G.tap`（645 行）里，当点中的是拼音答案 tile 且为语文时播一次：在 `if(S.sel===null){ S.sel=i; ... }` 分支内加：

```javascript
      if(S.subject==='cn'){ const t2=S.board[i]; if(t2 && t2.k==='a' && t2.code) playPy(t2.code); }
```

- [ ] **Step 6: 手动验收（含三种网络情形）**

`python3 server.py`：
1. **音频已就绪**（先 `ls audio/pinyin` 有文件、有 `audio/.ready`）：选「📖语文」→ 应**直接进**玩法，配对成功能听到发音，点拼音 tile 也发音。
2. **首次未就绪**（`rm -rf audio/` 后重启）：选「📖语文」→ 进「准备发音」屏 → 自动下载 → 成功后进玩法、有声。
3. **服务器断网模拟**（临时把 `AUDIO_ZIP_URL` 改成坏地址或拔网）：选「📖语文」→ 下载失败 → 出现「重试 / 继续（暂无发音）」→ 点「继续」能进玩法、静默无声但不卡死、可正常配对挖矿。（验完恢复 URL）

iPad/iPhone（同 WiFi 用局域网地址）抽测：选语文那次点击后，配对成功能出声（验证 iOS 手势解锁与 `audio/mp4`/`audio/mpeg` MIME）。

- [ ] **Step 7: Commit**

```bash
git add index.html
git commit -m "feat(ui): 运行时发音——playPy + iOS 解锁 + 首次进语文自动下载（含失败降级）"
```

---

## Task 8: 文档与端到端收尾

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: 全部前序任务。

- [ ] **Step 1: 更新 README**

在「文件结构」「离线说明」处补：

```markdown
## 语文 · 拼音

进标题后选「📖 语文拼音」即可玩「拼音配对挖矿」（汉字配拼音）。矿石/镐子/皮肤/星星与数学**共享**。

**发音**：首次进入语文时，**服务器**会自动从公共领域音频库下载真人发音到 `audio/`（约 10–30MB，仅服务器联网一次；之后手机/平板始终离线播放）。服务器若没联网，会提示「继续（暂无发音）」，游戏仍可玩。`audio/` 不纳入 git。

**重新生成字词数据**（仅在改了 `tools/gen_data.py` 词库后）：

    .venv-tools/bin/python3 tools/gen_data.py   # 重新生成 pinyin-data.js

（`pypinyin` 装在仓库根 `.venv-tools/` venv，不入 git；若不存在需一次性 `python3 -m venv .venv-tools && .venv-tools/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pypinyin`）
```

- [ ] **Step 2: 全量回归测试**

Run: `python3 test_server.py && (cd tools && python3 -m unittest test_gen_data -v)`
Expected: 全绿。

- [ ] **Step 3: 端到端冒烟清单**

`python3 server.py`，从零（清空进度）走一遍：登录 → 选学科 → 数学玩一把（不回归坏）→ 语文首次下载发音 → 拼音配对挖矿通关 → 用攒的矿石升镐/换皮肤 → 切玩家再登录，确认 `pyMatchStage` 进度保留。

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: README 补语文拼音玩法与发音获取说明"
```

---

## 一期完成定义（DoD）

- 标题 → 选学科 → 数学/语文 两条路径都能玩；数学完全无回归。
- 语文「拼音配对挖矿」：3 个世界、汉字↔拼音配对、挖矿/技能/升镐/皮肤/星星与数学共享、进度持久化。
- 发音：首次服务器自动下载，之后离线播放；服务器无网时优雅降级不阻断。
- 运行时仍零第三方依赖；`audio/` 不入 git，`pinyin-data.js` 入 git。
- `python3 test_server.py` 与 `tools/test_gen_data.py` 全绿。

## 后续（不在本计划）

- **二期**：👂听音找字 + 🎵声调小游戏（轻量引擎，复用本期音频与样式）。
- **三期**：🧩拼音拼读（新 PM 引擎；7 个课本顺序的拼音世界在此用上）。
- 双字词顺序发音、premium/edge-tts 音质升级、多音字 `polyphone_review.txt` 人工过审。
