# -*- coding: utf-8 -*-
"""将 templates 下 HTML 中的 Bootstrap Icons、Font Awesome、SortableJS CDN 替换为本地路径。"""
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")

REPLACEMENTS = [
    (
        re.compile(
            r"https://cdn\.jsdelivr\.net/npm/bootstrap-icons@1\.7\.2/font/bootstrap-icons\.css"
        ),
        "/static/css/bootstrap-icons.css",
    ),
    (
        re.compile(
            r"https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/6\.0\.0/css/all\.min\.css"
        ),
        "/static/css/font-awesome.min.css",
    ),
    (
        re.compile(
            r"https://cdn\.jsdelivr\.net/npm/sortablejs@1\.15\.0/Sortable\.min\.js"
        ),
        "/static/js/Sortable.min.js",
    ),
]

def main():
    count = 0
    for root, _dirs, files in os.walk(TEMPLATES_DIR):
        for name in files:
            if not name.endswith(".html"):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except Exception as e:
                print(f"  skip {path}: {e}")
                continue
            new_text = text
            for pattern, repl in REPLACEMENTS:
                new_text = pattern.sub(repl, new_text)
            if new_text != text:
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(new_text)
                count += 1
                print(f"  updated: {os.path.relpath(path, PROJECT_ROOT)}")
    print(f"Done. Updated {count} file(s).")

if __name__ == "__main__":
    main()
