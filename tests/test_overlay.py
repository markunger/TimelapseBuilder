import hashlib
import os
import tempfile
import unittest
from datetime import datetime

from PIL import Image, ExifTags

import overlay


def _make_jpeg(path, exif_datetime_original=None, exif_datetime=None):
    img = Image.new("RGB", (200, 150), (120, 150, 200))
    if exif_datetime_original or exif_datetime:
        exif = Image.Exif()
        if exif_datetime_original:
            exif[ExifTags.IFD.Exif] = {ExifTags.Base.DateTimeOriginal: exif_datetime_original}
        if exif_datetime:
            exif[ExifTags.Base.DateTime] = exif_datetime
        img.save(path, exif=exif)
    else:
        img.save(path)


class TestGetCaptureDatetime(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "test.jpg")

    def test_uses_datetime_original_when_present(self):
        _make_jpeg(self.path, exif_datetime_original="2024:02:02 08:30:00", exif_datetime="2024:01:01 00:00:00")
        result = overlay.get_capture_datetime(self.path)
        self.assertEqual(result, datetime(2024, 2, 2, 8, 30, 0))

    def test_falls_back_to_datetime_tag(self):
        _make_jpeg(self.path, exif_datetime="2024:03:03 09:15:00")
        result = overlay.get_capture_datetime(self.path)
        self.assertEqual(result, datetime(2024, 3, 3, 9, 15, 0))

    def test_falls_back_to_mtime_when_no_exif(self):
        _make_jpeg(self.path)
        mtime = datetime(2023, 5, 5, 12, 0, 0).timestamp()
        os.utime(self.path, (mtime, mtime))
        result = overlay.get_capture_datetime(self.path)
        self.assertEqual(result, datetime(2023, 5, 5, 12, 0, 0))


class TestStampImage(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.src = os.path.join(self.tmpdir, "src.jpg")
        self.dst = os.path.join(self.tmpdir, "stamped.jpg")
        _make_jpeg(self.src, exif_datetime_original="2024:06:15 10:00:00")

    def test_output_is_valid_jpeg(self):
        overlay.stamp_image(self.src, self.dst)
        with Image.open(self.dst) as img:
            img.verify()

    def test_original_is_untouched(self):
        with open(self.src, "rb") as f:
            original_hash = hashlib.sha256(f.read()).hexdigest()
        overlay.stamp_image(self.src, self.dst)
        with open(self.src, "rb") as f:
            new_hash = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(original_hash, new_hash)


if __name__ == "__main__":
    unittest.main()
