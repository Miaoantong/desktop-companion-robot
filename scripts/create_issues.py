#!/usr/bin/env python3
"""阶段追踪 Issue 发布脚本，兼仓库协作元数据批量配置。

用法：
    python scripts/create_issues.py --dry-run                  # 预览将创建哪些 Issue
    python scripts/create_issues.py --links                   # 输出预填「新建 Issue」链接
    GITHUB_TOKEN=xxx python scripts/create_issues.py          # 创建 5 个阶段 Issue
    python scripts/create_issues.py --setup --dry-run         # 匿名预览标签 / 里程碑 / 挂载
    GITHUB_TOKEN=xxx python scripts/create_issues.py --setup  # 批量补齐并挂载

--setup 做三件事，全部幂等（可重复运行）：
    1. 补 16 个自定义 Labels（stage/ area/ type/ constraint/）
    2. 建 5 个阶段 Milestones（含截止日）
    3. 给阶段 Issue 打 stage/P? 标签并挂到对应 Milestone，保留已有标签

前置条件：一个只作用于本仓库、带 Issues: Read and write 的 fine-grained PAT。
生成地址：https://github.com/settings/personal-access-tokens/new

token 只从环境变量读取，绝不写进仓库、命令行参数或日志。只依赖 Python 3 标准库。
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
REPO_API = f"https://api.github.com/repos/{OWNER}/{REPO}"
API = f"{REPO_API}/issues"
LABELS_API = f"{REPO_API}/labels"
MILESTONES_API = f"{REPO_API}/milestones"

# 与 docs/06_仓库协作规范.md 第 5 节一致
LABEL_GROUPS = (
    ("stage", "1D76DB", "阶段", ("P0", "P1", "P2", "P3", "P4")),
    ("area", "5319E7", "归属目录 / 层次", ("firmware", "hardware", "docs", "cognition", "ci")),
    ("type", "FBCA04", "改动性质", ("experiment", "benchmark", "refactor")),
    ("constraint", "D93F0B", "硬约束", ("realtime", "privacy", "offline")),
)
LABELS = [
    {"name": f"{prefix}/{value}", "color": color, "description": f"{desc} · {value}"}
    for prefix, color, desc, values in LABEL_GROUPS
    for value in values
]

# 与 docs/06_仓库协作规范.md 第 4 节一致，截止日取各阶段末月
MILESTONES = [
    {"stage": "P0", "title": "P0 表情脸 + 转头 + 可测量", "due_on": "2027-01-31T23:59:59Z",
     "description": "OLED 表情脸、双舵机转头、参数化渲染、延迟测量框架；结束时打 tag p0-face-neck"},
    {"stage": "P1", "title": "P1 电流感知触觉", "due_on": "2027-04-30T23:59:59Z",
     "description": "双通道电流采样、4 类分类、摸头分级、堵转保护、60 秒 demo；结束时打 tag p1-current-touch"},
    {"stage": "P2", "title": "P2 异构架构 + 隐私在场感知", "due_on": "2027-08-31T23:59:59Z",
     "description": "UART 协议、心跳降级、跨板时钟同步、唤醒词、雷达在场检测；结束时打 tag p2-heterogeneous"},
    {"stage": "P3", "title": "P3 认知层", "due_on": "2028-01-31T23:59:59Z",
     "description": "行为标签、主动干预四级、打扰成本建模、遗忘曲线记忆；结束时打 tag p3-cognition"},
    {"stage": "P4", "title": "P4 完整作品与开源整理", "due_on": "2028-05-31T23:59:59Z",
     "description": "外壳、benchmark、消融实验、开源资料、可选对话模块；结束时发 Release v1.0.0"},
]


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
        "User-Agent": "desktop-companion-robot-issue-creator",
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


def setup_repo(token: str, dry_run: bool = False) -> int:
    """批量补齐 Labels / Milestones，并把阶段 Issue 挂载到位。"""
    print(f"--- 仓库协作元数据（{'预览' if dry_run else '执行'}）---")

    label_names = {x["name"] for x in api_request(f"{LABELS_API}?per_page=100", token) or []}
    milestone_numbers = {
        x["title"]: x["number"]
        for x in api_request(f"{MILESTONES_API}?state=all&per_page=100", token) or []
    }
    issues = api_request(f"{API}?state=all&per_page=100", token) or []

    missing_labels = [x for x in LABELS if x["name"] not in label_names]
    print(f"Labels：远端已有 {len(label_names)} 个，待补 {len(missing_labels)} 个")
    if dry_run:
        for spec in missing_labels:
            print(f"  [预览] + 标签 {spec['name']}")
    else:
        for spec in missing_labels:
            api_request(LABELS_API, token, spec)
            print(f"  [已创建] 标签 {spec['name']}")

    missing_ms = [m for m in MILESTONES if m["title"] not in milestone_numbers]
    print(f"Milestones：远端已有 {len(milestone_numbers)} 个，待补 {len(missing_ms)} 个")
    if dry_run:
        for spec in missing_ms:
            print(f"  [预览] + 里程碑 {spec['title']}（截止 {spec['due_on'][:10]}）")
    else:
        for spec in missing_ms:
            payload = {
                "title": spec["title"],
                "state": "open",
                "due_on": spec["due_on"],
                "description": spec["description"],
            }
            result = api_request(MILESTONES_API, token, payload)
            milestone_numbers[spec["title"]] = result["number"]
            print(f"  [已创建] 里程碑 #{result['number']} {spec['title']}")

    print("阶段 Issue 挂载：")
    updated = 0
    for spec in MILESTONES:
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
            f"{API}/{issue['number']}",
            token,
            {"labels": wanted, "milestone": target_ms},
            method="PATCH",
        )
        print(f"  [已更新] #{issue['number']} → {stage_label} + {spec['title']}（保留原有 {len(current)} 个标签）")
        updated += 1

    print(f"\n完成：标签 +{len(missing_labels)}，里程碑 +{len(missing_ms)}，Issue 更新 {updated} 个")
    return 0


def http_error(error: urllib.error.HTTPError) -> int:
    detail = error.read().decode("utf-8", "replace")
    print(f"失败：HTTP {error.code}: {detail[:200]}", file=sys.stderr)
    if error.code == 401:
        print("token 无效或已被撤销 —— 请重新生成 fine-grained PAT", file=sys.stderr)
    elif error.code == 403:
        print("该 token 需要本仓库的 Issues: Read and write 权限，或已触发限流", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="发布阶段追踪 Issue / 批量配置仓库协作元数据")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入")
    parser.add_argument("--links", action="store_true", help="输出 GitHub 预填新建 Issue 链接")
    parser.add_argument("--setup", action="store_true", help="批量补齐 Labels / Milestones 并挂载阶段 Issue")
    args = parser.parse_args()

    if args.setup:
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if not token and not args.dry_run:
            print("缺少 GITHUB_TOKEN。用法：GITHUB_TOKEN=xxx python scripts/create_issues.py --setup",
                  file=sys.stderr)
            return 1
        try:
            return setup_repo(token, args.dry_run)
        except urllib.error.HTTPError as error:
            return http_error(error)

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
            return http_error(error)
        print(f"[已创建] #{result['number']} {title}\n  {result['html_url']}")
        created += 1

    print(f"\n完成：新建 {created} 个，跳过 {len(cards) - created} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
