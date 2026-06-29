#!/usr/bin/env python3
"""构建期：英语主题词库 -> en-data.js（运行时纯静态、零依赖）。
仅在开发机运行；产物 en-data.js 入 git。"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "en-data.js")
AUDIO_DIR = os.path.join(HERE, "..", "audio", "en")


def audio_key(text):
    """词/句 -> 发音文件名（不含扩展名）。前后端必须一致：
    小写 -> 非 [a-z0-9] 串折叠为单个 '_' -> 去首尾 '_'。"""
    s = re.sub(r"[^a-z0-9]+", "_", text.strip().lower())
    return s.strip("_")


# 主题词库（外研社《Join In》六年级 G6 标准）：(world_id, en, zh, emoji)。加词只需往这里塞、重跑脚本。
# emoji 尽量保持唯一：看图选词只凭 emoji 出题，两词同 emoji 会让它们互为「正确项」（不公平）。
WORDS = [
    # 1 学校科目
    (1, "maths", "数学", "➕"), (1, "music", "音乐", "🎵"),
    (1, "art", "美术", "🎨"), (1, "science", "科学", "🔬"),
    (1, "history", "历史", "📜"), (1, "drama", "戏剧", "🎭"),
    (1, "geography", "地理", "🌍"), (1, "English", "英语", "🔤"),
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
    (5, "Easter", "复活节", "🐰"), (5, "Thanksgiving", "感恩节", "🍗"),
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
    (7, "world", "世界", "🌐"), (7, "ocean", "海洋", "🌊"),
]

WORLD_META = [
    (1, "🎒 学校科目", "var(--gold)"),
    (2, "🐾 动物世界", "var(--grass)"),
    (3, "🏙️ 城市地点", "var(--cyan)"),
    (4, "🍎 食物健康", "var(--red)"),
    (5, "🎉 节日庆典", "var(--gold)"),
    (6, "🦸 职业人物", "var(--grass)"),
    (7, "🎯 爱好梦想", "var(--cyan)"),
]


# 连词成句默认句库（G6 语法）：(world_id, en, zh)。3–7 词，用上表词 + 小函数词。
# 注意：句子里不要用缩写（I'm / don't / it's）。tokenize 把撇号当词内字符，audio_key 把撇号折叠成 _，
# 二者分段数会不一致（test_word_count_matches_audio_key_parts 会报错）。要缩写就拆开写（I am / do not）。
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


def tts_mp3(text):
    """英文文本 -> mp3 字节。Google translate_tts 简单 GET（构建期联网一次）。
    可选升级：改用 edge-tts 神经语音（需 pip install edge-tts）。"""
    url = "https://translate.google.com/translate_tts?" + urllib.parse.urlencode(
        {"ie": "UTF-8", "q": text, "tl": "en", "client": "tw-ob"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


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


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "audio":
        gen_audio()
    else:
        build()
