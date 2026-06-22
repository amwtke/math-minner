# Math Miner 本地多人服务器版 — 设计文档

日期:2026-06-22
状态:已批准,准备实现

## 1. 背景与目标

现状:`math-miner.html` 是一个 885 行、完全自包含的单文件像素风数学游戏(给 7-8 岁孩子练加减/凑十)。存档写在浏览器 `localStorage['mathminer_save_v1']`(每 1.5 秒自动存),唯一外部依赖是 Google Fonts(`Press Start 2P` + `Noto Sans SC`)。

目标:改成**本地可部署的 Python 服务器版**,支持**多玩家选名字登录**,每个玩家在服务器上有独立存档,局域网内多设备(手机/平板/其他电脑)可同时连入游玩。

非目标(YAGNI):密码/账号安全体系、云端部署、排行榜、跨账号社交、HTTPS。

## 2. 关键决策(已确认)

- **登录方式**:选名字即登录,无密码。名字不存在则新建空存档。
- **访问范围**:局域网多设备。服务器绑 `0.0.0.0`,需支持并发。
- **后端**:Python **标准库**(`http.server.ThreadingHTTPServer`),**零第三方依赖**。`python3 server.py` 一条命令启动。
- **存储**:每玩家一个 JSON 文件 `data/<name>.json`,写锁 + 原子写(临时文件 + `os.replace`)防并发损坏。
- **字体**:像素字体 `Press Start 2P` 本地化为 `fonts/PressStart2P.woff2`(`@font-face` 引用,离线可用);中文去掉 Google 外链,回退系统中文字体(苹方/雅黑)。

## 3. 文件结构

```
math-miner/
├── server.py                # 标准库 HTTP 服务器(静态文件 + 存档 API)
├── index.html               # 游戏本体(由 math-miner.html 改造:加登录屏 + 服务器存档 + 本地字体)
├── fonts/
│   └── PressStart2P.woff2    # 像素字体(离线)
├── data/                     # 每玩家一个 JSON 存档(运行时生成,git 忽略)
│   └── .gitkeep
├── start.sh                  # Mac/Linux 一键启动
├── start.bat                 # Windows 一键启动
├── README.md                 # 更新运行说明
└── math-miner.html           # 保留原单文件版(可选)
```

## 4. 后端 API(server.py)

服务器职责:① 提供静态文件(`index.html`、`fonts/*`);② 提供存档 REST API。基于 `http.server.ThreadingHTTPServer` + 自定义 `BaseHTTPRequestHandler`。

| 方法 + 路径 | 作用 | 返回 |
|---|---|---|
| `GET /` | 返回 `index.html` | HTML |
| `GET /fonts/<f>` | 返回字体文件 | woff2 |
| `GET /api/players` | 列出已有玩家(扫描 `data/*.json`) | `{"players":["小明","乐乐"]}` |
| `POST /api/login` body `{"name":"小明"}` | 登录;不存在则建空档 | `{"ok":true,"name":"小明","save":{...}}` |
| `GET /api/save?name=小明` | 读存档 | 存档 JSON(无则 `{}`) |
| `POST /api/save?name=小明` body=存档 JSON | 原子写存档 | `{"ok":true}` |

### 名字安全校验
- 允许:中文、英文字母、数字,长度 1–12。
- 拒绝并返回 400:含 `/`、`\`、`.`、空白控制字符,或超长/为空。
- 文件名直接用校验后的名字 + `.json`,杜绝路径穿越(`..`)。

### 并发与原子性
- `ThreadingHTTPServer` 每请求一线程。
- 全局 `dict[name] -> threading.Lock`,写某玩家存档时持其锁。
- 原子写:写 `data/<name>.json.tmp` → `os.replace()` 到正式文件。

### 存档数据形状(与现状一致,不变)
```json
{ "res": ..., "tool": ..., "skinsOwned": ..., "skin": ...,
  "stage": ..., "crushStage": ..., "stars": ..., "totalCleared": ... }
```

## 5. 登录流程(客户端新增一屏)

游戏启动 → 显示「选择玩家」屏(新 `#login` screen,排在 `#title` 前):
- `GET /api/players`,把玩家渲染成像素头像 + 名字,点击即 `POST /api/login` 进入。
- 「➕ 新玩家」输入框:输名字 → `POST /api/login` 新建并进入。
- 登录成功:当前玩家名存内存变量 + `sessionStorage`(刷新免重选),用 login 返回的 `save` 直接载入,跳到原 `#title`。
- 标题栏显示当前玩家,提供「切换玩家」按钮:清 `sessionStorage` 当前玩家 → 回登录屏。

## 6. 客户端存档改动(最小侵入)

保留 `saveGame()`/`loadGame()`/`resetSave()` 的调用点不变,只换内部实现:

- `loadGame()`:从登录返回的 `save` 载入(已有数据,无需再请求);字段映射逻辑沿用现有 `forEach` 写回 `S`。
- `saveGame()`:`POST /api/save?name=<当前玩家>`,body 为现有那 8 个字段的 JSON。1.5 秒自动存档逻辑保留;加**防抖**(同一时刻只发一个在途请求)+ **失败静默重试**,服务器临时不可达不影响游玩。
- `resetSave()`:`POST` 一个空存档到当前玩家,清空服务器进度。
- 服务器为唯一存档来源;旧 `localStorage` 存档忽略。

## 7. 字体离线化

- 下载 `Press Start 2P` 的 woff2 到 `fonts/PressStart2P.woff2`;`index.html` 顶部 `@font-face { font-family:'Press Start 2P'; src:url('/fonts/PressStart2P.woff2'); }`。
- 删除 `<link href="https://fonts.googleapis.com/...">`;CSS 变量 `--cn` 回退 `system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif`。

## 8. 启动脚本

- `start.sh`:`#!/usr/bin/env bash` → `python3 "$(dirname "$0")/server.py" "$@"`,可加端口参数。
- `start.bat`:`python server.py %*`。
- `server.py` 启动时打印本机所有可访问 URL(`http://<局域网IP>:<port>`),方便其他设备输入。

## 9. 错误处理

- API 出错统一返回 JSON `{"ok":false,"error":"..."}` + 合适状态码(400 校验失败 / 404 未知路径 / 500 内部错误)。
- 服务器端写存档异常:返回 500,客户端静默重试(下一个 1.5s 周期)。
- 客户端网络失败:`saveGame` catch 后不打断游戏;`loadGame`/登录失败给出可重试的提示。
- 名字校验失败:登录屏内联提示「名字只能用中英文和数字,1–12 位」。

## 10. 测试策略

- **服务器单元/集成测试**(`test_server.py`,标准库 `unittest` + `http.client`,启动临时服务器在临时 `data/` 目录):
  - 名字校验:合法通过、非法(`../`、空、超长、含 `/`)被拒。
  - `login` 新玩家建空档;再次 `login` 返回已存数据。
  - `save` 后 `save?name=` 读回一致;`players` 列表包含该玩家。
  - 并发写同一玩家不损坏文件(多线程打存档,最终 JSON 可解析)。
  - 路径穿越尝试(`name=../../etc/passwd`)被拒,不在 data 目录外写文件。
- **客户端冒烟**(Chrome DevTools MCP):起服务器 → 打开页面 → 新建玩家 → 玩一关 → 刷新页面验证进度从服务器恢复 → 切换玩家互不串档。

## 11. 验收标准

1. `python3 server.py` 零依赖启动,打印局域网可访问 URL。
2. 同一 WiFi 下另一设备用 IP 能打开并游玩。
3. 两个不同名字玩家存档互相独立、互不覆盖。
4. 刷新/重连后进度从服务器恢复。
5. 断网(无 Google)时像素字体与中文均正常显示。
6. 服务器测试全绿。
