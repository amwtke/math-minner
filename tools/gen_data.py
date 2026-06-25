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
