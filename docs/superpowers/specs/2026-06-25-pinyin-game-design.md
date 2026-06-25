# 语文·拼音矿工 设计文档

**日期**：2026-06-25
**作者**：amwtke（设计协作：Claude）
**状态**：设计已确认，待写实现计划

## 1. 目标与约束

在现有「方块数学矿工」里新增一个**语文/拼音**学科，给 1–2 年级（6–8 岁）小学生练拼音。

硬约束（沿用现有项目的设计基因，不得破坏）：

- **同一体系、共享积分**：矿石（木/石/铁/钻）、星星 ★、镐子+技能、皮肤、心，全部跨学科共享；存档同一份。
- **像素 / Minecraft 风格**：复用现有 `.tile` / `.world` / HUD / overlay 视觉与音效。
- **运行时零第三方依赖、完全离线可用**：前端仍是静态文件，断网可玩；`server.py` 仅用标准库。第三方工具（pypinyin）只在**构建期**用，绝不进运行时。唯一例外：**语文发音音频首次需服务器联网一次**自动拉取（见 §6.1），之后全离线；数学玩法与所有游玩设备始终 100% 离线。
- **本地多人服务器版**：进度按玩家名存服务器 `data/<名字>.json`，新字段对 `server.py` 透明。

非目标（YAGNI，本期不做）：

- 不做账号体系/排行榜/联机对战之外的任何新基础设施。
- 不做手写识别、不做语音输入（孩子说、机器判）。
- 不做 Service Worker / PWA 离线包（现有 HTTP 缓存已够，保持「单文件前端」洁癖）。

## 2. 导航架构

现状：标题页「开始游戏」按钮 `onclick="G.goModes()"`（index.html:210），`G.goModes` 在 index.html:991 被重定义为 `function(){ show('modes'); }`，直接进写死了两个数学玩法的 `#modes` 屏。

改为三层：

```
标题页 → 【新】#subjects 选学科屏 → #modes 玩法屏（按学科动态渲染）
```

1. 新增 `#subjects` 屏（位于 `#title` 与 `#modes` 之间），复用 `.world` 大卡样式，两张卡：**➗ 数学**、**📖 语文拼音**。
2. 标题按钮改 `onclick="G.goSubjects()"`；新增 `G.goSubjects(){ show('subjects'); }`。
3. `G.goModes` 改为接收学科参数：`G.goModes = function(subj){ S.subject = subj; renderModes(subj); show('modes'); }`。
4. 新增 `renderModes(subj)`：
   - `subj==='math'` → 渲染现有两卡（配对挖矿→`G.goWorlds`、消消乐→`M.start`）。把现 `#modes` 写死的两个 `div` 移进这里。
   - `subj==='cn'` → 渲染四卡（拼音配对挖矿→`PG.start`、拼音拼读→`PM.start`、声调小游戏→`TONE.start`、听音找字→`LISTEN.start`）。
5. 返回键：各语文玩法的「🏠 玩法」按钮 `onclick="G.goModes(S.subject)"`；`#subjects` 屏加「↩ 标题」返回。`#modes` 现有「🗑️ 清空进度」按钮保留。

⚠️ 风险点：`G.goModes` 在 991 行被覆盖、`G` 对象内部并没有 `goModes` 方法，容易漏改导致数学入口或返回键断掉。必须统一改这一处。

## 3. 拼音世界地图（按部编版课本顺序解锁，非字典序）

依据：部编版（统编版）一年级上册语文，汉语拼音（一）第 1–8 课 + 汉语拼音（二）第 9–13 课。**先单韵母 → 再声母 → 后复韵母/鼻韵母**。

| # | 世界 | 聚焦 | 内容 | 对应课 |
|---|---|---|---|---|
| A | 🌱 单韵母草原 | 6 单韵母 + 四声入门 | a o e i u ü | 1–2 |
| B | ⛏️ 声母矿洞·前段 | 易发音声母 + 首次两拼 | b p m f d t n l | 3–4 |
| C | 🪨 声母矿洞·中段 | g k h j q x + **ü 去两点** | g k h j q x | 5–6 |
| D | 🔁 平翘舌矿井 | + 整体认读① | z c s zh ch sh r · zhi chi shi ri zi ci si yi wu yu | 7–8 |
| E | 🏞️ 复韵母山谷 | 9 复韵母 + ye yue | ai ei ui ao ou iu ie üe er | 9–11 |
| F | 🕳️ 鼻韵母洞窟 | 前鼻 + 三拼 + yin yun yuan | an en in un ün | 12 |
| G | 💎 后鼻韵母深渊·毕业 | 后鼻 + ying + 综合 BOSS | ang eng ing ong | 13 |

数据校验（多源核对）：声母 23（教学含零声母 y/w）、韵母 24（单 6 + 复 9 含特殊韵母 er + 前鼻 5 + 后鼻 4）、整体认读 16（zhi chi shi ri zi ci si yi wu yu ye yue yin yun yuan ying）。

每关只引入 1–2 课新内容、控制 4–8 题；拼读/出题只用**已解锁**的声母+韵母组合，**绝不超纲**。

### 拼音教学易错点（出题/数据/录音必须遵守）

1. **j q x y 与 ü 相拼去两点**：ju=jü、qu=qü、xu=xü、yu=yü；但 **n l 与 ü 相拼保留两点**：nü(女)、lü(绿)。题面与音频要区分 nu/nü、lu/lü。
2. **整体认读音节只整块认读、不拆拼**：拼读玩法不得要求用声母+韵母拼出 zhi/chi/yuan 等；它们在配对/听音里作为整块出现。
3. **标调位置**：有 a 标 a；无 a 标 o 或 e；iu 标 u、ui 标 i；i 上标调去掉点。一个音节只一个调号，轻声不标。
4. **平翘舌（z-zh / c-ch / s-sh）、前后鼻（an-ang / in-ing）** 是最大听辨难点，做成「听音找字 / 声调小游戏」的对照辨音题。
5. **字形**：拼音用清晰印刷体（注意 a/ɑ、g/ɡ 单层写法），别用像素英文字体显示拼音/汉字（见 §6 字体处理）。

## 4. 四种玩法

所有玩法共用：心（命）、星星 ★、矿石、镐子等级/技能、皮肤、连击、发矿与扣血计分、win/lose overlay。

### 4.1 🔤 拼音配对挖矿 —— 复用现有配对引擎（投入最小）

玩法：点「汉字 tile（妈）」再点「拼音 tile（mā）」配对成功就挖矿；可反向（拼音→汉字）。配对成功播该音节发音。

引擎：**泛化现有 `G.buildBoard/tap/success/fail/giveOre/技能/HUD`（index.html:568–700）**。核心配对逻辑只认 `pid` 与 `k`（'q'/'a'），不关心内容，故近乎零改动：

- 把 `buildBoard` 里算式生成段（572–583）抽成**题库生成器**，产出 `pairs=[{txt:'妈', ans:'mā'}]`。
- `renderBoard`（596）的 `.val` 已直接渲染字符串，汉字/拼音直接显示；给拼音/汉字 tile 加 `.tile.cn` 用中文字体、字号调小。
- `d.dots` 在汉字模式必须置 `false`（拼音 tile 渲染点阵计数会出错）。
- `success`（659）末尾调 `playPy(...)` 播音节。

### 4.2 🧩 拼音拼读 —— 新写 PM 引擎（不要改消消乐）

玩法：顶部显示目标字「八」+ 🔊；下方三行按钮：**声母行 / 韵母行 / 声调行**；各选一个拼出 `b + a + ¯ → bā`，与目标音节比对，正确则挖矿。

引擎决策：**另写 `PM`（PinyinSpell）引擎，不改造消消乐 `M`。** 理由：`M` 整套建立在「相邻格子求和==target」（相邻约束 / gravity 下落 / sum / paths DFS），与「三类各选其一拼成音节」根本不是一个模型，硬复用会处处别扭、引入大量边界 bug。

PM **只抄 `M` 的关卡外壳**：`cfg(stage)` 难度曲线、hearts/score/combo、`giveOre`、win/lose。核心交互全新（三组候选按钮 + 累积选择 + 比对目标）。候选只列**已解锁**的声母/韵母；整体认读音节不进拼读（按整块在别的玩法出现）。

### 4.3 🎵 声调小游戏 —— 轻量新引擎

玩法：出一个字/无调音节，4 个声调键 `ˉ ˊ ˇ ˋ`，点对的挖矿、点错扣心；出题与答对时播音频。重点拿平翘舌/前后鼻易混字做辨音。

引擎：轻量 `TONE`（几十行），复用 `.tile` 样式 + `giveOre` 风格发矿/扣血/计分 + 音频。不硬塞进 `buildBoard` 的 `pid` 体系（四个声调答案池易撞 pid）。

### 4.4 👂 听音找字 —— 轻量新引擎（音频驱动）

玩法：顶部 🔊 播一个音节，下方 N 个候选汉字 tile，点出读该音的字；答对复播、挖矿。

引擎：轻量 `LISTEN`，复用 `.tile` 样式 + 发矿/扣血/计分；核心是「单选对/错」+ 音频播放，不是两两 pid 配对。

## 5. 内容与拼音数据生成

- **字/词库 ~300 条**，已按难度分 3 级、按主题分组（数字/家人/身体/自然天象/动物/植物/颜色/方位/反义/食物/水果/动作/学校/时间/衣物/家居/景物/情绪/礼貌用语/双字词…）。
- **拼音不手打**：构建期脚本 `tools/gen_data.py` 用 **pypinyin** 由汉字生成：带调拼音（`Style.TONE`）、声母（`INITIALS`）、韵母（`FINALS`）、声调数字（`Style.TONE3` 取尾数 1–4，轻声 0/5）。原因：几百个声调手打必错，且 pypinyin 能按词消歧多音字。
- **产物 = `pinyin-data.js`**（一个 `window.PINYIN_DATA = {...}` 全局 + `SHENGMU/YUNMU/TONES` 表）。
  - ⚠️ **必须是 `.js` 不是 `.json`**：给 `.json` 开静态白名单会顺带让人能直接 GET `data/<玩家>.json` 拿到别人存档。`.js` 已在白名单，安全。
- 多音字防护：①优先选儿童语境读音唯一的字；②高频多音字只放进读音确定的词（长大 zhǎng / 长短 cháng）；③双字词用整词消歧 + 人工抽查轻声（爸爸/星星/弟弟叠词第二字轻声 tone=0）；④构建脚本输出 `polyphone_review.txt` 供人工过一遍再发布。重点核对：长/地/发/和/为/着/觉/乐/教/数/分/重/行/还/得。

数据结构（每条）：`{hz:'妈', py:'mā', sm:'m', ym:'a', tone:1, audio:'ma1'}`。

## 6. 音频系统

**音源（已选定）**：`davinfifield/mp3-chinese-pinyin-sound`（GitHub，The Unlicense / 公共领域），~1600 个真人女声 mp3，命名 `ma1.mp3`（拼音字母 + 声调数字）。体积 10–30MB。**仅家庭局域网自用、不公开发布**（来源链不完全清晰，故不对外分发）。

### 6.1 获取策略：运行时按需自动拉取（音频不入 git）

音频文件**不进 git**（二进制大 + 来源链不清）。改为**服务器在运行时按需拉取**，触发点 = 玩家**首次进入「语文」学科**：

1. 前端进 `#subjects` 选「📖语文」→ 调 `GET /api/audio/status`。已就绪 → 直接进语文玩法；未就绪 → 显示「首次进入语文，正在下载发音资源…」进度屏，调 `POST /api/audio/fetch`。
2. **服务器**（不是浏览器）用标准库 `urllib` 下载 davinfifield 仓库 zip **一次**（codeload，约 10–30MB），`zipfile` 解出音节 mp3 到 `audio/pinyin/`，全部成功后写 `audio/.ready` 哨兵。完成 → 前端进入语文。
3. 之后任何设备、任何时候都从本地服务器离线取音频，**不再联网**。

要点：

- **只有服务器机器需要联网一次**；手机/平板等游玩设备始终离线——与现有「局域网设备离线」一致。**数学玩法永远 100% 离线、不受影响**。
- **整包 zip 一次性下载**优于逐个抓几百个小文件：一条连接、更稳、不踩 GitHub 限流（刚经历过网络抖动，稳健性优先）。
- **并发保护**：`ThreadingHTTPServer` 下用服务器端锁 + 下载中状态标志，多设备同时触发只下一次。
- **幂等/可重跑**：已存在文件跳过；`.ready` 哨兵在全部解压成功后才写；中途失败可重跑补齐。
- **服务器离线兜底**：拉取失败**不阻断游戏**——前端给「继续（暂无发音）」按钮，降级静音+纯视觉，提示「服务器联网后重进语文即可补全发音」。
- **零第三方依赖**：`urllib.request` + `zipfile` 全是 Python 标准库，`server.py` 不引入任何包。

✅ davinfifield 仓库结构已联网核实：默认分支 `master`、mp3 在 `mp3/` 子目录、zip 直链 `https://codeload.github.com/davinfifield/mp3-chinese-pinyin-sound/zip/refs/heads/master`、ü 写作 `uu`、The Unlicense。

### 6.2 落地细节

- 目录 `audio/pinyin/<code>.mp3`（与 `fonts/` 平级，现有静态服务自动托管，无需新路由）。`<code>` = 不带声调字母 + 调号数字（`ba1` `mao1` `hao3`）。轻声用 `5` 或省略。
- **ü 的文件名按 davinfifield 实际命名**（已联网核实：ü 写作 `uu`，lü→`luu3.mp3`、nǚ→`nuu3.mp3`、lüe→`luue`；ju/qu/xu/yu 不变）。前端用 `/api/audio/status` 判断整体是否就绪；单个文件缺失则 `.catch` 静默降级，不需单独 manifest。
- 单字发音 = 直接播放其音节文件。**davinfifield 只有音节级音频，没有整词录音**，故多字词（如「太阳」）= 按 `PINYIN_DATA` 里每个字的 code **顺序播放**（`tai4` → `yang2`，间隔 ~120ms），不做音频拼接。一期可只对单字玩法发音，双字词发音放二期。

**server.py 改动**（静态白名单 +4 行；外加音频拉取端点 ~50 行，全标准库）：

```python
# ALLOWED_STATIC_EXT(第 26–29 行)追加：
".m4a", ".mp3", ".aac", ".ogg", ".wav",
# _content_type(第 214–229 行)追加（m4a 必须是 audio/mp4，否则 iOS 拒播）：
(".mp3", "audio/mpeg"),
(".m4a", "audio/mp4"),
```

新增两个 API（见 §6.1）：
- `GET /api/audio/status` → `{ready: bool, have: N}`，依据 `audio/.ready` 哨兵与 `audio/pinyin/` 实有文件数。
- `POST /api/audio/fetch` → 加服务器锁；`urllib.request` 下 davinfifield zip → `zipfile` 解压到 `audio/pinyin/` → 写 `.ready`；返回结果/进度。失败返回错误码，前端走降级兜底。

安全面不变：`_serve_static` 仍拒以点开头路径段、`commonpath` 越界防御照常；文件名走 ASCII（拼音码）零额外风险。下载只写入 `audio/` 子树并对解压条目做路径越界校验（zip-slip 防御）。可选：把 `audio/` 的 `Cache-Control` 改 `immutable` 长缓存（性能优化，非必需）。

**前端播放（纯 HTML5 Audio，离线，无库）**：

- `playPy(code)` helper 放在 `beep()` 旁（index.html:430 附近），仿 `beep` 的 try/catch 离线兜底——无文件/不支持时静默，不打断游戏。
- 单例音频池 `Map<code, Audio>` 复用，`currentTime=0` 重播，`.play().catch(()=>{})` 兜底。
- **iOS/Safari 首次播放须用户手势解锁**：在 `#subjects` 选学科的第一次点击里跑一次「静音 Audio play→pause」预热，否则 iPad 不出声。
- 进关时按本屏所需 code 预加载（几十 KB，瞬时）。
- **新增下载进度屏 `#audioFetch`**：选语文且未就绪时显示，调 `/api/audio/fetch`，展示「正在下载发音…」与进度/转圈；成功进语文，失败显示「继续（暂无发音）」降级按钮。

## 7. 状态与存档

新增 state（freshState 初始化）：

- `S.subject`：当前学科 `'math'|'cn'`。
- `S.mode`：当前语文玩法 `'pyMatch'|'pySpell'|'tone'|'listen'`。
- `S.pyStage`：`{pyMatch:0, tone:0, listen:0}`（配对类语文玩法关卡，类比数学 `S.stage`）。
- `S.spellStage`：拼读关卡（类比 `S.crushStage`）。
- `PG/PM/TONE/LISTEN` 运行时对象用局部 `let` 持有，**不进存档**（类比 `CR`）。

存档：

- `SAVE_FIELDS`（index.html:446）追加 `'pyStage'`、`'spellStage'`。
- `applySave`（496）照 `stage` 兜底：`S.pyStage = Object.assign({pyMatch:0,tone:0,listen:0}, S.pyStage||{})`，防旧档缺键「第 NaN 关」。
- 经济系统（res/tool/skin/stars）天然跨学科共享，无需新增——正是「矿石镐子皮肤共享」题意。
- server.py 的 `_post_save` 原样存任意 JSON，**不必改 Python 存档逻辑**。

## 8. 分期实现

- **一期（闭环）**：`#subjects` 选学科屏 + 导航改造 + 🔤拼音配对挖矿（泛化配对引擎）+ `tools/gen_data.py` 内容管线 + `pinyin-data.js` + 音频接入（server.py 静态白名单 + `/api/audio/status`、`/api/audio/fetch` 拉取端点 + `#audioFetch` 下载屏 + `playPy`）。跑通从登录→选语文→（首次自动下载发音）→配对→挖矿→升镐 的完整闭环。
- **二期**：👂听音找字 + 🎵声调小游戏（两个轻量引擎，复用一期搭好的音频与样式）。
- **三期**：🧩拼音拼读（新 PM 引擎，最重）。

## 9. 风险与对策

| 风险 | 对策 |
|---|---|
| tile 现用像素英文字体，汉字/拼音会乱 | 新增 `.tile.cn{font-family:var(--cn)}`、字号调小；声调符号 ā á ǎ à 也必须用 `--cn` |
| `G.goModes` 991 行覆盖、易漏改断掉数学入口 | 统一改造这一处，回归测试数学两玩法入口与返回键 |
| `d.dots` 汉字模式渲染点阵出错 | 题库为 cn 时强制 `d.dots=false` |
| 旧存档无新字段→第 NaN 关 | `applySave` 用 `Object.assign` 兜底 |
| 把消消乐 M 硬改成拼读 | 明确不走这条路，另写 PM，只抄关卡外壳 |
| iOS 音频自动播放被拒 | 所有 `playPy` 在点击回调内；首次手势静音解锁；听音找字自动复播也须在手势链内 |
| 音频文件 ü/缺失音节 | 单文件缺失则播放 `.catch` 静默降级；下载逻辑按 davinfifield 实际命名（ü→`uu`，已核实）映射 |
| 多音字读错音 | 见 §5 多音字防护 + `polyphone_review.txt` 人工过审 |
| 运行时拉取失败 / 服务器无网 | 不阻断游戏，降级静音+「继续」按钮；联网后重进语文补全；下载加锁防并发、`.ready` 哨兵保证幂等可重跑 |
| davinfifield 仓库结构/分支 未来变化 | 已核实 `master`/`mp3/`/ü→`uu`/Unlicense；解压做 zip-slip 路径越界校验 |
| 多设备同时首次进语文触发并发下载 | 服务器端锁 + 下载中状态标志，只下一次，其余等待结果 |

## 10. 涉及文件清单

| 文件 | 改动 |
|---|---|
| `index.html` | +250~350 行：`#subjects` 屏 + `#audioFetch` 下载屏 + 导航改造 + 配对引擎泛化 + PM/TONE/LISTEN 引擎 + `playPy` + 引用 `pinyin-data.js`；新增 `.tile.cn` 等样式 |
| `server.py` | +~4 行静态白名单/MIME；+~50 行音频拉取端点（`/api/audio/status`、`/api/audio/fetch`，`urllib`+`zipfile` 标准库） |
| `tools/gen_data.py` | 新增：pypinyin **构建期**生成 `pinyin-data.js` + `polyphone_review.txt`（仅开发机跑一次，产物入 git） |
| `pinyin-data.js` | 构建产物，**入 git**（小文本）：`PINYIN_DATA` + `SHENGMU/YUNMU/TONES` |
| `audio/pinyin/*.mp3`、`audio/.ready` | 运行时由服务器拉取生成，**不入 git**（`.gitignore` 加 `audio/`） |
| `.gitignore` | 追加 `audio/` |
| `README.md` | 补语文玩法、首次进入语文需服务器联网一次拉取发音的说明 |

## 11. 运行时零依赖确认

pypinyin 只在 `tools/gen_data.py`（构建机）运行，产出纯静态 `pinyin-data.js`（入 git）。音频由 `server.py` 用标准库 `urllib`+`zipfile` 运行时按需拉取（不入 git、首次需服务器联网一次），产物是纯静态 mp3。前端与 `server.py` 全程零第三方依赖。
