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

Each step below has a gray command block. For each one: click inside
the Terminal window, paste the command (**⌘V**), and press **Return**
to run it. Wait until you see the "you'll know this step is done when"
line for that step before moving to the next one.

### 1. Install Xcode Command Line Tools (gives you `git`)

Copy the command below, paste it into Terminal, and press **Return**:
```
xcode-select --install
```

**You'll know this step is done when:** a graphical popup appears —
click **Install**, agree to the license, and wait for it to finish
downloading (a few minutes). If Terminal instead immediately shows
`xcode-select: error: command line tools are already installed`,
that's fine too — just move on to the next step.

> **You may also see a generic malware/security warning pop up**
> (seen on macOS Tahoe) when running this command. It's safe to
> dismiss and doesn't stop the install from continuing.

> **If this fails with a network error:** skip straight to downloading
> it directly instead — go to
> [developer.apple.com/download/all](https://developer.apple.com/download/all/)
> in a browser, sign in with any free Apple ID, search "Command Line
> Tools," download the `.dmg` matching your macOS version, and run
> that installer by hand.

### 2. Install Homebrew (lets you install ffmpeg and Python packages)

Copy the command below, paste it into Terminal, and press **Return**:
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

This will ask you to press **Return** again to confirm, and may ask
for your Mac's login password — typing a password in Terminal shows
nothing on screen (no dots, no cursor movement), that's normal, just
type it and press Return.

**You'll know this step is done when:** Terminal prints
`Installation successful!` and returns to a normal prompt line.

It also prints a "Next steps" block with 1-3 commands to add Homebrew
to your PATH (common on Apple Silicon Macs, which includes the 2021
24" iMac). Copy and paste exactly what it shows you — it will look
like the two lines below — and press **Return**:
```
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**You'll know this step is done when:** Terminal returns to a normal
prompt line with no error message (these two commands print nothing
on success — that's expected, not a sign of a problem).

Then confirm Homebrew is really installed. Copy the command below,
paste it into Terminal, and press **Return**:
```
brew --version
```

**You'll know this step is done when:** you see something like
`Homebrew 4.x.x` printed — the word "Homebrew" followed by a version
number confirms it installed correctly.

### 3. Install ffmpeg and Python (with Tkinter for the GUI)

Copy the command below, paste it into Terminal, and press **Return**:
```
brew install ffmpeg python-tk
```

Homebrew may list what it's about to install and ask you to type **y**
and press **Return** to confirm before it starts downloading.

**You'll know this step is done when:** Terminal returns to a normal
prompt line with no errors (this can take a few minutes).

### 4. Download this project

Copy the command below, paste it into Terminal, and press **Return**:
```
git clone https://github.com/markunger/TimelapseBuilder.git ~/Projects/TimelapseBuilder
cd ~/Projects/TimelapseBuilder
```

**You'll know this step is done when:** Terminal shows `Cloning into
'.../TimelapseBuilder'...` followed by a short summary, and the prompt
changes to show you're now inside the `TimelapseBuilder` folder.

> **For reference (not required to know):** `git clone` downloads a
> fresh copy of the project one time. If the project ever gets
> updated later, you don't clone again — you run `git pull` from
> inside this same folder to fetch just the changes.

### 5. Install this project's Python dependencies

Copy the command below, paste it into Terminal, and press **Return**:
```
pip3 install --break-system-packages -r requirements.txt
```

**You'll know this step is done when:** Terminal shows a line like
`Successfully installed pillow-... watchdog-...` and returns to a
normal prompt.

> **For reference (not required to know):** `--break-system-packages`
> is needed because Homebrew's Python normally blocks a plain `pip
> install` to protect its own managed packages (you may see an
> `externally-managed-environment` error without it). That's fine
> here — it's a dedicated install for this one small project.

### 6. Add the Desktop shortcut

This creates a "Timelapse Builder" icon on your Desktop with a custom
black/white icon, so you can launch the app without navigating to
this project folder every time.

Copy the whole block below, paste it into Terminal, and press
**Return** (run this from inside the project folder, i.e. right after
step 5 above):
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

**You'll know this step is done when:** a black "Timelapse Builder"
icon appears on your Desktop.

> **For reference (not required to know):** the icon is deliberately
> set on both the real file and the Desktop shortcut — if it's only
> set on the shortcut, macOS can revert the shortcut's icon to a
> generic one after a restart. If that ever happens (most likely
> after a future `git pull` updates the launcher file), delete the
> shortcut with `rm ~/Desktop/"Timelapse Builder.command"` and re-run
> this whole step again — a restart alone won't fix it.

### 7. Point Canon EOS Utility (or your camera software) at the save folder

By default this app watches `~/Desktop/TL_Folder`. Set your camera
software's "save to" destination to that same folder (the app will
create it automatically the first time you click Start if it doesn't
exist yet — or you can pick a different folder from within the app
once it's open).

There's no Terminal command for this step — it's done inside your
camera software's own settings/preferences.

### 8. Launch the app

Double-click the **Timelapse Builder** icon on your Desktop (the one
created in step 6).

The **first time** you do this, macOS will likely refuse and say the
file is from an "unidentified developer." This is normal for any
script you write yourself rather than download from the App Store.
To get past it, just this once:
- **Right-click** (or Control-click) the **Timelapse Builder** Desktop
  icon and choose **Open** from the menu (don't just double-click).
- Click **Open Anyway** in the dialog that appears. On newer versions
  of macOS this button appears under **System Settings → Privacy &
  Security**, near the bottom of the page.
- After this first time, plain double-clicking will work normally.

**You'll know this step is done when:** a Terminal window briefly
opens behind it, then the TimelapseBuilder app window appears with a
Watch folder field, two checkboxes, and a Start button.

### 9. Folder access prompt

The first time the app actually reads or writes files on your Desktop,
macOS may ask "Terminal would like to access files in your Desktop
folder" — click **OK**. If you accidentally clicked "Don't Allow" and
it's not prompting again, fix it manually: **System Settings → Privacy
& Security → Files and Folders**, then enable Desktop access for
Terminal.

## Using the app

1. Open the app (double-click the **Timelapse Builder** Desktop icon).
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

## Shutting down the app

1. If the app is actively watching, click **Stop** (optional — closing
   the window does this safely too, automatically).
2. Close the TimelapseBuilder window (click the red button in the
   top-left corner, or press **⌘Q** while it's focused).
3. A Terminal window is still open behind it — that's normal, it's
   what actually ran the app. You'll know it's safe to close because
   it prints `TimelapseBuilder closed.` once the app window is gone.
   Click into that Terminal window and close it too (**⌘W**, or **⌘Q**
   to quit Terminal entirely if it's the only window open).

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
