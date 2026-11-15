#!/usr/bin/env python3
"""校验仓库内 Markdown 的相对链接是否指向真实存在的文件。

用法：python scripts/check_docs.py
退出码：0 = 全部通过；1 = 存在断链或错误的绝对路径链接。

只依赖 Python 3 标准库，本地与 CI 用同一套判断。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "data:", "#")


def iter_markdown(root: Path):
    for path in sorted(root.rglob("*.md")):
        if ".git" in path.parts or "node_modules" in path.parts:
            continue
        yield path


def extract_targets(text: str) -> list[str]:
    targets = []
    for raw in LINK_RE.findall(text):
        raw = raw.strip()
        if not raw:
            continue
        target = raw.split()[0]
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        targets.append(target)
    return targets


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    for target in extract_targets(path.read_text(encoding="utf-8")):
        if not target or target.startswith(SKIP_PREFIXES):
            continue
        clean = target.split("#", 1)[0].split("?", 1)[0]
        if not clean:
            continue
        if clean.startswith("/"):
            errors.append(f"  不应使用绝对路径: {target}")
            continue
        resolved = (path.parent / clean).resolve()
        if not resolved.exists():
            errors.append(f"  目标不存在: {target}")
    return errors


def main() -> int:
    files = list(iter_markdown(ROOT))
    total_links = 0
    failures: list[tuple[Path, list[str]]] = []

    for path in files:
        text = path.read_text(encoding="utf-8")
        total_links += len(extract_targets(text))
        errors = check_file(path)
        if errors:
            failures.append((path.relative_to(ROOT), errors))

    print(f"扫描 {len(files)} 个 Markdown 文件，{total_links} 个链接")
    if failures:
        for rel, errors in failures:
            print(f"\n[断链] {rel}")
            for line in errors:
                print(line)
        print(f"\n共 {len(failures)} 个文件存在问题")
        return 1

    print("全部相对链接均指向真实存在的文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
