"""Terminal-only entry point: watches config.py's saved (or default) folder
with the saved toggle states. Run the GUI (gui.py) for folder/toggle picking."""

import argparse
import sys

import config as config_module

try:
    from core import Watcher, WatcherConfig
except ImportError as e:
    print(f"Missing required Python package: {e.name}")
    print("Run this in Terminal to install it, then try again:")
    print("  pip3 install -r requirements.txt")
    sys.exit(1)


def main():
    saved = config_module.load_config()
    parser = argparse.ArgumentParser(description="Watch a folder and build a looping timelapse video.")
    parser.add_argument("--folder", default=saved["watch_folder"])
    parser.add_argument("--delete-raw", action="store_true", default=saved["delete_raw"])
    parser.add_argument("--overlay-timestamp", action="store_true", default=saved["overlay_timestamp"])
    parser.add_argument("--focus-stack", action="store_true", default=saved["focus_stack_enabled"])
    parser.add_argument("--stack-size", type=int, default=saved["stack_size"])
    parser.add_argument("--monitor-index", type=int, default=saved["monitor_index"])
    args = parser.parse_args()

    watcher_config = WatcherConfig(
        folder=args.folder,
        delete_raw=args.delete_raw,
        overlay_timestamp=args.overlay_timestamp,
        focus_stack_enabled=args.focus_stack,
        stack_size=args.stack_size,
        monitor_index=args.monitor_index,
    )
    watcher = Watcher(watcher_config)
    print(f"Watching {args.folder}")
    print(f"  delete_raw={args.delete_raw}, overlay_timestamp={args.overlay_timestamp}")
    if args.focus_stack:
        print(f"  focus_stack enabled: stack_size={args.stack_size}, monitor_index={args.monitor_index}")
    print("Press Ctrl+C to stop.")
    watcher.run_blocking()
    print("Observer stopped")


if __name__ == "__main__":
    main()
