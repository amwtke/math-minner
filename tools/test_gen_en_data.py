import unittest
from gen_en_data import audio_key, tokenize, build, WORDS, SENTENCES, WORLD_META


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


class DataShapeTest(unittest.TestCase):
    def test_seven_worlds_and_word_count(self):
        self.assertEqual(len(WORLD_META), 7)
        self.assertEqual(len(WORDS), 68)
        ids = {w[0] for w in WORDS}
        self.assertEqual(ids, {1, 2, 3, 4, 5, 6, 7})

    def test_sentences_use_only_known_function_or_listed_handling(self):
        # 句库非空、每句有中文、词数在 3..7
        self.assertTrue(len(SENTENCES) >= 20)
        for (_w, en, zh) in SENTENCES:
            self.assertTrue(zh)
            self.assertTrue(3 <= len(tokenize(en)) <= 7)


if __name__ == "__main__":
    unittest.main()
