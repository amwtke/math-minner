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


# ---------- 按课本拼音进度给单字自动分世界 ----------
# 部编版一上拼音顺序：单韵母 → 声母(bpmf dtnl / gkh jqx) → 平翘舌 z c s zh ch sh r
# → 复韵母 → 鼻韵母。一个字「最晚才学到的那个成分」决定它属于哪一关，越往后越难。
# 下面三个函数是纯函数（不依赖 pypinyin），单测直接喂声母/韵母串即可。
_INI_S2 = set("b p m f d t n l".split())          # 声母·前段
_INI_S3 = set("g k h j q x".split())              # 声母·中段
_INI_S4 = set("z c s zh ch sh r".split())         # 平翘舌
_FINAL_SINGLE = {"a", "o", "e", "i", "u", "v", "er", "ê"}
# 16 个整体认读音节（只整块认读、不拆声母+韵母拼读）
WHOLE_SYLLABLES = set("zhi chi shi ri zi ci si yi wu yu ye yue yin yun yuan ying".split())


def initial_stage(initial):
    """声母引入阶段：零声母/整体认读=1，bpmf dtnl=2，gkh jqx=3，平翘舌=4。"""
    if initial in _INI_S4:
        return 4
    if initial in _INI_S3:
        return 3
    if initial in _INI_S2:
        return 2
    return 1


def final_stage(final):
    """韵母引入阶段：单韵母=1，复韵母=5，鼻韵母(带 n/ng)=6。

    入参是 pypinyin strict 韵母串（ü 记作 v）。带鼻音(含 n)的归鼻韵母；
    其余非单韵母（ai/ei/uei/ao/ou/iou/ie/ve/ua/uo…含介母）归复韵母。
    """
    f = final.replace("ü", "v")
    if "n" in f:                       # an en in vn uen / ang eng ing ong / ian iang uang…
        return 6
    if f in _FINAL_SINGLE:
        return 1
    return 5                           # 复韵母（含 i/u/ü 介母的二合/三合韵母）


def world_for(initial, final):
    """单字所属世界 id（1..6）= max(声母阶段, 韵母阶段)。"""
    return max(initial_stage(initial), final_stage(final))


# 6 个「单字」世界的展示信息（id 与 world_for 返回值对应）。
PHON_WORLDS = [
    (1, "🌱 单韵母草原", "var(--grass)"),
    (2, "🪨 声母石洞·前 bpmf·dtnl", "var(--stone)"),
    (3, "⛰️ 声母石洞·后 gkh·jqx", "var(--dirt)"),
    (4, "🌀 平翘舌矿井 zcs·zhchsh", "var(--cyan)"),
    (5, "🏞️ 复韵母山谷", "var(--gold)"),
    (6, "🕳️ 鼻韵母深洞", "var(--pur)"),
]

# 单字库：顺手按难度堆放，最终由 world_for 自动归位（重复字只收一次）。
CHARS = (
    # 单韵母 / 整体认读（多落到世界 1）
    "一 衣 五 午 雨 鱼 语 玉 二 耳 儿 饿 鹅 "
    # bpmf dtnl + 单韵母（世界 2）
    "爸 八 笔 不 怕 爬 婆 妈 马 米 目 母 麻 发 大 弟 地 第 的 土 兔 他 她 那 拿 你 泥 路 鹿 绿 拉 力 "
    # gkh jqx + 单韵母（世界 3）
    "哥 个 歌 河 喝 和 盒 鸽 鸡 七 骑 去 西 习 洗 喜 苦 哭 库 课 棵 客 "
    # 平翘舌 z c s zh ch sh r（世界 4）
    "字 自 词 四 死 思 丝 知 纸 之 吃 池 是 十 师 史 日 入 如 "
    # 复韵母（世界 5）
    "我 也 月 来 太 白 在 海 开 爱 菜 才 美 飞 黑 给 水 回 高 好 猫 桃 跑 草 老 鸟 小 苗 笑 叫 "
    "走 手 口 头 都 牛 六 九 球 花 瓜 多 火 "
    # 鼻韵母（世界 6）
    "三 山 看 天 蓝 班 安 干 门 人 分 很 心 今 林 金 星 明 名 听 红 工 东 中 虫 空 "
    "羊 方 房 光 黄 长 唱 朋 风 龙 冬 云 春 文 问"
).split()

# 「词语」世界（双字，最难，放在所有单字世界之后）。
WORD_WORLDS = [
    {"id": 7, "name": "🧩 词语小山", "icon": "var(--red)", "words": [
        "爸爸", "妈妈", "哥哥", "弟弟", "姐姐", "妹妹",
        "老师", "同学", "朋友", "你好", "谢谢", "再见",
        "上学", "回家", "白天", "黑夜", "太阳", "月亮",
        "星星", "白云", "大山", "小河", "花草", "树木"]},
    {"id": 8, "name": "💎 词语深渊", "icon": "var(--grass-d)", "words": [
        "老虎", "熊猫", "小鸟", "蜜蜂", "蝴蝶", "青蛙",
        "大象", "兔子", "苹果", "西瓜", "葡萄", "香蕉",
        "火车", "飞机", "轮船", "气球", "学校", "黑板",
        "铅笔", "书包", "雨伞", "唱歌", "跳舞", "画画"]},
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
        # 每个字一个 davinfifield 音频码（顺序播放多字词）。
        # davinfifield 几乎没有轻声(末尾 5)音频；遇到轻声就改用该「单字本调」码——
        # 教师领读认字时正是用本调，且本调音频必有。显示拼音仍保留自然轻声。
        t3 = pinyin(hz, style=Style.TONE3, neutral_tone_with_five=True)
        out = []
        for ch, s in zip(hz, t3):
            code = normalize_code(s[0])
            if code.endswith("5"):
                solo = normalize_code(pinyin(ch, style=Style.TONE3, neutral_tone_with_five=True)[0][0])
                # 本调可用就用本调；本调仍轻声(如「子」)则退到无调裸码(davinfifield 的轻声文件名)
                code = solo if not solo.endswith("5") else solo[:-1]
            out.append(code)
        return out

    def part(hz, style):
        return pinyin(hz, style=style, strict=True)[0][0]

    data = {}
    poly = []          # 多音字人工复核清单
    seen_multi = set()

    def add(hz):
        if hz in data:
            return False
        ms = pinyin(hz, heteronym=True)
        if any(len(s) > 1 for s in ms) and hz not in seen_multi:
            poly.append(f"{hz}\t{ms}")
            seen_multi.add(hz)
        entry = {"py": disp(hz), "code": codes(hz)}
        if len(hz) == 1:                       # 单字补声母/韵母/整体认读标记，供「拼音拼读」用
            entry["sm"] = part(hz, Style.INITIALS)
            # 韵母用「书写形」(strict=False)：水→ui 牛→iu 春→un；且自带去点规则
            # （jqx+ü→u 如 去=qu；n/l+ü 保留两点 如 绿=lü、女=nü），正是课本拼读所教
            entry["ym"] = pinyin(hz, style=Style.FINALS, strict=False)[0][0].replace("v", "ü")
            if pinyin(hz, style=Style.NORMAL)[0][0] in WHOLE_SYLLABLES:
                entry["whole"] = True          # 整体认读只整块认读、不进拼读
        data[hz] = entry
        return True

    # 单字 -> 自动归世界
    buckets = {wid: [] for wid, _, _ in PHON_WORLDS}
    for hz in CHARS:
        if not add(hz):
            continue
        wid = world_for(part(hz, Style.INITIALS), part(hz, Style.FINALS))
        buckets[wid].append(hz)

    worlds = [{"id": wid, "name": name, "icon": icon, "words": buckets[wid]}
              for wid, name, icon in PHON_WORLDS]

    # 词语世界（显式分组）
    for w in WORD_WORLDS:
        for hz in w["words"]:
            add(hz)
        worlds.append({"id": w["id"], "name": w["name"], "icon": w["icon"], "words": w["words"]})

    js = (
        "/* 自动生成，勿手改。源：tools/gen_data.py（pypinyin）。 */\n"
        "window.PINYIN_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"
        "window.PINYIN_WORLDS = " + json.dumps(worlds, ensure_ascii=False) + ";\n"
    )
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(js)
    with open(os.path.join(HERE, "polyphone_review.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(poly))
    counts = " ".join(f"#{w['id']}={len(w['words'])}" for w in worlds)
    print(f"已写 {OUT}：{len(data)} 字/词，{len(worlds)} 世界（{counts}）；多音字待复核 {len(poly)} 条。")


if __name__ == "__main__":
    build()
