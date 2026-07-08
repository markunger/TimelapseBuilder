# TimelapseBuilder

Watches a folder for new photos from a tethered camera (via Canon EOS
Utility or similar) and automatically builds a looping timelapse video as
each new photo arrives. Optionally deletes the RAW file that accompanies
each JPEG (so the Mac's disk doesn't fill up before the camera's memory
card does), and optionally stamps each frame with its capture date/time.

## One-time setup (new Mac)

This path avoids needing `git` or an Apple ID for most of the setup.
The one exception is ffmpeg (step 4), which still uses Homebrew — the
most standard/trusted way to get ffmpeg on a Mac — and Homebrew itself
needs Xcode Command Line Tools (a free, no-login install, but one that
occasionally fails with a network error on some machines; see
[Troubleshooting](#troubleshooting-xcode-command-line-tools-network-error)
below if that happens to you).

### Open Terminal

Terminal is the app that runs some of the commands below.
- Press **⌘ Command + Space** to open Spotlight Search.
- Type `Terminal` and press **Return**.

You'll paste each gray command block below into that window one at a
time (click inside the window, paste with **⌘V**, press **Return** to
run it, then wait for it to finish before pasting the next one).

### 1. Download this project (no git needed)

- Go to https://github.com/markunger/TimelapseBuilder in a browser.
- Click the green **Code** button → **Download ZIP**.
- Double-click the downloaded zip file in your Downloads folder to
  unzip it (Finder does this automatically).
- In Terminal, move it somewhere permanent and go into it:
  ```
  mkdir -p ~/Projects
  mv ~/Downloads/TimelapseBuilder-main ~/Projects/TimelapseBuilder
  cd ~/Projects/TimelapseBuilder
  ```

(Already comfortable with git? See [Alternative: using git](#alternative-using-git-instead-of-downloading-a-zip) at the bottom instead.)

### 2. Install Python (with Tkinter for the GUI)

- Download the macOS installer from
  [python.org/downloads](https://www.python.org/downloads/) and run it
  — a normal double-click `.pkg` installer, no Apple ID needed.
- Back in Terminal, confirm it worked:
  ```
  python3 --version
  python3 -m tkinter
  ```
  A small test window should pop up for the second command (close it,
  that's just confirming Tkinter works). If either command says
  "command not found," quit and reopen Terminal so it picks up the
  freshly-installed `python3`, then try again.

### 3. Install this project's Python packages

```
pip3 install -r requirements.txt
```

### 4. Install ffmpeg (via Homebrew)

Homebrew needs Xcode Command Line Tools first:
```
xcode-select --install
```
Click **Install** in the popup, agree to the license, and wait for it
to finish (a few minutes) before continuing. If it says "command line
tools are already installed," just move on. **If this fails with a
network error**, see
[Troubleshooting](#troubleshooting-xcode-command-line-tools-network-error)
below before continuing.

Then install Homebrew:
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
This asks you to press **Return** to confirm, and may ask for your
Mac's login password — typing a password in Terminal shows nothing on
screen (no dots, no cursor movement), that's normal. When it finishes,
it prints a "Next steps" block with 1-3 commands to add Homebrew to
your PATH (common on Apple Silicon Macs, which includes the 2021 24"
iMac) — copy and run exactly what it shows you, which looks like:
```
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```
Then confirm it worked, and install ffmpeg:
```
brew --version
brew install ffmpeg
```

### 5. Point Canon EOS Utility (or your camera software) at a save folder

By default this app watches `~/Desktop/TL_Folder`. Set your camera
software's "save to" destination to that same folder (the app will
create it automatically the first time you click Start if it doesn't
exist yet — or pick a different folder from within the app).

### 6. Launch the app

As a safety net, make sure the launcher is executable (this should
already be true after unzipping, but costs nothing to confirm):
```
chmod +x "Timelapse Builder.command"
```

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

### 7. Folder access prompt

The first time the app actually reads or writes files on your Desktop,
macOS may ask "Terminal would like to access files in your Desktop
folder" — click **OK**. If you accidentally clicked "Don't Allow" and
it's not prompting again, fix it manually: **System Settings → Privacy
& Security → Files and Folders**, then enable Desktop access for
Terminal.

## Troubleshooting: Xcode Command Line Tools network error

If `xcode-select --install` fails with a network error — even on a
fully up-to-date macOS, not just an old one — try these in order:

1. **Just retry.** Apple's download servers are sometimes flaky.
2. **Check the date/time is correct and set automatically**
   (System Settings → General → Date & Time). A wrong clock causes TLS
   failures that show up as a generic network error.
3. **Check for a non-Apple Software Update server** (common on
   managed/work Macs):
   ```
   defaults read /Library/Preferences/com.apple.SoftwareUpdate CatalogURL
   ```
   If this prints a URL that isn't Apple's own servers, that's likely
   why it's failing.
4. **Check if the Mac is enrolled in MDM with restrictions:**
   ```
   profiles status -type enrollment
   ```
5. **Get the actual underlying error** (the installer's message is
   usually vague):
   ```
   curl -Iv https://swcdn.apple.com 2>&1 | tail -30
   ```
6. **As a last resort**, download Command Line Tools manually (this
   does require signing in with a free Apple ID) from
   [developer.apple.com/download/all](https://developer.apple.com/download/all/) —
   search "Command Line Tools," find the version matching your macOS
   release, and install the `.dmg` by hand.

## Desktop shortcut

There's a "Timelapse Builder" icon on the Desktop — a Finder alias
pointing at `Timelapse Builder.command` in this project folder, with a
custom black/white "WL/TB" icon from `assets/icon.icns` (included in
this repo, so it's identical on every machine). A plain Unix symlink
won't show the custom icon correctly on the Desktop — it has to be a
real Finder alias — so recreate it with (run this from inside the
project folder, i.e. right after step 1 above):

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

## Alternative: using git instead of downloading a ZIP

If you already have (or don't mind installing) Xcode Command Line
Tools and git, cloning is a bit nicer than a ZIP download — it lets you
`git pull` for updates instead of re-downloading each time:

```
git clone https://github.com/markunger/TimelapseBuilder.git ~/Projects/TimelapseBuilder
cd ~/Projects/TimelapseBuilder
```

You can also skip the python.org installer and get Python + Tkinter
through Homebrew instead:

```
brew install python-tk
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
