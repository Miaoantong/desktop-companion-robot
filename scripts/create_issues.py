#!/usr/bin/env python3
"""把 .github/ISSUES/P0~P4.md 发布为 GitHub 阶段追踪 Issue。

用法：
    python scripts/create_issues.py --dry-run          # 只预览，不调用 API
    python scripts/create_issues.py --links           # 输出 GitHub 预填「新建 Issue」链接
    GITHUB_TOKEN=xxx python scripts/create_issues.py  # 真正创建

前置条件：一个只作用于本仓库、带 Issues: Read and write 的 fine-grained PAT。
生成地址：https://github.com/settings/personal-access-tokens/new

token 只从环境变量读取，绝不写进仓库、命令行参数或日志。
只依赖 Python 3 标准库。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / ".github" / "ISSUES"
OWNER = "Miaoantong"
REPO = "desktop-companion-robot"
API = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"


def parse_card(path: Path) -> tuple[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ").strip()
    for index, line in enumerate(lines):
        if line.strip() == "---":
            body = "\n".join(lines[index + 1:]).strip()
            return title, body + "\n"
    raise ValueError(f"{path}: 找不到 --- 分隔线")


def load_cards() -> list[tuple[str, str]]:
    return [parse_card(path) for path in sorted(CARDS.glob("P?.md"))]


def api_request(url: str, token: str, data=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "desktop-companion-robot-issue-creator",
    }
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        url, data=body, headers=headers, method="POST" if data is not None else "GET"
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def existing_titles(token: str) -> set[str]:
    try:
        issues = api_request(f"{API}?state=all&per_page=100", token)
    except urllib.error.HTTPError as error:
        print(f"警告：读取现有 Issue 失败（HTTP {error.code}），跳过重复检查", file=sys.stderr)
        return set()
    return {issue["title"] for issue in issues}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="只预览，不创建")
    parser.add_argument("--links", action="store_true", help="输出 GitHub 预填新建 Issue 链接")
    args = parser.parse_args()

    cards = load_cards()
    if not cards:
        print("没有找到 .github/ISSUES/P?.md", file=sys.stderr)
        return 1

    if args.links:
        for title, body in cards:
            url = (
                f"https://github.com/{OWNER}/{REPO}/issues/new"
                f"?title={quote(title)}&body={quote(body)}"
            )
            print(f"\n{title}\n{url}")
        return 0

    if args.dry_run:
        for title, body in cards:
            print(f"[预览] {title}  （正文 {len(body)} 字符）")
        print(f"\n共 {len(cards)} 张卡；设置 GITHUB_TOKEN 后去掉 --dry-run 即可创建")
        return 0

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print("缺少 GITHUB_TOKEN。用法：GITHUB_TOKEN=xxx python scripts/create_issues.py", file=sys.stderr)
        return 1

    existing = existing_titles(token)
    created = 0
    for title, body in cards:
        if title in existing:
            print(f"[跳过] 已存在：{title}")
            continue
        try:
            result = api_request(API, token, {"title": title, "body": body})
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")
            print(f"[失败] {title} → HTTP {error.code}: {detail[:200]}", file=sys.stderr)
            if error.code == 403:
                print("该 token 需要本仓库的 Issues: Read and write 权限", file=sys.stderr)
            return 1
        print(f"[已创建] #{result['number']} {title}\n  {result['html_url']}")
        created += 1

    print(f"\n完成：新建 {created} 个，跳过 {len(cards) - created} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
