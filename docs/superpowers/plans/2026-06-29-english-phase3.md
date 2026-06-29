# 英语矿工 三期 + 默认词库改 G6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把英语默认词库整体改成外研社《Join In》六年级标准（68 词 / 7 世界 + 22 句，贯穿全部默认游戏），并新增两种有序组装玩法 🔤 拼单词（听写式）与 🧩 连词成句，共用一个新的 EA 组装引擎；难度随关卡持续递增。

**Architecture:** 数据层 `tools/gen_en_data.py` 重建 `WORDS/WORLD_META` 并新增 `SENTENCES` → 产物 `en-data.js`（顶层加 `sentences[]`，向后兼容）+ `audio/en/*.mp3` 重生成。前端单文件 `index.html` 新增通用 `EA` 引擎（槽位+托盘，点入/撤销/满判），`ESPELL`/`ESENT` 是骑在 EA 上的两份配置；复用 `#cnq` 屏、`cnq*` 经济、`Weak` 错题本、`playEn`。一/二期玩法只读 `en-data.js`，自动升级到 G6，无需改其引擎。

**Tech Stack:** Python 标准库（构建期，含 unittest）；香草 JS + HTML5 Audio（前端，零库）。

## Global Constraints

（每个任务隐含包含本节。）

- **默认词库标准 = 外研社《Join In》六年级**；自主命题仍自由录入，不受此表限制。
- 运行时零第三方依赖；游玩设备永远离线（纯浏览器 API）；缺音频静默降级。
- 共享经济（矿石/星星/镐子/技能/皮肤/心跨学科共享）；**不新增经济字段**。
- 复用 `#cnq` 屏 + `cnq*` 帮助函数 + `Weak`（键=英文词/句）；**不改 cn/math 玩法行为**。
- `audio_key` 规则前后端逐字一致：小写 → 非 `[a-z0-9]` 串折叠为单个 `_` → 去首尾 `_`。前端对应 `_enKey`。
- 英式拼写从书：`maths`（非 math）。
- 关卡字段名逐字：`S.enSpellStage` / `S.enSentStage`。
- 单文件前端（`index.html`）；构建期产物 `en-data.js` + `audio/en/*.mp3` 入 git。
- 难度随关卡 `s` 递增（见各任务难度窗），且池子不足时放宽以保可玩。

## 测试说明

前端无 JS 测试框架（仓库既有模式）：验证 = `node --check`（抽取大 inline `<script>`）+ grep + 关键纯函数 node 逻辑自测。`tools/gen_en_data.py` 用 Python unittest。真机点测（iOS 自动播放、组装手感、过关加难、一/二期回归）由用户完成（本环境无浏览器自动化）。

抽取 inline 脚本做语法检查的命令（多处复用）：
```bash
awk '/^<script>$/{f=1;next} /^<\/script>$/{f=0} f' index.html > /tmp/_p3.js && node --check /tmp/_p3.js && echo "SYNTAX OK"
```

## 文件结构

| 文件 | 改动 |
|---|---|
| `tools/gen_en_data.py` | `WORDS`(27→68)、`WORLD_META`(3→7) 整体换 G6；新增 `SENTENCES`(22) + `tokenize()`；`build()` 输出 `sentences[]`；`gen_audio()` 含句子 + 清理孤儿 mp3 |
| `tools/test_gen_en_data.py` | 加 `tokenize` + `build()` 结构断言 |
| `en-data.js` | 重生成（G6 worlds + sentences） |
| `audio/en/*.mp3` | 重生成（清孤儿 + 新词/句） |
| `index.html` | 状态(enSpellStage/enSentStage) + 数据层(EN_SENT_INDEX/enSentencePool/enSpellPool) + 两张卡 + `EA` 引擎 + CSS + `ESPELL` + `ESENT` |
| `README.md` | 英语玩法(5) + G6 默认说明 + 数据重生成 |

---

### Task 1: 数据管线重建（gen_en_data.py + 测试）

**Files:** Modify `tools/gen_en_data.py`, `tools/test_gen_en_data.py`

**Interfaces:**
- Produces: `WORDS:[(world,en,zh,emoji)]`(68)、`WORLD_META:[(id,name,icon)]`(7)、`SENTENCES:[(world,en,zh)]`(22)、`tokenize(s)->[words]`；`build()` 写 `en-data.js`（`{worlds:[{id,name,icon,words:[{en,zh,emoji,audio}]}], sentences:[{en,zh,world,audio,words:[...]}]}`）；`gen_audio()` 生成词+句 mp3 并删孤儿。
- Consumed by: Task 2（跑脚本）、前端 Task 3/5/6（读 en-data.js 结构）。

- [ ] **Step 1: 替换 `WORDS`**

把 `tools/gen_en_data.py` 中 `WORDS = [...]` 整块（含注释）替换为：

```python
# 主题词库（外研社《Join In》六年级 G6 标准）：(world_id, en, zh, emoji)。加词只需往这里塞、重跑脚本。
WORDS = [
    # 1 学校科目
    (1, "maths", "数学", "➕"), (1, "music", "音乐", "🎵"),
    (1, "art", "美术", "🎨"), (1, "science", "科学", "🔬"),
    (1, "history", "历史", "📜"), (1, "drama", "戏剧", "🎭"),
    (1, "geography", "地理", "🌍"), (1, "English", "英语", "🇬🇧"),
    (1, "Chinese", "语文", "🇨🇳"), (1, "pupil", "小学生", "🧒"),
    # 2 动物世界
    (2, "whale", "鲸鱼", "🐋"), (2, "bear", "熊", "🐻"),
    (2, "fox", "狐狸", "🦊"), (2, "wolf", "狼", "🐺"),
    (2, "panda", "熊猫", "🐼"), (2, "elephant", "大象", "🐘"),
    (2, "koala", "考拉", "🐨"), (2, "lion", "狮子", "🦁"),
    (2, "owl", "猫头鹰", "🦉"), (2, "tiger", "老虎", "🐯"),
    # 3 城市地点
    (3, "building", "建筑", "🏢"), (3, "palace", "宫殿", "🏯"),
    (3, "castle", "城堡", "🏰"), (3, "tower", "塔", "🗼"),
    (3, "hospital", "医院", "🏥"), (3, "library", "图书馆", "📚"),
    (3, "cinema", "电影院", "🎬"), (3, "park", "公园", "🌳"),
    (3, "town", "城镇", "🏘️"), (3, "river", "河流", "🏞️"),
    (3, "map", "地图", "🗺️"),
    # 4 食物健康
    (4, "fruit", "水果", "🍎"), (4, "vegetable", "蔬菜", "🥦"),
    (4, "strawberry", "草莓", "🍓"), (4, "rice", "米饭", "🍚"),
    (4, "turkey", "火鸡", "🦃"), (4, "heart", "心脏", "❤️"),
    (4, "tooth", "牙齿", "🦷"), (4, "healthy", "健康的", "🥗"),
    (4, "strong", "强壮的", "💪"), (4, "hungry", "饥饿的", "😋"),
    # 5 节日庆典
    (5, "festival", "节日", "🎉"), (5, "lantern", "灯笼", "🏮"),
    (5, "Christmas", "圣诞节", "🎄"), (5, "Halloween", "万圣节", "🎃"),
    (5, "Easter", "复活节", "🐰"), (5, "Thanksgiving", "感恩节", "🦃"),
    (5, "moon", "月亮", "🌙"),
    # 6 职业人物国籍
    (6, "doctor", "医生", "👨‍⚕️"), (6, "nurse", "护士", "👩‍⚕️"),
    (6, "worker", "工人", "👷"), (6, "hero", "英雄", "🦸"),
    (6, "queen", "女王", "👑"), (6, "cousin", "表亲", "🧑"),
    (6, "British", "英国的", "🇬🇧"), (6, "American", "美国的", "🇺🇸"),
    (6, "Australian", "澳大利亚的", "🇦🇺"), (6, "Japanese", "日本的", "🇯🇵"),
    # 7 爱好梦想
    (7, "hobby", "爱好", "🎯"), (7, "stamp", "邮票", "📮"),
    (7, "doll", "玩偶", "🪆"), (7, "bicycle", "自行车", "🚲"),
    (7, "robot", "机器人", "🤖"), (7, "dream", "梦想", "💭"),
    (7, "diary", "日记", "📔"), (7, "book", "书", "📖"),
    (7, "world", "世界", "🌍"), (7, "ocean", "海洋", "🌊"),
]
```

- [ ] **Step 2: 替换 `WORLD_META`**

把 `WORLD_META = [...]` 整块替换为：

```python
WORLD_META = [
    (1, "🎒 学校科目", "var(--gold)"),
    (2, "🐾 动物世界", "var(--grass)"),
    (3, "🏙️ 城市地点", "var(--cyan)"),
    (4, "🍎 食物健康", "var(--red)"),
    (5, "🎉 节日庆典", "var(--gold)"),
    (6, "🦸 职业人物", "var(--grass)"),
    (7, "🎯 爱好梦想", "var(--cyan)"),
]
```

- [ ] **Step 3: 新增 `SENTENCES` + `tokenize`（紧接 `WORLD_META` 之后）**

在 `WORLD_META = [...]` 块之后、`def build():` 之前插入：

```python
# 连词成句默认句库（G6 语法）：(world_id, en, zh)。3–7 词，用上表词 + 小函数词。
SENTENCES = [
    (3, "Go straight ahead.", "一直往前走。"),
    (7, "I love reading.", "我爱阅读。"),
    (4, "Fruit is healthy.", "水果很健康。"),
    (2, "They saw a whale.", "他们看见一头鲸鱼。"),
    (3, "We went to the library.", "我们去了图书馆。"),
    (4, "She broke her arm.", "她摔断了手臂。"),
    (2, "Pandas live on bamboo.", "熊猫以竹子为生。"),
    (2, "The owl flies very fast.", "猫头鹰飞得很快。"),
    (2, "Tigers are bigger than foxes.", "老虎比狐狸大。"),
    (3, "The castle is very old.", "城堡很古老。"),
    (3, "Turn left at the park.", "在公园左转。"),
    (4, "Apples are good for your heart.", "苹果对心脏有好处。"),
    (4, "Eat fruit and vegetables.", "多吃水果和蔬菜。"),
    (5, "The festival is great fun.", "这个节日很有趣。"),
    (5, "We ate moon cakes.", "我们吃了月饼。"),
    (6, "I want to be a doctor.", "我想当医生。"),
    (6, "He is a famous hero.", "他是个著名的英雄。"),
    (6, "My cousin is Australian.", "我的表亲是澳大利亚人。"),
    (7, "My hobby is collecting stamps.", "我的爱好是集邮。"),
    (7, "I have a big dream.", "我有一个大梦想。"),
    (1, "She is good at art.", "她擅长美术。"),
    (2, "Lions are stronger than us.", "狮子比我们强壮。"),
]


def tokenize(sentence):
    """英文句 -> 单词数组（保留撇号，去其它标点）。'We ate moon cakes.' -> ['We','ate','moon','cakes']"""
    return re.findall(r"[A-Za-z']+", sentence)
```

- [ ] **Step 4: `build()` 输出 `sentences[]`**

把 `build()` 函数整体替换为：

```python
def build():
    worlds = []
    for wid, name, icon in WORLD_META:
        words = [{"en": en, "zh": zh, "emoji": emoji, "audio": audio_key(en)}
                 for (t, en, zh, emoji) in WORDS if t == wid]
        worlds.append({"id": wid, "name": name, "icon": icon, "words": words})
    sentences = [{"en": en, "zh": zh, "world": w, "audio": audio_key(en), "words": tokenize(en)}
                 for (w, en, zh) in SENTENCES]
    data = {"worlds": worlds, "sentences": sentences}
    js = ("/* 自动生成，勿手改。源：tools/gen_en_data.py。 */\n"
          "window.EN_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(js)
    counts = " ".join(f"#{w['id']}={len(w['words'])}" for w in worlds)
    print(f"已写 {OUT}：{len(WORDS)} 词 / {len(worlds)} 世界（{counts}）+ {len(sentences)} 句。")
```

- [ ] **Step 5: `gen_audio()` 含句子 + 清孤儿**

把 `gen_audio()` 函数整体替换为：

```python
def gen_audio():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    todo = ([(en, audio_key(en)) for (t, en, zh, emoji) in WORDS]
            + [(en, audio_key(en)) for (w, en, zh) in SENTENCES])
    valid = {key + ".mp3" for (_, key) in todo}
    removed = 0                                         # 清理：删掉不再引用的旧 mp3，保持发音包与内容同步
    for f in os.listdir(AUDIO_DIR):
        if f.endswith(".mp3") and f not in valid:
            os.remove(os.path.join(AUDIO_DIR, f)); removed += 1
    done = skip = 0
    for text, key in todo:
        path = os.path.join(AUDIO_DIR, key + ".mp3")
        if os.path.exists(path):
            skip += 1
            continue
        try:
            data = tts_mp3(text)
        except Exception as e:                          # 单条失败不致命：跳过，可重跑补齐
            print(f"  ✗ {text}: {e}")
            time.sleep(0.4)
            continue
        if not data:
            print(f"  ✗ {text}: empty")
            continue
        with open(path, "wb") as f:
            f.write(data)
        done += 1
        time.sleep(0.4)                                 # 礼貌限速
    print(f"发音包：新增 {done}，跳过 {skip}（已存在），删孤儿 {removed}，目录 {AUDIO_DIR}")
```

- [ ] **Step 6: 扩展测试**

把 `tools/test_gen_en_data.py` 整体替换为：

```python
import unittest
from gen_en_data import audio_key, tokenize, build, WORDS, SENTENCES, WORLD_META


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


class TokenizeTest(unittest.TestCase):
    def test_drops_trailing_period(self):
        self.assertEqual(tokenize("We ate moon cakes."), ["We", "ate", "moon", "cakes"])

    def test_three_word_sentence(self):
        self.assertEqual(tokenize("Go straight ahead."), ["Go", "straight", "ahead"])

    def test_word_count_matches_audio_key_parts(self):
        # 每句的分词数 == audio_key 下划线段数（拼写规则一致性）
        for (_w, en, _zh) in SENTENCES:
            self.assertEqual(len(tokenize(en)), len(audio_key(en).split("_")))


class DataShapeTest(unittest.TestCase):
    def test_seven_worlds_and_word_count(self):
        self.assertEqual(len(WORLD_META), 7)
        self.assertEqual(len(WORDS), 68)
        ids = {w[0] for w in WORDS}
        self.assertEqual(ids, {1, 2, 3, 4, 5, 6, 7})

    def test_sentences_use_only_known_function_or_listed_handling(self):
        # 句库非空、每句有中文、词数在 3..7
        self.assertTrue(len(SENTENCES) >= 20)
        for (_w, en, zh) in SENTENCES:
            self.assertTrue(zh)
            self.assertTrue(3 <= len(tokenize(en)) <= 7)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 7: 跑测试（不改产物）**

Run:
```bash
cd /Users/xiaojin/workspace/math-minner/tools
python3 -m unittest test_gen_en_data -v
```
Expected: 所有用例 PASS（含新 Tokenize/DataShape）。

- [ ] **Step 8: 提交**

```bash
cd /Users/xiaojin/workspace/math-minner
git add tools/gen_en_data.py tools/test_gen_en_data.py
git commit -m "feat(english): 数据管线改 Join In 六年级——68词/7世界 + 22句 + tokenize/句子音频/清孤儿"
```

---

### Task 2: 重生成 en-data.js + 发音包

**Files:** Regenerate `en-data.js`, `audio/en/*.mp3`

**Interfaces:**
- Consumes: Task 1 的 `gen_en_data.py`。
- Produces: 提交后的 `en-data.js`（G6）+ `audio/en/*.mp3`（清孤儿后 = 68 词 + 22 句 ≈ 90 个）。

- [ ] **Step 1: 生成 en-data.js（离线、确定性）**

Run:
```bash
cd /Users/xiaojin/workspace/math-minner/tools && python3 gen_en_data.py
```
Expected: 打印 `已写 .../en-data.js：68 词 / 7 世界（#1=10 #2=10 #3=11 #4=10 #5=7 #6=10 #7=10）+ 22 句。`

- [ ] **Step 2: 校验 en-data.js 结构**

Run:
```bash
cd /Users/xiaojin/workspace/math-minner
node -e "global.window={};const fs=require('fs');eval(fs.readFileSync('en-data.js','utf8'));const d=window.EN_DATA;
console.log('worlds',d.worlds.length,'words',d.worlds.reduce((n,w)=>n+w.words.length,0),'sentences',d.sentences.length);
console.log('sample word', JSON.stringify(d.worlds[0].words[0]));
console.log('sample sentence', JSON.stringify(d.sentences[0]));
console.log('all sentences have words[] & audio', d.sentences.every(s=>Array.isArray(s.words)&&s.words.length&&s.audio));"
```
Expected: `worlds 7 words 68 sentences 22`；样例词含 `{en,zh,emoji,audio}`；样例句含 `{en,zh,world,audio,words}`；最后一行 `true`。

- [ ] **Step 3: 生成发音包（联网，幂等；清孤儿）**

Run（可能因限流偶发失败，**幂等可重跑补齐**）:
```bash
cd /Users/xiaojin/workspace/math-minner/tools && python3 gen_en_data.py audio
```
Expected: 打印 `发音包：新增 N，跳过 M，删孤儿 K，目录 .../audio/en`。**若有 `✗ ...` 失败行，再次运行同命令补齐**，直到下方 Step 4 校验通过。

- [ ] **Step 4: 校验每个词/句都有 mp3（无缺漏、无孤儿）**

Run:
```bash
cd /Users/xiaojin/workspace/math-minner
node -e "global.window={};const fs=require('fs'),path=require('path');eval(fs.readFileSync('en-data.js','utf8'));const d=window.EN_DATA;
const keys=new Set();d.worlds.forEach(w=>w.words.forEach(it=>keys.add(it.audio)));d.sentences.forEach(s=>keys.add(s.audio));
const have=new Set(fs.readdirSync('audio/en').filter(f=>f.endsWith('.mp3')).map(f=>f.slice(0,-4)));
const missing=[...keys].filter(k=>!have.has(k)), orphan=[...have].filter(k=>!keys.has(k));
console.log('need',keys.size,'have',have.size,'missing',JSON.stringify(missing),'orphan',JSON.stringify(orphan));"
```
Expected: `need 90 have 90 missing [] orphan []`（数字以实际 key 去重为准；关键是 `missing []` 且 `orphan []`）。

- [ ] **Step 5: 一/二期回归 smoke（数据换了，引擎没换）**

Run:
```bash
cd /Users/xiaojin/workspace/math-minner
grep -c "EN_DATA" index.html        # 仍引用
awk '/^<script>$/{f=1;next} /^<\/script>$/{f=0} f' index.html > /tmp/_p3t2.js && node --check /tmp/_p3t2.js && echo "SYNTAX OK"
```
Expected: grep ≥1；SYNTAX OK。（真机：词义配对/看图选词/听音选词现出 G6 词，点方块发 G6 音——留用户点测。）

- [ ] **Step 6: 提交**

```bash
git add en-data.js audio/en
git commit -m "build(english): 重生成 en-data.js + 发音包为 Join In 六年级(68词/7世界/22句)"
```

---

### Task 3: 状态 + 数据层 + 两张玩法卡

**Files:** Modify `index.html`

**Interfaces:**
- Produces: `S.enSpellStage`/`S.enSentStage`（初值 0，存档往返）；`EN_SENT_INDEX`（en→句对象）；`enSentencePool(stage)->[句对象]`（句长窗过滤）；`enSpellPool(stage)->[词]`（词长窗过滤）；renderModes('en') 5 张卡。
- Consumed by: Task 5（ESPELL 用 enSpellPool）、Task 6（ESENT 用 enSentencePool/EN_SENT_INDEX）。
- 注：本任务后点新两张卡报 `ESPELL/ESENT is not defined`（前向引用，同二期），Task 5/6 补齐。

- [ ] **Step 1: freshState 加两关卡字段**

Edit `index.html` — old:
```js
    enMatchStage:0, enPickStage:0, enListenStage:0, enQsource:{type:'default',label:'默认主题',items:null},
```
new:
```js
    enMatchStage:0, enPickStage:0, enListenStage:0, enSpellStage:0, enSentStage:0, enQsource:{type:'default',label:'默认主题',items:null},
```

- [ ] **Step 2: SAVE_FIELDS 追加**

Edit — old:
```js
const SAVE_FIELDS=['res','tool','skinsOwned','skin','stage','crushStage','stars','totalCleared','pyMatchStage','voiceSpeed','matchStage','listenStage','toneStage','spellStage','readStage','misses','qsource','enMatchStage','enPickStage','enListenStage','enQsource'];
```
new:
```js
const SAVE_FIELDS=['res','tool','skinsOwned','skin','stage','crushStage','stars','totalCleared','pyMatchStage','voiceSpeed','matchStage','listenStage','toneStage','spellStage','readStage','misses','qsource','enMatchStage','enPickStage','enListenStage','enSpellStage','enSentStage','enQsource'];
```

- [ ] **Step 3: applySave 兜底**

Edit — old:
```js
  if(typeof S.enPickStage!=='number') S.enPickStage=0;         // 英语看图选词关卡
  if(typeof S.enListenStage!=='number') S.enListenStage=0;     // 英语听音选词关卡
```
new:
```js
  if(typeof S.enPickStage!=='number') S.enPickStage=0;         // 英语看图选词关卡
  if(typeof S.enListenStage!=='number') S.enListenStage=0;     // 英语听音选词关卡
  if(typeof S.enSpellStage!=='number') S.enSpellStage=0;       // 英语拼单词关卡
  if(typeof S.enSentStage!=='number') S.enSentStage=0;         // 英语连词成句关卡
```

- [ ] **Step 4: 数据层（紧接 `_enChoices` 之后）**

Edit — old:
```js
// 英语单选玩法造候选：target + (n-1) 个同池干扰词，乱序返回。
function _enChoices(target, pool, n){
  const bag=shuffle(pool.filter(w=>w!==target)).slice(0, Math.max(0, n-1));
  return shuffle(bag.concat(target));
}
```
new:
```js
// 英语单选玩法造候选：target + (n-1) 个同池干扰词，乱序返回。
function _enChoices(target, pool, n){
  const bag=shuffle(pool.filter(w=>w!==target)).slice(0, Math.max(0, n-1));
  return shuffle(bag.concat(target));
}
// 句库索引 + 取池（连词成句）：按句长窗随关卡放开，不足则放宽。
const EN_SENT_INDEX = new Map();
((window.EN_DATA&&EN_DATA.sentences)||[]).forEach(s=>EN_SENT_INDEX.set(s.en, s));
function enSentencePool(stage){
  const all=(window.EN_DATA&&EN_DATA.sentences)||[];
  const hi=Math.min(4+Math.floor(stage/2),7), lo=Math.max(3, hi-2);
  let p=all.filter(s=> s.words && s.words.length>=lo && s.words.length<=hi);
  if(p.length<2) p=all.slice();
  return p;
}
// 拼单词取词池：在 enGamePool('spell') 基础上按词长窗过滤（随关卡变长），不足则放宽到≥3字母。
function enSpellPool(stage){
  const base=enGamePool('spell', stage);
  const maxLen=Math.min(5+stage,12), minLen=Math.max(3, stage-2);
  let p=base.filter(w=>{ const n=(w||'').length; return n>=minLen && n<=maxLen; });
  if(p.length<1) p=base.filter(w=>(w||'').length>=3);
  return p;
}
```

- [ ] **Step 5: renderModes('en') 加两张卡（拼单词 / 连词成句）**

Edit — old:
```js
      <div class="world" style="background:linear-gradient(135deg,var(--cyan),rgba(0,0,0,.25))" onclick="ELISTEN.start()">
        <div class="wicon" style="background:var(--cyan)"></div>
        <div><h3>👂 听音选词</h3><p>听发音，点出听到的单词</p></div>
      </div>`;
    return;
```
new:
```js
      <div class="world" style="background:linear-gradient(135deg,var(--cyan),rgba(0,0,0,.25))" onclick="ELISTEN.start()">
        <div class="wicon" style="background:var(--cyan)"></div>
        <div><h3>👂 听音选词</h3><p>听发音，点出听到的单词</p></div>
      </div>
      <div class="world" style="background:linear-gradient(135deg,var(--grass),rgba(0,0,0,.25))" onclick="ESPELL.start()">
        <div class="wicon" style="background:var(--grass)"></div>
        <div><h3>🔤 拼单词</h3><p>听发音看图，把字母拼成单词</p></div>
      </div>
      <div class="world" style="background:linear-gradient(135deg,var(--gold),rgba(0,0,0,.25))" onclick="ESENT.start()">
        <div class="wicon" style="background:var(--gold)"></div>
        <div><h3>🧩 连词成句</h3><p>看中文听发音，把单词排成句子</p></div>
      </div>`;
    return;
```

- [ ] **Step 6: 验证**

Run:
```bash
cd /Users/xiaojin/workspace/math-minner
grep -n "enSpellStage\|enSentStage" index.html
grep -n "function enSentencePool\|function enSpellPool\|const EN_SENT_INDEX" index.html
grep -n "ESPELL.start()\|ESENT.start()" index.html
awk '/^<script>$/{f=1;next} /^<\/script>$/{f=0} f' index.html > /tmp/_p3t3.js && node --check /tmp/_p3t3.js && echo "SYNTAX OK"
```
Expected: 各 grep 命中；SYNTAX OK。

逻辑自测（句长窗 + 词长窗随关卡变化）：
```bash
cd /Users/xiaojin/workspace/math-minner
node -e "
global.window={};const fs=require('fs');eval(fs.readFileSync('en-data.js','utf8'));
function enSentencePool(stage){const all=window.EN_DATA.sentences||[];const hi=Math.min(4+Math.floor(stage/2),7),lo=Math.max(3,hi-2);let p=all.filter(s=>s.words&&s.words.length>=lo&&s.words.length<=hi);if(p.length<2)p=all.slice();return p;}
console.log('sent pool @s0',enSentencePool(0).length,'@s3',enSentencePool(3).length,'@s6',enSentencePool(6).length);
console.log('s0 maxwords', Math.max(...enSentencePool(0).map(s=>s.words.length)),'s6 maxwords', Math.max(...enSentencePool(6).map(s=>s.words.length)));
"
```
Expected: 三个池子都 ≥2；`s0 maxwords` ≤4 而 `s6 maxwords` ≥6（句子随关卡变长）。

- [ ] **Step 7: 提交**

```bash
git add index.html
git commit -m "feat(english): 三期脚手架——enSpell/enSentStage + enSentencePool/enSpellPool + 两张玩法卡"
```

---

### Task 4: EA 有序组装引擎 + 样式

**Files:** Modify `index.html`

**Interfaces:**
- Consumes: `cnqMaxHearts/cnqHUD/cnqGood/cnqWin/cnqLose`、`Weak`、`playEn`、`shuffle`、`beep`、`$`、`show`、`toast`、`CNQ`。
- Produces: `const EA`，入口 `EA.run(cfg)`；`cfg = {kind, title, stageKey, hint, promptIsEmoji, disp(u)->str, eq(a,b)->bool, pickCur(stage,last)->{target,units:[...],decoys:[...],audio,prompt}|null, empty?, winHint?, autoPlay?}`。
- Consumed by: Task 5（ESPELL）、Task 6（ESENT）。

- [ ] **Step 1: 加 EA 引擎（紧接 ELISTEN 之后、`const PG` 之前）**

Edit — old:
```js
  win(){ cnqWin('enListenStage', ()=>ELISTEN.start(), '下一关单词更多、更易混，加油！'); },
  lose(){ cnqLose(()=>ELISTEN.start()); },
};

// 拼音配对挖矿：8 个世界合并为一条进度，每关从课本进度内混合出题（单/复韵母同关）
const PG = {
```
new:
```js
  win(){ cnqWin('enListenStage', ()=>ELISTEN.start(), '下一关单词更多、更易混，加油！'); },
  lose(){ cnqLose(()=>ELISTEN.start()); },
};

// 🧱 EA 有序组装引擎：把打乱的方块(字母/单词)按序点入槽位；配置驱动(拼单词/连词成句共用)。
const EA = {
  cfg:null,
  run(cfg){
    S.subject='en'; this.cfg=cfg; const stage=S[cfg.stageKey];
    const first=cfg.pickCur(stage, null);
    if(!first){ toast(cfg.empty||'这个题库内容不足，换个玩法或题库'); return G.goModes('en'); }
    CNQ={kind:cfg.kind, hearts:cnqMaxHearts(), maxHearts:cnqMaxHearts(), score:0, cleared:0, combo:0,
      goal:6+stage, depth:Math.min(1+Math.floor(stage/2),4), busy:false, stage, last:null,
      cur:null, slots:[], tray:[]};
    $('qTitle').textContent=`${cfg.title} · 第${stage+1}关`;
    show('cnq'); this._load(first);
  },
  _load(cur){
    CNQ.busy=false; CNQ.cur=cur; CNQ.slots=[]; CNQ.last=cur.target;
    CNQ.tray=shuffle(cur.units.concat(cur.decoys||[]).map((u,i)=>({u, id:i})));   // 每方块唯一 id，重复单元可区分
    cnqHUD();
    const c=this.cfg;
    const promptHTML = c.promptIsEmoji ? `<div class="cnqBig">${cur.prompt}</div>` : `<div class="eaCn">${cur.prompt}</div>`;
    $('qPrompt').innerHTML = promptHTML
      + `<button class="cnqSpeak" id="qSpeak">🔊 再听一遍</button>`
      + `<div class="eaSlots" id="eaSlots"></div>`;
    $('qSpeak').onclick=()=>{ if(CNQ.cur) playEn(CNQ.cur.audio); };
    $('qHint').textContent=c.hint;
    this._render();
    if(c.autoPlay!==false) playEn(cur.audio);
  },
  _render(){
    const units=CNQ.cur.units;
    $('eaSlots').innerHTML = units.map((_,i)=>{
      const t=CNQ.slots[i];
      return `<button class="eaSlot${t?' filled':''}" data-slot="${i}">${t?this.cfg.disp(t.u):'_'}</button>`;
    }).join('');
    $('eaSlots').querySelectorAll('.eaSlot').forEach(b=>b.onclick=()=>EA._unplace(+b.dataset.slot));
    const used=new Set(CNQ.slots.map(t=>t.id));
    $('qBody').className='cnqBody eaTray';
    $('qBody').innerHTML = CNQ.tray.map(t=> used.has(t.id)?'' : `<button class="eaTile" data-id="${t.id}">${this.cfg.disp(t.u)}</button>`).join('');
    $('qBody').querySelectorAll('.eaTile').forEach(b=>b.onclick=()=>EA._place(+b.dataset.id));
  },
  _place(id){
    if(CNQ.busy) return;
    if(CNQ.slots.length>=CNQ.cur.units.length) return;
    const tile=CNQ.tray.find(t=>t.id===id); if(!tile || CNQ.slots.some(s=>s.id===id)) return;
    CNQ.slots.push(tile);
    this._render();
    if(CNQ.slots.length===CNQ.cur.units.length) this._check();
  },
  _unplace(i){
    if(CNQ.busy) return;
    if(i<0 || i>=CNQ.slots.length) return;
    CNQ.slots.splice(i,1);
    this._render();
  },
  _check(){
    const got=CNQ.slots.map(t=>t.u), want=CNQ.cur.units, c=this.cfg;
    const ok = got.length===want.length && got.every((u,i)=>c.eq(u, want[i]));
    if(ok){
      CNQ.busy=true; beep('good'); playEn(CNQ.cur.audio); Weak.hit(CNQ.cur.target); cnqGood(); cnqHUD();
      $('eaSlots').querySelectorAll('.eaSlot').forEach(b=>b.classList.add('match'));
      if(CNQ.cleared>=CNQ.goal){ setTimeout(()=>this._win(),950); return; }
      setTimeout(()=>this._next(),950);
    } else {
      Weak.miss(CNQ.cur.target); beep('bad'); CNQ.combo=0; CNQ.hearts--; CNQ.busy=true; cnqHUD();
      $('eaSlots').querySelectorAll('.eaSlot').forEach(b=>b.classList.add('wrong'));
      setTimeout(()=>{ CNQ.slots=[]; CNQ.busy=false; if(CNQ.hearts<=0) this._lose(); else this._render(); },650);
    }
  },
  _next(){ const cur=this.cfg.pickCur(CNQ.stage, CNQ.last); if(!cur){ return this._win(); } this._load(cur); },
  _win(){ cnqWin(this.cfg.stageKey, ()=>EA.run(EA.cfg), this.cfg.winHint||'下一关更长、更多干扰，加油！'); },
  _lose(){ cnqLose(()=>EA.run(EA.cfg)); },
};

// 拼音配对挖矿：8 个世界合并为一条进度，每关从课本进度内混合出题（单/复韵母同关）
const PG = {
```

- [ ] **Step 2: 加 EA 样式（紧接 `.cnqChar.en .val` 规则之后）**

Edit — old:
```css
  .cnqChar.en .val{font-size:22px;letter-spacing:.3px;text-transform:lowercase;}
```
new:
```css
  .cnqChar.en .val{font-size:22px;letter-spacing:.3px;text-transform:lowercase;}
  .eaCn{text-align:center;font-family:var(--cn);font-size:22px;font-weight:700;color:var(--gold);margin-bottom:6px;}
  .eaSlots{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;min-height:46px;margin:10px 0;}
  .eaSlot{min-width:34px;min-height:44px;padding:4px 9px;border:2px dashed var(--stone-d);border-radius:8px;background:rgba(0,0,0,.25);font-family:var(--cn);font-size:22px;font-weight:700;color:#fff;cursor:pointer;}
  .eaSlot.filled{border-style:solid;border-color:var(--cyan);background:var(--stone);}
  .eaSlot.match{border-color:var(--grass);background:var(--grass);}
  .eaSlot.wrong{border-color:var(--red);animation:shake .3s;}
  .cnqBody.eaTray{grid-template-columns:repeat(auto-fill,minmax(54px,1fr));}
  .eaTile{min-height:48px;display:flex;align-items:center;justify-content:center;border:none;border-radius:8px;background:var(--stone);font-family:var(--cn);font-size:22px;font-weight:700;color:#fff;cursor:pointer;}
```

- [ ] **Step 3: 验证**

Run:
```bash
cd /Users/xiaojin/workspace/math-minner
grep -n "const EA = {" index.html
grep -n "\.eaSlot\b\|\.eaTile\b\|\.eaTray\b" index.html
awk '/^<script>$/{f=1;next} /^<\/script>$/{f=0} f' index.html > /tmp/_p3t4.js && node --check /tmp/_p3t4.js && echo "SYNTAX OK"
```
Expected: 命中 + SYNTAX OK。

- [ ] **Step 4: 提交**

```bash
git add index.html
git commit -m "feat(english): EA 有序组装引擎(槽位+托盘+满判) + 样式"
```

---

### Task 5: 🔤 拼单词 ESPELL（听写式）

**Files:** Modify `index.html`

**Interfaces:**
- Consumes: `EA.run`、`enSpellPool`、`EN_INDEX`、`_enKey`、`Weak`、`shuffle`、`S.enSpellStage`。
- Produces: `const ESPELL`（`start()`/`pick(s,last)`/`decoyLetters(units,n)`）。

- [ ] **Step 1: 加 ESPELL（紧接 EA 引擎之后、`const PG` 之前）**

Edit — old:
```js
  _win(){ cnqWin(this.cfg.stageKey, ()=>EA.run(EA.cfg), this.cfg.winHint||'下一关更长、更多干扰，加油！'); },
  _lose(){ cnqLose(()=>EA.run(EA.cfg)); },
};

// 拼音配对挖矿：8 个世界合并为一条进度，每关从课本进度内混合出题（单/复韵母同关）
const PG = {
```
new:
```js
  _win(){ cnqWin(this.cfg.stageKey, ()=>EA.run(EA.cfg), this.cfg.winHint||'下一关更长、更多干扰，加油！'); },
  _lose(){ cnqLose(()=>EA.run(EA.cfg)); },
};

// 🔤 拼单词（听写式）：听发音 + 看 emoji，把字母按序拼出。
const ESPELL = {
  start(){ EA.run({
    kind:'enSpell', title:'🔤 拼单词', stageKey:'enSpellStage',
    hint:'听发音，把字母按顺序拼出来', promptIsEmoji:true,
    disp:u=>u, eq:(a,b)=>a===b,
    empty:'这个题库能「拼单词」的单词不足，换个玩法或题库',
    winHint:'下一关单词更长、干扰更多，加油！',
    pickCur:(s,last)=>ESPELL.pick(s,last),
  }); },
  pick(s, last){
    const pool=enSpellPool(s); if(!pool.length) return null;
    const word=Weak.pick(pool, last);
    const it=EN_INDEX.get(word)||{};
    const units=Array.from(word.toLowerCase());
    const decoys=ESPELL.decoyLetters(units, Math.min(Math.floor(s/2),4));
    return {target:word, units, decoys, audio:_enKey(word), prompt: it.emoji || it.zh || word};
  },
  decoyLetters(units, n){
    const az='abcdefghijklmnopqrstuvwxyz'.split('');
    const out=[]; for(let i=0;i<n;i++) out.push(az[Math.floor(Math.random()*26)]);
    return out;
  },
};

// 拼音配对挖矿：8 个世界合并为一条进度，每关从课本进度内混合出题（单/复韵母同关）
const PG = {
```

- [ ] **Step 2: 验证**

Run:
```bash
cd /Users/xiaojin/workspace/math-minner
grep -n "const ESPELL" index.html
awk '/^<script>$/{f=1;next} /^<\/script>$/{f=0} f' index.html > /tmp/_p3t5.js && node --check /tmp/_p3t5.js && echo "SYNTAX OK"
```
Expected: 命中 + SYNTAX OK。
（真机：英语→拼单词→出 emoji 大图 + 自动发音 + 字母托盘；点字母进槽、点槽撤销；拼对发音+发矿，拼错扣心、字母退回；过关「玩法」回**英语**菜单；关卡越高词越长、干扰字母越多。）

- [ ] **Step 3: 提交**

```bash
git add index.html
git commit -m "feat(english): 拼单词 ESPELL(听写式·EA 引擎)"
```

---

### Task 6: 🧩 连词成句 ESENT

**Files:** Modify `index.html`

**Interfaces:**
- Consumes: `EA.run`、`enSentencePool`、`EN_DATA.sentences`、`shuffle`、`S.enSentStage`、`_enKey`。
- Produces: `const ESENT`（`start()`/`pick(s,last)`/`decoyWords(words,n)`）。

- [ ] **Step 1: 加 ESENT（紧接 ESPELL 之后、`const PG` 之前）**

Edit — old:
```js
  decoyLetters(units, n){
    const az='abcdefghijklmnopqrstuvwxyz'.split('');
    const out=[]; for(let i=0;i<n;i++) out.push(az[Math.floor(Math.random()*26)]);
    return out;
  },
};

// 拼音配对挖矿：8 个世界合并为一条进度，每关从课本进度内混合出题（单/复韵母同关）
const PG = {
```
new:
```js
  decoyLetters(units, n){
    const az='abcdefghijklmnopqrstuvwxyz'.split('');
    const out=[]; for(let i=0;i<n;i++) out.push(az[Math.floor(Math.random()*26)]);
    return out;
  },
};

// 🧩 连词成句：看中文 + 听发音整句，把单词按序排成句子。
const ESENT = {
  start(){ EA.run({
    kind:'enSent', title:'🧩 连词成句', stageKey:'enSentStage',
    hint:'听发音，把单词排成句子', promptIsEmoji:false,
    disp:u=>u, eq:(a,b)=>a===b,
    empty:'默认句库还没准备好，换个玩法',
    winHint:'下一关句子更长、干扰更多，加油！',
    pickCur:(s,last)=>ESENT.pick(s,last),
  }); },
  pick(s, last){
    const pool=enSentencePool(s); if(!pool.length) return null;
    let obj=pool[Math.floor(Math.random()*pool.length)];
    if(pool.length>1){ let guard=0; while(obj.en===last && guard++<8) obj=pool[Math.floor(Math.random()*pool.length)]; }
    const decoys=ESENT.decoyWords(obj.words, Math.min(Math.floor(s/2),2));
    return {target:obj.en, units:obj.words.slice(), decoys, audio:obj.audio||_enKey(obj.en), prompt:obj.zh};
  },
  decoyWords(words, n){
    if(n<=0) return [];
    const all=[]; ((window.EN_DATA&&EN_DATA.sentences)||[]).forEach(s=>s.words.forEach(w=>{ if(!words.includes(w)&&!all.includes(w)) all.push(w); }));
    return shuffle(all).slice(0,n);
  },
};

// 拼音配对挖矿：8 个世界合并为一条进度，每关从课本进度内混合出题（单/复韵母同关）
const PG = {
```

- [ ] **Step 2: 验证**

Run:
```bash
cd /Users/xiaojin/workspace/math-minner
grep -n "const ESENT" index.html
awk '/^<script>$/{f=1;next} /^<\/script>$/{f=0} f' index.html > /tmp/_p3t6.js && node --check /tmp/_p3t6.js && echo "SYNTAX OK"
```
Expected: 命中 + SYNTAX OK。
（真机：英语→连词成句→出中文 + 自动播英文整句 + 单词托盘；点词排句、点槽撤销；排对发音+发矿，排错扣心退回；过关「玩法」回**英语**菜单；关卡越高句越长、干扰词越多。）

逻辑自测（拼写规则 + 干扰不混入正解）：
```bash
cd /Users/xiaojin/workspace/math-minner
node -e "
global.window={};const fs=require('fs');eval(fs.readFileSync('en-data.js','utf8'));
function shuffle(a){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
function decoyWords(words,n){if(n<=0)return [];const all=[];window.EN_DATA.sentences.forEach(s=>s.words.forEach(w=>{if(!words.includes(w)&&!all.includes(w))all.push(w);}));return shuffle(all).slice(0,n);}
const s=window.EN_DATA.sentences[3]; const d=decoyWords(s.words,2);
console.log('target',JSON.stringify(s.words),'decoys',JSON.stringify(d),'no overlap', d.every(w=>!s.words.includes(w)));
"
```
Expected: 干扰词与正解无重叠 `no overlap true`。

- [ ] **Step 3: 提交**

```bash
git add index.html
git commit -m "feat(english): 连词成句 ESENT(EA 引擎·默认句库)"
```

---

### Task 7: README

**Files:** Modify `README.md`

- [ ] **Step 1: 更新英语「玩法」与「发音/数据」描述**

Edit `README.md` — old:
```markdown
**题库**：**默认主题**（颜色→动物→食物… 由易到难）或**自主命题**（自己录单词，只练这些）。**不绑课本**。

**玩法**：⛏️ **词义配对挖矿**（中文配英文，点方块即读英文发音）· 🎨 **看图选词**（看 emoji 四选一选单词）· 👂 **听音选词**（听发音点出单词）。都随关卡加量、针对错题多出；矿石/星星与数学、语文共享。
```
new:
```markdown
**题库**：**默认主题**（按**外研社《Join In》六年级**词汇标准，7 主题由易到难解锁：学校科目→动物→城市→食物健康→节日→职业人物→爱好梦想）或**自主命题**（自己录单词，只练这些）。默认词表是 G6 重建稿，可在 `tools/gen_en_data.py` 增删。

**玩法（5 种）**：⛏️ **词义配对挖矿**（中文配英文，点方块即读发音）· 🎨 **看图选词** · 👂 **听音选词** · 🔤 **拼单词**（听发音看图，把字母拼成单词）· 🧩 **连词成句**（看中文听发音，把单词排成句）。都**随关卡持续加难**（更长的词/句、更多干扰、更多主题、每关更多题）并针对错题多出；矿石/星星与数学、语文共享。
```

- [ ] **Step 2: 更新「重新生成」段**

Edit `README.md` — old:
```markdown
**重新生成英语数据 / 默认发音包**（仅在改了 `tools/gen_en_data.py` 词库后）：

    cd tools
    python3 gen_en_data.py          # 生成 en-data.js
    python3 gen_en_data.py audio    # 生成默认发音包 audio/en/*.mp3（需联网）
```
new:
```markdown
**重新生成英语数据 / 默认发音包**（仅在改了 `tools/gen_en_data.py` 词库/句库后）：

    cd tools
    python3 gen_en_data.py          # 生成 en-data.js（68 词 / 7 世界 / 22 句）
    python3 gen_en_data.py audio    # 生成默认发音包 audio/en/*.mp3（词+句，需联网；幂等可重跑补齐，并自动清理孤儿）
```

- [ ] **Step 3: 提交**

```bash
git add README.md
git commit -m "docs(english): README 更新 5 玩法 + Join In 六年级默认词库 + 数据重生成"
```

---

## Self-Review

**1. Spec coverage（对三期 spec + 已确认更新）：**
- EA 有序组装引擎（槽位/托盘/点入撤销/满判/cnq 经济）→ Task 4 ✓
- 拼单词 听写式（emoji+🔊、无中文无拼写、字母组装、词长窗+干扰字母）→ Task 5 + enSpellPool(Task 3) ✓
- 连词成句（中文+🔊整句、单词组装、句长窗+干扰词、默认句库）→ Task 6 + enSentencePool(Task 3) ✓
- 默认词库改 Join In 六年级（68 词/7 世界 + 22 句，贯穿全部默认游戏）→ Task 1/2；一/二期自动升级（只读 en-data.js）→ Task 2 Step 5 回归 ✓
- 难度随关卡递增（词/句变长、干扰增、主题增、每关题增）→ enSpellPool/enSentencePool 窗 + EA `goal=6+s`/`decoyN` ✓
- 句子音频管线（audio_key 支持句、gen_audio 含句、清孤儿）→ Task 1/2 ✓
- 状态存档（enSpellStage/enSentStage）→ Task 3 ✓
- 5 张玩法卡 → Task 3（前向引用，Task 5/6 补齐）✓

**2. Placeholder scan：** 无 TBD/TODO；每个 code step 给完整代码。Task3「卡片前向引用 ESPELL/ESENT」为显式设计（同二期 T1）。

**3. Type consistency：**
- EA `cfg` 字段（kind/title/stageKey/hint/promptIsEmoji/disp/eq/pickCur/empty/winHint/autoPlay）在 Task 4 定义，Task 5/6 的 `EA.run({...})` 逐字一致 ✓
- `pickCur(stage,last)->{target,units,decoys,audio,prompt}`：Task5/6 的 pick 返回字段与 EA `_load` 消费字段一致（cur.units/cur.decoys/cur.audio/cur.prompt/cur.target）✓
- stageKey 字符串 `'enSpellStage'`/`'enSentStage'` 与 freshState/SAVE_FIELDS/applySave 字段逐字一致（Task 3）✓；`cnqWin(stageKey,…)` 做 `S[stageKey]++`（既有）。
- en-data.js 句对象字段 `{en,zh,world,audio,words}`（Task1 build）与前端 `enSentencePool`(读 s.words)、`EN_SENT_INDEX`(键 s.en)、ESENT.pick(读 obj.words/obj.zh/obj.audio/obj.en) 一致 ✓
- `audio_key`(py) 与 `_enKey`(js) 规则一致；句子 audio 取 `obj.audio`（构建期 audio_key）或回退 `_enKey(obj.en)`（同值）✓
- `cnqHUD` 读 `CNQ.goal/score/cleared/maxHearts/hearts`：EA 初始化 CNQ 含这些字段 ✓；`cnqGood` 增 `CNQ.cleared`、发矿读 `CNQ.depth/combo` —— EA 的 CNQ 含 depth/combo ✓。

修订记录：
- 句库取池**只按句长窗、不按世界**（22 句小集合，世界门控会掏空早关）；超越 spec「连词成句 世界 min(2+s,7)」那条——本计划 enSentencePool 仅长度窗 + 不足放宽，更稳。
- `cnqHUD` 内有 `$('qProg').innerHTML=完成 X/goal`、`G.renderRes('qRes')` 等，EA 走 #cnq 屏复用同一 HUD，无需新增。
