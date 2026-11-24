# Usage guide

Step-by-step instructions, every command explained, and what to do when something goes wrong.

> فارسی: [docs/USAGE.fa.md](USAGE.fa.md)

## Contents

- [1. Before you start](#1-before-you-start)
- [2. Install the patch](#2-install-the-patch)
- [3. Check that it worked](#3-check-that-it-worked)
- [4. Keep it after updates](#4-keep-it-after-updates)
- [5. Remove the patch](#5-remove-the-patch)
- [6. Command reference](#6-command-reference)
- [7. Troubleshooting](#7-troubleshooting)
- [8. Uninstall everything](#8-uninstall-everything)

---

## 1. Before you start

| Requirement | How to check |
| --- | --- |
| Windows 10 / 11 | `winver` |
| QwenWork installed | The folder `C:\Program Files\QwenWork` exists |
| Python 3.8+ | `python --version` (or `py --version`) |
| Administrator account | Your user can approve UAC prompts |

Close QwenWork before the first run. The script can close it for you, but closing it yourself avoids losing a
chat that is still streaming.

## 2. Install the patch

### Option A — the .bat file (easiest)

1. Download this repository (**Code → Download ZIP**) and extract it anywhere.
2. Double-click **`QwenWork-RTL.bat`**.
3. Choose **`1`** (Install / update patch).
4. Accept the Windows UAC prompt.
5. Wait for `[OK] QwenWork: patch applied.` and for the app to reopen.

### Option B — the command line

```powershell
git clone https://github.com/neeM4c/qwenwork-rtl.git
cd qwenwork-rtl
python qwenwork_rtl.py --install
```

What the output looks like:

```text
QwenWork RTL + Vazir  v1.0.0

[*] QwenWork: injecting RTL patch...
[*] QwenWork: verifying archive integrity...
[OK] QwenWork: patch applied.
[*] QwenWork: restarting...

Done.
```

## 3. Check that it worked

1. Open any conversation with Persian text — it should be right-aligned in Vazirmatn.
2. Type a Persian sentence in the message box; the box should flip to right-to-left.
3. Ask for a table or a list; columns and bullets should start from the right.
4. Paste a code block; it must stay left-to-right.

You can also ask the script:

```powershell
python qwenwork_rtl.py --status
```

```text
QwenWork RTL + Vazir  v1.0.0

  QwenWork
    archive : C:\Program Files\QwenWork\<version>\resources\app.asar
    installed: True
    patched  : True
    current  : True
    running  : True

    guard    : True RTL Patch Guard
    guard log: C:\Users\<you>\AppData\Local\RTL-Patch\guard.log
    font     : embedded Vazirmatn
```

| Field | Meaning |
| --- | --- |
| `installed` | QwenWork was found on this machine. |
| `patched` | The archive contains a patch (any version). |
| `current` | It is the patch this script version produces. `False` means: run `--install` to upgrade it. |
| `running` | QwenWork is open right now. |
| `guard` | The logon guard is registered. |

## 4. Keep it after updates

Every QwenWork update replaces `app.asar`, which drops the patch. Install the guard once:

```powershell
python qwenwork_rtl.py --install-guard
```

The guard is a scheduled task named **`RTL Patch Guard`** that:

- starts at every logon with the highest privileges (no UAC prompt for you),
- wakes up every 15 seconds,
- re-applies the patch when it sees an unpatched archive and QwenWork is closed.

Verify it with `--status` (`guard: True RTL Patch Guard`) or in *Task Scheduler*. Its log lives at
`%LOCALAPPDATA%\RTL-Patch\guard.log`:

```text
2026-01-14 19:12:03 guard started (pid 12172)
2026-01-14 20:44:51 qwenwork: unpatched archive detected; applying patch
2026-01-14 20:44:53 qwenwork: patched
```

Do not want a background task? Skip this step and simply run `--install` after each update.

## 5. Remove the patch

```powershell
python qwenwork_rtl.py --restore
```

QwenWork is closed, the injected block is removed, the archive is verified, and the app reopens with its
original look. The guard can stay installed: it remembers that you asked for the original look (in
`%LOCALAPPDATA%\RTL-Patch\restored.json`) and leaves the archive alone until the next update replaces it.
To remove the guard as well:

```powershell
python qwenwork_rtl.py --remove-guard
```

## 6. Command reference

| Command | Needs admin | Description |
| --- | :---: | --- |
| `python qwenwork_rtl.py` | — | Interactive menu (default option: install). |
| `--install` / `-i` | yes | Apply, upgrade or repair the patch. Restarts QwenWork if it was open. |
| `--restore` / `-r` | yes | Remove the patch. |
| `--status` | no | Show the state of everything, changes nothing. |
| `--install-guard` | yes | Register the logon guard. |
| `--remove-guard` | yes | Unregister the guard. |
| `--watch [--silent]` | yes | Run the guard loop in the foreground; `--silent` writes to the log only. |

Add `--silent` to any command to suppress the final "Press Enter" pause (useful in scripts).

Exit codes: `0` success, `1` failure (nothing was written).

## 7. Troubleshooting

### "archive is locked"

QwenWork is still running or a helper process holds the file.

```powershell
taskkill /F /IM QwenWork.exe /T
python qwenwork_rtl.py --install
```

### "No matching app found for target: all"

QwenWork was not found in the supported folders:

```text
C:\Program Files\QwenWork
C:\Program Files (x86)\QwenWork
%LOCALAPPDATA%\Programs\QwenWork
```

Open an issue with the output of `dir "C:\Program Files\QwenWork"` and your install path.

### The patch is applied but the window looks the same

Reload the renderer with `Ctrl+R`. If the app was open during patching, restart it completely
(tray icon → Quit, then start again).

### Persian text is RTL but the font is not Vazirmatn

A more specific rule in that panel is winning. Open an issue with a screenshot — the selector list is one
block in `qwenwork_rtl.py`.

### The patch disappears after an update

That is expected: updates replace the archive. Install the guard (section 4).

### Windows Defender or an antivirus warns

The script rewrites a file under `Program Files` and registers a scheduled task, which some scanners flag.
You can read every line — it is one plain Python file and it never downloads anything.

### Python is not recognised

Install it from [python.org](https://www.python.org/downloads/windows/) and tick **Add python.exe to PATH**.
On machines with the Microsoft Store stub, `py --version` may work while `python` does not.

## 8. Uninstall everything

```powershell
python qwenwork_rtl.py --restore
python qwenwork_rtl.py --remove-guard
```

Then delete the extracted folder and, if you want, the state directory:

```powershell
Remove-Item "$env:LOCALAPPDATA\RTL-Patch" -Recurse -Force
```

Nothing else is left behind: no services, no registry keys, no files inside QwenWork's folder.
