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
# emoji 为空串 "" 表示该词无图标。
# WORDS 共 150 词。源：tools/sdd/joinin-g6-comprehensive.md §A
WORDS = [
    # 世界1 🎒 学校科目 · School Subjects & Ordinals (21 words)
    (1, "Chinese",   "语文",           "🇨🇳"),
    (1, "maths",     "数学",           "➕"),
    (1, "English",   "英语",           "🇬🇧"),
    (1, "science",   "科学",           "🔬"),
    (1, "music",     "音乐",           "🎵"),
    (1, "art",       "美术",           "🎨"),
    (1, "history",   "历史",           "📜"),
    (1, "PE",        "体育",           "⚽"),
    (1, "drama",     "戏剧",           "🎭"),
    (1, "French",    "法语",           "🇫🇷"),
    (1, "geography", "地理",           "🌐"),
    (1, "first",     "第一",           "🥇"),
    (1, "second",    "第二",           "🥈"),
    (1, "third",     "第三",           "🥉"),
    (1, "fourth",    "第四",           ""),
    (1, "fifth",     "第五",           ""),
    (1, "sixth",     "第六",           ""),
    (1, "pupil",     "小学生",         "🧒"),
    (1, "fun",       "有趣的；乐趣",   "😄"),
    (1, "practise",  "练习",           ""),
    (1, "classical", "古典的",         ""),
    # 世界2 🐾 动物世界 · Animals in Danger (15 words)
    (2, "whale",      "鲸鱼",   "🐋"),
    (2, "bear",       "熊",     "🐻"),
    (2, "fox",        "狐狸",   "🦊"),
    (2, "wolf",       "狼",     "🐺"),
    (2, "panda",      "大熊猫", "🐼"),
    (2, "elephant",   "大象",   "🐘"),
    (2, "koala",      "考拉",   "🐨"),
    (2, "lion",       "狮子",   "🦁"),
    (2, "owl",        "猫头鹰", "🦉"),
    (2, "tiger",      "老虎",   "🐯"),
    (2, "animal",     "动物",   "🐾"),
    (2, "endangered", "濒危的", ""),
    (2, "wild",       "野生的", ""),
    (2, "danger",     "危险",   ""),
    (2, "survey",     "调查",   ""),
    # 世界3 🏙️ 城市地点 · Big Cities & Places (27 words)
    (3, "building",  "建筑物",    "🏢"),
    (3, "capital",   "首都",      "🏛️"),
    (3, "palace",    "宫殿",      "🏯"),
    (3, "castle",    "城堡",      "🏰"),
    (3, "tower",     "塔",        "🗼"),
    (3, "hospital",  "医院",      "🏥"),
    (3, "library",   "图书馆",    "📚"),
    (3, "cinema",    "电影院",    "🎬"),
    (3, "park",      "公园",      "🌳"),
    (3, "town",      "城镇",      "🏘️"),
    (3, "river",     "河流",      "🏞️"),
    (3, "lake",      "湖",        ""),
    (3, "map",       "地图",      "🗺️"),
    (3, "east",      "东方",      ""),
    (3, "west",      "西方",      ""),
    (3, "north",     "北方",      ""),
    (3, "south",     "南方",      ""),
    (3, "middle",    "中部；中间", ""),
    (3, "right",     "右方",      ""),
    (3, "direction", "方向",      "🧭"),
    (3, "famous",    "著名的",    "⭐"),
    (3, "country",   "国家",      ""),
    (3, "culture",   "文化",      ""),
    (3, "around",    "在周围",    ""),
    (3, "behind",    "在后面",    ""),
    (3, "thousand",  "千",        ""),
    (3, "hundred",   "百",        ""),
    # 世界4 🍎 食物健康（含身体部位） · Food, Health & Body (23 words)
    (4, "fruit",      "水果",       "🍎"),
    (4, "vegetable",  "蔬菜",       "🥦"),
    (4, "strawberry", "草莓",       "🍓"),
    (4, "rice",       "米饭",       "🍚"),
    (4, "turkey",     "火鸡",       "🦃"),
    (4, "orange",     "橙子",       "🍊"),
    (4, "healthy",    "健康的",     ""),
    (4, "unhealthy",  "不健康的",   ""),
    (4, "heart",      "心脏",       "❤️"),
    (4, "bone",       "骨头",       ""),
    (4, "tooth",      "牙齿",       "🦷"),
    (4, "eye",        "眼睛",       "👁️"),
    (4, "arm",        "手臂",       ""),
    (4, "leg",        "腿",         "🦵"),
    (4, "head",       "头",         ""),
    (4, "strong",     "强壮的",     "💪"),
    (4, "hungry",     "饥饿的",     "😋"),
    (4, "ill",        "生病的",     "🤒"),
    (4, "hurt",       "受伤；疼",   ""),
    (4, "memory",     "记忆力",     ""),
    (4, "bandage",    "绷带",       ""),
    (4, "ambulance",  "救护车",     "🚑"),
    (4, "exercise",   "锻炼；练习", ""),
    # 世界5 🎉 节日庆典 · Festivals & Celebrations (10 words)
    (5, "festival",     "节日",           "🎉"),
    (5, "Halloween",    "万圣节",         "🎃"),
    (5, "Thanksgiving", "感恩节",         "🍂"),
    (5, "Christmas",    "圣诞节",         "🎄"),
    (5, "Easter",       "复活节",         "🐰"),
    (5, "lantern",      "灯笼",           "🏮"),
    (5, "moon",         "月亮",           "🌕"),
    (5, "lunar",        "农历的；月亮的", "🌙"),
    (5, "celebrate",    "庆祝",           ""),
    (5, "important",    "重要的",         ""),
    # 世界6 🦸 职业·人物·国籍 · Jobs, People & Nationalities (18 words)
    (6, "doctor",      "医生",                   "👨‍⚕️"),
    (6, "nurse",       "护士",                   "👩‍⚕️"),
    (6, "worker",      "工人",                   "👷"),
    (6, "hero",        "英雄",                   "🦸"),
    (6, "queen",       "女王",                   "👑"),
    (6, "cousin",      "表亲",                   "🧑"),
    (6, "British",     "英国的；英国人",         ""),
    (6, "American",    "美国的；美国人",         "🇺🇸"),
    (6, "Australian",  "澳大利亚的；澳大利亚人", "🇦🇺"),
    (6, "Spanish",     "西班牙的；西班牙人",     "🇪🇸"),
    (6, "Japanese",    "日本的；日本人",         "🇯🇵"),
    (6, "Korean",      "韩国的；韩国人",         "🇰🇷"),
    (6, "brave",       "勇敢的",                 ""),
    (6, "wise",        "明智的",                 ""),
    (6, "helpful",     "乐于助人的",             ""),
    (6, "hardworking", "勤劳的",                 ""),
    (6, "friendly",    "友好的",                 ""),
    (6, "nationality", "国籍",                   ""),
    # 世界7 🎯 爱好梦想（含读书/科技/过去的经历） · Hobbies, Dreams & Past Tense (36 words)
    (7, "hobby",     "爱好",                    "🎯"),
    (7, "stamp",     "邮票",                    "📮"),
    (7, "doll",      "玩具娃娃",                "🪆"),
    (7, "bicycle",   "自行车",                  "🚲"),
    (7, "robot",     "机器人",                  "🤖"),
    (7, "dream",     "梦想",                    "💭"),
    (7, "diary",     "日记",                    "📔"),
    (7, "world",     "世界",                    "🌍"),
    (7, "book",      "书",                      "📖"),
    (7, "ocean",     "海洋",                    "🌊"),
    (7, "collect",   "收集",                    ""),
    (7, "wish",      "希望；愿望",              ""),
    (7, "glad",      "高兴的",                  "😊"),
    (7, "dangerous", "危险的",                  ""),
    (7, "war",       "战争",                    ""),
    (7, "fast",      "快的；快速地",            ""),
    (7, "enough",    "足够的",                  ""),
    (7, "sure",      "确定的",                  ""),
    (7, "joy",       "喜悦",                    ""),
    (7, "imagine",   "想象",                    ""),
    (7, "author",    "作者",                    ""),
    (7, "bookworm",  "书虫",                    "🐛"),
    (7, "page",      "页",                      ""),
    (7, "plan",      "计划",                    ""),
    (7, "went",      "去（go的过去式）",         ""),
    (7, "saw",       "看见（see的过去式）",      ""),
    (7, "came",      "来（come的过去式）",       ""),
    (7, "broke",     "打破（break的过去式）",    ""),
    (7, "fell",      "摔倒（fall的过去式）",     ""),
    (7, "had",       "有（have的过去式）",       ""),
    (7, "found",     "找到（find的过去式）",     ""),
    (7, "wrote",     "写（write的过去式）",      ""),
    (7, "ate",       "吃（eat的过去式）",        ""),
    (7, "drank",     "喝（drink的过去式）",      ""),
    (7, "spoke",     "说（speak的过去式）",      ""),
    (7, "kept",      "保持；写（keep的过去式）", ""),
]

WORLD_META = [
    (1, "🎒 学校科目",      "var(--gold)"),
    (2, "🐾 动物世界",      "var(--grass)"),
    (3, "🏙️ 城市地点",     "var(--cyan)"),
    (4, "🍎 食物健康（含身体）", "var(--red)"),
    (5, "🎉 节日庆典",      "var(--gold)"),
    (6, "🦸 职业人物",      "var(--grass)"),
    (7, "🎯 爱好梦想",      "var(--cyan)"),
]

# 短语库（外研社《Join In》六年级 G6 标准）：(world_id, en, zh)。
# 多词短语（含空格），共 25 条。源：.superpowers/sdd/joinin-g6-comprehensive.md §B
PHRASES = [
    # 世界1 学校科目 (2)
    (1, "be good at", "擅长"),
    (1, "get along",  "相处融洽"),
    # 世界2 动物世界 (3)
    (2, "live on",           "靠…生活；以…为食"),
    (2, "South China tiger", "华南虎"),
    (2, "in danger",         "处于危险中"),
    # 世界3 城市地点 (5)
    (3, "straight ahead", "一直往前走"),
    (3, "more than",      "多于；超过"),
    (3, "far from",       "远离"),
    (3, "get on",         "上（车）；相处"),
    (3, "twin towers",    "双子塔"),
    # 世界5 节日庆典 (6)
    (5, "Mid-Autumn Festival",  "中秋节"),
    (5, "Spring Festival",      "春节"),
    (5, "Lantern Festival",     "元宵节"),
    (5, "Dragon Boat Festival", "端午节"),
    (5, "moon cake",            "月饼"),
    (5, "get together",         "聚在一起"),
    # 世界6 职业人物国籍 (1)
    (6, "be born in", "出生于"),
    # 世界7 爱好梦想 (8)
    (7, "keep a diary",      "写日记"),
    (7, "be different from", "与…不同"),
    (7, "once a month",      "每月一次"),
    (7, "free time",         "空闲时间"),
    (7, "at the moment",     "此刻；当前"),
    (7, "think about",       "想念；考虑"),
    (7, "look up",           "查阅；向上看"),
    (7, "cry out",           "大声喊叫"),
]

# 连词成句句库（外研社《Join In》六年级 G6 标准）：(world_id, en, zh)。
# 无缩写。注意：§C 标题注明 45 句，但 §C P 表实际含 46 行（off-by-one in source doc）。
# 此处收录全部 46 行，与源文件 P 表保持一致。详见 task-p4-1-report.md。
SENTENCES = [
    # P1 · Simple present (be) — 7 sentences
    (1, "Maths is my favourite subject.",                    "数学是我最喜欢的科目。"),
    (1, "History and Geography are my favourite subjects.",  "历史和地理是我最喜欢的科目。"),
    (2, "The panda is an endangered animal.",                "大熊猫是一种濒危动物。"),
    (3, "London is the capital of England.",                 "伦敦是英格兰的首都。"),
    (4, "Fruit is good for your health.",                    "水果对你的健康有好处。"),
    (5, "Christmas is in December.",                         "圣诞节在十二月。"),
    (6, "My cousin is Australian.",                          "我的表亲是澳大利亚人。"),
    # P2 · Simple present (action verb) — 4 sentences
    (2, "Pandas live on bamboo.",                            "熊猫靠竹子为食。"),
    (3, "He lives far from the city.",                       "他住得离城市很远。"),
    (4, "Vegetables help keep you healthy.",                 "蔬菜有助于保持健康。"),
    (7, "She collects stamps in her free time.",             "她在空闲时间集邮。"),
    # P3 · Present continuous — 3 sentences
    (1, "We are practising drama.",                          "我们正在练习戏剧。"),
    (3, "They are walking straight ahead.",                  "他们正在笔直往前走。"),
    (7, "I am keeping a diary this week.",                   "我这周在写日记。"),
    # P4 · Simple past (irregular verbs) — 9 sentences
    (3, "We went to the palace yesterday.",                  "我们昨天去了宫殿。"),
    (4, "She broke her arm in the accident.",                "她在事故中摔断了手臂。"),
    (4, "He fell and hurt his leg.",                         "他摔倒并伤了腿。"),
    (5, "We ate moon cakes at the festival.",                "我们在节日里吃了月饼。"),
    (6, "She spoke Japanese very well.",                     "她的日语说得很好。"),
    (7, "He wrote a long diary entry.",                      "他写了一篇很长的日记。"),
    (7, "They saw a whale in the ocean.",                    "他们在海洋中看见了一头鲸鱼。"),
    (7, "She drank orange juice at breakfast.",              "她早餐喝了橙汁。"),
    (7, "I found a good book in the library.",               "我在图书馆找到了一本好书。"),
    # P5 · Simple past (regular verb) — 1 sentence
    (5, "We celebrated the festival together.",              "我们一起庆祝了这个节日。"),
    # P6 · Comparatives — 4 sentences
    (2, "Elephants are bigger than bears.",                  "大象比熊大。"),
    (2, "There are fewer wolves now.",                       "现在狼的数量更少了。"),
    (4, "Fruit is healthier than rice.",                     "水果比米饭更健康。"),
    (6, "She is braver than her brother.",                   "她比她的哥哥更勇敢。"),
    # P7 · Future — be going to — 3 sentences
    (3, "We are going to visit the castle.",                 "我们打算去参观城堡。"),
    (6, "She is going to be a nurse.",                       "她打算成为一名护士。"),
    (7, "I am going to keep a diary.",                       "我打算写日记。"),
    # P8 · Future — will — 2 sentences
    (2, "There will be fewer endangered animals.",           "濒危动物将会减少。"),
    (7, "The robot will help us in the future.",             "未来机器人将帮助我们。"),
    # P9 · be good at + noun/gerund — 2 sentences
    (1, "She is good at maths and science.",                 "她擅长数学和科学。"),
    (7, "He is good at collecting stamps.",                  "他擅长集邮。"),
    # P10 · Imperatives & directions — 3 sentences
    (3, "Go straight ahead and turn left.",                  "一直往前走，然后左转。"),
    (3, "Take the third right to the park.",                 "在第三个路口右转去公园。"),
    (4, "Eat more fruit and vegetables.",                    "多吃水果和蔬菜。"),
    # P11 · Wh-questions — 3 sentences
    (2, "How many pandas are there now?",                    "现在有多少只大熊猫？"),
    (5, "What did you do at the festival?",                  "你在节日里做了什么？"),
    (7, "How often do you keep a diary?",                    "你多久写一次日记？"),
    # P12 · There is / There are / There were — 3 sentences
    (2, "There are only a few wild tigers.",                 "野生老虎只剩几只。"),
    (3, "There is a famous palace in Beijing.",              "北京有一座著名的宫殿。"),
    (5, "There were many lanterns at the festival.",         "节日上有很多灯笼。"),
    # P13 · love / like + gerund — 2 sentences
    (7, "I love reading books about heroes.",                "我喜欢读关于英雄的书。"),
    (7, "She likes collecting dolls.",                       "她喜欢收集玩偶。"),
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
    phrases = [{"en": en, "zh": zh, "world": w, "audio": audio_key(en)}
               for (w, en, zh) in PHRASES]
    sentences = [{"en": en, "zh": zh, "world": w, "audio": audio_key(en), "words": tokenize(en)}
                 for (w, en, zh) in SENTENCES]
    data = {"worlds": worlds, "phrases": phrases, "sentences": sentences}
    js = ("/* 自动生成，勿手改。源：tools/gen_en_data.py。 */\n"
          "window.EN_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(js)
    counts = " ".join(f"#{w['id']}={len(w['words'])}" for w in worlds)
    print(f"已写 {OUT}：{len(WORDS)} 词 / {len(PHRASES)} 短语 / {len(worlds)} 世界（{counts}）+ {len(sentences)} 句。")


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
            + [(en, audio_key(en)) for (w, en, zh) in PHRASES]
            + [(en, audio_key(en)) for (w, en, zh) in SENTENCES])
    valid = {key + ".mp3" for (_, key) in todo}
    removed = 0                                          # 清理：删掉不再引用的旧 mp3，保持发音包与内容同步
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
        except Exception as e:                           # 单条失败不致命：跳过，可重跑补齐
            print(f"  ✗ {text}: {e}")
            time.sleep(0.4)
            continue
        if not data:
            print(f"  ✗ {text}: empty")
            continue
        with open(path, "wb") as f:
            f.write(data)
        done += 1
        time.sleep(0.4)                                  # 礼貌限速
    print(f"发音包：新增 {done}，跳过 {skip}（已存在），删孤儿 {removed}，目录 {AUDIO_DIR}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "audio":
        gen_audio()
    else:
        build()
