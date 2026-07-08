import os
import tempfile
import unittest

from core import find_matching_raw


class TestFindMatchingRaw(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _touch(self, name):
        open(os.path.join(self.tmpdir, name), "w").close()

    def test_exact_stem_match(self):
        self._touch("IMG_0001.JPG")
        self._touch("IMG_0001.CR2")
        self.assertEqual(
            find_matching_raw(self.tmpdir, "IMG_0001"),
            os.path.join(self.tmpdir, "IMG_0001.CR2"),
        )

    def test_case_insensitive_extension(self):
        self._touch("IMG_0002.jpg")
        self._touch("IMG_0002.cr3")
        self.assertIsNotNone(find_matching_raw(self.tmpdir, "IMG_0002"))

    def test_near_miss_longer_stem_does_not_match(self):
        self._touch("IMG_00011.CR2")
        self.assertIsNone(find_matching_raw(self.tmpdir, "IMG_0001"))

    def test_near_miss_suffixed_stem_does_not_match(self):
        self._touch("IMG_0001_edit.CR2")
        self.assertIsNone(find_matching_raw(self.tmpdir, "IMG_0001"))

    def test_unrelated_mp4_never_matches(self):
        self._touch("output_video.mp4")
        self._touch("temp_output_video.mp4")
        self.assertIsNone(find_matching_raw(self.tmpdir, "output_video"))
        self.assertIsNone(find_matching_raw(self.tmpdir, "temp_output_video"))

    def test_no_match_returns_none(self):
        self._touch("IMG_0003.JPG")
        self.assertIsNone(find_matching_raw(self.tmpdir, "IMG_0003"))


if __name__ == "__main__":
    unittest.main()
