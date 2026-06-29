# 英语矿工 二期（看图选词 + 听音选词）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给英语学科加两种"单选辨认"玩法 —— 🎨 看图选词（看 emoji 四选一选单词）和 👂 听音选词（听发音点出单词），复用现有 `#cnq` 单元玩法外壳与 `cnq*` 计分/发矿/过关逻辑。

**Architecture:** 复用拼音单元玩法那套：`#cnq` 屏 + `cnq*` 帮助函数（`cnqHUD/cnqOre/cnqGood/cnqWin/cnqLose/cnqHit/cnqMiss`，全部学科无关，只读写 `CNQ`+`S`）+ 错题本 `Weak`（键=英文词，已在一期验证对英文键安全）。新增两个轻量引擎 `EPICK`/`ELISTEN`（仿 `READ`/`LISTEN`），题池走已有 `enGamePool`（按世界进度出词），发音走一期的 `playEn(_enKey(word))`，图用 `EN_INDEX` 里的 emoji（无图退中文、再退英文本身）。

**Tech Stack:** 香草 JS + HTML5 Audio（前端，零库）。无新数据、无新音频管线（单词音频与 emoji 一期已具备）。

## Global Constraints

（每个任务隐含包含本节。）

- **运行时零第三方依赖、游玩设备永远离线**：纯浏览器 API。
- **共享经济**：矿石/星星/镐子/技能/皮肤/心跨学科共享；不新增经济字段。
- **复用 `#cnq` 屏 + `cnq*` 帮助函数 + `Weak` 错题本**（键=英文词）；不改 cn/math 任何玩法。
- **发音**：`playEn(_enKey(word))`，单文件 mp3，缺文件静默降级（一期已实现）。
- **图**：用 `EN_INDEX.get(word).emoji`；无 emoji 退 `zh`；再无退英文词本身（自主命题纯英文词的退化情形，可玩）。
- **题库**：复用 `enGamePool(kind, stage)`（默认按世界 1..(1+关) 出词；自主命题出录入词）。`kind` 传 `'pick'`/`'listen'`（当前实现不按 kind 分流，返回同一词池，符合预期）。
- **English tile/选项字体**：用 `var(--cn)`（含 sans 兜底），不用像素英文字体。
- **关卡进度字段**：`S.enPickStage` / `S.enListenStage`（与拼音 listenStage 等物理隔离）。
- 只改 `index.html`（README 在最后一个任务）。

## 测试说明

前端无 JS 测试框架（仓库既有模式）。每个任务的验证 = `node --check`（抽取大 inline `<script>` 块语法检查）+ grep 确认编辑落位 + 可选 node 纯函数逻辑测试（`_enChoices`）。真机点测（点玩法→听/看→答对发音→过关→返回）由用户在真实 app 完成（本环境无浏览器自动化）。

## 文件结构

| 文件 | 改动 |
|---|---|
| `index.html` | 状态字段(enPickStage/enListenStage) + `_enChoices` 帮助 + `.cnqChar.en` 样式 + `#cnq`/cnqWin/cnqLose home 按钮学科化 + renderModes('en') 加两卡 + 新引擎 `EPICK`/`ELISTEN` |
| `README.md` | 英语小节补两玩法 |

---

### Task 1: 共享脚手架（状态字段 + `_enChoices` + 样式 + home 按钮学科化 + 两张玩法卡）

**Files:** Modify `index.html`

**Interfaces:**
- Produces: `S.enPickStage:number`、`S.enListenStage:number`（初值 0）；`_enChoices(target:string, pool:string[], n:number)->string[]`（含 target 的 n 个乱序候选）；renderModes('en') 渲染 3 张卡（词义配对/看图选词/听音选词）。
- Consumed by: Task 2（EPICK）、Task 3（ELISTEN）。
- 注：本任务后点「看图选词」「听音选词」卡会报 `EPICK/ELISTEN is not defined`（前向引用，与一期 T5 同理），Task 2/3 补齐。验收只看卡片出现 + node --check 过。

- [ ] **Step 1: freshState 加两关卡字段**

Edit — old:

```js
    enMatchStage:0, enQsource:{type:'default',label:'默认主题',items:null},
    pyMatchStage:pyStageDefaults() };
```

new:

```js
    enMatchStage:0, enPickStage:0, enListenStage:0, enQsource:{type:'default',label:'默认主题',items:null},
    pyMatchStage:pyStageDefaults() };
```

- [ ] **Step 2: SAVE_FIELDS 追加**

Edit — old:

```js
const SAVE_FIELDS=['res','tool','skinsOwned','skin','stage','crushStage','stars','totalCleared','pyMatchStage','voiceSpeed','matchStage','listenStage','toneStage','spellStage','readStage','misses','qsource','enMatchStage','enQsource'];
```

new:

```js
const SAVE_FIELDS=['res','tool','skinsOwned','skin','stage','crushStage','stars','totalCleared','pyMatchStage','voiceSpeed','matchStage','listenStage','toneStage','spellStage','readStage','misses','qsource','enMatchStage','enPickStage','enListenStage','enQsource'];
```

- [ ] **Step 3: applySave 兜底两字段**

Edit — old:

```js
  if(typeof S.enMatchStage!=='number') S.enMatchStage=0;       // 英语配对关卡
  if(!S.enQsource || typeof S.enQsource!=='object' || !S.enQsource.type)
    S.enQsource={type:'default',label:'默认主题',items:null};  // 英语题库：默认/自主命题
  if(!SKINS[S.skin]) S.skin='steve';
```

new:

```js
  if(typeof S.enMatchStage!=='number') S.enMatchStage=0;       // 英语配对关卡
  if(typeof S.enPickStage!=='number') S.enPickStage=0;         // 英语看图选词关卡
  if(typeof S.enListenStage!=='number') S.enListenStage=0;     // 英语听音选词关卡
  if(!S.enQsource || typeof S.enQsource!=='object' || !S.enQsource.type)
    S.enQsource={type:'default',label:'默认主题',items:null};  // 英语题库：默认/自主命题
  if(!SKINS[S.skin]) S.skin='steve';
```

- [ ] **Step 4: 加 `_enChoices` 帮助函数（紧接 enGamePool 之后、`_wsample` 之前）**

Edit — old:

```js
  const maxW=_enMaxWorld(stage), out=[];
  ((window.EN_DATA&&EN_DATA.worlds)||[]).forEach(w=>{ if(w.id<=maxW) w.words.forEach(it=>out.push(it.en)); });
  return out;
}
function _wsample(items, weightFn, n){  // 按权重不放回抽 n 个
```

new:

```js
  const maxW=_enMaxWorld(stage), out=[];
  ((window.EN_DATA&&EN_DATA.worlds)||[]).forEach(w=>{ if(w.id<=maxW) w.words.forEach(it=>out.push(it.en)); });
  return out;
}
// 英语单选玩法造候选：target + (n-1) 个同池干扰词，乱序返回。
function _enChoices(target, pool, n){
  const bag=shuffle(pool.filter(w=>w!==target)).slice(0, Math.max(0, n-1));
  return shuffle(bag.concat(target));
}
function _wsample(items, weightFn, n){  // 按权重不放回抽 n 个
```

- [ ] **Step 5: `.cnqChar.en` 样式（紧接 `.cnqChar .val` 规则后）**

Edit — old:

```css
  .cnqChar .val{font-family:var(--cn);font-size:30px;font-weight:700;color:#fff;}
```

new:

```css
  .cnqChar .val{font-family:var(--cn);font-size:30px;font-weight:700;color:#fff;}
  .cnqChar.en .val{font-size:22px;letter-spacing:.3px;text-transform:lowercase;}
```

- [ ] **Step 6: `#cnq` 屏 home 按钮学科化**

Edit — old:

```html
      <button class="btn gray" onclick="G.goModes('cn')">🏠 玩法</button>
      <button class="btn cyan" onclick="G.openCraft()">🔨 融合</button>
```

new:

```html
      <button class="btn gray" onclick="G.goModes(S.subject)">🏠 玩法</button>
      <button class="btn cyan" onclick="G.openCraft()">🔨 融合</button>
```

- [ ] **Step 7: cnqWin 覆盖层 home 按钮学科化**

Edit — old:

```html
    <button class="btn gray" onclick="G.close('cnqWin');G.goModes('cn')">玩法</button>
```

new:

```html
    <button class="btn gray" onclick="G.close('cnqWin');G.goModes(S.subject)">玩法</button>
```

- [ ] **Step 8: cnqLose 覆盖层 home 按钮学科化**

Edit — old:

```html
    <button class="btn gray" onclick="G.close('cnqLose');G.goModes('cn')">玩法</button>
```

new:

```html
    <button class="btn gray" onclick="G.close('cnqLose');G.goModes(S.subject)">玩法</button>
```

- [ ] **Step 9: renderModes('en') 加两张卡（看图选词 / 听音选词）**

Edit — old:

```js
    list.innerHTML = `
      <div class="world" style="background:linear-gradient(135deg,var(--gold),rgba(0,0,0,.25))" onclick="EG.start()">
        <div class="wicon" style="background:var(--gold)"></div>
        <div><h3>⛏️ 词义配对挖矿</h3><p>中文配英文，点方块听发音</p></div>
      </div>`;
    return;
```

new:

```js
    list.innerHTML = `
      <div class="world" style="background:linear-gradient(135deg,var(--gold),rgba(0,0,0,.25))" onclick="EG.start()">
        <div class="wicon" style="background:var(--gold)"></div>
        <div><h3>⛏️ 词义配对挖矿</h3><p>中文配英文，点方块听发音</p></div>
      </div>
      <div class="world" style="background:linear-gradient(135deg,var(--red),rgba(0,0,0,.25))" onclick="EPICK.start()">
        <div class="wicon" style="background:var(--red)"></div>
        <div><h3>🎨 看图选词</h3><p>看图(emoji)，四选一选单词</p></div>
      </div>
      <div class="world" style="background:linear-gradient(135deg,var(--cyan),rgba(0,0,0,.25))" onclick="ELISTEN.start()">
        <div class="wicon" style="background:var(--cyan)"></div>
        <div><h3>👂 听音选词</h3><p>听发音，点出听到的单词</p></div>
      </div>`;
    return;
```

- [ ] **Step 10: 验证**

Run:
```bash
cd /Users/xiaojin/workspace/math-minner
grep -n "enPickStage\|enListenStage" index.html        # freshState/SAVE_FIELDS/applySave 各处
grep -n "function _enChoices" index.html
grep -n "EPICK.start()\|ELISTEN.start()" index.html    # 两张卡
grep -n "G.goModes(S.subject)" index.html              # 三处(450/553/560)
awk '/^<script>$/{f=1;next} /^<\/script>$/{f=0} f' index.html > /tmp/_p2t1.js && node --check /tmp/_p2t1.js && echo "SYNTAX OK"
```
Expected: 所有 grep 命中；`G.goModes(S.subject)` 至少 3 处；SYNTAX OK。

可选 node 逻辑测：
```bash
node -e "global.window={};const fs=require('fs');function shuffle(a){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;} function _enChoices(t,p,n){const b=shuffle(p.filter(w=>w!==t)).slice(0,Math.max(0,n-1));return shuffle(b.concat(t));} const c=_enChoices('apple',['apple','cat','dog','egg','fish'],4); console.log('len',c.length,'has target',c.includes('apple'),'unique',new Set(c).size===c.length);"
```
Expected: `len 4 has target true unique true`。

- [ ] **Step 11: 提交**

```bash
git add index.html
git commit -m "feat(english): 二期脚手架——enPick/enListenStage + _enChoices + cnq home 学科化 + 两张玩法卡"
```

---

### Task 2: 🎨 看图选词 `EPICK` 引擎

**Files:** Modify `index.html`

**Interfaces:**
- Consumes: `enGamePool('pick',stage)`、`EN_INDEX`、`_enChoices`、`_enKey`、`playEn`、`Weak`、`cnq*` 帮助、`S.enPickStage`。
- Produces: `const EPICK`（`start()`/`next()`/`answer()`/`win()`/`lose()`）。

- [ ] **Step 1: 加 `EPICK` 引擎（紧接 READ 引擎之后、`const PG` 之前）**

Edit — old:

```js
// 拼音配对挖矿：8 个世界合并为一条进度，每关从课本进度内混合出题（单/复韵母同关）
const PG = {
```

new:

```js
// 🎨 看图选词：看 emoji（无图退中文/英文）→ 4 选 1 选英文词
const EPICK = {
  start(){
    S.subject='en'; const stage=S.enPickStage;
    const pool=enGamePool('pick', stage);
    if(pool.length<2){ toast('这个题库能「看图选词」的单词不足，换个玩法或题库'); return G.goModes('en'); }
    CNQ={kind:'enPick', hearts:cnqMaxHearts(), maxHearts:cnqMaxHearts(), score:0, cleared:0, combo:0,
      goal:6+stage, n:Math.min(4,pool.length), depth:Math.min(1+Math.floor(stage/2),4),
      busy:false, pool, last:null, cur:null};
    $('qTitle').textContent=`🎨 看图选词 · 第${stage+1}关`;
    show('cnq'); this.next();
  },
  next(){
    CNQ.busy=false;
    const target=Weak.pick(CNQ.pool, CNQ.last); CNQ.last=target;
    const it=EN_INDEX.get(target)||{};
    const prompt=it.emoji || it.zh || target;            // 有图用图；无图退中文；再无退英文本身
    const choices=_enChoices(target, CNQ.pool, CNQ.n);
    CNQ.cur={target, audio:_enKey(target)};
    cnqHUD();
    $('qPrompt').innerHTML=`<div class="cnqBig">${prompt}</div>`;
    $('qHint').textContent='看图，选对应的单词';
    $('qBody').className='cnqBody listenGrid';
    $('qBody').innerHTML=choices.map(w=>`<button class="cnqChar en" data-w="${w}"><span class="val">${w}</span></button>`).join('');
    $('qBody').querySelectorAll('.cnqChar').forEach(b=>b.onclick=()=>EPICK.answer(b.dataset.w,b));
  },
  answer(w,el){
    if(CNQ.busy) return;
    if(w===CNQ.cur.target){
      CNQ.busy=true; beep('good'); cnqHit(el); playEn(CNQ.cur.audio); Weak.hit(CNQ.cur.target); cnqGood(); cnqHUD();
      if(CNQ.cleared>=CNQ.goal){ setTimeout(()=>this.win(),850); return; }
      setTimeout(()=>this.next(),850);
    } else {
      Weak.miss(CNQ.cur.target); cnqMiss(el);
      if(CNQ.hearts<=0){ CNQ.busy=true; setTimeout(()=>this.lose(),320); }
    }
  },
  win(){ cnqWin('enPickStage', ()=>EPICK.start(), '下一关单词更多、范围更广，加油！'); },
  lose(){ cnqLose(()=>EPICK.start()); },
};

// 拼音配对挖矿：8 个世界合并为一条进度，每关从课本进度内混合出题（单/复韵母同关）
const PG = {
```

- [ ] **Step 2: 验证**

Run:
```bash
cd /Users/xiaojin/workspace/math-minner
grep -n "const EPICK" index.html
grep -n "cnqWin('enPickStage'" index.html
awk '/^<script>$/{f=1;next} /^<\/script>$/{f=0} f' index.html > /tmp/_p2t2.js && node --check /tmp/_p2t2.js && echo "SYNTAX OK"
```
Expected: 命中 + SYNTAX OK。
（真机点测：英语→看图选词→出现 emoji 大图 + 4 个英文词，点对发音+发矿+进度，点错扣心，6+关过关弹「再来一关」，「玩法」按钮回**英语**玩法屏。）

- [ ] **Step 3: 提交**

```bash
git add index.html
git commit -m "feat(english): 看图选词 EPICK 引擎(emoji→四选一选词)"
```

---

### Task 3: 👂 听音选词 `ELISTEN` 引擎

**Files:** Modify `index.html`

**Interfaces:**
- Consumes: `enGamePool('listen',stage)`、`_enChoices`、`_enKey`、`playEn`、`Weak`、`cnq*` 帮助、`S.enListenStage`。
- Produces: `const ELISTEN`（`start()`/`next()`/`answer()`/`win()`/`lose()`）。

- [ ] **Step 1: 加 `ELISTEN` 引擎（紧接 Task 2 加的 `EPICK` 之后、`const PG` 之前）**

Edit — old:

```js
  win(){ cnqWin('enPickStage', ()=>EPICK.start(), '下一关单词更多、范围更广，加油！'); },
  lose(){ cnqLose(()=>EPICK.start()); },
};

// 拼音配对挖矿：8 个世界合并为一条进度，每关从课本进度内混合出题（单/复韵母同关）
const PG = {
```

new:

```js
  win(){ cnqWin('enPickStage', ()=>EPICK.start(), '下一关单词更多、范围更广，加油！'); },
  lose(){ cnqLose(()=>EPICK.start()); },
};

// 👂 听音选词：🔊 播单词发音 → 4 选 1 点出听到的词
const ELISTEN = {
  start(){
    S.subject='en'; const stage=S.enListenStage;
    const pool=enGamePool('listen', stage);
    if(pool.length<2){ toast('这个题库能「听音选词」的单词不足，换个玩法或题库'); return G.goModes('en'); }
    CNQ={kind:'enListen', hearts:cnqMaxHearts(), maxHearts:cnqMaxHearts(), score:0, cleared:0, combo:0,
      goal:6+stage, n:Math.min(3+Math.floor(stage/2),8), depth:Math.min(1+Math.floor(stage/2),4),
      busy:false, pool, last:null, cur:null};
    $('qTitle').textContent=`👂 听音选词 · 第${stage+1}关`;
    show('cnq'); this.next();
  },
  next(){
    CNQ.busy=false;
    const target=Weak.pick(CNQ.pool, CNQ.last); CNQ.last=target;
    const choices=_enChoices(target, CNQ.pool, CNQ.n);
    CNQ.cur={target, audio:_enKey(target)};
    cnqHUD();
    $('qPrompt').innerHTML=`<button class="cnqSpeak" id="qSpeak">🔊 再听一遍</button>`;
    $('qSpeak').onclick=()=>{ if(CNQ.cur) playEn(CNQ.cur.audio); };
    $('qHint').textContent='听发音，点出对应的单词';
    $('qBody').className='cnqBody listenGrid';
    $('qBody').innerHTML=choices.map(w=>`<button class="cnqChar en" data-w="${w}"><span class="val">${w}</span></button>`).join('');
    $('qBody').querySelectorAll('.cnqChar').forEach(b=>b.onclick=()=>ELISTEN.answer(b.dataset.w,b));
    playEn(CNQ.cur.audio);
  },
  answer(w,el){
    if(CNQ.busy) return;
    if(w===CNQ.cur.target){
      CNQ.busy=true; beep('good'); cnqHit(el); playEn(CNQ.cur.audio); Weak.hit(CNQ.cur.target); cnqGood(); cnqHUD();
      if(CNQ.cleared>=CNQ.goal){ setTimeout(()=>this.win(),850); return; }
      setTimeout(()=>this.next(),850);
    } else {
      Weak.miss(CNQ.cur.target); cnqMiss(el);
      if(CNQ.hearts<=0){ CNQ.busy=true; setTimeout(()=>this.lose(),320); }
    }
  },
  win(){ cnqWin('enListenStage', ()=>ELISTEN.start(), '下一关单词更多、更易混，加油！'); },
  lose(){ cnqLose(()=>ELISTEN.start()); },
};

// 拼音配对挖矿：8 个世界合并为一条进度，每关从课本进度内混合出题（单/复韵母同关）
const PG = {
```

- [ ] **Step 2: 验证**

Run:
```bash
cd /Users/xiaojin/workspace/math-minner
grep -n "const ELISTEN" index.html
grep -n "cnqWin('enListenStage'" index.html
awk '/^<script>$/{f=1;next} /^<\/script>$/{f=0} f' index.html > /tmp/_p2t3.js && node --check /tmp/_p2t3.js && echo "SYNTAX OK"
```
Expected: 命中 + SYNTAX OK。
（真机点测：英语→听音选词→自动播发音 + 「🔊 再听一遍」可复播 + 4 个英文词，点对发音+发矿，点错扣心，过关返回**英语**玩法屏。）

- [ ] **Step 3: 提交**

```bash
git add index.html
git commit -m "feat(english): 听音选词 ELISTEN 引擎(听发音→四选一选词)"
```

---

### Task 4: README 二期玩法

**Files:** Modify `README.md`

- [ ] **Step 1: 更新英语「玩法」描述**

Edit `README.md` — old:

```markdown
**玩法（一期）**：⛏️ **词义配对挖矿** —— 中文配英文，**点方块即读英文发音**，配对成功挖矿；随关卡单词更多、范围更广，并针对错题多出。
```

new:

```markdown
**玩法**：⛏️ **词义配对挖矿**（中文配英文，点方块即读英文发音）· 🎨 **看图选词**（看 emoji 四选一选单词）· 👂 **听音选词**（听发音点出单词）。都随关卡加量、针对错题多出；矿石/星星与数学、语文共享。
```

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs(english): README 补二期玩法(看图选词/听音选词)"
```

---

## Self-Review

**1. Spec coverage（对 `2026-06-29-english-game-design.md` §4.2/§4.3）：**
- §4.2 看图选词（复用 READ 四选一外壳；emoji 题面；无图退中文）→ Task 2 ✓
- §4.3 听音选词（复用 LISTEN；playEn 目标词；候选英文词）→ Task 3 ✓
- §7 状态存档（enPickStage/enListenStage + SAVE_FIELDS + applySave 兜底）→ Task 1 ✓
- 错题本对英文键安全（一期已验证 PD→null、Weak.similar→[]）→ 复用，无需改 Weak ✓
- 跨学科 home 导航（cnq 屏/overlay 学科化）→ Task 1 Step 6-8 ✓（一期未覆盖，因 EG 走 winOv 而非 cnq；本期单元玩法首次用 cnq，故必须修）

**2. Placeholder scan：** 无 TBD/TODO；每个 code step 都给完整代码。Task1 的"卡片前向引用 EPICK/ELISTEN"是显式设计（同一期 T5），非占位。

**3. Type consistency：**
- `EPICK`/`ELISTEN` 与 `READ`/`LISTEN` 结构一致：`CNQ={kind,hearts,maxHearts,score,cleared,combo,goal,n,depth,busy,pool,last,cur}`；`CNQ.cur={target,audio}`。
- `cnqWin(stageKey, restart, hintLine)` 调用：`'enPickStage'`/`'enListenStage'` 与 freshState/SAVE_FIELDS/applySave 字段名逐字一致 ✓
- `_enChoices(target,pool,n)` 在 Task1 定义、Task2/3 调用，签名一致 ✓
- `_enKey`（一期 T8 已存在）、`playEn`（一期 T3）、`EN_INDEX`（一期 T6）、`cnq*`（拼音既有）—— 均为既有依赖，本期不重定义 ✓
- 选项按钮：`data-w` 属性 + `dataset.w`，EPICK/ELISTEN 一致 ✓
- 卡片 onclick `EPICK.start()`/`ELISTEN.start()`（Task1）与引擎对象名（Task2/3）一致 ✓

修订记录：发现 `#cnq` 屏(行450)、cnqWin(553)、cnqLose(560) 的「玩法」按钮硬编码 `G.goModes('cn')`——英语单元玩法复用 cnq 会被弹回语文菜单。已在 Task 1 Step 6-8 改为 `G.goModes(S.subject)`（cn 玩法 S.subject==='cn'，行为不变）。
