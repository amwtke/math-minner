import unittest
from gen_en_data import audio_key


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


if __name__ == "__main__":
    unittest.main()
