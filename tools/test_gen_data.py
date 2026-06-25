import unittest
from gen_data import normalize_code, initial_stage, final_stage, world_for


class WorldForTest(unittest.TestCase):
    """按课本拼音进度归世界（喂 pypinyin strict 声母/韵母串，纯函数无需 pypinyin）。"""

    def test_single_final_zero_initial_is_world1(self):
        self.assertEqual(world_for("", "a"), 1)    # 啊
        self.assertEqual(world_for("", "v"), 1)    # 鱼(ü)
        self.assertEqual(world_for("", "er"), 1)   # 二

    def test_initial_groups_advance_world(self):
        self.assertEqual(world_for("b", "a"), 2)   # 爸
        self.assertEqual(world_for("g", "e"), 3)   # 哥
        self.assertEqual(world_for("zh", "i"), 4)  # 知

    def test_compound_final_dominates_over_initial(self):
        self.assertEqual(world_for("", "uo"), 5)   # 我：零声母也因复韵母进世界5
        self.assertEqual(world_for("h", "ao"), 5)  # 好
        self.assertEqual(world_for("sh", "uei"), 5)  # 水

    def test_nasal_final_is_world6(self):
        self.assertEqual(world_for("", "vn"), 6)     # 云(ün)
        self.assertEqual(world_for("g", "uang"), 6)  # 光
        self.assertEqual(world_for("h", "ong"), 6)   # 红
        self.assertEqual(final_stage("ian"), 6)      # 天

    def test_initial_stage_boundaries(self):
        self.assertEqual(initial_stage(""), 1)
        self.assertEqual(initial_stage("l"), 2)
        self.assertEqual(initial_stage("x"), 3)
        self.assertEqual(initial_stage("r"), 4)


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
