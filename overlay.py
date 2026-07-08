"""EXIF datetime extraction and timestamp stamping for timelapse frames."""

import os
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ExifTags

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
)

_font_cache = {}


def _load_font(size):
    if size in _font_cache:
        return _font_cache[size]
    font = None
    for path in _FONT_CANDIDATES:
        try:
            font = ImageFont.truetype(path, size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
    _font_cache[size] = font
    return font


def get_capture_datetime(path):
    """Best-effort capture time: EXIF DateTimeOriginal -> EXIF DateTime -> file mtime."""
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
            raw = exif_ifd.get(ExifTags.Base.DateTimeOriginal) or exif.get(ExifTags.Base.DateTime)
        if raw:
            return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return datetime.fromtimestamp(os.path.getmtime(path))


def stamp_image(src_path, dst_path, dt=None):
    """Write a copy of src_path to dst_path with a bold white / black-drop-shadow
    timestamp burned into the top-right corner. Never modifies src_path."""
    if dt is None:
        dt = get_capture_datetime(src_path)
    text = dt.strftime(DATETIME_FORMAT)

    img = Image.open(src_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    font = _load_font(max(18, img.height // 30))

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = 20
    x = img.width - margin - tw
    y = margin

    shadow_offset = 2
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=(255, 255, 255))

    img.save(dst_path, "JPEG", quality=95)
