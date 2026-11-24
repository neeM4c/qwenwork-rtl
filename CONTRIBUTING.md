# Contributing

Thanks for taking the time to improve this project. Bug reports, selector fixes and translations are all
welcome — you do not need to be a Python expert.

## Reporting a problem

Open an [issue](https://github.com/neeM4c/qwenwork-rtl/issues/new/choose) and include:

1. the output of `python qwenwork_rtl.py --status`,
2. your Windows version and the QwenWork version (from `C:\Program Files\QwenWork\updater.cfg`),
3. what you expected and what happened,
4. a screenshot if a specific panel still looks wrong.

## Fixing a panel that stays left-aligned

Most visual bugs are one missing selector. In `qwenwork_rtl.py`, look for `BLOCK_SEL` (elements that should
follow their content direction) and `SKIP_SEL` (elements that must stay LTR, such as code and terminals).

1. Open QwenWork, press `Ctrl+Shift+I`, inspect the element.
2. If it is a text container, add its `[data-slot="…"]` or class to `BLOCK_SEL`.
3. If it must never be flipped, add it to `SKIP_SEL`.
4. Bump `RTL_VERSION` by one so existing installs are upgraded automatically.

## Development setup

```powershell
git clone https://github.com/neeM4c/qwenwork-rtl.git
cd qwenwork-rtl
python qwenwork_rtl.py --status   # no writes, no admin rights needed
```

There is no build step and no third-party dependency. Keep it that way: **standard library only**.

### Testing a change safely

Never experiment on a live install you care about. Copy the archive and patch the copy:

```powershell
Copy-Item "C:\Program Files\QwenWork\<version>\resources\app.asar" .\test.asar
```

Then point `QwenWorkTarget.asar_path()` at `test.asar` in a scratch script, run the install, reopen the
archive and confirm: every packed file is readable, `out/renderer/index.html` contains exactly one
`RTL-PATCH-START` block, and `--restore` reproduces the original bytes (`Get-FileHash` before and after).

## Pull requests

- One topic per PR, with a short description of *why*.
- Keep output messages in English — the Windows console cannot render Persian reliably.
- Do not reformat unrelated code; diffs should stay readable.
- Mention the QwenWork version you tested with.

## Commit messages

`type: short summary` — for example `fix: keep table headers right-aligned` or `docs: add Persian FAQ`.
Common types: `feat`, `fix`, `docs`, `refactor`, `chore`.

## Translations

`README.fa.md` and `docs/USAGE.fa.md` mirror the English files. If you add a section, add it to both, and keep
the anchor links working in each language.
