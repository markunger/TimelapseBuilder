"""Minimal Tkinter front-end for TimelapseBuilder — folder picker, RAW-delete
and timestamp-overlay toggles, Start/Stop, and a live log."""

import os
import queue
import sys
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk

import config as config_module

try:
    from core import Watcher, WatcherConfig
except ImportError as e:
    print(f"Missing required Python package: {e.name}")
    print("Run this in Terminal to install it, then try again:")
    print("  pip3 install -r requirements.txt")
    sys.exit(1)

POLL_INTERVAL_MS = 200


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("TimelapseBuilder")
        self.root.geometry("480x420")

        self.watcher = None
        self.msg_queue = queue.Queue()

        saved = config_module.load_config()
        self.folder_var = tk.StringVar(value=saved["watch_folder"])
        self.delete_raw_var = tk.BooleanVar(value=saved["delete_raw"])
        self.overlay_var = tk.BooleanVar(value=saved["overlay_timestamp"])

        self._build_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(POLL_INTERVAL_MS, self._drain_queue)

    def _build_widgets(self):
        pad = {"padx": 10, "pady": 6}

        folder_frame = ttk.Frame(self.root)
        folder_frame.pack(fill="x", **pad)
        ttk.Label(folder_frame, text="Watch folder:").pack(anchor="w")
        entry_row = ttk.Frame(folder_frame)
        entry_row.pack(fill="x")
        self.folder_entry = ttk.Entry(entry_row, textvariable=self.folder_var, state="readonly")
        self.folder_entry.pack(side="left", fill="x", expand=True)
        self.browse_button = ttk.Button(entry_row, text="Choose Folder...", command=self._choose_folder)
        self.browse_button.pack(side="left", padx=(6, 0))

        self.delete_raw_check = ttk.Checkbutton(
            self.root, text="Delete RAW files (CR2/CR3, etc.) after each shot",
            variable=self.delete_raw_var,
        )
        self.delete_raw_check.pack(anchor="w", **pad)

        self.overlay_check = ttk.Checkbutton(
            self.root, text="Stamp capture date/time on video frames",
            variable=self.overlay_var,
        )
        self.overlay_check.pack(anchor="w", **pad)

        control_row = ttk.Frame(self.root)
        control_row.pack(fill="x", **pad)
        self.toggle_button = ttk.Button(control_row, text="Start", command=self._toggle)
        self.toggle_button.pack(side="left")
        self.status_label = ttk.Label(control_row, text="Idle")
        self.status_label.pack(side="left", padx=(10, 0))

        self.start_time_label = ttk.Label(self.root, text="Timelapse Start: —")
        self.start_time_label.pack(anchor="w", **pad)

        ttk.Label(self.root, text="Log:").pack(anchor="w", padx=10)
        self.log_text = scrolledtext.ScrolledText(self.root, height=12, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # --- actions -------------------------------------------------------

    def _choose_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.folder_var.get() or os.path.expanduser("~/Desktop"))
        if chosen:
            self.folder_var.set(chosen)

    def _toggle(self):
        if self.watcher is None:
            self._start()
        else:
            self._stop()

    def _start(self):
        folder = self.folder_var.get().strip()
        if not folder:
            self._append_log("Please choose a watch folder first.")
            return

        config_module.save_config({
            "watch_folder": folder,
            "delete_raw": self.delete_raw_var.get(),
            "overlay_timestamp": self.overlay_var.get(),
        })

        watcher_config = WatcherConfig(
            folder=folder,
            delete_raw=self.delete_raw_var.get(),
            overlay_timestamp=self.overlay_var.get(),
            log=self._queue_log,
            on_start_time=self._queue_start_time,
        )
        self.watcher = Watcher(watcher_config)
        self.watcher.start()

        self.toggle_button.config(text="Stop")
        self.status_label.config(text="Watching...")
        self.browse_button.config(state="disabled")
        self.delete_raw_check.config(state="disabled")
        self.overlay_check.config(state="disabled")

    def _stop(self):
        if self.watcher is not None:
            self.watcher.stop()
            self.watcher = None
        self.toggle_button.config(text="Start")
        self.status_label.config(text="Idle")
        self.browse_button.config(state="normal")
        self.delete_raw_check.config(state="normal")
        self.overlay_check.config(state="normal")

    def _on_close(self):
        self._stop()
        self.root.destroy()

    # --- thread-safe log/label updates ----------------------------------

    def _queue_log(self, message):
        self.msg_queue.put(("log", message))

    def _queue_start_time(self, dt):
        self.msg_queue.put(("start_time", dt.strftime("%Y-%m-%d %H:%M:%S")))

    def _drain_queue(self):
        while True:
            try:
                kind, payload = self.msg_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "log":
                self._append_log(payload)
            elif kind == "start_time":
                self.start_time_label.config(text=f"Timelapse Start: {payload}")
        self.root.after(POLL_INTERVAL_MS, self._drain_queue)

    def _append_log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
