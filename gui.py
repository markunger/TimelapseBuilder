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
        self.root.geometry("480x380")
        self.root.config(bg="black")

        self.watcher = None
        self.msg_queue = queue.Queue()
        self.log_visible = tk.BooleanVar(value=False)

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
        pad = {"padx": 10, "pady": 6}

        # Main content frame
        main_frame = tk.Frame(self.root, bg="black")
        main_frame.pack(fill="both", expand=True)

        # Folder selection
        folder_frame = tk.Frame(main_frame, bg="black")
        folder_frame.pack(fill="x", **pad)
        tk.Label(folder_frame, text="Watch folder:", bg="black", fg="white").pack(anchor="w")
        entry_row = tk.Frame(folder_frame, bg="black")
        entry_row.pack(fill="x")
        self.folder_entry = tk.Entry(entry_row, textvariable=self.folder_var, state="readonly")
        self.folder_entry.pack(side="left", fill="x", expand=True)
        self.browse_button = tk.Button(entry_row, text="Choose Folder...", command=self._choose_folder)
        self.browse_button.pack(side="left", padx=(6, 0))

        # Checkboxes
        self.delete_raw_check = tk.Checkbutton(
            main_frame, text="Delete RAW files (CR2/CR3, etc.) after each shot",
            variable=self.delete_raw_var, bg="black", fg="white", selectcolor="black"
        )
        self.delete_raw_check.pack(anchor="w", **pad)

        self.overlay_check = tk.Checkbutton(
            main_frame, text="Stamp capture date/time on video frames",
            variable=self.overlay_var, bg="black", fg="white", selectcolor="black"
        )
        self.overlay_check.pack(anchor="w", **pad)

        self.focus_stack_check = tk.Checkbutton(
            main_frame, text="Focus stack timelapse",
            variable=self.focus_stack_var, command=self._on_focus_stack_toggle,
            bg="black", fg="white", selectcolor="black"
        )
        self.focus_stack_check.pack(anchor="w", **pad)

        self.focus_stack_frame = tk.Frame(main_frame, bg="black")
        self.focus_stack_frame.pack(fill="x", padx=20, pady=(0, 6))
        tk.Label(self.focus_stack_frame, text="Stack size:", bg="black", fg="white").pack(side="left", padx=(0, 6))
        self.stack_size_entry = tk.Entry(self.focus_stack_frame, textvariable=self.stack_size_var, width=8)
        self.stack_size_entry.pack(side="left", padx=(0, 12))
        self.stack_size_entry.config(state="normal" if self.focus_stack_var.get() else "disabled")
        tk.Label(self.focus_stack_frame, text="Monitor photo #:", bg="black", fg="white").pack(side="left", padx=(0, 6))
        self.monitor_index_entry = tk.Entry(self.focus_stack_frame, textvariable=self.monitor_index_var, width=8)
        self.monitor_index_entry.pack(side="left")
        self.monitor_index_entry.config(state="normal" if self.focus_stack_var.get() else "disabled")

        # Control row (Start/Stop button and status)
        control_row = tk.Frame(main_frame, bg="black")
        control_row.pack(fill="x", **pad)
        self.toggle_button = tk.Button(control_row, text="Start", command=self._toggle, bg="#87CEEB", fg="black", font=("Helvetica", 12, "bold"), padx=10, pady=4)
        self.toggle_button.pack(side="left")
        self.status_label = tk.Label(control_row, text="Idle", bg="black", fg="#FFA500", font=("Helvetica", 11, "bold"))
        self.status_label.pack(side="left", padx=(10, 0))

        self.start_time_label = tk.Label(main_frame, text="Timelapse Start: —", bg="black", fg="white")
        self.start_time_label.pack(anchor="w", **pad)

        # Log toggle and log area
        log_header_frame = tk.Frame(main_frame, bg="black")
        log_header_frame.pack(fill="x", padx=10, pady=(6, 0))
        tk.Label(log_header_frame, text="Log:", bg="black", fg="white").pack(side="left")
        self.log_toggle_button = tk.Button(log_header_frame, text="Show", command=self._toggle_log, bg="gray20", fg="white", padx=8, pady=2)
        self.log_toggle_button.pack(side="left", padx=(10, 0))

        self.log_frame = tk.Frame(main_frame, bg="black")
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=12, state="disabled", bg="black", fg="white")
        self.log_text.pack(fill="both", expand=True, padx=0, pady=(0, 10))

    # --- actions -------------------------------------------------------

    def _choose_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.folder_var.get() or os.path.expanduser("~/Desktop"))
        if chosen:
            self.folder_var.set(chosen)

    def _on_focus_stack_toggle(self):
        enabled = self.focus_stack_var.get()
        for widget in (self.stack_size_entry, self.monitor_index_entry):
            widget.config(state="normal" if enabled else "disabled")

    def _toggle_log(self):
        if self.log_visible.get():
            self.log_frame.pack_forget()
            self.log_visible.set(False)
            self.log_toggle_button.config(text="Show")
            self.root.geometry("480x380")
        else:
            self.log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            self.log_visible.set(True)
            self.log_toggle_button.config(text="Hide")
            self.root.geometry("480x520")

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

        self.toggle_button.config(text="Stop", bg="#FF4444")
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
        self.toggle_button.config(text="Start", bg="#87CEEB")
        self.status_label.config(text="Idle", fg="#FFA500")
        self.browse_button.config(state="normal")
        self.delete_raw_check.config(state="normal")
        self.overlay_check.config(state="normal")
        self.focus_stack_check.config(state="normal")
        # Re-enable or disable the focus stack input fields based on checkbox state
        stack_enabled = "normal" if self.focus_stack_var.get() else "disabled"
        self.stack_size_entry.config(state=stack_enabled)
        self.monitor_index_entry.config(state=stack_enabled)

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
