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
        self.root.title("WonderLab Timelapse Builder")
        self.root.geometry("390x500")
        self.root.config(bg="black")

        self.watcher = None
        self.msg_queue = queue.Queue()

        saved = config_module.load_config()
        self.folder_var = tk.StringVar(value=saved["watch_folder"])
        self.delete_raw_var = tk.BooleanVar(value=saved["delete_raw"])
        self.overlay_var = tk.BooleanVar(value=saved["overlay_timestamp"])
        self.focus_stack_var = tk.BooleanVar(value=saved["focus_stack_enabled"])
        self.stack_size_var = tk.StringVar(value=str(saved["stack_size"]))
        self.monitor_index_var = tk.StringVar(value=str(saved["monitor_index"]))

        self._build_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(POLL_INTERVAL_MS, self._drain_queue)

    def _build_widgets(self):
        bg_color = "#B9BBB6"
        self.root.config(bg=bg_color)
        self.root.geometry("390x500")

        pad = {"padx": 12, "pady": 8}

        # Main content frame with buffer
        main_frame = tk.Frame(self.root, bg=bg_color)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Folder selection
        folder_frame = tk.Frame(main_frame, bg=bg_color)
        folder_frame.pack(fill="x", **pad)
        tk.Label(folder_frame, text="Watch folder:", bg=bg_color, fg="black", font=("Helvetica", 10, "bold")).pack(anchor="w")
        self.folder_entry = tk.Entry(folder_frame, textvariable=self.folder_var, state="readonly", relief=tk.FLAT, bg="white", fg="black")
        self.folder_entry.pack(fill="x", pady=(4, 4))
        self.browse_button = tk.Button(folder_frame, text="Choose Folder...", command=self._choose_folder)
        self.browse_button.pack(anchor="w")

        # Options section header
        tk.Label(main_frame, text="Options:", bg=bg_color, fg="black", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=12, pady=(12, 6))

        # Checkboxes
        self.delete_raw_check = tk.Checkbutton(
            main_frame, text="Delete RAW Files",
            variable=self.delete_raw_var, bg=bg_color, fg="black", selectcolor=bg_color
        )
        self.delete_raw_check.pack(anchor="w", **pad)

        self.overlay_check = tk.Checkbutton(
            main_frame, text="Add Capture Date/Time",
            variable=self.overlay_var, bg=bg_color, fg="black", selectcolor=bg_color
        )
        self.overlay_check.pack(anchor="w", **pad)

        self.focus_stack_check = tk.Checkbutton(
            main_frame, text="Focus Stack Timelapse",
            variable=self.focus_stack_var, command=self._on_focus_stack_toggle,
            bg=bg_color, fg="black", selectcolor=bg_color
        )
        self.focus_stack_check.pack(anchor="w", **pad)

        # Focus stack options frame (always shown)
        self.focus_stack_frame = tk.Frame(main_frame, bg=bg_color)
        self.focus_stack_frame.pack(fill="x", padx=30, pady=(0, 6))
        tk.Label(self.focus_stack_frame, text="Stack size:", bg=bg_color, fg="black").pack(side="left", padx=(0, 6))
        self.stack_size_entry = tk.Entry(self.focus_stack_frame, textvariable=self.stack_size_var, width=5, relief=tk.FLAT, bg="white", fg="black")
        self.stack_size_entry.pack(side="left", padx=(0, 12))
        tk.Label(self.focus_stack_frame, text="Monitor photo #:", bg=bg_color, fg="black").pack(side="left", padx=(0, 6))
        self.monitor_index_entry = tk.Entry(self.focus_stack_frame, textvariable=self.monitor_index_var, width=5, relief=tk.FLAT, bg="white", fg="black")
        self.monitor_index_entry.pack(side="left")
        self._update_focus_stack_state()

        # Control row (Start/Stop button and status)
        control_row = tk.Frame(main_frame, bg=bg_color)
        control_row.pack(fill="x", padx=12, pady=(20, 8))
        self.toggle_button = tk.Button(
            control_row, text="Start", command=self._toggle,
            bg="#87CEEB", fg="black", font=("Helvetica", 12, "bold"), width=8
        )
        self.toggle_button.pack(side="left")
        self.status_label = tk.Label(control_row, text="Idle", bg=bg_color, fg="#CC6600", font=("Helvetica", 11, "bold"))
        self.status_label.pack(side="left", padx=(15, 0))

        self.start_time_label = tk.Label(main_frame, text="Timelapse Start: —", bg=bg_color, fg="black", font=("Helvetica", 10, "bold"))
        self.start_time_label.pack(anchor="w", **pad)

        # Log section
        self.log_frame = tk.Frame(main_frame, bg=bg_color)
        self.log_frame.pack(fill="both", expand=True, padx=0, pady=8)
        tk.Label(self.log_frame, text="Log:", bg=bg_color, fg="black", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=0, pady=(0, 4))
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame, height=10, state="disabled",
            bg="white", fg="black", insertbackground="black", relief=tk.FLAT
        )
        self.log_text.pack(fill="both", expand=True, padx=0, pady=0)

    # --- actions -------------------------------------------------------

    def _choose_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.folder_var.get() or os.path.expanduser("~/Desktop"))
        if chosen:
            self.folder_var.set(chosen)

    def _on_focus_stack_toggle(self):
        self._update_focus_stack_state()

    def _update_focus_stack_state(self):
        enabled = self.focus_stack_var.get()
        state = "normal" if enabled else "disabled"
        for widget in (self.stack_size_entry, self.monitor_index_entry):
            widget.config(state=state)

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

        # Validate focus stack settings if enabled
        focus_stack_enabled = self.focus_stack_var.get()
        stack_size = 1
        monitor_index = 1
        if focus_stack_enabled:
            try:
                stack_size = int(self.stack_size_var.get())
                monitor_index = int(self.monitor_index_var.get())
                if stack_size < 2:
                    self._append_log("Stack size must be at least 2.")
                    return
                if monitor_index < 1 or monitor_index > stack_size:
                    self._append_log(f"Monitor photo must be between 1 and {stack_size}.")
                    return
            except ValueError:
                self._append_log("Stack size and monitor photo must be valid integers.")
                return

        config_module.save_config({
            "watch_folder": folder,
            "delete_raw": self.delete_raw_var.get(),
            "overlay_timestamp": self.overlay_var.get(),
            "focus_stack_enabled": focus_stack_enabled,
            "stack_size": stack_size,
            "monitor_index": monitor_index,
        })

        watcher_config = WatcherConfig(
            folder=folder,
            delete_raw=self.delete_raw_var.get(),
            overlay_timestamp=self.overlay_var.get(),
            focus_stack_enabled=focus_stack_enabled,
            stack_size=stack_size,
            monitor_index=monitor_index,
            log=self._queue_log,
            on_start_time=self._queue_start_time,
        )
        self.watcher = Watcher(watcher_config)
        self.watcher.start()

        self.toggle_button.config(text="Stop", bg="#FF4444", fg="black")
        self.status_label.config(text="Watching...", fg="#00AA00")
        self.browse_button.config(state="disabled")
        self.delete_raw_check.config(state="disabled")
        self.overlay_check.config(state="disabled")
        self.focus_stack_check.config(state="disabled")
        self.stack_size_entry.config(state="disabled")
        self.monitor_index_entry.config(state="disabled")

    def _stop(self):
        if self.watcher is not None:
            self.watcher.stop()
            self.watcher = None
        self.toggle_button.config(text="Start", bg="#87CEEB", fg="black")
        self.status_label.config(text="Idle", fg="#CC6600")
        self.browse_button.config(state="normal")
        self.delete_raw_check.config(state="normal")
        self.overlay_check.config(state="normal")
        self.focus_stack_check.config(state="normal")

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
