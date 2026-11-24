# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 1.x | yes |

## What this tool touches

- It rewrites `resources/app.asar` **on your own machine** so QwenWork renders Persian right-to-left.
- It can register one scheduled task (`RTL Patch Guard`) that runs the same script at logon.
- It never sends data anywhere, never downloads code at runtime, and stores only two small files in
  `%LOCALAPPDATA%\RTL-Patch\` (the guard log and a `restored.json` marker).

If you find behaviour that contradicts the list above, that is a security bug.

## Reporting a vulnerability

Please **do not open a public issue**. Use
[GitHub private vulnerability reporting](https://github.com/neeM4c/qwenwork-rtl/security/advisories/new)
and include:

1. the affected version (`python qwenwork_rtl.py --status`),
2. a description of the problem and its impact,
3. reproduction steps, if you have them.

You will get an acknowledgement as soon as possible, and a fix or explanation before any public disclosure.

## Out of scope

- Vulnerabilities in QwenWork itself — report those to its vendor.
- The fact that the patch edits an application archive; that is the whole point of the project and it is
  fully reversible with `--restore`.
