"""Offline checks that do not need QwenWork to be installed.

Run with:  python tests/smoke_test.py
"""

import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "qwenwork_rtl.py")


def load_module():
    spec = importlib.util.spec_from_file_location("qwenwork_rtl", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    module = load_module()
    failures = []

    def check(name, condition):
        print(("ok   " if condition else "FAIL ") + name)
        if not condition:
            failures.append(name)

    snippet = module.qwenwork_snippet()
    check("tool version is set", bool(module.TOOL_VERSION))
    check("snippet has both markers", module.MARK_START in snippet and module.MARK_END in snippet)
    check("snippet carries the version token", module.VERSION_TOKEN in snippet)
    check("snippet embeds the font", "data:font/ttf;base64," in snippet)
    check("snippet overrides the ui font variable", "--qw-font-family-sans" in snippet)
    check("snippet detects persian text", "\\u0600-\\u06FF" in snippet)
    check("snippet pins code to ltr", "direction:ltr" in snippet or "direction: ltr" in snippet)

    original = "<html><head><title>t</title></head><body><p>hi</p></body></html>"
    patched = original.replace("</head>", snippet + "\n</head>", 1)
    check("patched html is detected", module.html_is_patched(patched))
    check("patched html is current", module.html_is_current(patched))
    check("restore reproduces the original bytes", module.strip_snippet(patched) == original)
    check("clean html is not reported as patched", not module.html_is_patched(original))
    check("legacy markers are stripped too",
          module.strip_snippet(module.LEGACY_START + "x" + module.LEGACY_END + "</head>") == "</head>")

    print("")
    if failures:
        print("%d check(s) failed" % len(failures))
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
