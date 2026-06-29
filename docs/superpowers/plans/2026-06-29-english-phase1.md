# 英语矿工 一期（词义配对挖矿闭环）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在「方块数学矿工」里加第三学科 📕 英语，跑通 登录 → 选英语 → 词义配对挖矿（中↔英、点击发音）→ 挖矿升镐 的完整闭环，并支持自主命题（自录词 + 服务器现生成发音）。

**Architecture:** 复用现有像素配对引擎与共享经济。英语数据由构建脚本 `tools/gen_en_data.py` 生成 `en-data.js`（`window.EN_DATA`）；默认发音包构建期用 TTS 经 `urllib` 生成 `audio/en/*.mp3` 并入 git；自主命题发音由 `server.py` 新增 `/api/en/tts` 按需经 `urllib` 现生成、缓存、离线静音降级。前端新增 `playEn()`、英语题库与配对引擎 `EG`，全部挂在现有 `S.subject` 三态（`math`/`cn`/`en`）上。

**Tech Stack:** 纯 Python 标准库（server.py / 构建脚本运行时）、构建期 TTS（Google translate_tts HTTP，`urllib`，可选 edge-tts 升级）、香草 JS + HTML5 Audio（前端，零库）。

## Global Constraints

（每个任务的要求都隐含包含本节，数值逐字照设计文档 `docs/superpowers/specs/2026-06-29-english-game-design.md`。）

- **运行时零第三方依赖**：`server.py` 与前端只用标准库 / 浏览器原生 API。第三方 TTS 只在构建期或服务器「现生成」时经 `urllib` 调用，不引入任何 pip 包到 `server.py`。
- **游玩设备永远离线**：手机/平板从本地服务器取静态 mp3；只有服务器在「生成新发音」时短暂联网，失败则静音降级、不阻断游戏。
- **共享经济**：矿石（wood/stone/iron/diamond）、星星 ★、镐子 `S.tool`、技能、皮肤、心，跨学科共享同一份存档；英语不新增任何经济字段。
- **题库数据是 `.js` 不是 `.json`**：`en-data.js` 用 `window.EN_DATA=...`；严禁产出 `.json`（会让静态白名单泄漏 `data/<玩家>.json` 存档）。
- **audio key 规则（前后端必须逐字一致）**：`text.strip().lower()` → 把 `[^a-z0-9]+` 替换为 `_` → 去首尾 `_`。例：`"Apple"→"apple"`、`"ice cream"→"ice_cream"`、`"I like apples."→"i_like_apples"`。
- **不绑课本**：英语题库只有「主题默认」与「自主命题」两种，**不做「跟着课本」**。
- **像素风一致**：复用 `.tile` / `.world` / HUD / `winOv` / `loseOv` 视觉与 `beep()` 音效；英文用清晰拉丁字体（`var(--cn)` 含 sans 兜底），不用像素英文字体显示单词。

## 测试说明（本仓库现实）

- **Python（`tools/`、`server.py`）有单元测试**：`unittest`，参照 `tools/test_gen_data.py`、`test_server.py`。这些任务走真正的 TDD（先写失败测试）。
- **前端 `index.html` 无 JS 测试框架**（整个项目的语文/数学玩法都是手动浏览器验证）。前端任务的「测试」= 明确的浏览器操作步骤 + 预期现象。遵循既有模式，不在本期引入 JS 测试运行器。
- 启动应用：`python3 server.py` → 浏览器开 `http://localhost:8000`。

## 文件结构（创建 / 修改）

| 文件 | 职责 | 本期改动 |
|---|---|---|
| `tools/gen_en_data.py` | 构建期：主题词库 → `en-data.js` + 默认发音包 | **新建** |
| `tools/test_gen_en_data.py` | `audio_key` 等纯函数单测 | **新建** |
| `en-data.js` | 运行时英语数据 `window.EN_DATA` | **新建（构建产物，入 git）** |
| `audio/en/*.mp3` | 英语发音（默认包入 git；自定义运行时生成、不入 git） | **新建** |
| `.gitignore` | 豁免默认包路径 `audio/en/` | 改 |
| `index.html` | 学科卡 / 题库 / `playEn` / 配对引擎 `EG` / 状态存档 | 改（多处，见各任务） |
| `server.py` | `/api/en/tts` 现生成自定义发音 | 改（+1 路由 +~45 行） |
| `test_server.py` | `/api/en/tts` 的 key 函数 + 路由测试 | 改 |
| `README.md` | 英语玩法与发音说明 | 改 |

**核心闭环 = Task 1–6**（用户点名的「词义配对挖矿闭环」，可独立交付）。**Task 7–8** = 自主命题 + 现生成发音（设计文档一期范围）。**Task 9** = README。

---

### Task 1: 英语数据管线 `gen_en_data.py` → `en-data.js`

**Files:**
- Create: `tools/gen_en_data.py`
- Test: `tools/test_gen_en_data.py`
- Produce: `en-data.js`（运行脚本生成）

**Interfaces:**
- Produces: `audio_key(text:str)->str`（key 规则，见 Global Constraints）；`build()` 写出 `en-data.js`，内含 `window.EN_DATA = {worlds:[{id:int,name:str,icon:str,words:[{en,zh,emoji,audio}]}]}`。
- Consumed by: Task 2（用同一 `WORDS`/`audio_key` 生成发音包）、Task 6（前端读 `window.EN_DATA`）。

- [ ] **Step 1: 写失败测试 `tools/test_gen_en_data.py`**

```python
import unittest
from gen_en_data import audio_key


class AudioKeyTest(unittest.TestCase):
    def test_simple_word_lowercased(self):
        self.assertEqual(audio_key("Apple"), "apple")
        self.assertEqual(audio_key("red"), "red")

    def test_spaces_become_single_underscore(self):
        self.assertEqual(audio_key("ice cream"), "ice_cream")
        self.assertEqual(audio_key("a   b"), "a_b")

    def test_sentence_punctuation_stripped(self):
        self.assertEqual(audio_key("I like apples."), "i_like_apples")

    def test_trim_surrounding_whitespace_and_underscores(self):
        self.assertEqual(audio_key("  red  "), "red")
        self.assertEqual(audio_key("!hi!"), "hi")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行，确认失败**

Run: `cd tools && python3 -m unittest test_gen_en_data -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'gen_en_data'`）

- [ ] **Step 3: 写 `tools/gen_en_data.py`（数据部分，先不含发音）**

```python
#!/usr/bin/env python3
"""构建期：英语主题词库 -> en-data.js（运行时纯静态、零依赖）。
另含默认发音包生成（见 gen_audio，需联网，Task 2 启用）。
仅在开发机运行；产物 en-data.js + audio/en/*.mp3 入 git。"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "en-data.js")
AUDIO_DIR = os.path.join(HERE, "..", "audio", "en")


def audio_key(text):
    """词/句 -> 发音文件名（不含扩展名）。前后端必须一致：
    小写 -> 非 [a-z0-9] 串折叠为单个 '_' -> 去首尾 '_'。"""
    s = re.sub(r"[^a-z0-9]+", "_", text.strip().lower())
    return s.strip("_")


# 主题词库：(world_id, en, zh, emoji)。加词只需往这里塞、重跑脚本。
WORDS = [
    # 1 颜色 & 数字
    (1, "red", "红色", "🔴"), (1, "blue", "蓝色", "🔵"),
    (1, "green", "绿色", "🟢"), (1, "yellow", "黄色", "🟡"),
    (1, "one", "一", "1️⃣"), (1, "two", "二", "2️⃣"),
    (1, "three", "三", "3️⃣"), (1, "five", "五", "5️⃣"),
    (1, "ten", "十", "🔟"),
    # 2 动物
    (2, "cat", "猫", "🐱"), (2, "dog", "狗", "🐶"),
    (2, "bird", "鸟", "🐦"), (2, "fish", "鱼", "🐟"),
    (2, "pig", "猪", "🐷"), (2, "duck", "鸭子", "🦆"),
    (2, "tiger", "老虎", "🐯"), (2, "panda", "熊猫", "🐼"),
    (2, "rabbit", "兔子", "🐰"),
    # 3 食物 & 水果
    (3, "apple", "苹果", "🍎"), (3, "banana", "香蕉", "🍌"),
    (3, "egg", "鸡蛋", "🥚"), (3, "rice", "米饭", "🍚"),
    (3, "milk", "牛奶", "🥛"), (3, "cake", "蛋糕", "🍰"),
    (3, "bread", "面包", "🍞"), (3, "grape", "葡萄", "🍇"),
    (3, "orange", "橙子", "🍊"),
]

WORLD_META = [
    (1, "🎨 颜色数字洞", "var(--gold)"),
    (2, "🐾 动物草原", "var(--grass)"),
    (3, "🍎 食物果园", "var(--red)"),
]


def build():
    worlds = []
    for wid, name, icon in WORLD_META:
        words = [{"en": en, "zh": zh, "emoji": emoji, "audio": audio_key(en)}
                 for (t, en, zh, emoji) in WORDS if t == wid]
        worlds.append({"id": wid, "name": name, "icon": icon, "words": words})
    js = ("/* 自动生成，勿手改。源：tools/gen_en_data.py。 */\n"
          "window.EN_DATA = " + json.dumps({"worlds": worlds}, ensure_ascii=False) + ";\n")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(js)
    counts = " ".join(f"#{w['id']}={len(w['words'])}" for w in worlds)
    print(f"已写 {OUT}：{len(WORDS)} 词，{len(worlds)} 世界（{counts}）。")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "audio":
        gen_audio()          # Task 2 加入
    else:
        build()
```

> 注：`gen_audio` 在 Task 2 加入；本步先让 `if __name__` 分支引用它会 NameError —— 故本步把末尾改成只调 `build()`：先用下面这版 `if __name__`，Task 2 再替换。

把末尾 `if __name__` 暂时写成：

```python
if __name__ == "__main__":
    build()
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd tools && python3 -m unittest test_gen_en_data -v`
Expected: PASS（4 tests）

- [ ] **Step 5: 生成 `en-data.js` 并肉眼检查**

Run: `cd tools && python3 gen_en_data.py`
Expected: 打印 `已写 .../en-data.js：27 词，3 世界（#1=9 #2=9 #3=9）。`
Run: `head -c 200 ../en-data.js`
Expected: 以 `window.EN_DATA = {"worlds":[{"id":1,...` 开头。

- [ ] **Step 6: 提交**

```bash
git add tools/gen_en_data.py tools/test_gen_en_data.py en-data.js
git commit -m "feat(english): 主题词库管线 gen_en_data.py + en-data.js"
```

---

### Task 2: 默认发音包（构建期 TTS）+ 入 git

**Files:**
- Modify: `tools/gen_en_data.py`（加 `tts_mp3` / `gen_audio`，恢复 `if __name__` 的 `audio` 分支）
- Modify: `.gitignore`（豁免 `audio/en/`）
- Produce: `audio/en/*.mp3`

**Interfaces:**
- Produces: `tts_mp3(text:str)->bytes`（经 `urllib` 取英文发音 mp3）；`gen_audio()` 为每个 `WORDS` 词写 `audio/en/<audio_key>.mp3`（已存在则跳过）。
- Consumed by: Task 3（`playEn` 播放这些文件）。

- [ ] **Step 1: 在 `gen_en_data.py` 加发音生成函数**（插在 `build()` 之后、`if __name__` 之前）

```python
def tts_mp3(text):
    """英文文本 -> mp3 字节。Google translate_tts 简单 GET（构建期联网一次）。
    可选升级：改用 edge-tts 神经语音（需 pip install edge-tts）。"""
    url = "https://translate.google.com/translate_tts?" + urllib.parse.urlencode(
        {"ie": "UTF-8", "q": text, "tl": "en", "client": "tw-ob"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def gen_audio():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    todo = [(en, audio_key(en)) for (t, en, zh, emoji) in WORDS]
    done = skip = 0
    for en, key in todo:
        path = os.path.join(AUDIO_DIR, key + ".mp3")
        if os.path.exists(path):
            skip += 1
            continue
        try:
            data = tts_mp3(en)
        except Exception as e:                       # 单词失败不致命：跳过，可重跑补齐
            print(f"  ✗ {en}: {e}")
            continue
        with open(path, "wb") as f:
            f.write(data)
        done += 1
        time.sleep(0.4)                              # 礼貌限速，避免被限流
    print(f"发音包：新增 {done}，跳过 {skip}（已存在），目录 {AUDIO_DIR}")
```

- [ ] **Step 2: 恢复 `if __name__` 的 audio 分支**

把文件末尾替换为：

```python
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "audio":
        gen_audio()
    else:
        build()
```

- [ ] **Step 3: `.gitignore` 豁免默认包**

查看当前：`grep -n audio .gitignore`（预期有一行 `audio/` 忽略拼音音频）。在该行**之后**追加豁免行，使 `.gitignore` 含：

```
audio/
!audio/en/
!audio/en/**
```

（拼音 `audio/pinyin/` 仍被忽略；只放行英语默认包。）

- [ ] **Step 4: 生成发音包（需联网）**

Run: `cd tools && python3 gen_en_data.py audio`
Expected: 打印 `发音包：新增 27，跳过 0…`；`ls ../audio/en | wc -l` → `27`。
Run: 浏览器或播放器试听 `audio/en/apple.mp3` 应读出 “apple”。
> 若构建机无法访问该端点：可重跑补齐；或暂时跳过本任务——闭环仍可玩（`playEn` 缺文件静默降级），发音后补。

- [ ] **Step 5: 提交**

```bash
git add tools/gen_en_data.py .gitignore audio/en
git commit -m "feat(english): 默认发音包(构建期 TTS)入 git + .gitignore 豁免"
```

---

### Task 3: 前端 `playEn()` + 引入 `en-data.js`

**Files:**
- Modify: `index.html`（引入脚本；在 `playPy` 旁加 `playEn`）

**Interfaces:**
- Consumes: `audio/en/<key>.mp3`、`VOICE_SPEEDS`/`_voiceIdx`（已存在，index.html:625-631）。
- Produces: 全局 `playEn(key:string)`，播 `/audio/en/<key>.mp3`，按语速档调 `playbackRate`，缺文件静默降级；全局 `window.EN_DATA`。

- [ ] **Step 1: 引入 `en-data.js`**（在 pinyin-data.js 之后）

Edit `index.html` — old:

```html
<script src="/pinyin-data.js"></script>
<script>
```

new:

```html
<script src="/pinyin-data.js"></script>
<script src="/en-data.js"></script>
<script>
```

- [ ] **Step 2: 加 `playEn`**（紧接 `playPy` 之后、`avatarHTML` 之前）

Edit `index.html` — old:

```js
  step();
}
function avatarHTML(skinId,small){
```

new:

```js
  step();
}
// 英语发音：单文件 mp3（词或整句各一段），按语速档调倍速；缺文件静默降级。
const _enPool = new Map();
function playEn(key){
  if(!key) return;
  const sp = VOICE_SPEEDS[_voiceIdx()] || VOICE_SPEEDS[2];
  let a=_enPool.get(key);
  if(!a){ a=new Audio('/audio/en/'+key+'.mp3'); _enPool.set(key,a); }
  a.currentTime=0;
  try{ a.playbackRate = sp.rate; }catch(e){}
  a.play().catch(()=>{});
}
function avatarHTML(skinId,small){
```

- [ ] **Step 3: 手动验证**

Run: `python3 server.py`，浏览器开 `http://localhost:8000`，登录任意玩家。
打开浏览器控制台执行：`playEn('apple')`。
Expected: 听到 “apple”（若 Task 2 已生成）；`EN_DATA.worlds.length` → `3`。无报错。

- [ ] **Step 4: 提交**

```bash
git add index.html
git commit -m "feat(english): 引入 en-data.js + playEn 发音 helper"
```

---

### Task 4: 状态与存档（`S.enMatchStage` / `S.enQsource` / `diffFor` 英语档）

**Files:**
- Modify: `index.html`（`freshState`、`SAVE_FIELDS`、`applySave`、`diffFor`）

**Interfaces:**
- Produces: `S.enMatchStage:number`（英语配对关卡，初值 0）、`S.enQsource:{type,label,items}`（英语题库，默认 `{type:'default',label:'默认主题',items:null}`）；`diffFor` 在 `S.subject==='en'` 时返回 `{pairs, dots:false, en:true, dl}`。
- Consumed by: Task 5/6/7。

- [ ] **Step 1: `freshState` 加英语字段**

Edit `index.html` — old:

```js
    matchStage:0, listenStage:0, toneStage:0, spellStage:0, readStage:0,
    pyMatchStage:pyStageDefaults() };
```

new:

```js
    matchStage:0, listenStage:0, toneStage:0, spellStage:0, readStage:0,
    enMatchStage:0, enQsource:{type:'default',label:'默认主题',items:null},
    pyMatchStage:pyStageDefaults() };
```

- [ ] **Step 2: `SAVE_FIELDS` 追加英语字段**

Edit `index.html` — old:

```js
const SAVE_FIELDS=['res','tool','skinsOwned','skin','stage','crushStage','stars','totalCleared','pyMatchStage','voiceSpeed','matchStage','listenStage','toneStage','spellStage','readStage','misses','qsource'];
```

new:

```js
const SAVE_FIELDS=['res','tool','skinsOwned','skin','stage','crushStage','stars','totalCleared','pyMatchStage','voiceSpeed','matchStage','listenStage','toneStage','spellStage','readStage','misses','qsource','enMatchStage','enQsource'];
```

- [ ] **Step 3: `applySave` 加英语兜底**

Edit `index.html` — old:

```js
  if(!S.qsource || typeof S.qsource!=='object' || !S.qsource.type)
    S.qsource={type:'default',label:'默认游戏',items:null};   // 选题：默认/自主命题
```

new:

```js
  if(!S.qsource || typeof S.qsource!=='object' || !S.qsource.type)
    S.qsource={type:'default',label:'默认游戏',items:null};   // 选题：默认/自主命题
  if(typeof S.enMatchStage!=='number') S.enMatchStage=0;       // 英语配对关卡
  if(!S.enQsource || typeof S.enQsource!=='object' || !S.enQsource.type)
    S.enQsource={type:'default',label:'默认主题',items:null};  // 英语题库：默认/自主命题
```

- [ ] **Step 4: `diffFor` 加英语分支**

Edit `index.html` — old:

```js
function diffFor(world, stage){
  const cn = S.subject==='cn';
  const list = cn ? PINYIN_WORLDS : WORLDS;
```

new:

```js
function diffFor(world, stage){
  if(S.subject==='en'){                                       // 英语配对：4→8 对随关卡上升
    const pairs = Math.min(4 + Math.floor(stage/2), 8);
    return {pairs, dots:false, en:true, dl:Math.min(4,Math.floor(stage/2))};
  }
  const cn = S.subject==='cn';
  const list = cn ? PINYIN_WORLDS : WORLDS;
```

- [ ] **Step 5: 手动验证**

刷新页面，控制台执行：`S.enMatchStage` → `0`；`S.enQsource.type` → `"default"`；`S.subject='en'; diffFor(1,0)` → `{pairs:4,dots:false,en:true,dl:0}`；执行后把 `S.subject` 改回 `'math'`。

- [ ] **Step 6: 提交**

```bash
git add index.html
git commit -m "feat(english): 状态与存档字段 enMatchStage/enQsource + diffFor 英语档"
```

---

### Task 5: 导航（学科卡 + `enterEn` + `renderModes('en')` + 返回键）

**Files:**
- Modify: `index.html`（`#subjects` HTML、`G.enterEn`、`renderModes`、`G.modesBack`、`G.gameHome`）

**Interfaces:**
- Consumes: `G.goModes`、`_unlockAudio`、`renderModes`（已存在）。
- Produces: `G.enterEn()`（解锁音频→进英语玩法）；`renderModes('en')` 渲染英语玩法卡（本期 1 张：词义配对挖矿 → `EG.start()`）。
- 注：`EG` 在 Task 6 定义；本任务点卡会报错，验收只看「卡片出现」。本期 `enterEn` 直接进默认题库玩法屏（题库选择屏在 Task 8 接入）。

- [ ] **Step 1: `#subjects` 加英语卡**

Edit `index.html` — old:

```html
      <div class="world" style="background:linear-gradient(135deg,var(--grass),rgba(0,0,0,.25))" onclick="_unlockAudio();G.enterCn()">
        <div class="wicon" style="background:var(--grass)"></div>
        <div><h3>📖 语文拼音</h3><p>汉字配拼音 · 挖方块学拼音</p></div>
      </div>
    </div>
```

new:

```html
      <div class="world" style="background:linear-gradient(135deg,var(--grass),rgba(0,0,0,.25))" onclick="_unlockAudio();G.enterCn()">
        <div class="wicon" style="background:var(--grass)"></div>
        <div><h3>📖 语文拼音</h3><p>汉字配拼音 · 挖方块学拼音</p></div>
      </div>
      <div class="world" style="background:linear-gradient(135deg,var(--gold),rgba(0,0,0,.25))" onclick="G.enterEn()">
        <div class="wicon" style="background:var(--gold)"></div>
        <div><h3>📕 英语</h3><p>中英配对 · 看图听词 · 练语感</p></div>
      </div>
    </div>
```

- [ ] **Step 2: 加 `G.enterEn`**（紧接 `G.enterCn` 定义之后）

Edit `index.html` — old:

```js
G.enterCn = async function(){
  _unlockAudio();
  const ok = await Audio2.gate();
  if(ok) G.goQsrc();          // 进语文先选题库；失败时停在 #audioFetch，由用户选重试/跳过
};
```

new:

```js
G.enterCn = async function(){
  _unlockAudio();
  const ok = await Audio2.gate();
  if(ok) G.goQsrc();          // 进语文先选题库；失败时停在 #audioFetch，由用户选重试/跳过
};
// 英语默认发音包随仓库提供（已离线），无需下载门；本期直接进默认题库玩法屏。
G.enterEn = function(){
  _unlockAudio();
  S.subject='en';
  S.enQsource={type:'default',label:'默认主题',items:null};
  G.goModes('en');
};
```

- [ ] **Step 3: `renderModes` 加英语分支**

Edit `index.html` — old:

```js
function renderModes(subj){
  const list=$('modeList');
  $('modeTitle').textContent = subj==='cn' ? '语文 · 选择玩法' : '数学 · 选择玩法';
  const src=$('modeSrc'), back=$('modeBack');
  if(subj==='cn'){
```

new:

```js
function renderModes(subj){
  const list=$('modeList');
  $('modeTitle').textContent = subj==='cn' ? '语文 · 选择玩法' : (subj==='en' ? '英语 · 选择玩法' : '数学 · 选择玩法');
  const src=$('modeSrc'), back=$('modeBack');
  if(subj==='en'){
    if(back) back.textContent='↩ 学科';
    if(src) src.innerHTML = `📚 题库：<b>${(S.enQsource&&S.enQsource.label)||'默认主题'}</b>`
      + ((S.enQsource&&S.enQsource.items&&S.enQsource.items.length) ? `（${S.enQsource.items.length} 词）` : '');
    list.innerHTML = `
      <div class="world" style="background:linear-gradient(135deg,var(--gold),rgba(0,0,0,.25))" onclick="EG.start()">
        <div class="wicon" style="background:var(--gold)"></div>
        <div><h3>⛏️ 词义配对挖矿</h3><p>中文配英文，点方块听发音</p></div>
      </div>`;
    return;
  }
  if(subj==='cn'){
```

- [ ] **Step 4: `G.modesBack` 加英语分支**

Edit `index.html` — old:

```js
G.modesBack = function(){ if(S.subject==='cn') G.goQsrc(); else G.goSubjects(); };
```

new:

```js
G.modesBack = function(){ if(S.subject==='cn') G.goQsrc(); else G.goSubjects(); };   // 英语本期直接回学科；Task 8 接题库屏后改为 G.goEnQsrc()
```

（本期英语 `modesBack` 走 `else` → `goSubjects()`，无需改；此行仅加注释占位。Task 8 再改。）

- [ ] **Step 5: `G.gameHome` 加英语分支**

Edit `index.html` — old:

```js
G.gameHome = function(){ if(S.subject==='cn') G.goModes('cn'); else G.goWorlds(); };
```

new:

```js
G.gameHome = function(){ if(S.subject==='cn') G.goModes('cn'); else if(S.subject==='en') G.goModes('en'); else G.goWorlds(); };
```

- [ ] **Step 6: 手动验证**

刷新 → 登录 → 标题「开始游戏」→ 学科屏出现三张卡（数学 / 语文拼音 / 📕 英语）。点 📕 英语 → 进玩法屏，标题「英语 · 选择玩法」，出现 1 张「⛏️ 词义配对挖矿」卡，右上「↩ 学科」可回学科屏。（点卡片此时报 `EG is not defined`，正常，Task 6 修。）

- [ ] **Step 7: 提交**

```bash
git add index.html
git commit -m "feat(english): 学科卡 + enterEn + renderModes('en') 导航"
```

---

### Task 6: 词义配对挖矿引擎 `EG` + 中英棋盘 + 点击发音（**核心闭环完成**）

**Files:**
- Modify: `index.html`（英语数据层 `enGamePool`；`EG` 引擎；`buildBoard` 分发；`buildEnglishBoard`；`renderBoard`/`tap`/`success`/`fail`/`win`/`nextLevel`/`retry`/`lose`/`renderVoiceCtl` 的英语分支；`.tile.en` 样式）

**Interfaces:**
- Consumes: `window.EN_DATA`、`Weak.choose/hit/miss`、`diffFor`、`playEn`、`G.buildPinyinBoard` 同款外壳。
- Produces: `EG.start()`/`EG.startLevel()`；`enGamePool(kind,stage)->string[]`（英语词 key 列表）；`G.buildEnglishBoard(d)`；`EN_INDEX`（`Map<en,{en,zh,emoji,audio}>`）。

- [ ] **Step 1: 加英语数据层 + 取题池**（插在 `_readWords()` 定义之后，即 cn 的 `gamePool` 帮助函数区末尾）

Edit `index.html` — old:

```js
function _readWords(){ return PINYIN_WORLDS.filter(w=>w.id>=7).flatMap(w=>w.words).filter(h=>PD(h)); }  // 看拼音选词：词语池(世界7-8)
```

new:

```js
function _readWords(){ return PINYIN_WORLDS.filter(w=>w.id>=7).flatMap(w=>w.words).filter(h=>PD(h)); }  // 看拼音选词：词语池(世界7-8)
// ===== 英语数据层：EN_INDEX 查词 → 条目；enGamePool 取题池（默认按世界进度 / 自主命题取录入词）=====
const EN_INDEX = new Map();
((window.EN_DATA&&EN_DATA.worlds)||[]).forEach(w=>w.words.forEach(it=>EN_INDEX.set(it.en, it)));
function _enMaxWorld(stage){ return Math.min(1+stage, (window.EN_DATA&&EN_DATA.worlds.length)||1); }  // 世界 1..(1+关)逐关放开
function enGamePool(kind, stage){
  if(S.enQsource && S.enQsource.type!=='default'){
    return (S.enQsource.items||[]).filter(en=>EN_INDEX.has(en));   // 自主命题：只用录入且已入库的词
  }
  const maxW=_enMaxWorld(stage), out=[];
  ((window.EN_DATA&&EN_DATA.worlds)||[]).forEach(w=>{ if(w.id<=maxW) w.words.forEach(it=>out.push(it.en)); });
  return out;
}
```

- [ ] **Step 2: `buildBoard` 分发英语**

Edit `index.html` — old:

```js
    const d = S.diff;
    if(S.subject==='cn'){ return this.buildPinyinBoard(d); }
```

new:

```js
    const d = S.diff;
    if(S.subject==='cn'){ return this.buildPinyinBoard(d); }
    if(S.subject==='en'){ return this.buildEnglishBoard(d); }
```

- [ ] **Step 3: 加 `buildEnglishBoard`**（紧接 `buildPinyinBoard` 之后）

Edit `index.html` — old:

```js
    const custom = S.qsource && S.qsource.type!=='default';
    $('worldName').innerHTML = `🔤 ${custom?S.qsource.label:'拼音配对'} · 第${stage+1}关`;
  },
```

new:

```js
    const custom = S.qsource && S.qsource.type!=='default';
    $('worldName').innerHTML = `🔤 ${custom?S.qsource.label:'拼音配对'} · 第${stage+1}关`;
  },

  buildEnglishBoard(d){
    const stage=S.enMatchStage;
    const pool=enGamePool('match', stage);
    const chosen=Weak.choose(pool, d.pairs);            // 含「针对错题多出相似题」
    const pairs=chosen.map(en=>{ const it=EN_INDEX.get(en)||{en,zh:en,audio:''};
      return {zh:it.zh, en:it.en, audio:it.audio}; });
    let tiles=[];
    pairs.forEach((p,i)=>{
      tiles.push({k:'q',pid:i,txt:p.zh,audio:p.audio,done:false});   // 中文题面（点也发英文音）
      tiles.push({k:'a',pid:i,ans:p.en,audio:p.audio,done:false});   // 英文答案
    });
    shuffle(tiles);
    S.board=tiles; S.sel=null; S.busy=false;
    this.renderHUD(); this.renderBoard(); this.renderSkills(); this.renderVoiceCtl();
    const hb=$('homeBtn'); if(hb) hb.textContent='🏠 玩法';
    const custom = S.enQsource && S.enQsource.type!=='default';
    $('worldName').innerHTML = `⛏️ ${custom?S.enQsource.label:'词义配对'} · 第${stage+1}关`;
  },
```

- [ ] **Step 4: `renderBoard` 支持英语 tile 类与标签**

Edit `index.html` — old:

```js
  renderBoard(){
    const dots = S.diff && S.diff.dots;
    const cnc = S.subject==='cn' ? ' cn' : '';
    $('board').innerHTML = S.board.map((t,i)=>{
      if(t.done) return `<div class="tile gone"></div>`;
      if(t.k==='q'){
        return `<button class="tile q${cnc} ${S.sel===i?'sel':''}" data-i="${i}">
          <span class="tag pix">${S.subject==='cn'?'汉字':'题目'}</span><span class="val">${t.txt}</span></button>`;
      }else{
        let dd='';
        if(dots){ let s=''; for(let n=0;n<Math.min(t.ans,20);n++) s+=`<span class="dot"></span>`; dd=`<div class="dots">${s}</div>`; }
        return `<button class="tile a${cnc} ${S.sel===i?'sel':''}" data-i="${i}">
          <span class="tag pix">${S.subject==='cn'?'拼音':'答案'}</span><span class="val">${t.ans}</span>${dd}</button>`;
      }
    }).join('');
```

new:

```js
  renderBoard(){
    const dots = S.diff && S.diff.dots;
    const cnc = S.subject==='cn' ? ' cn' : (S.subject==='en' ? ' en' : '');
    const qTag = S.subject==='cn'?'汉字':(S.subject==='en'?'中文':'题目');
    const aTag = S.subject==='cn'?'拼音':(S.subject==='en'?'English':'答案');
    $('board').innerHTML = S.board.map((t,i)=>{
      if(t.done) return `<div class="tile gone"></div>`;
      if(t.k==='q'){
        return `<button class="tile q${cnc} ${S.sel===i?'sel':''}" data-i="${i}">
          <span class="tag pix">${qTag}</span><span class="val">${t.txt}</span></button>`;
      }else{
        let dd='';
        if(dots){ let s=''; for(let n=0;n<Math.min(t.ans,20);n++) s+=`<span class="dot"></span>`; dd=`<div class="dots">${s}</div>`; }
        return `<button class="tile a${cnc} ${S.sel===i?'sel':''}" data-i="${i}">
          <span class="tag pix">${aTag}</span><span class="val">${t.ans}</span>${dd}</button>`;
      }
    }).join('');
```

- [ ] **Step 5: `tap` 加英语「点击即发音」**

Edit `index.html` — old:

```js
  tap(i){
    if(S.busy) return;
    const t=S.board[i]; if(!t||t.done) return;
    if(S.sel===null){ S.sel=i; this.renderBoard(); return; }   // 点方块不发声，配对正确后才读音
```

new:

```js
  tap(i){
    if(S.busy) return;
    const t=S.board[i]; if(!t||t.done) return;
    if(S.subject==='en' && t.audio) playEn(t.audio);           // 英语：点任意方块即读英文（边配边磨耳朵）
    if(S.sel===null){ S.sel=i; this.renderBoard(); return; }   // 拼音：点方块不发声，配对正确后才读音
```

- [ ] **Step 6: `success` 加英语分支（发音 + 错题本）**

Edit `index.html` — old:

```js
  success(i,j){
    beep('good');
    if(S.subject==='cn' && typeof playPy==='function'){
      const codes=(S.board[i].code||S.board[j].code||[]);
      playPy(codes);
      const qt=(S.board[i].k==='q'?S.board[i]:S.board[j]).txt; Weak.hit(qt);   // 答对：错题本减权
    }
```

new:

```js
  success(i,j){
    beep('good');
    if(S.subject==='cn' && typeof playPy==='function'){
      const codes=(S.board[i].code||S.board[j].code||[]);
      playPy(codes);
      const qt=(S.board[i].k==='q'?S.board[i]:S.board[j]).txt; Weak.hit(qt);   // 答对：错题本减权
    }
    if(S.subject==='en'){
      const aT=(S.board[i].k==='a'?S.board[i]:S.board[j]);
      playEn(aT.audio); Weak.hit(aT.ans);                                       // 答对：读英文 + 错题本减权（键=英文词）
    }
```

- [ ] **Step 7: `fail` 加英语错题记账**

Edit `index.html` — old:

```js
  fail(i,j){
    if(S.subject==='cn'){ const qt=(S.board[i].k==='q'?S.board[i]:S.board[j]).txt; Weak.miss(qt); }  // 答错：记错题
```

new:

```js
  fail(i,j){
    if(S.subject==='cn'){ const qt=(S.board[i].k==='q'?S.board[i]:S.board[j]).txt; Weak.miss(qt); }  // 答错：记错题
    if(S.subject==='en'){ const aT=(S.board[i].k==='a'?S.board[i]:S.board[j]); Weak.miss(aT.ans); }  // 答错：记错题（键=英文词）
```

- [ ] **Step 8: `win`/`nextLevel`/`retry`/`lose` 兼容英语**

Edit `index.html` — old:

```js
    const tip = S.subject==='cn' ? '下一关字词更多、更难（逐步加入复韵母）' : '下一关数字更大、方块更多';
```

new:

```js
    const tip = S.subject==='cn' ? '下一关字词更多、更难（逐步加入复韵母）' : (S.subject==='en' ? '下一关单词更多、范围更广' : '下一关数字更大、方块更多');
```

Edit `index.html` — old:

```js
    const wh=$('winHomeBtn'); if(wh) wh.textContent = S.subject==='cn'?'🏠 玩法':'地图';
```

new:

```js
    const wh=$('winHomeBtn'); if(wh) wh.textContent = S.subject==='math'?'地图':'🏠 玩法';
```

Edit `index.html` — old:

```js
  nextLevel(){ this.close('winOv'); toast('🔥 难度提升！');
    if(S.subject==='cn'){ S.matchStage++; PG.startLevel(); }
    else { S.stage[S.world]++; this.startWorld(S.world); } },
  retry(){ this.close('loseOv'); if(S.subject==='cn') PG.startLevel(); else this.startWorld(S.world); },
  lose(){ const lh=$('loseHomeBtn'); if(lh) lh.textContent = S.subject==='cn'?'🏠 玩法':'地图'; $('loseOv').classList.add('on'); },
```

new:

```js
  nextLevel(){ this.close('winOv'); toast('🔥 难度提升！');
    if(S.subject==='cn'){ S.matchStage++; PG.startLevel(); }
    else if(S.subject==='en'){ S.enMatchStage++; EG.startLevel(); }
    else { S.stage[S.world]++; this.startWorld(S.world); } },
  retry(){ this.close('loseOv'); if(S.subject==='cn') PG.startLevel(); else if(S.subject==='en') EG.startLevel(); else this.startWorld(S.world); },
  lose(){ const lh=$('loseHomeBtn'); if(lh) lh.textContent = S.subject==='math'?'地图':'🏠 玩法'; $('loseOv').classList.add('on'); },
```

- [ ] **Step 9: `renderVoiceCtl` 对英语也显示（语速影响 `playEn`）**

Edit `index.html` — old:

```js
  renderVoiceCtl(){
    const el=$('voiceCtl'); if(!el) return;
    if(S.subject!=='cn'){ el.style.display='none'; el.innerHTML=''; return; }
    const idx=_voiceIdx(); el.style.display='flex';
    el.innerHTML = `<span class="vcLbl">🔊 语速</span>` +
      VOICE_SPEEDS.map((s,i)=>`<button type="button" class="vcBtn${i===idx?' on':''}" data-vs="${i}">${s.name}</button>`).join('');
    el.querySelectorAll('.vcBtn[data-vs]').forEach(b=>{ b.onclick=()=>{
      S.voiceSpeed=+b.dataset.vs; _unlockAudio(); G.renderVoiceCtl(); saveGame();
      const ex=(S.board||[]).find(t=>t.k==='a'&&t.code&&t.code.length); if(ex) playPy(ex.code);
    }; });
  },
```

new:

```js
  renderVoiceCtl(){
    const el=$('voiceCtl'); if(!el) return;
    if(S.subject==='math'){ el.style.display='none'; el.innerHTML=''; return; }
    const idx=_voiceIdx(); el.style.display='flex';
    el.innerHTML = `<span class="vcLbl">🔊 语速</span>` +
      VOICE_SPEEDS.map((s,i)=>`<button type="button" class="vcBtn${i===idx?' on':''}" data-vs="${i}">${s.name}</button>`).join('');
    el.querySelectorAll('.vcBtn[data-vs]').forEach(b=>{ b.onclick=()=>{
      S.voiceSpeed=+b.dataset.vs; _unlockAudio(); G.renderVoiceCtl(); saveGame();
      if(S.subject==='en'){ const ex=(S.board||[]).find(t=>t.k==='a'&&t.audio); if(ex) playEn(ex.audio); }
      else { const ex=(S.board||[]).find(t=>t.k==='a'&&t.code&&t.code.length); if(ex) playPy(ex.code); }
    }; });
  },
```

- [ ] **Step 10: 加 `EG` 引擎对象**（紧接 `PG` 对象之后）

Edit `index.html` — old:

```js
const PG = {
  start(){ S.subject='cn';
    if(!gamePool('match', S.matchStage).length){ toast('这个题库还没有可配对的字词'); return G.goModes('cn'); }
    this.startLevel(); },
  startLevel(){
    S.subject='cn'; S.curStage=S.matchStage;
    S.world=Math.min(1+Math.floor(S.matchStage/2),4);   // 复用为发矿「深度」(1→4 随关卡)
    S.diff=diffFor(1, S.matchStage);
    S.maxHearts = S.tool>=2?6:5; if(S.tool>=4) S.maxHearts=7;
    S.hearts=S.maxHearts; S.skillUses={}; S.shield=false;
    SKILLS.forEach(s=>{ if(S.tool>=s.tier) S.skillUses[s.key]=s.uses; });
    G.buildPinyinBoard(S.diff); show('game');
  },
};
```

new:

```js
const PG = {
  start(){ S.subject='cn';
    if(!gamePool('match', S.matchStage).length){ toast('这个题库还没有可配对的字词'); return G.goModes('cn'); }
    this.startLevel(); },
  startLevel(){
    S.subject='cn'; S.curStage=S.matchStage;
    S.world=Math.min(1+Math.floor(S.matchStage/2),4);   // 复用为发矿「深度」(1→4 随关卡)
    S.diff=diffFor(1, S.matchStage);
    S.maxHearts = S.tool>=2?6:5; if(S.tool>=4) S.maxHearts=7;
    S.hearts=S.maxHearts; S.skillUses={}; S.shield=false;
    SKILLS.forEach(s=>{ if(S.tool>=s.tier) S.skillUses[s.key]=s.uses; });
    G.buildPinyinBoard(S.diff); show('game');
  },
};

// 英语词义配对挖矿：复用配对引擎外壳，按世界进度（或自主命题）混合出题
const EG = {
  start(){ S.subject='en';
    if(!enGamePool('match', S.enMatchStage).length){ toast('这个题库还没有可配对的单词'); return G.goModes('en'); }
    this.startLevel(); },
  startLevel(){
    S.subject='en'; S.curStage=S.enMatchStage;
    S.world=Math.min(1+Math.floor(S.enMatchStage/2),4);   // 发矿「深度」
    S.diff=diffFor(1, S.enMatchStage);
    S.maxHearts = S.tool>=2?6:5; if(S.tool>=4) S.maxHearts=7;
    S.hearts=S.maxHearts; S.skillUses={}; S.shield=false;
    SKILLS.forEach(s=>{ if(S.tool>=s.tier) S.skillUses[s.key]=s.uses; });
    G.buildEnglishBoard(S.diff); show('game');
  },
};
```

- [ ] **Step 11: 加 `.tile.en` 样式**（在 line 346 的 `<style>` 块开头插入）

Edit `index.html` — old:

```html
<style>
  .crushGrid{display:grid;gap:6px;margin-top:6px;}
```

new:

```html
<style>
  .tile.en .val{font-family:var(--cn);font-weight:700;font-size:20px;letter-spacing:.4px;text-transform:lowercase;line-height:1.15;}
  .tile.en.q .val{font-family:var(--cn);}   /* 中文题面也用清晰中文体 */
  .crushGrid{display:grid;gap:6px;margin-top:6px;}
```

- [ ] **Step 12: 手动验证（完整闭环）**

`python3 server.py` → 浏览器 → 登录 → 学科屏 → 📕 英语 → 点「⛏️ 词义配对挖矿」。
Expected：
1. 棋盘出现中文方块（标签「中文」）与英文方块（标签「English」），如 `苹果` / `apple`。
2. 点任一方块听到对应英文发音（如点 `苹果` 或 `apple` 都读 “apple”）。
3. 配对正确：方块消除、发英文音、掉矿石、★ 增加；配对错误：扣心、抖动。
4. 全部配对完成 → `winOv` 过关面板，「再来一关」→ `S.enMatchStage` 自增、下一关更多对。
5. 上方 🔊 语速 慢/正常/快 可切换并即时试听。
6. 切回数学 / 语文，两科照常（回归）。

控制台抽查：`S.enMatchStage`（过一关后应 ≥1）。

- [ ] **Step 13: 提交**

```bash
git add index.html
git commit -m "feat(english): 词义配对挖矿引擎 EG + 中英棋盘 + 点击发音(核心闭环)"
```

---

### Task 7: `server.py` 新增 `/api/en/tts`（自主命题现生成发音）

**Files:**
- Modify: `server.py`（key 函数、TTS 取音、路由、`make_server` 加 `en_audio_dir`）
- Modify: `test_server.py`（key 函数 + 路由测试）

**Interfaces:**
- Produces: `en_audio_key(text:str)->str`（与前端/构建脚本逐字一致）；`POST /api/en/tts {texts:[...]}` → 为每个文本（缺失时）经 `urllib` 生成 `audio/en/<key>.mp3`，返回 `{ok:true, made:int, have:int}`；离线/失败仍返回 `{ok:true, made:0, ...}`（不阻断游戏）。
- Consumed by: Task 8（自主命题录入后调用）。

- [ ] **Step 1: 在 `test_server.py` 加 key 函数测试（先失败）**

`test_server.py` 已 `import server`，故直接用 `server.en_audio_key`（与 `server.valid_name` 同风格）。在 `NameValidationTests` 类**之后**加：

```python
class EnAudioKeyTest(unittest.TestCase):
    def test_key_matches_frontend_rule(self):
        self.assertEqual(server.en_audio_key("Apple"), "apple")
        self.assertEqual(server.en_audio_key("ice cream"), "ice_cream")
        self.assertEqual(server.en_audio_key("I like apples."), "i_like_apples")
        self.assertEqual(server.en_audio_key("  red  "), "red")
```

Run: `python3 -m unittest test_server -v`
Expected: FAIL（`AttributeError: module 'server' has no attribute 'en_audio_key'`）

- [ ] **Step 2: 在 `server.py` 加 key 函数 + 取音函数**（放在 `_content_type` 之前的模块级区域，紧接 `_download_zip` 之后）

```python
import re   # 加到文件顶部 import 区（与 io/json/os… 同列）


def en_audio_key(text):
    """英文词/句 -> 发音文件名（与前端 playEn、tools/gen_en_data.audio_key 逐字一致）。"""
    return re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")


def _en_tts_mp3(text, timeout=20):
    """英文文本 -> mp3 字节，经 Google translate_tts 简单 GET（标准库 urllib）。"""
    import urllib.parse
    url = "https://translate.google.com/translate_tts?" + urllib.parse.urlencode(
        {"ie": "UTF-8", "q": text, "tl": "en", "client": "tw-ob"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()
```

- [ ] **Step 3: 加路由 + handler**

在 `do_POST` 里加路由（紧接 `/api/audio/fetch` 行之后）— old:

```python
        if path == "/api/audio/fetch":
            return self._audio_fetch()
        return self._send_json(404, {"ok": False, "error": "not found"})
```

new:

```python
        if path == "/api/audio/fetch":
            return self._audio_fetch()
        if path == "/api/en/tts":
            return self._en_tts()
        return self._send_json(404, {"ok": False, "error": "not found"})
```

在 `_audio_fetch` 方法之后加 handler：

```python
    def _en_tts(self):
        try:
            body = self._read_body()
        except BodyTooLarge:
            return self._send_json(413, {"ok": False, "error": "请求体过大"})
        except ValueError:
            return self._send_json(400, {"ok": False, "error": "bad json"})
        texts = body.get("texts") if isinstance(body, dict) else None
        if not isinstance(texts, list):
            return self._send_json(400, {"ok": False, "error": "texts must be a list"})
        os.makedirs(self.server.en_audio_dir, exist_ok=True)
        made = 0
        for t in texts:
            if not isinstance(t, str) or not t.strip():
                continue
            key = en_audio_key(t)
            if not key:
                continue
            path = os.path.join(self.server.en_audio_dir, key + ".mp3")
            if os.path.exists(path):
                continue
            try:
                data = _en_tts_mp3(t)
            except Exception:                      # 离线/失败：跳过该词，前端静音降级，不阻断
                continue
            with open(path, "wb") as f:
                f.write(data)
            made += 1
        have = sum(1 for f in os.listdir(self.server.en_audio_dir)
                   if f.endswith(".mp3")) if os.path.isdir(self.server.en_audio_dir) else 0
        return self._send_json(200, {"ok": True, "made": made, "have": have})
```

- [ ] **Step 4: `make_server` 加英语音频目录**

Edit `server.py` — old:

```python
    srv.audio_dir = os.path.join(srv.web_dir, "audio", "pinyin")
    srv.ready_sentinel = os.path.join(srv.web_dir, "audio", ".ready")
    srv.audio_lock = threading.Lock()
    return srv
```

new:

```python
    srv.audio_dir = os.path.join(srv.web_dir, "audio", "pinyin")
    srv.en_audio_dir = os.path.join(srv.web_dir, "audio", "en")
    srv.ready_sentinel = os.path.join(srv.web_dir, "audio", ".ready")
    srv.audio_lock = threading.Lock()
    return srv
```

- [ ] **Step 5: 在 `test_server.py` 的 `ServerHTTPTests` 类里加两个路由测试**

夹具说明（已读 `test_server.py`）：`ServerHTTPTests.setUp` 用临时 `web_dir` 起服务器，`self.port` 是端口，`self.srv.en_audio_dir` = Task 7 Step 4 加的英语音频目录（位于临时 `web_dir/audio/en`）；模块级 `_post(port, path, obj)->(status, bytes)`；网络靠 monkeypatch（仿 `test_audio_fetch_empty_zip` 替换 `server._download_zip`）。在 `ServerHTTPTests` 内加：

```python
    def test_en_tts_existing_word_skips_network(self):
        en_dir = self.srv.en_audio_dir
        os.makedirs(en_dir, exist_ok=True)
        with open(os.path.join(en_dir, "apple.mp3"), "wb") as f:
            f.write(b"ID3fake")
        status, data = _post(self.port, "/api/en/tts", {"texts": ["apple"]})
        self.assertEqual(status, 200)
        j = json.loads(data)
        self.assertTrue(j["ok"])
        self.assertEqual(j["made"], 0)          # 已存在→跳过→不联网
        self.assertGreaterEqual(j["have"], 1)

    def test_en_tts_new_word_generates_via_mocked_tts(self):
        original = server._en_tts_mp3
        server._en_tts_mp3 = lambda text, timeout=20: b"ID3fake"   # 避免真实联网
        try:
            status, data = _post(self.port, "/api/en/tts", {"texts": ["zzqnew"]})
            self.assertEqual(status, 200)
            j = json.loads(data)
            self.assertEqual(j["made"], 1)
            self.assertTrue(os.path.exists(os.path.join(self.srv.en_audio_dir, "zzqnew.mp3")))
        finally:
            server._en_tts_mp3 = original
```

- [ ] **Step 6: 运行测试**

Run: `python3 -m unittest test_server -v`
Expected: PASS（含 `EnAudioKeyTest`、`EnTtsRouteTest`，且原有测试不回归）

- [ ] **Step 7: 提交**

```bash
git add server.py test_server.py
git commit -m "feat(english): server /api/en/tts 自主命题现生成发音(urllib 标准库)"
```

---

### Task 8: 自主命题英语题库（题库屏 + 录入 + 接 `/api/en/tts`）

**Files:**
- Modify: `index.html`（英语题库屏 `#enQsrc`、录入屏 `#enCustom`、`G.enterEn`/`G.modesBack` 改接题库屏、`enGamePool` 已支持 custom）

**Interfaces:**
- Consumes: `EN_INDEX`、`/api/en/tts`、`enGamePool`（custom 分支 Task 6 已就绪）。
- Produces: `G.goEnQsrc()`、`G.enPickDefault()`、`G.openEnCustom()`/`G.enCustomPreview()`/`G.enCustomStart()`；`S.enQsource={type:'custom',label:'自主命题',items:[...]}`。

- [ ] **Step 1: 加英语题库屏 + 录入屏 HTML**（紧接 `#audioFetch` 段之后、`<style>` 之前）

Edit `index.html` — old:

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

new:

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

  <!-- 英语题库：默认主题 / 自主命题 -->
  <section id="enQsrc" class="screen">
    <div class="userBar"><span></span>
      <button class="btn gray" style="font-size:11px;padding:6px 10px" onclick="G.goSubjects()">↩ 学科</button></div>
    <div class="logo pix" style="font-size:20px">选择题库</div>
    <div style="display:grid;gap:14px;margin-top:22px">
      <div class="world" style="background:linear-gradient(135deg,var(--gold),rgba(0,0,0,.25))" onclick="G.enPickDefault()">
        <div class="wicon" style="background:var(--gold)"></div>
        <div><h3>📚 默认主题</h3><p>颜色·动物·食物… 由易到难</p></div>
      </div>
      <div class="world" style="background:linear-gradient(135deg,var(--cyan),rgba(0,0,0,.25))" onclick="G.openEnCustom()">
        <div class="wicon" style="background:var(--cyan)"></div>
        <div><h3>✏️ 自主命题</h3><p>自己录想练的单词，只练这些</p></div>
      </div>
    </div>
    <p class="tip" id="enQsrcTip" style="margin-top:20px">选好题库，再进玩法</p>
  </section>

  <!-- 英语自主命题：录入单词 -->
  <section id="enCustom" class="screen">
    <div class="userBar"><span></span>
      <button class="btn gray" style="font-size:11px;padding:6px 10px" onclick="G.goEnQsrc()">↩ 题库</button></div>
    <div class="logo pix" style="font-size:18px">✏️ 自主命题（英语）</div>
    <p class="tip" style="margin-top:10px">输入想练的单词，用空格或换行隔开。<br>例：apple cat red dog book</p>
    <textarea id="enCustomInput" class="nameInput" style="width:100%;height:120px;margin-top:10px;resize:none;font-size:18px;line-height:1.7"
      oninput="G.enCustomPreview()" placeholder="type words here…"></textarea>
    <p class="tip" id="enCustomHint" style="margin-top:8px">已识别 0 个</p>
    <div class="closeRow" style="margin-top:8px">
      <button class="btn green" id="enCustomStartBtn" onclick="G.enCustomStart()" disabled>开始练习 ▶</button>
    </div>
  </section>
```

- [ ] **Step 2: `enterEn` / `modesBack` 改走题库屏**

Edit `index.html` — old:

```js
// 英语默认发音包随仓库提供（已离线），无需下载门；本期直接进默认题库玩法屏。
G.enterEn = function(){
  _unlockAudio();
  S.subject='en';
  S.enQsource={type:'default',label:'默认主题',items:null};
  G.goModes('en');
};
```

new:

```js
// 英语默认发音包随仓库提供（已离线），无需下载门；进英语先选题库。
G.enterEn = function(){ _unlockAudio(); S.subject='en'; G.goEnQsrc(); };
G.goEnQsrc = function(){ S.subject='en';
  const t=$('enQsrcTip'); if(t) t.textContent = (S.enQsource&&S.enQsource.type!=='default')
    ? `当前题库：${S.enQsource.label}（${(S.enQsource.items||[]).length} 词）· 选「默认主题」可换回`
    : '选好题库，再进玩法';
  show('enQsrc'); };
G.enPickDefault = function(){ S.enQsource={type:'default',label:'默认主题',items:null}; saveGame(); G.goModes('en'); };
G.openEnCustom = function(){ const ta=$('enCustomInput');
  if(S.enQsource && S.enQsource.type==='custom' && (S.enQsource.items||[]).length) ta.value=S.enQsource.items.join(' ');
  G.enCustomPreview(); show('enCustom'); ta.focus(); };
G.enCustomPreview = function(){
  const toks=(($('enCustomInput').value||'').toLowerCase().split(/[^a-z']+/)).map(t=>t.trim()).filter(Boolean);
  const seen=new Set(), ok=[], unknown=[];
  toks.forEach(t=>{ if(seen.has(t)) return; seen.add(t);
    (EN_INDEX.has(t)?ok:unknown).push(t); });
  G._enCustomItems = ok.concat(unknown);   // 已入库优先；未入库也收（发音将现生成）
  $('enCustomHint').innerHTML = `已识别 <b style="color:var(--grass)">${ok.length}</b> 个`
    + (unknown.length ? ` · <span style="color:var(--gold)">${unknown.length} 个新词（发音现生成）</span>` : '');
  $('enCustomStartBtn').disabled = G._enCustomItems.length===0;
};
G.enCustomStart = async function(){
  const items=(G._enCustomItems||[]).slice(); if(!items.length) return;
  S.enQsource={type:'custom', label:'自主命题', items}; saveGame();
  try{ await fetch('/api/en/tts',{method:'POST',headers:{'Content-Type':'application/json'},
       body:JSON.stringify({texts:items})}); }catch(e){}   // 失败不阻断：缺音静默降级
  G.goModes('en');
};
```

- [ ] **Step 3: `modesBack` 英语回题库屏**

Edit `index.html` — old:

```js
G.modesBack = function(){ if(S.subject==='cn') G.goQsrc(); else G.goSubjects(); };   // 英语本期直接回学科；Task 8 接题库屏后改为 G.goEnQsrc()
```

new:

```js
G.modesBack = function(){ if(S.subject==='cn') G.goQsrc(); else if(S.subject==='en') G.goEnQsrc(); else G.goSubjects(); };
```

- [ ] **Step 4: 自主命题词若未入 `EN_INDEX`，棋盘需能显示**

`buildEnglishBoard` 的 `EN_INDEX.get(en)||{en,zh:en,audio:''}` 已兜底（新词无中文则中文面显示英文本身、audio 为该词 key）。但自主命题应让新词也有 audio/zh。改 `enGamePool` 的 custom 分支与 `buildEnglishBoard` 兜底，使新词用 `audio_key`：

Edit `index.html` — old:

```js
function enGamePool(kind, stage){
  if(S.enQsource && S.enQsource.type!=='default'){
    return (S.enQsource.items||[]).filter(en=>EN_INDEX.has(en));   // 自主命题：只用录入且已入库的词
  }
```

new:

```js
function _enKey(t){ return (t||'').trim().toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_+|_+$/g,''); }
function enGamePool(kind, stage){
  if(S.enQsource && S.enQsource.type!=='default'){
    return (S.enQsource.items||[]).filter(Boolean);               // 自主命题：录入词全用（新词发音现生成）
  }
```

Edit `index.html` — old:

```js
    const pairs=chosen.map(en=>{ const it=EN_INDEX.get(en)||{en,zh:en,audio:''};
      return {zh:it.zh, en:it.en, audio:it.audio}; });
```

new:

```js
    const pairs=chosen.map(en=>{ const it=EN_INDEX.get(en)||{en, zh:en, audio:_enKey(en)};
      return {zh:it.zh, en:it.en, audio:it.audio}; });
```

- [ ] **Step 5: 手动验证**

`python3 server.py`（联网）→ 英语 → 题库屏出现「默认主题 / 自主命题」。
- 选默认主题 → 进配对，照常。
- 自主命题 → 录入 `apple cat red sun book` → 提示已识别（apple/cat/red 入库，sun/book 新词）→ 开始练习。新词 `book`/`sun` 也出现在棋盘；点击/答对应能听到发音（服务器已现生成 `audio/en/book.mp3`、`sun.mp3`，检查文件已出现）。离线时新词静音但仍可配对。
- 题库屏「↩ 学科」、玩法屏「↩ 题库」返回正确。

- [ ] **Step 6: 提交**

```bash
git add index.html
git commit -m "feat(english): 自主命题英语题库 + 录入接 /api/en/tts 现生成发音"
```

---

### Task 9: README 英语章节

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 加英语小节**（仿「## 语文 · 拼音」小节，放其后）

```markdown
## 英语

进标题后选「📕 英语」，先**选题库**，再玩。矿石/镐子/皮肤/星星与数学、语文**共享**。

**题库**：**默认主题**（颜色→动物→食物… 由易到难）或**自主命题**（自己录单词，只练这些）。**不绑课本**。

**玩法（一期）**：⛏️ **词义配对挖矿** —— 中文配英文，**点方块即读英文发音**，配对成功挖矿；随关卡单词更多、范围更广，并针对错题多出。

**发音**：默认主题的发音**随仓库提供、始终离线**。自主命题的新词，由**服务器**首次录入时联网用 TTS 现生成一次到 `audio/en/`（之后离线）；服务器没联网则该词静音、配对仍可玩。`audio/en/` 默认包入 git，自定义生成的发音不入 git。

**重新生成英语数据 / 默认发音包**（仅在改了 `tools/gen_en_data.py` 词库后）：

    cd tools
    python3 gen_en_data.py          # 生成 en-data.js
    python3 gen_en_data.py audio    # 生成默认发音包 audio/en/*.mp3（需联网）
```

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs(english): README 英语玩法与发音说明"
```

---

## Self-Review

**1. Spec coverage（对 `2026-06-29-english-game-design.md`）：**
- §2 导航（学科卡/题库屏/renderModes/modesBack 补 en）→ Task 5、8 ✓
- §3 主题地图（颜色→动物→食物…由易到难）→ Task 1 `WORLD_META`/`_enMaxWorld` ✓（一期落地前 3 个世界，加世界=往 `WORDS`/`WORLD_META` 加、重跑）
- §4.1 词义配对（中↔英主模式 + emoji 字段 + 点击发音）→ Task 6 ✓（emoji 字段已入 `EN_DATA`，看图选词在二期用）
- §5 数据管线（en-data.js / audio_key / 自主命题）→ Task 1、8 ✓
- §6 音频（默认包构建期预生成入 git + 自定义服务器 urllib 现生成 + playEn + 离线降级 + iOS 解锁）→ Task 2、3、6（_unlockAudio 复用）、7 ✓
- §7 状态存档（S.subject='en'、enMatchStage、enQsource、SAVE_FIELDS、applySave 兜底）→ Task 4 ✓
- §8 一期范围（导航 + 词义配对 + 内容管线 + 音频 + 自主命题）→ Task 1–9 ✓
- 二期/三期玩法（看图选词/听音选词/拼单词/连词成句）→ 本期不做（设计文档明列分期）✓

**2. Placeholder scan：** 无 TBD/TODO。Task 1 Step 3 的「先用临时 `if __name__`、Task 2 再替换」是显式两步，非占位。Task 7 Step 5 给了测试代码并标注「按现有夹具命名适配」——这是对未知夹具命名的合理适配说明，非占位（key 测试是完整可跑的）。

**3. Type consistency：**
- key 规则三处一致：`tools/gen_en_data.audio_key`、`server.en_audio_key`、前端 `_enKey`（均为 `lower → [^a-z0-9]+→_ → 去首尾_`）✓
- `EN_DATA.worlds[].words[]` 字段 `{en,zh,emoji,audio}` 在 Task 1 产出、Task 6 `EN_INDEX`/`buildEnglishBoard` 消费一致 ✓
- tile 携带 `audio`（q、a 都带），`success`/`fail`/`tap` 读 `aT.audio`/`t.audio` 一致 ✓
- `EG.startLevel`/`buildEnglishBoard`/`nextLevel`/`retry` 都用 `S.enMatchStage` ✓
- `enGamePool(kind,stage)` 签名与 `gamePool` 对齐；Task 8 custom 分支返回录入词、default 分支按世界 ✓

修订记录：Task 8 Step 4 收紧了 Task 6 的 custom 兜底（新词用 `_enKey` 生成 audio、`enGamePool` custom 不再要求已入库），保证自主命题新词可玩且发音键与服务器一致。
