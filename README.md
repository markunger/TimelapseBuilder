# TimelapseBuilder

Watches a folder for new photos from a tethered camera (via Canon EOS
Utility or similar) and automatically builds a looping timelapse video as
each new photo arrives. Optionally deletes the RAW file that accompanies
each JPEG (so the Mac's disk doesn't fill up before the camera's memory
card does), and optionally stamps each frame with its capture date/time.

## One-time setup (new Mac)

### Open Terminal

Terminal is the app that runs the commands below.
- Press **⌘ Command + Space** to open Spotlight Search.
- Type `Terminal` and press **Return**.

You'll paste each gray command block below into that window one at a
time (click inside the window, paste with **⌘V**, press **Return** to
run it, then wait for it to finish before pasting the next one).

### 1. Install Xcode Command Line Tools (gives you `git`)

```
xcode-select --install
```

This opens a graphical popup — click **Install**, agree to the license,
and wait for it to finish downloading (a few minutes) before continuing.
If it says `command line tools are already installed`, that's fine —
just move on to the next step.

**If this fails with a network error**, skip straight to downloading it
directly instead: go to
[developer.apple.com/download/all](https://developer.apple.com/download/all/)
in a browser, sign in with any free Apple ID, search "Command Line
Tools," download the `.dmg` matching your macOS version, and run that
installer by hand.

### 2. Install Homebrew (lets you install ffmpeg and Python packages)

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

This will ask you to press **Return** to confirm, and may ask for your
Mac's login password — typing a password in Terminal shows nothing on
screen (no dots, no cursor movement), that's normal, just type it and
press Return.

When it finishes, it prints a "Next steps" block with 1-3 commands to
add Homebrew to your PATH (common on newer Macs with Apple Silicon,
which includes the 2021 24" iMac) — copy and run exactly what it shows
you, which looks like:

```
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Then confirm it worked:

```
brew --version
```

You should see something like `Homebrew 4.x.x` printed — the word
"Homebrew" followed by a version number confirms it installed correctly.

### 3. Install ffmpeg and Python (with Tkinter for the GUI)

```
brew install ffmpeg python-tk
```

Homebrew may list what it's about to install and ask you to type **y**
and press **Return** to confirm before it starts downloading.

### 4. Download this project

```
git clone https://github.com/markunger/TimelapseBuilder.git ~/Projects/TimelapseBuilder
cd ~/Projects/TimelapseBuilder
```

Cloning (rather than downloading the ZIP from GitHub) preserves the
launcher's executable permission and lets you `git pull` for updates
later.

### 5. Install this project's Python dependencies

```
pip3 install --break-system-packages -r requirements.txt
```

`--break-system-packages` is needed because Homebrew's Python normally
blocks plain `pip install` to protect its own managed packages (you may
see an `externally-managed-environment` error without it). This is
fine here — it's a dedicated install for this one small project.

### 6. Point Canon EOS Utility (or your camera software) at a save folder

By default this app watches `~/Desktop/TL_Folder`. Set your camera
software's "save to" destination to that same folder (the app will
create it automatically the first time you click Start if it doesn't
exist yet — or pick a different folder from within the app).

### 7. Launch the app

Double-click **`Timelapse Builder.command`** (there's a Desktop shortcut
with a custom icon for this — see below).

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

### 8. Folder access prompt

The first time the app actually reads or writes files on your Desktop,
macOS may ask "Terminal would like to access files in your Desktop
folder" — click **OK**. If you accidentally clicked "Don't Allow" and
it's not prompting again, fix it manually: **System Settings → Privacy
& Security → Files and Folders**, then enable Desktop access for
Terminal.

## Desktop shortcut

There's a "Timelapse Builder" icon on the Desktop — a Finder alias
pointing at `Timelapse Builder.command` in this project folder, with a
custom black/white "WL/TB" icon from `assets/icon.icns` (included in
this repo, so it's identical on every machine). A plain Unix symlink
won't show the custom icon correctly on the Desktop — it has to be a
real Finder alias — so recreate it with (run this from inside the
project folder, i.e. right after step 4 above):

```
brew install fileicon

fileicon set "Timelapse Builder.command" assets/icon.icns

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

The icon must be set on **both** the real file and the Desktop alias —
if it's only set on the alias, macOS can re-derive the alias's icon
from its (uncustomized) target during an icon-cache rebuild, which
shows up as the Desktop icon reverting to a generic one after a
restart.

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
