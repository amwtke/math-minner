# 英语矿工 三期设计 —— 拼单词 + 连词成句（EA 组装引擎）

> 承接 `2026-06-29-english-game-design.md`（总设计，§4.4/§4.5）与一/二期实现。本文是三期的细化设计。

## 目标

给英语学科再加两种**有序组装**玩法，覆盖「拼写/自然拼读」与「语序/句型」两个语感维度：

- 🔤 **拼单词（听写式）**：听发音 + 看图，把打乱的**字母**按顺序拼成单词。
- 🧩 **连词成句**：看中文 + 听发音，把打乱的**单词**按顺序排成英文短句。

两者共用一个新的 **EA（English Assembly）有序组装引擎**，复用 `#cnq` 屏、`cnq*` 经济（矿石/心/星/连击）、`Weak` 错题本、`playEn` 发音。**难度随关卡进度持续增大**（见 §5，本期硬性要求）。

## 1. EA 引擎（有序组装）

**机制**：目标是一个有序单元序列（字母数组 或 单词数组）。
- 屏上分两区：**槽位区**（已拼出的序列，从左到右）+ **托盘区**（打乱的可点方块，含若干干扰单元）。
- 点托盘方块 → 落入下一个空槽（该方块从托盘移除/置灰）。
- 点已落入槽位的方块 → 退回托盘（撤销，支持改错）。
- 槽位填满即自动判定：
  - **对** → `beep('good')`、`playEn(目标音)`、`Weak.hit(目标)`、`cnqGood()`（计分+发矿）、槽位标绿；满 `goal` 过关，否则下一题。
  - **错** → `beep('bad')`、扣 1 心、`Weak.miss(目标)`、槽位闪红后全部退回托盘重拼；心为 0 则 `cnqLose`。
- 复用 `cnqMaxHearts/cnqHUD/cnqOre/cnqGood/cnqWin/cnqLose`、`#cnq` 屏（`qTitle/qPrompt/qHint/qBody`）、`Weak`、`playEn`。

**状态**：`CNQ = {kind, hearts, maxHearts, score, cleared, combo, goal, depth, busy, pool, last, cur, slots, tray}`，其中 `cur = {target, units:[...有序正解], audio:key}`；`tray` = `shuffle(units + 干扰单元)`；`slots` = 已点入的单元数组。

**两种配置骑在 EA 上**：单元粒度不同（字母 / 单词）、题面不同、题池与干扰来源不同、过关字段不同。其余完全共享。

## 2. 🔤 拼单词（ESPELL，听写式）

- **题面**：`emoji` 大图 + 🔊 **进入即自动播一次** + 「🔊 再听一遍」按钮。**不显示中文、不显示拼写**（听写式，用户选定）。
- **单元**：目标单词的字母 `Array.from(word)`（保留重复字母，如 egg→e,g,g）。
- **题池**：复用 `enGamePool('spell', stage)`（默认主题按世界进度出词；自主命题出录入词）。再按**长度窗**过滤（见 §5）。单词需 ≥3 字母。
- **干扰**：托盘混入 `decoyN` 个随机 a–z 字母（§5）。
- **过关字段**：`S.enSpellStage`。
- **自主命题**：纯英文词也可玩（凭音听写，题面退化为「emoji 缺失 → 仅 🔊」，仍成立）。
- **降级备注**：听写式对「认词」基础学习者偏难。若真机上太挫败，softening 方案（进入先显示单词几秒 / 加 💡 提示按钮）是 ~2 行改动，留作可选后续。

## 3. 🧩 连词成句（ESENT）

- **题面**：**中文翻译** + 🔊 **进入即自动播一次英文整句** + 「🔊 再听一遍」。
- **单元**：句子的单词数组（数据里显式存 `words:[...]`，不含句末句号；槽位预览按空格拼接并在末尾补「.」）。
- **题池**：`enSentencePool(stage)` —— **默认句库**（§4），按长度窗 + 主题范围过滤（§5）。**本期不支持自主命题句子**（用户选定）。
- **干扰**：托盘混入 `decoyN` 个干扰单词（取自其它句子中、不在本句的词）（§5）。
- **过关字段**：`S.enSentStage`。
- **大小写/句型语感**：单词方块按句中自然形态显示（首词首字母大写、末尾「.」），有意保留——首字母大写本身是「句子开头」的教学线索。

## 4. 默认句库（内容，可编辑）

短句 3–5 词，只用已学词 + 小函数词集（I, a, the, is, it, like, see, have, and, big, small）。每句构建期生成真人音频。起始集（按主题，长度分布兼顾早关池子健康）：

**主题1 颜色数字**
- I like red. 我喜欢红色。(3)
- It is blue. 它是蓝色的。(3)
- I like blue. 我喜欢蓝色。(3)
- I see two cats. 我看见两只猫。(4)
- I have three eggs. 我有三个鸡蛋。(4)

**主题2 动物**
- I like cats. 我喜欢猫。(3)
- I like pandas. 我喜欢熊猫。(3)
- It is a dog. 它是一只狗。(4)
- I see a cat. 我看见一只猫。(4)
- I have a fish. 我有一条鱼。(4)
- The pig is big. 猪很大。(4)
- The bird is small. 鸟很小。(4)

**主题3 食物**
- I like cake. 我喜欢蛋糕。(3)
- I like milk. 我喜欢牛奶。(3)
- I like apples. 我喜欢苹果。(3)
- I see a banana. 我看见一根香蕉。(4)
- The cake is big. 蛋糕很大。(4)
- I like bread and eggs. 我喜欢面包和鸡蛋。(5)

（共 18 句：3 词 ×8、4 词 ×9、5 词 ×1。3 词句充足，保证早关池子健康。用户可在 spec 评审时增删。）

## 5. 难度随进度递增（本期硬性要求）

关卡 `s`（0 起）每过一关 `S[stageKey]++`，以下维度**单调变难**：

**🔤 拼单词（stage s）**
- 主题范围：`maxW = min(1 + s, 3)`（解锁更多主题词）。
- 单词长度窗：`hi = min(3 + floor(s/2), 6)`，`lo = max(3, hi - 2)`；池 = 世界 1..maxW 内 `lo ≤ len ≤ hi` 的词（不足 2 个则放宽到该范围全部词）。→ 越往后越长（3→4→5→6 字母）。
- 干扰字母：`decoyN = min(floor(s/2), 4)`（0,0,1,1,2,2,3,3,4…）。
- 每关题量：`goal = 6 + s`。发矿档：`depth = min(1 + floor(s/2), 4)`。

**🧩 连词成句（stage s）**
- 主题范围：`maxW = min(2 + s, 3)`（句库小，解锁略快保池子健康）。
- 句长窗：`hi = min(3 + floor(s/2), 5)`，`lo = (s >= 4 ? 4 : 3)`；池 = 主题 1..maxW 内 `lo ≤ 词数 ≤ hi` 的句（不足 2 句则放宽）。→ 越往后句子越长（3→4→5 词）、越偏长句。
- 干扰单词：`decoyN = min(floor(s/2), 2)`（0,0,1,1,2…）。
- 每关题量：`goal = 6 + s`。发矿档：`depth = min(1 + floor(s/2), 4)`。

> 综合效果：目标更长 + 干扰更多 + 主题更广 + 每关题更多，随关卡持续加难。与一/二期玩法的 `goal=6+stage`、世界逐关解锁、`depth` 递增一致。

## 6. 数据管线 & 存档

- `tools/gen_en_data.py`：新增 `SENTENCES = [(world_id, en, zh)]`；`build()` 在 `EN_DATA` 顶层加 `sentences:[{en, zh, audio:audio_key(en), words:[...去尾句号后空格分词], world}]`（**向后兼容**：`worlds` 不变，旧前端只读 `worlds`）。`gen_audio()` 扩展为也给每个句子生成 mp3（`audio_key` 已支持句子）。
- `en-data.js`：`window.EN_DATA = {worlds:[...], sentences:[...]}`。
- 前端数据层：`enSentencePool(stage)` 取默认句库并按 §5 过滤；`EN_SENT_INDEX`（en→句对象）。拼单词复用 `enGamePool('spell', stage)`（再按长度窗过滤）。
- 存档：`S.enSpellStage` / `S.enSentStage` 入 `freshState` + `SAVE_FIELDS` + `applySave` 兜底（同二期模式）。
- 导航：`renderModes('en')` 加两张卡（英语菜单变 5 玩法）。
- 发音：拼单词 `playEn(_enKey(word))`（已有）；连词成句 `playEn(_enKey(en整句))`（默认包构建期生成；缺则静默降级）。

## 7. 全局约束（承自总设计）

- 运行时零第三方依赖；游玩设备永远离线（纯浏览器 API）；缺音频静默降级。
- 共享经济（矿石/星星/镐子/技能/皮肤/心跨学科共享）；不新增经济字段。
- 复用 `#cnq` 屏 + `cnq*` + `Weak`（键=英文词/句）；不改 cn/math 玩法行为。
- `audio_key` 规则前后端逐字一致（小写→非 [a-z0-9] 折叠为 `_`→去首尾 `_`）。
- 单文件前端（`index.html`），构建期产物 `en-data.js` + `audio/en/*.mp3` 入 git。

## 8. 单元边界

- `EA`：通用有序组装引擎（不知字母/单词；只认 `cur.units`、`tray`、`slots`）。输入：`{title, prompt(cur), audio(cur), pickTarget(stage)→cur, stageKey, hint}` 配置。
- `ESPELL` / `ESENT`：各自的配置对象（题面、题池+难度窗、干扰生成、stageKey）。
- 数据层 `enSentencePool` / 长度窗过滤：纯函数，可 node 逻辑自测。

## 9. 构建顺序（分两段）

1. **拼单词段**：EA 引擎 + ESPELL（无新数据，自包含可交付）。
2. **连词成句段**：句库数据管线（gen_en_data + en-data + 音频）+ ESENT。

## 10. 测试

前端无 JS 测试框架（仓库既有模式）：`node --check` 抽取 inline `<script>` + grep + 关键纯函数（长度窗过滤、`enSentencePool`、EA 判定）node 逻辑自测。`gen_en_data.py` 的句子分词/`audio_key` 加 unittest 断言。真机点测（iOS 自动播放、组装手感、过关加难）由用户完成（本环境无浏览器自动化）。

---

## 已确认更新（2026-06-29）—— 默认词库改为《Join In》六年级，超越本期 §4/§5

用户确认：**所有英语默认游戏**（一期 词义配对 / 二期 看图选词·听音选词 / 三期 拼单词·连词成句）的默认内容统一改用 **外研社《Join In》六年级**词汇标准。自主命题仍自由录入，不受此表限制。

**确认后的内容（本节为准，取代 §4 草稿句库）**：见 `.superpowers/sdd/joinin-g6-curated.md`（已确认稿）——
- **68 词 / 7 世界**：① 学校科目 ② 动物世界 ③ 城市地点 ④ 食物健康 ⑤ 节日庆典 ⑥ 职业人物国籍 ⑦ 爱好梦想。每词 `(world, en, zh, emoji)`。英式拼写从书：`maths`。
- **22 句 G6 句库**（连词成句用）：含一般现在时/过去式/比较级/be good at/祈使，3–7 词。
- 词级为 G6 重建（单元结构高可信、非逐词官方原表）；用户已确认。

**跨期范围**：这是对**默认数据包**的重建，不只是三期新增——
- `tools/gen_en_data.py` 的 `WORDS`（27→68）、`WORLD_META`（3→7）整体替换为 G6，并新增 `SENTENCES`（22）。
- 重新生成 `en-data.js` 与 `audio/en/*.mp3`（全部新词+新句，约 90 个 mp3，构建期联网一次）。
- 一期/二期玩法读取 `en-data.js`，**自动升级到 G6 内容**，无需改其引擎代码。
- `_enMaxWorld` 现 cap 到 `EN_DATA.worlds.length`（=7），世界逐关解锁不变。

**难度窗（按 G6 词长重调，取代 §5 数值）**：G6 词更长(3–12 字母)、句更长(3–7 词)，调窗防早关掏空且持续加难：
- 🔤 **拼单词**：世界 `min(1+s,7)`；词长 `maxLen=min(5+s,12)`、`minLen=max(3, s-2)`；干扰字母 `min(⌊s/2⌋,4)`；每关 `6+s` 题。
- 🧩 **连词成句**：世界 `min(2+s,7)`；句长 `hi=min(4+⌊s/2⌋,7)`、`lo=max(3,hi-2)`；干扰词 `min(⌊s/2⌋,2)`；每关 `6+s` 题。
- 两者池子不足 2 个时放宽（先放宽长度窗，再放宽世界范围），保证可玩。
- 发矿档 `min(1+⌊s/2⌋,4)`、心数由镐子档共享（沿用）。
