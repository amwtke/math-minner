import json
import unittest
from gen_en_data import audio_key, tokenize, build, WORDS, PHRASES, SENTENCES, WORLD_META


class AudioKeyTest(unittest.TestCase):
    def test_simple_word_lowercased(self):
        self.assertEqual(audio_key("Apple"), "apple")
        self.assertEqual(audio_key("red"), "red")

    def test_spaces_become_single_underscore(self):
        self.assertEqual(audio_key("ice cream"), "ice_cream")
        self.assertEqual(audio_key("a   b"), "a_b")

    def test_sentence_punctuation_stripped(self):
        self.assertEqual(audio_key("I like apples."), "i_like_apples")

    def test_trim_surrounding_whitespace_and_underscores(self):
        self.assertEqual(audio_key("  red  "), "red")
        self.assertEqual(audio_key("!hi!"), "hi")


class TokenizeTest(unittest.TestCase):
    def test_drops_trailing_period(self):
        self.assertEqual(tokenize("We ate moon cakes."), ["We", "ate", "moon", "cakes"])

    def test_three_word_sentence(self):
        self.assertEqual(tokenize("Go straight ahead."), ["Go", "straight", "ahead"])

    def test_word_count_matches_audio_key_parts(self):
        # 每句的分词数 == audio_key 下划线段数（拼写规则一致性）
        for (_w, en, _zh) in SENTENCES:
            self.assertEqual(len(tokenize(en)), len(audio_key(en).split("_")))


class CountsTest(unittest.TestCase):
    def test_words_count(self):
        self.assertEqual(len(WORDS), 150)

    def test_phrases_count(self):
        self.assertEqual(len(PHRASES), 25)

    def test_sentences_count(self):
        # §C P-tables yield 46 rows; source doc header says 45 (off-by-one in the md).
        # We encode all P-table rows faithfully — see task-p4-1-report.md for details.
        self.assertEqual(len(SENTENCES), 46)

    def test_per_world_word_counts_sum_to_150(self):
        world_ids = [wid for (wid, _n, _c) in WORLD_META]
        total = 0
        for wid in world_ids:
            count = sum(1 for (w, _e, _z, _m) in WORDS if w == wid)
            total += count
        self.assertEqual(total, 150)

    def test_per_world_word_counts_individual(self):
        def wcount(wid):
            return sum(1 for (w, _e, _z, _m) in WORDS if w == wid)
        self.assertEqual(wcount(1), 21)
        self.assertEqual(wcount(2), 15)
        self.assertEqual(wcount(3), 27)
        self.assertEqual(wcount(4), 23)
        self.assertEqual(wcount(5), 10)
        self.assertEqual(wcount(6), 18)
        self.assertEqual(wcount(7), 36)


class EmojiUniquenessTest(unittest.TestCase):
    def test_non_empty_emojis_are_unique(self):
        emojis = [emoji for (_w, _e, _z, emoji) in WORDS if emoji]
        self.assertEqual(len(emojis), len(set(emojis)),
                         "Duplicate emojis found: " +
                         str([e for e in emojis if emojis.count(e) > 1]))


class TokenShapeTest(unittest.TestCase):
    def test_words_are_single_token(self):
        for (_w, en, _z, _m) in WORDS:
            self.assertNotIn(" ", en, f"WORDS entry contains space: {en!r}")

    def test_phrases_are_multi_token(self):
        for (_w, en, _z) in PHRASES:
            self.assertIn(" ", en, f"PHRASES entry has no space: {en!r}")

    def test_sentences_not_empty_zh(self):
        for (_w, _e, zh) in SENTENCES:
            self.assertTrue(zh)

    def test_sentences_word_count_in_range(self):
        # §C header says 3–8 words each
        for (_w, en, _zh) in SENTENCES:
            count = len(tokenize(en))
            self.assertTrue(3 <= count <= 8,
                            f"Sentence word count {count} out of range 3-8: {en!r}")


class BuildShapeTest(unittest.TestCase):
    def _load_data(self):
        import tempfile, os, sys
        # redirect OUT to a temp file
        import gen_en_data as m
        orig_out = m.OUT
        tmp = tempfile.mktemp(suffix=".js")
        m.OUT = tmp
        try:
            m.build()
            with open(tmp, encoding="utf-8") as f:
                content = f.read()
        finally:
            m.OUT = orig_out
            if os.path.exists(tmp):
                os.remove(tmp)
        # strip JS wrapper
        json_str = content.replace("/* 自动生成，勿手改。源：tools/gen_en_data.py。 */\n", "")
        json_str = json_str.replace("window.EN_DATA = ", "").rstrip(";\n")
        return json.loads(json_str)

    def test_top_level_keys(self):
        data = self._load_data()
        self.assertIn("worlds", data)
        self.assertIn("phrases", data)
        self.assertIn("sentences", data)

    def test_worlds_count(self):
        data = self._load_data()
        self.assertEqual(len(data["worlds"]), 7)

    def test_spot_check_word_has_audio(self):
        data = self._load_data()
        all_words = [w for world in data["worlds"] for w in world["words"]]
        audio_keys = {w["audio"] for w in all_words}
        self.assertIn("maths", audio_keys)
        self.assertIn("panda", audio_keys)

    def test_spot_check_phrase_has_audio(self):
        data = self._load_data()
        phrase_texts = {p["en"] for p in data["phrases"]}
        self.assertIn("moon cake", phrase_texts)
        phrase = next(p for p in data["phrases"] if p["en"] == "moon cake")
        self.assertEqual(phrase["audio"], "moon_cake")
        self.assertTrue(phrase["audio"])

    def test_spot_check_sentence_has_audio_and_words(self):
        data = self._load_data()
        sentence = next(s for s in data["sentences"]
                        if s["en"] == "Pandas live on bamboo.")
        self.assertTrue(sentence["audio"])
        self.assertEqual(sentence["words"], ["Pandas", "live", "on", "bamboo"])

    def test_blank_emoji_word_included(self):
        data = self._load_data()
        all_words = {w["en"]: w for world in data["worlds"] for w in world["words"]}
        self.assertIn("fourth", all_words)
        self.assertEqual(all_words["fourth"]["emoji"], "")

    def test_seven_worlds(self):
        self.assertEqual(len(WORLD_META), 7)
        ids = {w[0] for w in WORDS}
        self.assertEqual(ids, {1, 2, 3, 4, 5, 6, 7})


if __name__ == "__main__":
    unittest.main()
