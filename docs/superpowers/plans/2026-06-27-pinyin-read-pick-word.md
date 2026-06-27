# 「🔎 看拼音选词」Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给拼音学科加第 5 个玩法「🔎 看拼音选词」——读出屏幕上的拼音（字或词），从 4 个候选汉字/词里点对的那个。

**Architecture:** 复用现有 `#cnq` 屏 + `CNQ` 运行时，新增一个与 `LISTEN` 同构的 `READ` 对象；干扰项只用现有读音数据（同声母/韵母/声调），不引入任何新数据文件。所有改动集中在 `index.html`，外加一处 `README.md` 文案。

**Tech Stack:** 纯静态前端（原生 ES：箭头函数、模板串、`spread`/`flatMap`）；`server.py` 仅标准库；无前端构建、无 npm。

## Global Constraints

- **运行时零第三方依赖、可离线**：不新增数据文件、不加任何库；干扰项只用 `PD(h)` 里已有的 `py`/`code`/`sm`/`ym`。
- **复用而非另起**：HUD、矿石经济（`cnqOre/cnqGood`）、过关失败遮罩（`cnqWin/cnqLose`）、错题强化（`Weak`）、题库选择（`gamePool`）、选目标（`Weak.pick`）一律复用，禁止复制其逻辑。
- **存档对 `server.py` 透明**：只在 `S` 上加 `readStage` 一个数字字段，并纳入 `SAVE_FIELDS` 与旧档迁移。
- **这是"读"的游戏**：答题前**绝不**自动发声；只在**答对后**朗读。
- **去歧义铁律**：4 个候选里，除正确项外，没有任何一项的**带调拼音**（`PD(h).py`）与正确项相同。
- **测试机制**：本项目前端无单测框架、运行时仅依赖 Python（不可假设有 Node）。沿用既有 CNQ 家族（`LISTEN/TONE/PM`）的做法——**人工浏览器点测 + 浏览器控制台断言**作为每个任务的验收闭环。每步给出确切点击路径 / 控制台片段 / 预期输出。

---

## File Structure

| 文件 | 职责 | 改动 |
|---|---|---|
| `index.html` | 全部玩法逻辑与样式（项目惯例：游戏逻辑都在此） | 加 `readStage` 存档字段、`gamePool('read')` 取题、`_readWords()` 辅助、`.readPy` 样式、`READ` 对象、选择玩法第 5 张卡 |
| `README.md` | 用户文档 | 「4 种玩法」→「5 种」并补一条说明 |

两个任务：
- **Task 1 = 数据/存档层**（取题池 + 关卡进度存档）——可独立审查，与 UI 无关。
- **Task 2 = 玩法本体**（`READ` 对象 + 入口卡 + 样式 + README）——一个完整可玩的交付物。

---

## Task 1: 取题池与关卡存档

**Files:**
- Modify: `index.html:599`（默认 `S`）
- Modify: `index.html:655`（`SAVE_FIELDS`）
- Modify: `index.html:715`（旧档迁移）
- Modify: `index.html:1458`（`gamePool`）+ 在 `_matchPool` 附近加 `_readWords()`

**Interfaces:**
- Produces:
  - `S.readStage: number`（默认 0，已存档、旧档自动补 0）
  - `gamePool('read', stage)` → `string[]`：默认题库下为「世界 1..min(3+stage,6) 的单字」，`stage>=3` 起并入「世界 7–8 的词语」；自主命题下为用户录入且 `PD()` 查得到的全部字/词。
  - `_readWords()` → `string[]`：世界 7、8 的全部词语。

- [ ] **Step 1: 默认存档加 `readStage`**

在 `index.html:599` 把 `matchStage:0, listenStage:0, toneStage:0, spellStage:0,` 改为：

```js
    matchStage:0, listenStage:0, toneStage:0, spellStage:0, readStage:0,
```

- [ ] **Step 2: 纳入 `SAVE_FIELDS`**

在 `index.html:655` 的 `SAVE_FIELDS` 数组里，把 `'spellStage'` 后补上 `'readStage'`：

```js
const SAVE_FIELDS=['res','tool','skinsOwned','skin','stage','crushStage','stars','totalCleared','pyMatchStage','voiceSpeed','matchStage','listenStage','toneStage','spellStage','readStage','misses','qsource'];
```

- [ ] **Step 3: 旧档迁移补默认值**

在 `index.html:715` 把：

```js
  ['listenStage','toneStage','spellStage'].forEach(k=>{ if(typeof S[k]!=='number') S[k]=0; });
```

改为：

```js
  ['listenStage','toneStage','spellStage','readStage'].forEach(k=>{ if(typeof S[k]!=='number') S[k]=0; });
```

- [ ] **Step 4: 加 `_readWords()` 辅助**

在 `index.html` 的 `_matchPool` 函数（约 1484 行）之后另起一行加入：

```js
function _readWords(){ return PINYIN_WORLDS.filter(w=>w.id>=7).flatMap(w=>w.words); }  // 看拼音选词：词语池(世界7-8)
```

- [ ] **Step 5: `gamePool` 加 `read` 分支（自主命题）**

在 `gamePool`（约 1458 行）的自主命题段里，`if(kind==='match') return items.slice();` 这一行后面紧接着加：

```js
    if(kind==='read')  return items.filter(h=>PD(h));            // 看拼音选词：字+词都可考
```

- [ ] **Step 6: `gamePool` 加 `read` 分支（默认题库）**

在同函数默认题库段里，`if(kind==='match')  return _matchPool(Math.min(3+stage,8));` 这一行后面紧接着加：

```js
  if(kind==='read'){ let pool=_cnPool(_cnMaxWorld(stage));        // 单字 1..min(3+关,6)
    if(stage>=3) pool=pool.concat(_readWords()); return pool; }  // 第4关起并入词语
```

- [ ] **Step 7: 控制台验证取题池**

跑 `python3 server.py`，浏览器开 `http://localhost:8000`，选玩家 → 📖 语文拼音 →（若弹发音下载，等其就绪或跳过）→ 选题库选「默认游戏」→ 进「选择玩法」。按 F12 开控制台，运行：

```js
console.log('s0 singles?', gamePool('read',0).every(h=>h.length===1), 'len', gamePool('read',0).length);
console.log('s5 has words?', gamePool('read',5).some(h=>h.length>1), 'words', _readWords().length);
console.log('readStage', S.readStage);
```

Expected: `s0 singles? true ...`、`s5 has words? true words 48`、`readStage 0`（数字，不是 undefined）。

- [ ] **Step 8: 提交**

```bash
git add index.html
git commit -m "feat(pinyin): 看拼音选词——取题池与关卡存档(readStage/gamePool('read'))

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01YX5BksCCdazdU5b72Uw4Qo"
```

---

## Task 2: `READ` 玩法本体 + 入口卡

**Files:**
- Modify: `index.html:122`（在 `.cnqPy` 样式后加 `.readPy`）
- Modify: `index.html` `PM` 对象之后（约 1749 行）新增 `READ`
- Modify: `index.html:1403-1406`（`renderModes` 'cn' 列表，PM 卡后加第 5 张卡）
- Modify: `README.md:45,47,49,52`

**Interfaces:**
- Consumes（Task 1）：`gamePool('read', stage)`、`S.readStage`、`_readWords()`
- Consumes（现有）：`CNQ`、`cnqMaxHearts()`、`cnqHUD()`、`cnqGood()`、`cnqHit(el)`、`cnqMiss(el)`、`cnqWin(stageKey, restart, hint)`、`cnqLose(restart)`、`Weak.pick(pool, last)`、`Weak.hit(k)`、`Weak.miss(k)`、`Weak.similar(key, pool)`、`PD(hz)`→`{py,code,sm,ym}`、`PINYIN_WORLDS`、`playPy(codes)`、`shuffle(arr)`、`beep(name)`、`toast(msg)`、`show(id)`、`$(id)`、`G.goModes('cn')`
- Produces：全局 `const READ`，含 `READ.start()`、`READ.next()`、`READ._choices(target, pool, n)`→`string[]`（含正确项、去歧义、已洗牌）、`READ.pick(target)`、`READ.answer(hz, el)`、`READ.win()`、`READ.lose()`

- [ ] **Step 1: 加 `.readPy` 样式**

在 `index.html:122`（`.cnqPy{...}`）那一行之后另起一行加入：

```css
  .readPy{font-family:var(--cn);font-size:34px;font-weight:700;letter-spacing:1px;color:var(--gold);min-height:44px;}
```

- [ ] **Step 2: 新增 `READ` 对象**

在 `index.html` 的 `PM` 对象闭合 `};`（约 1749 行）之后、`// 拼音配对挖矿……` 注释之前，插入：

```js
const READ = {                                  // 🔎 看拼音选词：读拼音→4 选 1 选字/词（只用读音相近做干扰）
  start(){
    S.subject='cn'; const stage=S.readStage;
    const pool=gamePool('read', stage);
    if(pool.length<2){ toast('这个题库里能「看拼音选词」的字词不足，换个玩法或题库'); return G.goModes('cn'); }
    CNQ={kind:'read', stage, hearts:cnqMaxHearts(), maxHearts:cnqMaxHearts(), score:0, cleared:0, combo:0,
      goal:6+stage, n:Math.min(4,pool.length), depth:Math.min(1+Math.floor(stage/2),4),
      busy:false, pool, last:null, cur:null};
    $('qTitle').textContent=`🔎 看拼音选词 · 第${stage+1}关`;
    show('cnq'); this.next();
  },
  next(){
    CNQ.busy=false;
    const pool=CNQ.pool, st=CNQ.stage;
    const words=pool.filter(h=>h.length>1), singles=pool.filter(h=>h.length===1);
    let sub=pool;                                          // 字→词递进：词语比例随关卡升高(25%→60%)
    if(st>=3 && words.length){ const p=Math.min(0.25+0.1*(st-3), 0.6);
      sub = (Math.random()<p) ? words : (singles.length?singles:pool); }
    const target=Weak.pick(sub, CNQ.last); CNQ.last=target;
    const d=PD(target);
    const choices=this._choices(target, pool, CNQ.n);
    CNQ.cur={target, code:(d.code||[])};
    cnqHUD();
    $('qPrompt').innerHTML=`<div class="readPy">${d.py}</div>`;
    $('qHint').textContent='读出拼音，选对应的字 / 词';
    $('qBody').className='cnqBody listenGrid';
    $('qBody').innerHTML=choices.map(hz=>`<button class="cnqChar" data-hz="${hz}"><span class="val">${hz}</span></button>`).join('');
    $('qBody').querySelectorAll('.cnqChar').forEach(b=>b.onclick=()=>READ.answer(b.dataset.hz,b));
    // 不自动发声：这是「读拼音」的游戏
  },
  _choices(target, pool, n){                              // 造 n 个候选(含正确项)；干扰项带调拼音不得等于正确项
    const pyT=(PD(target)||{}).py, isWord=target.length>1;
    const valid=h=>{ const u=PD(h); return u && h!==target && u.py!==pyT; };   // 去歧义
    const cand=pool.filter(h=> isWord ? h.length>1 : h.length===1 ).filter(valid);
    let pref;
    if(isWord){                                           // 词语：同世界 / 共享一个字 优先
      const w=PINYIN_WORLDS.find(W=>W.words.includes(target));
      const sameWorld=cand.filter(h=> w && w.words.includes(h));
      const shareChar=cand.filter(h=> Array.from(target).some(c=>h.includes(c)));
      pref=Array.from(new Set(sameWorld.concat(shareChar)));
    } else {                                              // 单字：同声母/同韵母(读音易混)
      pref=Weak.similar(target, cand);
    }
    let bag=shuffle(pref.slice()).slice(0, n-1);
    if(bag.length<n-1){                                   // 不够则池内随机补齐
      const more=shuffle(cand.filter(h=>!bag.includes(h)));
      bag=bag.concat(more.slice(0, n-1-bag.length));
    }
    return shuffle(bag.concat(target));
  },
  pick(target){ return this._choices(target, CNQ.pool, CNQ.n); },
  answer(hz,el){
    if(CNQ.busy) return;
    if(hz===CNQ.cur.target){
      CNQ.busy=true; beep('good'); cnqHit(el); playPy(CNQ.cur.code); Weak.hit(CNQ.cur.target); cnqGood(); cnqHUD();
      if(CNQ.cleared>=CNQ.goal){ setTimeout(()=>this.win(),850); return; }
      setTimeout(()=>this.next(),850);
    } else {
      Weak.miss(CNQ.cur.target); cnqMiss(el);
      if(CNQ.hearts<=0){ CNQ.busy=true; setTimeout(()=>this.lose(),320); }
    }
  },
  win(){ cnqWin('readStage', ()=>READ.start(), '下一关开始出现词语，读准每个音节！'); },
  lose(){ cnqLose(()=>READ.start()); },
};
```

- [ ] **Step 3: 选择玩法加第 5 张卡**

在 `index.html` `renderModes` 的 `subj==='cn'` 分支里，拼音拼读（🧩）那张卡的结尾 `</div>`（约 1406 行，紧接 `` `;`` 之前）后面、模板字符串闭合反引号之前，插入第 5 张红色卡：

```js
      <div class="world" style="background:linear-gradient(135deg,var(--red),rgba(0,0,0,.25))" onclick="READ.start()">
        <div class="wicon" style="background:var(--red)"></div>
        <div><h3>🔎 看拼音选词</h3><p>读出拼音，选对的字 / 词</p></div>
      </div>
```

即结构变为 `...🧩 拼音拼读卡 </div>` + 上面这段 + `` `; ``。

- [ ] **Step 4: 控制台验证「去歧义铁律」（关键算法）**

刷新页面，进默认题库的「选择玩法」屏（保证 `PINYIN_DATA` 已加载、`READ` 已定义），F12 控制台运行：

```js
(() => {
  const pool = _cnPool(6).concat(_readWords());          // 单字(世界1-6) + 词语(7-8)
  let n = 0, bad = 0;
  for (let i = 0; i < 4000; i++) {
    const t = pool[Math.floor(Math.random() * pool.length)];
    const ch = READ._choices(t, pool, 4); n++;
    const pyT = PD(t).py;
    if (!ch.includes(t)) bad++;                           // 必含正确项
    else if (ch.some(h => h !== t && PD(h).py === pyT)) bad++;  // 干扰项不得撞正确项拼音
    else if (new Set(ch).size !== ch.length) bad++;       // 不重复
  }
  console.log('checked', n, 'bad', bad);
})();
```

Expected: `checked 4000 bad 0`。若 `bad` 非 0，说明 `_choices` 的去歧义/去重逻辑有问题，修正后重跑至 `bad 0`。

- [ ] **Step 5: 人工点测玩法体验**

仍在「选择玩法」屏：确认出现**第 5 张红色卡「🔎 看拼音选词」**，点进去：

1. 第 1 关：`qPrompt` 显示一段拼音（如 `yú`），下方 4 个汉字候选，**进题时不发声**。
2. 候选是读音易混的字（如 `yú` → 鱼/雨/玉/语 一类），且没有第二个候选的拼音等于题面。
3. 点**正确**项：变绿、朗读该字、`完成 x/goal` +1；连对有矿石/星星进账（看右上 HUD）。
4. 故意点**错**：红色抖动、心 -1；心扣光进失败遮罩，「重试」可重开本关。
5. 答够 `goal` 题：出过关遮罩（给 ⭐ 和宝箱），点「下一关」标题变「第 2 关」。

Expected：以上全部符合；尤其"进题不发声、答对才朗读"。

- [ ] **Step 6: 控制台验证词语关与存档**

控制台运行（验证字→词递进的词语分支与候选）：

```js
const wt = _readWords()[0];                               // 取一个词，如「爸爸」
console.log('word choices', READ._choices(wt, _cnPool(6).concat(_readWords()), 4));
S.readStage = 2; saveGame();                              // 模拟进度
```

Expected：`word choices` 是 4 个**词语**（长度>1）、含 `wt`、无重复。然后**刷新页面**，控制台 `S.readStage` 应为 `2`（存档已续上）。验证完把进度调回：`S.readStage=0; saveGame();`。

- [ ] **Step 7: 更新 README**

`README.md` 改 4 处：

L45 `…再玩 4 种玩法。` → `…再玩 5 种玩法。`

L47 整行替换为：

```markdown
**5 种玩法**：🔤 拼音配对挖矿（汉字配拼音）· 👂 听音找字 · 🎵 声调小游戏 · 🧩 拼音拼读 · 🔎 看拼音选词（读拼音选字/词）。每种都随关卡由易到难，并**针对错题多出相似题**（同声母/韵母）。
```

L49 `**选题（题库）** 决定 4 种玩法的出题范围：` → `**选题（题库）** 决定 5 种玩法的出题范围：`

L52 `…自己录入想练的字 / 词，4 种玩法只练这些…` → `…自己录入想练的字 / 词，5 种玩法只练这些…`

- [ ] **Step 8: 提交**

```bash
git add index.html README.md
git commit -m "feat(pinyin): 第5玩法🔎看拼音选词——读拼音四选一选字/词

读音相近做干扰(同声母/韵母/声调)，字→词递进；复用 CNQ 壳与错题强化，
答题前不发声、答对才朗读；去歧义铁律保证候选拼音唯一对应。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01YX5BksCCdazdU5b72Uw4Qo"
```

---

## Self-Review

**Spec coverage（逐节核对 spec → 任务）：**
- §2 入口卡 / 运行屏 → T2 S1（`.readPy`）、S2（`qPrompt`/`qBody`）、S3（红卡）✅
- §3 字→词递进、候选数 4、小池兜底 → T1 S5-6（池）、T2 S2（`n=min(4,pool)`、词语比例 ramp、`pool.length<2` 兜底）✅
- §4 去歧义铁律 + 单字同音近音 + 词语同世界/结构/共享字 → T2 S2 `_choices`，T2 S4 控制台 fuzz 验证 ✅
- §5 答题前不发声、答对朗读 → T2 S2（`next` 无 `playPy`、`answer` 对了才 `playPy`）、T2 S5 点测 ✅
- §6 `READ` 骨架 → T2 S2 ✅
- §7 集成点 7 处 → T1 S1/S2/S3/S5/S6 + T2 S2/S3 + README S7 ✅
- §8 验收 → T1 S7、T2 S4/S5/S6 ✅

**Placeholder scan：** 无 TBD/TODO；每段代码均完整可粘贴。✅

**Type consistency：** `READ._choices(target, pool, n)` 在 S2 定义、S4/S6 调用签名一致；`gamePool('read', stage)`、`_readWords()`、`S.readStage`、`cnqWin('readStage', …)` 命名前后一致；`PD(h).py` 判等贯穿去歧义逻辑。✅
