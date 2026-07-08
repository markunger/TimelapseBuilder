"""Watches a folder for new timelapse JPGs, optionally deletes matching RAW
files, optionally stamps a timestamp onto frames, and incrementally compiles
a looping mp4 via a per-photo segment cache + fast concat (so compile cost
stays roughly constant per new photo, regardless of how long the session has
been running)."""

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import Callable, Optional
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import overlay

RAW_EXTENSIONS = (".cr2", ".cr3", ".nef", ".arw", ".orf", ".raf", ".dng")

SEGMENTS_DIRNAME = ".tl_segments"
FRAMERATE = 24
PROGRESS_LOG_EVERY = 25


def _default_start_time_cb(dt):
    pass


@dataclass
class WatcherConfig:
    folder: str
    delete_raw: bool = False
    overlay_timestamp: bool = False
    log: Callable[[str], None] = print
    on_start_time: Callable[[datetime], None] = _default_start_time_cb


def find_matching_raw(folder, stem):
    """Return the path of a RAW file in `folder` whose name (without
    extension) exactly equals `stem`, or None. Exact-stem + fixed-extension
    matching means this can never match unrelated files like output_video.mp4."""
    with os.scandir(folder) as it:
        for entry in it:
            if not entry.is_file():
                continue
            name, ext = os.path.splitext(entry.name)
            if name == stem and ext.lower() in RAW_EXTENSIONS:
                return entry.path
    return None


def _run_ffmpeg(command, log, context):
    try:
        subprocess.run(command, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="replace") if e.stderr else ""
        log(f"{context} failed: {stderr.strip()[-500:] or e}")
        return False


class Handler(FileSystemEventHandler):
    def __init__(self, config: WatcherConfig):
        self.config = config
        self.image_counter = 0
        self.start_datetime = None
        self._segments_root = os.path.join(config.folder, SEGMENTS_DIRNAME)

    def log(self, msg):
        self.config.log(msg)

    # --- lifecycle -----------------------------------------------------

    def process_existing(self):
        existing = sorted(
            f for f in os.listdir(self.config.folder) if f.lower().endswith(".jpg")
        )
        if not existing:
            return
        self.log(f"Found {len(existing)} existing image(s), processing...")
        paths = [os.path.join(self.config.folder, name) for name in existing]
        self.start_datetime = min(overlay.get_capture_datetime(p) for p in paths)
        self.config.on_start_time(self.start_datetime)

        for i, path in enumerate(paths, start=1):
            self._handle_one(path, retry_raw=False)
            if i % PROGRESS_LOG_EVERY == 0:
                self.log(f"Processed {i}/{len(paths)} existing image(s)...")

        self.compile_video()

    def on_created(self, event):
        if event.is_directory or not event.src_path.lower().endswith(".jpg"):
            return
        self.image_counter += 1
        self.log(f"Image {self.image_counter} detected: {os.path.basename(event.src_path)}")
        self._handle_one(event.src_path, retry_raw=True)
        self.compile_video()

    # --- per-photo processing -------------------------------------------

    def _handle_one(self, jpg_path, retry_raw):
        if self.start_datetime is None:
            self.start_datetime = overlay.get_capture_datetime(jpg_path)
            self.config.on_start_time(self.start_datetime)

        if self.config.delete_raw:
            self._delete_matching_raw(jpg_path, retry=retry_raw)

    def _delete_matching_raw(self, jpg_path, retry):
        stem = os.path.splitext(os.path.basename(jpg_path))[0]
        folder = os.path.dirname(jpg_path)

        attempts = 4 if retry else 1
        raw_path = None
        for attempt in range(attempts):
            raw_path = find_matching_raw(folder, stem)
            if raw_path or attempt == attempts - 1:
                break
            time.sleep(0.5)

        if not raw_path:
            return
        try:
            os.remove(raw_path)
            self.log(f"Deleted RAW: {os.path.basename(raw_path)}")
        except OSError as e:
            self.log(f"Could not delete RAW {raw_path}: {e}")

    # --- segment cache / incremental compile ----------------------------

    def _mode_dir(self):
        mode = "stamped" if self.config.overlay_timestamp else "original"
        path = os.path.join(self._segments_root, mode)
        os.makedirs(path, exist_ok=True)
        return path

    def _ensure_segment(self, jpg_path, mode_dir):
        stem = os.path.splitext(os.path.basename(jpg_path))[0]
        segment_path = os.path.join(mode_dir, stem + ".mp4")
        if os.path.exists(segment_path):
            return segment_path

        if self.config.overlay_timestamp:
            fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
            os.close(fd)
            try:
                overlay.stamp_image(jpg_path, tmp_path)
                ok = self._encode_segment(tmp_path, segment_path)
            finally:
                os.remove(tmp_path)
        else:
            ok = self._encode_segment(jpg_path, segment_path)

        return segment_path if ok else None

    def _encode_segment(self, image_path, segment_path):
        tmp_segment = segment_path + ".tmp.mp4"
        command = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-frames:v", "1",
            "-r", str(FRAMERATE),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-profile:v", "baseline",
            "-level", "3.0",
            tmp_segment,
        ]
        if not _run_ffmpeg(command, self.log, f"Encoding frame for {os.path.basename(segment_path)}"):
            return False
        shutil.move(tmp_segment, segment_path)
        return True

    def compile_video(self):
        folder = self.config.folder
        jpgs = sorted(f for f in os.listdir(folder) if f.lower().endswith(".jpg"))
        if not jpgs:
            return

        mode_dir = self._mode_dir()
        manifest_lines = []
        for name in jpgs:
            segment_path = self._ensure_segment(os.path.join(folder, name), mode_dir)
            if segment_path:
                manifest_lines.append(f"file '{segment_path}'\n")

        if not manifest_lines:
            return

        manifest_path = os.path.join(self._segments_root, "manifest.txt")
        with open(manifest_path, "w") as f:
            f.writelines(manifest_lines)

        temp_output_video = os.path.join(folder, "temp_output_video.mp4")
        final_output_video = os.path.join(folder, "output_video.mp4")
        command = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", manifest_path,
            "-c", "copy",
            "-movflags", "faststart",
            temp_output_video,
        ]
        if not _run_ffmpeg(command, self.log, "Compiling video"):
            return

        shutil.move(temp_output_video, final_output_video)
        self.close_and_play_video(final_output_video)

    def close_and_play_video(self, video_path):
        try:
            subprocess.run(["pkill", "QuickTime Player"], check=False)
            time.sleep(1)
            applescript = f'''
            tell application "QuickTime Player"
                activate
                open POSIX file "{video_path}"
                set looping of document 1 to true
                play document 1
                activate
            end tell
            '''
            subprocess.run(["osascript", "-e", applescript], check=True)
        except subprocess.CalledProcessError as e:
            self.log(f"Error closing QuickTime Player or running AppleScript: {e}")
        except Exception as e:
            self.log(f"Error: {e}")


class Watcher:
    def __init__(self, config: WatcherConfig):
        self.config = config
        self.observer = Observer()
        self.handler = Handler(config)

    def start(self):
        os.makedirs(self.config.folder, exist_ok=True)
        self.handler.process_existing()
        self.observer.schedule(self.handler, self.config.folder, recursive=False)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join(timeout=5)

    def run_blocking(self):
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
