# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-24

First public release.

### Added

- Right-to-left rendering for QwenWork: per-block direction detection (first strong character wins),
  with a `MutationObserver` so streamed answers flip as soon as Persian arrives.
- Vazirmatn (variable, ~240 KB) embedded in the patch as base64 — no font installation required.
- Composer support: the message box follows the language you type.
- LTR isolation for code blocks, inline code, KaTeX, the Monaco editor and the terminal.
- `app.asar` writer with recalculated header fields, entry offsets and per-entry SHA-256 integrity blocks,
  plus a full read-back verification before the original archive is replaced.
- Logon guard (scheduled task with highest privileges) that re-applies the patch after an update.
- Restore command that removes the injected block and returns the original file byte for byte.
- `restored.json` marker so `--restore` is not undone by the guard until the archive really changes.
- English and Persian documentation, step-by-step usage guides, issue templates and a CI syntax check.

### Fixed

- A no-op `--install` no longer restarts the app just to report that it is already patched.
