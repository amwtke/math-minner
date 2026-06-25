# 方块数学矿工 (Math Miner)

像素风数学游戏,给 7-8 岁孩子练加减法和凑十法。
两种玩法:⛏️ 配对挖矿 · 💥 数字消消乐。
含工具融合、皮肤装扮、技能系统、动态难度。

**本地多人服务器版**:用 Python 启动一个服务器,家里多台设备(手机/平板/电脑)在同一 WiFi 下都能连进来玩;每个玩家选自己的名字登录,进度各自存在服务器上,互不覆盖。

## 运行

只需要装了 **Python 3**(无需任何第三方库):

    python3 server.py            # 默认端口 8000

或用一键脚本:

    ./start.sh                   # Mac / Linux
    start.bat                    # Windows(双击即可)

启动后终端会打印可访问地址,例如:

    本机:    http://localhost:8000
    局域网:  http://192.168.1.23:8000    ← 手机/平板用这个

- 在本机玩:浏览器打开 `http://localhost:8000`
- 其他设备玩:确保和电脑连同一个 WiFi,浏览器输入终端打印的「局域网」地址
- 自定端口:`python3 server.py 9000`(或 `./start.sh 9000`)

## 多人与存档

- 进游戏先到「选择玩家」屏:点头像直接进,或输入名字创建新玩家。
- 进度每 1.5 秒自动存到服务器 `data/<名字>.json`,换设备登录同名字即可续玩。
- 标题页右上角「↩ 切换玩家」可换人。
- 名字规则:中英文/数字,1–12 位。
- 存档文件在 `data/` 目录,家长可直接查看;`data/` 不纳入 git。
- 同一名字若在两台设备同时游玩,后保存的会覆盖先保存的(无冲突合并),建议每人用不同名字。

## 注意

- 服务器对**同一 WiFi 下所有设备开放、无需密码**,谁都能新建/修改存档。家用没问题,**公共/办公 WiFi 慎用**。
- 首次启动若系统弹出防火墙「是否允许传入连接」,请选**允许**,否则其他设备连不上。

## 语文 · 拼音

进标题后选「📖 语文拼音」即可玩「拼音配对挖矿」（汉字配拼音）。矿石/镐子/皮肤/星星与数学**共享**。

**关卡**：按部编版一上拼音进度分 8 个世界，越往后越难——单韵母 → 声母(bpmf/dtnl、gkh/jqx) → 平翘舌 → 复韵母 → 鼻韵母 → 两个「词语」世界（双字词）。单字由 `tools/gen_data.py` 按「最晚学到的声母/韵母」自动归位，加字只需往字库里塞、跑一次脚本。

**语速**：语文棋盘上方有「🔊 语速 慢/正常/快」开关（默认**快**，逐玩家存档）。它同时调节发音倍速与多字词音节间的停顿，词语连读不再拖沓。

**发音**：首次进入语文时，**服务器**会自动从公共领域音频库下载真人发音到 `audio/`（约 10–30MB，仅服务器联网一次；之后手机/平板始终离线播放）。服务器若没联网，会提示「继续（暂无发音）」，游戏仍可玩。`audio/` 不纳入 git。

**重新生成字词数据**（仅在改了 `tools/gen_data.py` 词库后）：

    .venv-tools/bin/python3 tools/gen_data.py   # 重新生成 pinyin-data.js

`pypinyin` 装在仓库根的 `.venv-tools/` 虚拟环境里（仅开发机用、不入 git）。若该环境不存在需一次性重建：

    python3 -m venv .venv-tools
    .venv-tools/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pypinyin

## 测试

    python3 test_server.py                           # 服务器单元/集成测试(标准库 unittest)
    cd tools && python3 -m unittest test_gen_data -v # 拼音数据生成测试

## 离线说明

**服务器版(`index.html`,经 `python3 server.py` 访问)完全离线可用**:像素字体已本地化(`fonts/PressStart2P.woff2`),中文用系统自带字体,断网也正常显示与游玩。

> 注:保留的原始单文件 `math-miner.html` 仍引用 Google Fonts,断网双击打开时像素字体会退化。要离线请用服务器版。

## 文件结构

    server.py          本地服务器(静态文件 + 存档 API + 音频下载,纯标准库)
    index.html         游戏本体(登录屏 + 服务器存档 + 本地字体)
    fonts/             像素字体
    data/              玩家存档(运行时生成)
    audio/             拼音真人发音 MP3(运行时按需下载,不纳入 git)
    pinyin-data.js     拼音字词数据(构建期生成,纳入 git)
    tools/gen_data.py  生成 pinyin-data.js 的脚本(需 pypinyin,仅开发机)
    test_server.py     服务器测试
    tools/test_gen_data.py  拼音数据生成测试
    start.sh / .bat    一键启动脚本
    math-miner.html    原始单文件版(保留,联网时可直接双击打开)
