import unittest
from gen_data import normalize_code


class NormalizeCodeTest(unittest.TestCase):
    def test_plain_syllable_unchanged(self):
        self.assertEqual(normalize_code("ma3"), "ma3")
        self.assertEqual(normalize_code("hao3"), "hao3")

    def test_v_form_to_uu(self):
        # pypinyin 默认 ü 输出为 v
        self.assertEqual(normalize_code("lv4"), "luu4")
        self.assertEqual(normalize_code("nv3"), "nuu3")

    def test_u_umlaut_to_uu(self):
        # 若 pypinyin 配置成输出 ü 字符也要兜住
        self.assertEqual(normalize_code("lü4"), "luu4")

    def test_compound_v(self):
        self.assertEqual(normalize_code("lve4"), "luue4")
        self.assertEqual(normalize_code("nve2"), "nuue2")

    def test_jqxy_u_not_touched(self):
        # ju/qu/xu/yu 里的 u 不是 ü，保持不变
        self.assertEqual(normalize_code("ju1"), "ju1")
        self.assertEqual(normalize_code("qu4"), "qu4")
        self.assertEqual(normalize_code("yu2"), "yu2")

    def test_neutral_tone_five(self):
        self.assertEqual(normalize_code("ma5"), "ma5")


if __name__ == "__main__":
    unittest.main()
