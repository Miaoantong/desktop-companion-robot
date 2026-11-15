#!/usr/bin/env python3
"""阶段追踪 Issue 发布 + 仓库非代码配置同步（声明式、幂等、免 PAT）。

配置来源：.github/repo-meta.json —— 改配置后跑一次 --setup 即可同步到 GitHub。

用法：
    python scripts/create_issues.py --dry-run                # 预览将创建哪些 Issue
    python scripts/create_issues.py --links                 # 输出预填新建 Issue 链接
    python scripts/create_issues.py                        # 创建 5 个阶段 Issue
    python scripts/create_issues.py --setup --dry-run       # 匿名预览全部仓库配置变更
    python scripts/create_issues.py --setup                # 同步到 GitHub

--setup 同步：description / homepage / topics / 自定义标签 / 阶段里程碑 / Issue 挂载。
全部幂等；更新 Issue 时保留它上面已有的其他标签。

凭据自动解析（按优先级，不需要手动新建 PAT）：
    1. 环境变量 GITHUB_TOKEN（显式覆盖，便于临时换身份）
    2. gh auth token（本机装了 GitHub CLI 且已登录时）
    3. git credential fill（复用 git push 使用的本机 OAuth 登录态）

token 只在内存中使用，不写文件、不进命令行参数、不打印。只依赖 Python 3 标准库。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / ".github" / "ISSUES"
CONFIG = ROOT / ".github" / "repo-meta.json"
OWNER = "Miaoantong"
REPO = "desktop-companion-robot"
GITHUB_API = "https://api.github.com"
REPO_API = f"{GITHUB_API}/repos/{OWNER}/{REPO}"
API = f"{REPO_API}/issues"
LABELS_API = f"{REPO_API}/labels"
MILESTONES_API = f"{REPO_API}/milestones"
TOPICS_API = f"{REPO_API}/topics"


def load_config() -> dict:
    if not CONFIG.exists():
        raise FileNotFoundError(f"缺少配置文件：{CONFIG}")
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    for key in ("labels", "milestones", "topics"):
        if key not in data:
            raise ValueError(f"{CONFIG} 缺少字段 {key}")
    return data


def resolve_token() -> tuple[str, str]:
    """按优先级找本机的长期 GitHub 凭据，返回 (token, 来源说明)。"""
    explicit = os.environ.get("GITHUB_TOKEN", "").strip()
    if explicit:
        return explicit, "环境变量 GITHUB_TOKEN"

    gh = shutil.which("gh")
    if gh:
        try:
            out = subprocess.run(
                [gh, "auth", "token"], capture_output=True, text=True, timeout=10
            )
            token = out.stdout.strip()
            if out.returncode == 0 and token:
                return token, "GitHub CLI 登录态（gh auth token）"
        except (OSError, subprocess.SubprocessError):
            pass

    try:
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
        out = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True, text=True, timeout=15, env=env,
        )
        for line in out.stdout.splitlines():
            if line.startswith("password="):
                token = line.split("=", 1)[1].strip()
                if token:
                    return token, "本机 Git 凭据（与 git push 同一份 OAuth 登录态）"
    except (OSError, subprocess.SubprocessError):
        pass

    return "", "无"


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


def api_request(url: str, token: str, data=None, method: str | None = None):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "desktop-companion-robot-repo-sync",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if data is not None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if method is None:
        method = "POST" if data is not None else "GET"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def existing_titles(token: str) -> set[str]:
    try:
        issues = api_request(f"{API}?state=all&per_page=100", token)
    except urllib.error.HTTPError as error:
        print(f"警告：读取现有 Issue 失败（HTTP {error.code}），跳过重复检查", file=sys.stderr)
        return set()
    return {issue["title"] for issue in issues}


def sync_about(token: str, config: dict, dry_run: bool) -> int:
    """同步 description / homepage / topics；权限不足时只警告，不阻断其余配置。"""
    try:
        repo = api_request(REPO_API, token)
        want_desc = config.get("description", "") or ""
        want_home = config.get("homepage", "") or ""
        want_topics = config.get("topics", []) or []
        need_about = (repo.get("description") or "") != want_desc or (repo.get("homepage") or "") != want_home
        # GitHub 返回的 topics 按字母排序，比较时忽略顺序，避免每次重复写入
        need_topics = sorted(repo.get("topics") or []) != sorted(want_topics)

        print(f"About：description / homepage {'待更新' if need_about else '已就绪'}，"
              f"topics {'待更新' if need_topics else '已就绪'}（目标 {len(want_topics)} 个）")
        if dry_run:
            if need_about:
                print(f"  [预览] description → {want_desc}")
            if need_topics:
                print(f"  [预览] topics → {', '.join(want_topics)}")
            return 0

        changed = 0
        if need_about:
            api_request(REPO_API, token,
                        {"description": want_desc, "homepage": want_home}, method="PATCH")
            print("  [已更新] description / homepage")
            changed += 1
        if need_topics:
            api_request(TOPICS_API, token, {"names": want_topics}, method="PUT")
            print(f"  [已更新] topics（{len(want_topics)} 个）")
            changed += 1
        return changed
    except urllib.error.HTTPError as error:
        print(f"  [警告] About 写入失败 HTTP {error.code}（通常需要仓库管理权限），跳过；其余配置继续",
              file=sys.stderr)
        return 0


def setup_repo(token: str, dry_run: bool = False) -> int:
    """按 .github/repo-meta.json 幂等同步仓库非代码配置。"""
    config = load_config()
    print(f"--- 仓库非代码配置（{'匿名预览' if dry_run else '同步执行'}）---")
    sync_about(token, config, dry_run)
    print()

    label_names = {x["name"] for x in api_request(f"{LABELS_API}?per_page=100", token) or []}
    milestone_numbers = {
        x["title"]: x["number"]
        for x in api_request(f"{MILESTONES_API}?state=all&per_page=100", token) or []
    }
    issues = api_request(f"{API}?state=all&per_page=100", token) or []

    labels = config["labels"]
    milestones = config["milestones"]
    missing_labels = [x for x in labels if x["name"] not in label_names]
    print(f"Labels：远端已有 {len(label_names)} 个，待补 {len(missing_labels)} 个")
    if dry_run:
        for spec in missing_labels:
            print(f"  [预览] + 标签 {spec['name']}")
    else:
        for spec in missing_labels:
            api_request(LABELS_API, token, spec)
            print(f"  [已创建] 标签 {spec['name']}")

    missing_ms = [m for m in milestones if m["title"] not in milestone_numbers]
    print(f"Milestones：远端已有 {len(milestone_numbers)} 个，待补 {len(missing_ms)} 个")
    if dry_run:
        for spec in missing_ms:
            print(f"  [预览] + 里程碑 {spec['title']}（截止 {spec['due_on'][:10]}）")
    else:
        for spec in missing_ms:
            payload = {
                "title": spec["title"], "state": "open",
                "due_on": spec["due_on"], "description": spec.get("description", ""),
            }
            result = api_request(MILESTONES_API, token, payload)
            milestone_numbers[spec["title"]] = result["number"]
            print(f"  [已创建] 里程碑 #{result['number']} {spec['title']}")

    print("阶段 Issue 挂载：")
    updated = 0
    for spec in milestones:
        stage = spec["stage"]
        issue = next((x for x in issues if x["title"].startswith(f"[{stage}]")), None)
        if issue is None:
            print(f"  [警告] 找不到 [{stage}] 开头的 Issue，跳过", file=sys.stderr)
            continue
        stage_label = f"stage/{stage}"
        current = [label["name"] for label in issue.get("labels", [])]
        current_ms = (issue.get("milestone") or {}).get("number")
        target_ms = milestone_numbers.get(spec["title"])
        wanted = sorted(set(current) | {stage_label})
        need_update = stage_label not in current or current_ms != target_ms

        if dry_run:
            action = "将更新" if need_update else "已就绪"
            print(f"  [预览] #{issue['number']} {action}：{stage_label} + {spec['title']}")
            continue
        if not need_update:
            print(f"  [跳过] #{issue['number']} 已就绪")
            continue
        if target_ms is None:
            print(f"  [失败] #{issue['number']}：里程碑 {spec['title']} 未创建", file=sys.stderr)
            return 1
        api_request(
            f"{API}/{issue['number']}", token,
            {"labels": wanted, "milestone": target_ms}, method="PATCH",
        )
        print(f"  [已更新] #{issue['number']} → {stage_label} + {spec['title']}（保留原有 {len(current)} 个标签）")
        updated += 1

    print(f"\n完成：标签 +{len(missing_labels)}，里程碑 +{len(missing_ms)}，Issue 更新 {updated} 个")
    print("配置来源：.github/repo-meta.json（改动这里后重跑一次即可）")
    return 0


def http_error(error: urllib.error.HTTPError) -> int:
    detail = error.read().decode("utf-8", "replace")
    print(f"失败：HTTP {error.code}: {detail[:200]}", file=sys.stderr)
    if error.code == 401:
        print("凭据无效或已被撤销 —— 检查本机 git 凭据，或重新登录 GitHub CLI", file=sys.stderr)
    elif error.code == 403:
        print("权限不足或触发限流 —— 该凭据需要本仓库的仓库管理 / Issues 写权限", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="发布阶段追踪 Issue / 同步仓库非代码配置")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入")
    parser.add_argument("--links", action="store_true", help="输出 GitHub 预填新建 Issue 链接")
    parser.add_argument("--setup", action="store_true", help="按 repo-meta.json 同步仓库非代码配置")
    args = parser.parse_args()

    if args.setup:
        if args.dry_run:
            token, source = "", "匿名预览（不读取凭据）"
        else:
            token, source = resolve_token()
            if not token:
                print("未找到可用的 GitHub 凭据。可设置 GITHUB_TOKEN，或先跑一次 gh auth login。",
                      file=sys.stderr)
                return 1
        print(f"凭据：{source}")
        try:
            if token:
                api_request(f"{GITHUB_API}/user", token)  # 提前验证，失败时给出清晰报错
            return setup_repo(token, args.dry_run)
        except urllib.error.HTTPError as error:
            return http_error(error)
        except (FileNotFoundError, ValueError, KeyError) as error:
            print(f"配置错误：{error}", file=sys.stderr)
            return 1

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
        print(f"\n共 {len(cards)} 张卡；去掉 --dry-run 即可创建（凭据自动解析）")
        return 0

    token, source = resolve_token()
    if not token:
        print("未找到可用的 GitHub 凭据。可设置 GITHUB_TOKEN，或先跑一次 gh auth login。",
              file=sys.stderr)
        return 1
    print(f"凭据：{source}")

    existing = existing_titles(token)
    created = 0
    for title, body in cards:
        if title in existing:
            print(f"[跳过] 已存在：{title}")
            continue
        try:
            result = api_request(API, token, {"title": title, "body": body})
        except urllib.error.HTTPError as error:
            return http_error(error)
        print(f"[已创建] #{result['number']} {title}\n  {result['html_url']}")
        created += 1

    print(f"\n完成：新建 {created} 个，跳过 {len(cards) - created} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
