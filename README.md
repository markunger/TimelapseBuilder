# TimelapseBuilder

Watches a folder for new photos from a tethered camera (via Canon EOS
Utility or similar) and automatically builds a looping timelapse video as
each new photo arrives. Optionally deletes the RAW file that accompanies
each JPEG (so the Mac's disk doesn't fill up before the camera's memory
card does), and optionally stamps each frame with its capture date/time.

## One-time setup (new Mac)

1. **Get the code.** Install Xcode Command Line Tools if needed
   (`xcode-select --install`, gives you `git`), then:
   ```
   git clone https://github.com/markunger/TimelapseBuilder.git ~/Projects/TimelapseBuilder
   cd ~/Projects/TimelapseBuilder
   ```
   Cloning (rather than downloading the ZIP from GitHub) preserves the
   launcher's executable permission and lets you `git pull` for updates
   later.

2. **Make sure ffmpeg is installed.**
   ```
   ffmpeg -version
   ```
   If that says "command not found," install it once with
   [Homebrew](https://brew.sh):
   ```
   brew install ffmpeg
   ```

3. **Install the Python dependencies.** Make sure `python3` has Tkinter
   available (the [python.org](https://www.python.org/downloads/)
   installer bundles it; Homebrew's python3 needs `brew install
   python-tk` added separately), then:
   ```
   pip3 install -r requirements.txt
   ```

4. **Point Canon EOS Utility (or your camera software) at a save folder.**
   By default this app watches `~/Desktop/TL_Folder`. Set your camera
   software's "save to" destination to that same folder (the app will
   create it automatically the first time you click Start if it doesn't
   exist yet — or pick a different folder from within the app).

5. **Launch the app** by double-clicking **`Timelapse Builder.command`**
   (there's a Desktop shortcut with a custom icon for this — see below).

   The **first time** you do this, macOS will likely refuse and say the
   file is from an "unidentified developer." This is normal for any
   script you write yourself rather than download from the App Store.
   To get past it, just this once:
   - **Right-click** (or Control-click) `Timelapse Builder.command`
     and choose **Open** from the menu (don't just double-click).
   - Click **Open Anyway** in the dialog that appears. On newer versions
     of macOS this button appears under **System Settings → Privacy &
     Security**, near the bottom of the page.
   - After this first time, plain double-clicking will work normally.

6. **Folder access prompt.** The first time the app actually reads or
   writes files on your Desktop, macOS may ask "Terminal would like to
   access files in your Desktop folder" — click **OK**. If you
   accidentally clicked "Don't Allow" and it's not prompting again, fix
   it manually: **System Settings → Privacy & Security → Files and
   Folders**, then enable Desktop access for Terminal.

## Desktop shortcut

There's a "Timelapse Builder" icon on the Desktop — a Finder alias
pointing at `Timelapse Builder.command` in this project folder, with a
custom black/white "WL/TB" icon from `assets/icon.icns` (included in
this repo, so it's identical on every machine). A plain Unix symlink
won't show the custom icon correctly on the Desktop — it has to be a
real Finder alias — so recreate it with:

```
brew install fileicon

osascript -e '
set targetFile to POSIX file "'"$(pwd)"'/Timelapse Builder.command" as alias
set desktopFolder to path to desktop folder
tell application "Finder"
    make new alias file to targetFile at desktopFolder
    set name of result to "Timelapse Builder.command"
end tell
'

fileicon set ~/Desktop/"Timelapse Builder.command" assets/icon.icns

osascript -e 'tell application "Finder" to set extension hidden of file (POSIX file "'"$HOME"'/Desktop/Timelapse Builder.command" as alias) to true'
```

## Using the app

1. Open the app (double-click the launcher).
2. Confirm or change the **Watch folder** — this must match where your
   camera software is saving photos.
3. Check the boxes for whatever you want:
   - **Delete RAW files** — removes each photo's RAW (CR2/CR3/etc.) once
     its matching JPEG has been processed, to save disk space.
   - **Stamp capture date/time on video frames** — burns the photo's
     capture time into the top-right corner of every frame.
4. Click **Start**. As new photos arrive, the log at the bottom shows
   progress, and `output_video.mp4` in the watch folder keeps rebuilding
   and looping in QuickTime.
5. Click **Stop** when you're done shooting.

Your folder choice and checkbox settings are remembered automatically
between launches (stored in
`~/Library/Application Support/TimelapseBuilder/config.json` — delete
that file if you ever want the app to reset to defaults).

## Terminal / advanced use

`itv.py` runs the same watcher without the GUI, using your last-saved
settings (or `--folder`, `--delete-raw`, `--overlay-timestamp` to
override them):

```
python3 itv.py --folder ~/Desktop/TL_Folder --delete-raw --overlay-timestamp
```

## Running the tests

```
python3 -m unittest discover tests
```
