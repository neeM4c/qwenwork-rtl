#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QwenWork RTL + Vazir patch.

    Makes Persian chat text right-to-left and switches the UI font to Vazirmatn.

  * DeepAI Code : right-to-left rendering of Persian chat text.
  * QwenWork    : right-to-left rendering + Vazir (Vazirmatn) font, embedded.

Nothing depends on hashed asset names, so the patch keeps working after app
updates, and every packed file hash is verified before the archive is swapped.

Usage:
    python rtl_patcher.py                         (interactive menu)
    python rtl_patcher.py --install               (patch every installed app)
    python rtl_patcher.py --target qwenwork --install
    python rtl_patcher.py --restore               (remove the patch)
    python rtl_patcher.py --status
    python rtl_patcher.py --install-guard         (auto-repair after updates)
    python rtl_patcher.py --remove-guard
    python rtl_patcher.py --watch                 (background guard, silent)
"""

import base64
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import time

STATE_DIR = os.path.expandvars(r"%LOCALAPPDATA%\RTL-Patch")
GUARD_SCRIPT = os.path.join(STATE_DIR, os.path.basename(os.path.abspath(__file__)))
GUARD_LOG = os.path.join(STATE_DIR, "guard.log")
STARTUP_DIR = os.path.expandvars(
    r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
)
STARTUP_FILE = os.path.join(STARTUP_DIR, "RTL-Patch-Guard.vbs")
LEGACY_STARTUP = os.path.join(STARTUP_DIR, "DeepAI-RTL-Guard.vbs")
TASK_NAME = "RTL Patch Guard"

MARK_START = "<!-- RTL-PATCH-START -->"
MARK_END = "<!-- RTL-PATCH-END -->"
# markers written by older builds; stripped so a stale patch never stacks up
LEGACY_START = "<!-- DEEPAI-RTL-START -->"
LEGACY_END = "<!-- DEEPAI-RTL-END -->"
TOOL_VERSION = "1.0.0"

RTL_VERSION = 5
VERSION_TOKEN = "<!-- RTL-PATCH-VERSION:%d -->" % RTL_VERSION


# ---------------------------------------------------------------------------
# Vazir font (embedded as base64, so the app does not depend on system fonts)
# ---------------------------------------------------------------------------

FONT_CANDIDATES = [
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\Vazirmatn[wght].ttf"),
    os.path.expandvars(r"%WINDIR%\Fonts\Vazirmatn[wght].ttf"),
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\Vazirmatn-RD[wght].ttf"),
    os.path.expandvars(r"%WINDIR%\Fonts\Vazirmatn-RD[wght].ttf"),
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\Vazirmatn-Regular.ttf"),
]

_FONT_B64_CACHE = None


def font_base64():
    global _FONT_B64_CACHE
    if _FONT_B64_CACHE is not None:
        return _FONT_B64_CACHE
    for path in FONT_CANDIDATES:
        try:
            if os.path.exists(path) and os.path.getsize(path) > 20000:
                with open(path, "rb") as f:
                    _FONT_B64_CACHE = base64.b64encode(f.read()).decode("ascii")
                return _FONT_B64_CACHE
        except Exception:
            continue
    _FONT_B64_CACHE = ""
    return _FONT_B64_CACHE


# ---------------------------------------------------------------------------
# QwenWork snippet (direction + Vazir font)
# ---------------------------------------------------------------------------

QWEN_CSS = r"""
    <style id="qwenwork-rtl-style">
/*__FONT_FACE__*/
      :root,
      :root[data-os] {
        --qw-font-family-sans: "Qwen Vazir", "Vazirmatn", "Vazir", -apple-system,
          BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC",
          "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
        --font-sans: var(--qw-font-family-sans);
        --font-ui: var(--qw-font-family-sans);
        --font-family-sans: var(--qw-font-family-sans);
        --font-family-base: var(--qw-font-family-sans);
      }
      .welcome-title,
      .login-title,
      .qw-session-home-welcome-title,
      [data-slot="session-home-welcome"] {
        font-family: var(--qw-font-family-sans) !important;
        font-variation-settings: normal !important;
      }
      [dir="rtl"] {
        text-align: right;
      }
      td[dir="rtl"],
      th[dir="rtl"] {
        text-align: right !important;
      }
      [dir="rtl"] pre,
      [dir="rtl"] code,
      pre[dir="rtl"],
      code[dir="rtl"],
      .qd-markdown-code-block,
      [data-slot="message-rich-code-block"],
      [data-slot="message-rich-math-block"],
      .katex {
        direction: ltr !important;
        unicode-bidi: isolate !important;
        text-align: left !important;
      }
      [dir="rtl"] blockquote,
      blockquote[dir="rtl"] {
        border-left-width: 0 !important;
        border-right-width: 2px !important;
        padding-left: 0 !important;
        padding-right: 0.85rem !important;
      }
    </style>
"""

QWEN_JS = r"""
    <script id="qwenwork-rtl-observer">
      (() => {
        if (window.__qwenRtlPatch) return;
        window.__qwenRtlPatch = true;

        const PERSIAN_RE = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
        const LATIN_RE = /[A-Za-z\u00C0-\u024F]/;
        const SKIP_SEL = [
          "pre",
          "code",
          "kbd",
          "samp",
          "math",
          "svg",
          ".katex",
          ".cm-editor",
          ".monaco-editor",
          ".xterm",
          '[data-slot="message-rich-code-block"]',
          '[data-slot="message-rich-math-block"]',
          '[contenteditable="true"]'
        ].join(",");
        const BLOCK_SEL = [
          "p",
          "li",
          "h1",
          "h2",
          "h3",
          "h4",
          "h5",
          "h6",
          "blockquote",
          "dd",
          "dt",
          "td",
          "th",
          "ul",
          "ol",
          "table",
          ".qw-im-text",
          '[data-slot="session-user-text"]',
          '[data-slot="message-rich-text"]',
          '[data-slot="message-body"]'
        ].join(",");

        function firstStrong(text) {
          if (!text) return null;
          let t = text.length > 4000 ? text.slice(0, 4000) : text;
          t = t.replace(/[\x60][^\x60]*[\x60]/g, " ");
          for (let i = 0; i < t.length; i += 1) {
            const ch = t.charAt(i);
            if (PERSIAN_RE.test(ch)) return "rtl";
            if (LATIN_RE.test(ch)) return "ltr";
          }
          return null;
        }

        function mark(el, dir) {
          if (el.getAttribute("dir") !== dir) el.setAttribute("dir", dir);
        }

        function applyBlock(el) {
          if (!el || el.nodeType !== 1) return;
          if (el.closest(SKIP_SEL)) return;
          const dir = firstStrong(el.textContent || "");
          if (dir) mark(el, dir);
        }

        function scan(root) {
          if (!root) return;
          if (root.nodeType === 1) {
            if (root.matches && root.matches(BLOCK_SEL)) applyBlock(root);
            if (root.querySelectorAll) {
              const list = root.querySelectorAll(BLOCK_SEL);
              for (let i = 0; i < list.length; i += 1) applyBlock(list[i]);
            }
          }
        }

        let scheduled = false;
        const pending = new Set();
        function scheduleScan(node) {
          pending.add(node && node.nodeType === 1 ? node : document.body);
          if (pending.size > 250) {
            pending.clear();
            pending.add(document.body);
          }
          if (scheduled) return;
          scheduled = true;
          requestAnimationFrame(() => {
            scheduled = false;
            const items = Array.from(pending);
            pending.clear();
            for (const item of items) scan(item);
          });
        }

        function applyEditable(el) {
          if (!el || el.nodeType !== 1 || el.disabled || el.readOnly) return;
          const value =
            typeof el.value === "string" ? el.value : el.textContent || "";
          const dir = firstStrong(value);
          if (dir) mark(el, dir);
        }

        document.addEventListener(
          "input",
          (event) => {
            const el = event.target;
            if (!el || el.nodeType !== 1) return;
            if (el.isContentEditable) {
              applyEditable(el);
              return;
            }
            if (el.tagName === "TEXTAREA") {
              applyEditable(el);
              return;
            }
            if (
              el.tagName === "INPUT" &&
              (!el.type || el.type === "text" || el.type === "search")
            ) {
              applyEditable(el);
            }
          },
          true
        );

        const start = () => {
          scan(document.body);
          document
            .querySelectorAll('[contenteditable="true"], textarea')
            .forEach((el) => applyEditable(el));
          const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
              if (mutation.type === "characterData") {
                const parent = mutation.target.parentElement;
                if (parent) scheduleScan(parent);
              } else if (mutation.type === "childList") {
                for (const node of mutation.addedNodes) {
                  if (node.nodeType === 1) scheduleScan(node);
                }
                scheduleScan(mutation.target);
              }
            }
          });
          observer.observe(document.documentElement, {
            childList: true,
            subtree: true,
            characterData: true,
          });
        };

        if (document.readyState === "loading") {
          document.addEventListener("DOMContentLoaded", start, { once: true });
        } else {
          start();
        }
      })();
    </script>
"""


def qwenwork_snippet():
    font = font_base64()
    if font:
        face = (
            '      @font-face {\n'
            '        font-family: "Qwen Vazir";\n'
            '        src: url(data:font/ttf;base64,' + font + ') format("truetype");\n'
            "        font-weight: 100 900;\n"
            "        font-style: normal;\n"
            "        font-display: swap;\n"
            "      }"
        )
    else:
        face = ""
    css = QWEN_CSS.replace("/*__FONT_FACE__*/", face)
    return "\n".join(
        [
            MARK_START,
            "    " + VERSION_TOKEN,
            css.strip("\n"),
            QWEN_JS.strip("\n"),
            MARK_END,
        ]
    )


# ---------------------------------------------------------------------------
# asar helpers
# ---------------------------------------------------------------------------

def read_header(f):
    u1, u2, u3, u4 = struct.unpack("<IIII", f.read(16))
    data_base = 8 + u2
    hdr_json = f.read(u4).decode("utf-8")
    return json.loads(hdr_json), data_base


def entry_node(hdr, parts):
    node = hdr
    for part in parts:
        node = node["files"][part]
    return node


def read_entry(asar_path, parts):
    with open(asar_path, "rb") as f:
        hdr, base = read_header(f)
        info = entry_node(hdr, parts)
        f.seek(base + int(info["offset"]))
        return f.read(int(info["size"]))


def compute_integrity(data):
    block_size = 4 * 1024 * 1024
    blocks = [
        hashlib.sha256(data[i : i + block_size]).hexdigest()
        for i in range(0, len(data), block_size)
    ]
    if not blocks:
        blocks.append(hashlib.sha256(b"").hexdigest())
    return {
        "algorithm": "SHA256",
        "hash": hashlib.sha256(data).hexdigest(),
        "blockSize": block_size,
        "blocks": blocks,
    }


def build_header_block(header_dict):
    json_bytes = json.dumps(
        header_dict, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    str_len = len(json_bytes)
    pad_len = (4 - (str_len % 4)) % 4
    padded = json_bytes + (b"\x00" * pad_len)
    u3 = 4 + len(padded)
    u2 = 4 + u3
    return struct.pack("<IIII", 4, u2, u3, str_len) + padded


def shift_offsets(node, threshold, delta):
    for _, item in node.get("files", {}).items():
        if "files" in item:
            shift_offsets(item, threshold, delta)
        elif "offset" in item and not item.get("unpacked", False):
            offset = int(item["offset"])
            if offset > threshold:
                item["offset"] = str(offset + delta)


def strip_snippet(html):
    changed = True
    while changed:
        changed = False
        for start, end in ((MARK_START, MARK_END), (LEGACY_START, LEGACY_END)):
            index = html.find(start)
            if index < 0:
                continue
            stop = html.find(end, index)
            if stop < 0:
                continue
            stop += len(end)
            if html[stop : stop + 1] == "\n":
                stop += 1
            html = html[:index] + html[stop:]
            changed = True
    return html


def html_is_patched(html):
    return MARK_START in html or LEGACY_START in html


def html_is_current(html):
    return MARK_START in html and VERSION_TOKEN in html


def rewrite_asar(asar_path, parts, transform):
    """Rewrite one packed entry. Returns the temp path, or None if unchanged."""
    with open(asar_path, "rb") as f:
        hdr, base = read_header(f)
        info = entry_node(hdr, parts)
        if info.get("unpacked", False):
            raise RuntimeError("entry is unpacked: " + "/".join(parts))
        old_offset = int(info["offset"])
        old_size = int(info["size"])
        f.seek(base + old_offset)
        old_bytes = f.read(old_size)
        new_bytes = transform(old_bytes)
        if new_bytes is None or new_bytes == old_bytes:
            return None

        delta = len(new_bytes) - old_size
        info["size"] = len(new_bytes)
        info["integrity"] = compute_integrity(new_bytes)
        shift_offsets(hdr, old_offset, delta)
        header_block = build_header_block(hdr)

        tmp_file = asar_path + (".rtl-tmp-%d" % os.getpid())
        try:
            with open(tmp_file, "wb") as out:
                out.write(header_block)
                f.seek(base)
                remaining = old_offset
                while remaining > 0:
                    chunk = f.read(min(4 * 1024 * 1024, remaining))
                    if not chunk:
                        raise RuntimeError("unexpected end of archive")
                    out.write(chunk)
                    remaining -= len(chunk)
                out.write(new_bytes)
                f.seek(base + old_offset + old_size)
                while True:
                    chunk = f.read(4 * 1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
        except Exception:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            raise
    return tmp_file


def verify_asar(asar_path, parts, expect_patched):
    checked = [0]
    with open(asar_path, "rb") as f:
        hdr, base = read_header(f)

        def walk(node):
            for _, item in node.get("files", {}).items():
                if "files" in item:
                    walk(item)
                    continue
                if item.get("unpacked", False):
                    continue
                expected = (item.get("integrity") or {}).get("hash")
                if not expected:
                    continue
                f.seek(base + int(item["offset"]))
                content = f.read(int(item["size"]))
                actual = hashlib.sha256(content).hexdigest()
                checked[0] += 1
                if actual != expected:
                    raise RuntimeError(
                        "Hash mismatch (%s != %s)" % (actual[:12], expected[:12])
                    )

        walk(hdr)

    if checked[0] < 100:
        raise RuntimeError("Unexpected archive structure; verification aborted.")

    html = read_entry(asar_path, parts).decode("utf-8", "replace")
    if expect_patched and not html_is_current(html):
        raise RuntimeError("Patched entry was not found in the new archive.")
    if not expect_patched and html_is_patched(html):
        raise RuntimeError("Patch markers are still present after restore.")
    print("[OK] SHA-256 verified for %d files." % checked[0])


# ---------------------------------------------------------------------------
# targets
# ---------------------------------------------------------------------------

class Target(object):
    key = ""
    label = ""
    entry = ("index.html",)

    def asar_path(self):
        raise NotImplementedError

    def exe_path(self):
        raise NotImplementedError

    def launcher_path(self):
        return self.exe_path()

    def process_names(self):
        return []

    def snippet(self):
        raise NotImplementedError

    def available(self):
        try:
            path = self.asar_path()
            return bool(path) and os.path.exists(path)
        except Exception:
            return False

    def is_patched(self):
        html = read_entry(self.asar_path(), self.entry).decode("utf-8", "replace")
        return html_is_patched(html)

    def is_current(self):
        html = read_entry(self.asar_path(), self.entry).decode("utf-8", "replace")
        return html_is_current(html)

    def is_running(self):
        for name in self.process_names():
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq " + name, "/NH"],
                capture_output=True,
                text=True,
                errors="replace",
            )
            if name.lower() in (result.stdout or "").lower():
                return True
        return False

    def stop(self):
        if not self.is_running():
            return False
        print("[*] Closing %s to unlock the archive..." % self.label)
        for name in self.process_names():
            subprocess.run(["taskkill", "/F", "/IM", name, "/T"], capture_output=True)
        for _ in range(30):
            if not self.is_running():
                break
            time.sleep(0.5)
        time.sleep(1.0)
        return True

    def start(self):
        # An inherited ELECTRON_RUN_AS_NODE turns the app into a plain node
        # process that exits immediately, so it must never reach the app.
        env = {
            key: value
            for key, value in os.environ.items()
            if key.upper() not in ("ELECTRON_RUN_AS_NODE", "ELECTRON_NO_ATTACH_CONSOLE")
        }
        for path in (self.launcher_path(), self.exe_path()):
            if path and os.path.exists(path):
                print("[*] Starting %s..." % self.label)
                subprocess.Popen([path], close_fds=True, env=env)
                return True
        return False


class QwenWorkTarget(Target):
    key = "qwenwork"
    label = "QwenWork"
    entry = ("out", "renderer", "index.html")

    ROOTS = [
        r"C:\Program Files\QwenWork",
        r"C:\Program Files (x86)\QwenWork",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\QwenWork"),
    ]

    def locate(self):
        for root in self.ROOTS:
            if not os.path.isdir(root):
                continue
            versions = []
            config = os.path.join(root, "updater.cfg")
            if os.path.exists(config):
                try:
                    with open(config, "r", encoding="utf-8-sig") as f:
                        versions.append(json.load(f).get("currentVersion"))
                except Exception:
                    pass
            try:
                found = [
                    name
                    for name in os.listdir(root)
                    if os.path.isdir(os.path.join(root, name, "resources"))
                ]
                found.sort(reverse=True)
                versions.extend(found)
            except Exception:
                pass
            for version in versions:
                if not version:
                    continue
                folder = os.path.join(root, version)
                asar = os.path.join(folder, "resources", "app.asar")
                if os.path.exists(asar):
                    return folder, asar
        return None, None

    def asar_path(self):
        return self.locate()[1] or ""

    def exe_path(self):
        folder = self.locate()[0]
        return os.path.join(folder, "QwenWork.exe") if folder else ""

    def launcher_path(self):
        return self.exe_path()

    def process_names(self):
        return ["QwenWork.exe", "qwenworkhelper.exe"]

    def snippet(self):
        return qwenwork_snippet()


TARGETS = [QwenWorkTarget()]


def select_targets(requested):
    if not requested or requested == "all":
        return [t for t in TARGETS if t.available()]
    keys = [k.strip().lower() for k in requested.split(",") if k.strip()]
    chosen = []
    for key in keys:
        for target in TARGETS:
            if target.key == key:
                chosen.append(target)
    return chosen


# ---------------------------------------------------------------------------
# install / restore
# ---------------------------------------------------------------------------

def can_write(path):
    try:
        with open(path, "r+b"):
            return True
    except OSError:
        return False


RESTORE_STATE = os.path.join(STATE_DIR, "restored.json")


def _archive_stamp(path):
    try:
        st = os.stat(path)
        return [st.st_mtime_ns, st.st_size]
    except OSError:
        return None


def _restore_state():
    try:
        with open(RESTORE_STATE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def mark_restored(asar, restored=True):
    """Remember that the user asked for the original look, so the guard stays out."""
    data = _restore_state()
    stamp = _archive_stamp(asar)
    if restored and stamp:
        data[asar] = stamp
    else:
        data.pop(asar, None)
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(RESTORE_STATE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def was_restored(asar):
    """True while the archive is untouched since the last --restore."""
    stamp = _archive_stamp(asar)
    return bool(stamp) and _restore_state().get(asar) == stamp


def install_target(target):
    asar = target.asar_path()
    if not asar or not os.path.exists(asar):
        print("[!] %s: archive not found." % target.label)
        return False
    if not can_write(asar):
        print("[!] %s: archive is locked. Close the app and try again." % target.label)
        return False
    if target.is_current():
        print("[OK] %s: patch already installed and up to date." % target.label)
        return False

    snippet = target.snippet()

    def transform(data):
        html = strip_snippet(data.decode("utf-8"))
        if "</head>" not in html:
            raise RuntimeError("Could not find </head> in " + "/".join(target.entry))
        return html.replace("</head>", snippet + "\n</head>", 1).encode("utf-8")

    print("[*] %s: injecting RTL patch..." % target.label)
    tmp_file = rewrite_asar(asar, target.entry, transform)
    if not tmp_file:
        print("[OK] %s: nothing to change." % target.label)
        return False
    try:
        print("[*] %s: verifying archive integrity..." % target.label)
        verify_asar(tmp_file, target.entry, expect_patched=True)
        os.replace(tmp_file, asar)
    except Exception:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        raise
    mark_restored(asar, False)
    print("[OK] %s: patch installed." % target.label)
    return True


def restore_target(target):
    asar = target.asar_path()
    if not asar or not os.path.exists(asar):
        print("[!] %s: archive not found." % target.label)
        return False
    if not can_write(asar):
        print("[!] %s: archive is locked. Close the app and try again." % target.label)
        return False
    if not target.is_patched():
        print("[OK] %s: no patch to remove." % target.label)
        return False

    def transform(data):
        return strip_snippet(data.decode("utf-8")).encode("utf-8")

    print("[*] %s: removing the patch..." % target.label)
    tmp_file = rewrite_asar(asar, target.entry, transform)
    if not tmp_file:
        print("[OK] %s: nothing to change." % target.label)
        return False
    try:
        verify_asar(tmp_file, target.entry, expect_patched=False)
        os.replace(tmp_file, asar)
    except Exception:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        raise
    mark_restored(asar, True)
    print("[OK] %s: original rendering restored." % target.label)
    return True


def run(mode, targets):
    applied = []
    error = None
    for target in targets:
        # never restart the app just to tell the user it is already done
        if mode == "restore" and not target.is_patched():
            print("[OK] %s: original files already in place." % target.label)
            continue
        if mode != "restore" and target.is_current():
            print("[OK] %s: patch already installed and up to date." % target.label)
            continue

        was_running = target.stop()
        try:
            changed = restore_target(target) if mode == "restore" else install_target(target)
            if changed:
                applied.append(target)
        except Exception as exc:
            error = exc
            print("[!] %s: %s" % (target.label, exc))
        finally:
            if was_running:
                target.start()
        if error is not None:
            return applied, error
    return applied, error


# ---------------------------------------------------------------------------
# guard (auto-repair after updates)
# ---------------------------------------------------------------------------

def log(message):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        if os.path.exists(GUARD_LOG) and os.path.getsize(GUARD_LOG) > 1000000:
            os.remove(GUARD_LOG)
        with open(GUARD_LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + message + "\n")
    except Exception:
        pass


def watch(silent=True):
    os.makedirs(STATE_DIR, exist_ok=True)
    if silent or sys.stdout is None:
        try:
            stream = open(GUARD_LOG, "a", encoding="utf-8", buffering=1)
            sys.stdout = stream
            sys.stderr = stream
        except Exception:
            pass
    log("guard started (pid %d)" % os.getpid())
    time.sleep(12)

    while True:
        for target in TARGETS:
            try:
                asar = target.asar_path()
                if not asar or not os.path.exists(asar):
                    continue
                if target.is_current():
                    continue
                if was_restored(asar):
                    # user asked for the original look and nothing changed since
                    continue
                if target.is_running():
                    continue
                if not can_write(asar):
                    continue
                log("%s: unpatched archive detected; applying patch" % target.key)
                changed = install_target(target)
                log("%s: %s" % (target.key, "patched" if changed else "nothing to do"))
            except Exception as exc:
                log("%s: failed: %r" % (target.key, exc))
        time.sleep(15)


def _terminate_watchers(markers):
    for marker in markers:
        script = (
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.CommandLine -like '*%s*' -and $_.ProcessId -ne %d } | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
            % (marker, os.getpid())
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
        )


def install_guard():
    os.makedirs(STATE_DIR, exist_ok=True)
    shutil.copy2(os.path.abspath(__file__), GUARD_SCRIPT)

    pythonw = sys.executable
    candidate = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if os.path.exists(candidate):
        pythonw = candidate

    action = '"%s" "%s" --watch --silent' % (pythonw, GUARD_SCRIPT)
    created = subprocess.run(
        [
            "schtasks",
            "/Create",
            "/TN",
            TASK_NAME,
            "/SC",
            "ONLOGON",
            "/RL",
            "HIGHEST",
            "/F",
            "/TR",
            action,
        ],
        capture_output=True,
        text=True,
        errors="replace",
    )

    if os.path.exists(LEGACY_STARTUP):
        try:
            os.remove(LEGACY_STARTUP)
        except Exception:
            pass

    _terminate_watchers(["RTL-Patch", "DeepAI-RTL"])
    time.sleep(0.5)

    if created.returncode == 0:
        subprocess.run(["schtasks", "/Run", "/TN", TASK_NAME], capture_output=True)
        print("[OK] Auto-repair guard installed as a scheduled task:")
        print("     " + TASK_NAME + " (runs elevated at every logon)")
    else:
        # Fallback: startup shortcut, only usable when the folders are writable.
        os.makedirs(STARTUP_DIR, exist_ok=True)
        vbs = (
            'Set sh = CreateObject("WScript.Shell")\r\n'
            'sh.Run """{py}"" ""{script}"" --watch --silent", 0, False\r\n'
        ).format(py=pythonw, script=GUARD_SCRIPT)
        with open(STARTUP_FILE, "w", encoding="utf-8") as f:
            f.write(vbs)
        flags = getattr(subprocess, "DETACHED_PROCESS", 0)
        subprocess.Popen(
            [pythonw, GUARD_SCRIPT, "--watch", "--silent"],
            close_fds=True,
            creationflags=flags,
        )
        print("[!] Could not create the scheduled task (needs administrator).")
        print("[*] Fallback startup shortcut installed:")
        print("     " + STARTUP_FILE)
        print("     Re-run this script as administrator for the full guard.")


def guard_installed():
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME],
        capture_output=True,
        text=True,
        errors="replace",
    )
    return result.returncode == 0 or os.path.exists(STARTUP_FILE)


def remove_guard():
    removed = False
    result = subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], capture_output=True
    )
    if result.returncode == 0:
        removed = True
    for path in (STARTUP_FILE, LEGACY_STARTUP, GUARD_SCRIPT):
        if os.path.exists(path):
            try:
                os.remove(path)
                removed = True
            except Exception:
                pass
    _terminate_watchers(["RTL-Patch", "DeepAI-RTL"])
    if removed:
        print("[OK] Auto-repair guard removed.")
    else:
        print("[*] Auto-repair guard was not installed.")


# ---------------------------------------------------------------------------
# status / main
# ---------------------------------------------------------------------------

def pause():
    if not sys.stdin or not sys.stdin.isatty():
        return
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


def status():
    print("QwenWork RTL + Vazir  v%s" % TOOL_VERSION)
    for target in TARGETS:
        asar = target.asar_path()
        print("")
        print("  " + target.label)
        print("    archive :", asar or "(not installed)")
        if not asar or not os.path.exists(asar):
            print("    installed:", False)
            continue
        print("    installed:", True)
        print("    patched  :", target.is_patched())
        print("    current  :", target.is_current())
        print("    running  :", target.is_running())
    print("")
    print("    guard    :", guard_installed(), TASK_NAME)
    print("    guard log:", GUARD_LOG)
    print("    font     :", "embedded Vazirmatn" if font_base64() else "system Vazirmatn")


def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return True


def elevate():
    """Re-launch this script as administrator. True when the new process started."""
    try:
        import ctypes
        script = os.path.abspath(__file__)
        params = subprocess.list2cmdline([script] + sys.argv[1:])
        code = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, os.path.dirname(script), 1)
        return code > 32
    except Exception:
        return False


def ensure_admin():
    """Patch files live under Program Files, so writing needs elevation."""
    if is_admin():
        return True
    if elevate():
        sys.exit(0)
    print("")
    print("[!] Administrator rights are required for this step.")
    print("    Right-click the .bat file and pick 'Run as administrator'.")
    pause()
    return False


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    args = [a.lower() for a in sys.argv[1:]]
    silent = "--silent" in args
    requested = "all"
    for index, arg in enumerate(args):
        if arg == "--target" and index + 1 < len(args):
            requested = args[index + 1]
        elif arg.startswith("--target="):
            requested = arg.split("=", 1)[1]

    if "--watch" in args:
        watch(silent=True)
        return
    if "--install-guard" in args or "--remove-guard" in args:
        if not ensure_admin():
            return
        if "--install-guard" in args:
            install_guard()
        else:
            remove_guard()
        if not silent:
            pause()
        return
    if "--status" in args:
        status()
        if not silent:
            pause()
        return

    mode = "install"
    if any(a in ("--restore", "restore", "-r") for a in args):
        mode = "restore"
    elif any(a in ("--install", "install", "-i") for a in args):
        mode = "install"
    else:
        print("=" * 62)
        print("  QwenWork RTL + Vazir  v%s" % TOOL_VERSION)
        print("=" * 62)
        print("")
        print("  [1] Install / update patch")
        print("  [2] Show status")
        print("  [3] Remove patch (restore the original look)")
        print("  [4] Install / repair the auto-repair guard")
        print("  [5] Remove the auto-repair guard")
        try:
            answer = input("\nChoose (default = 1): ").strip()
        except EOFError:
            answer = ""
        if answer == "2":
            status()
            pause()
            return
        elif answer == "3":
            requested, mode = "all", "restore"
        elif answer == "4":
            if ensure_admin():
                install_guard()
                pause()
            return
        elif answer == "5":
            if ensure_admin():
                remove_guard()
                pause()
            return

    if not ensure_admin():
        return

    targets = select_targets(requested)
    if not targets:
        print("[!] No matching app found for target: %s" % requested)
        if not silent:
            pause()
        sys.exit(1)

    _, error = run(mode, targets)

    if error is not None:
        print("\n[!] ERROR:", error)
        if not silent:
            pause()
        sys.exit(1)

    print("\nDone.")
    if not silent:
        pause()


if __name__ == "__main__":
    main()
