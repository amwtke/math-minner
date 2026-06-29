#!/usr/bin/env python3
"""构建期：英语主题词库 -> en-data.js（运行时纯静态、零依赖）。
仅在开发机运行；产物 en-data.js 入 git。"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "en-data.js")


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
    build()
