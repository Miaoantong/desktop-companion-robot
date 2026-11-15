# 阶段追踪卡（已发布为 Issue #1–#5）

这 5 个文件是 P0–P4 阶段 Issue 正文的**单一来源**，内容与 [`../../docs/01_项目规划.md`](../../docs/01_项目规划.md) 的验收清单一一对应。2026-11-15 已用个人 fine-grained PAT 发布为公开 Issue。

| 文件 | 阶段 | 已发布的 Issue |
|---|---|---|
| [P0.md](P0.md) | P0 · 2026.11 – 2027.01 | [#1 表情脸 + 转头 + 可测量](https://github.com/Miaoantong/desktop-companion-robot/issues/1) |
| [P1.md](P1.md) | P1 · 2027.02 – 2027.04 | [#2 电流感知触觉：无传感器力估计](https://github.com/Miaoantong/desktop-companion-robot/issues/2) |
| [P2.md](P2.md) | P2 · 2027.05 – 2027.08 | [#3 异构架构 + 隐私在场感知](https://github.com/Miaoantong/desktop-companion-robot/issues/3) |
| [P3.md](P3.md) | P3 · 2027.09 – 2028.01 | [#4 认知层：行为识别、主动策略与记忆](https://github.com/Miaoantong/desktop-companion-robot/issues/4) |
| [P4.md](P4.md) | P4 · 2028.02 – 2028.05 | [#5 完整作品与开源整理](https://github.com/Miaoantong/desktop-companion-robot/issues/5) |

## 维护约定

- 改动验收标准时，`docs/01_项目规划.md`、这里的卡片、GitHub 上的 Issue 正文**要同步更新**，否则下次重新发布会把 GitHub 侧的改动覆盖掉。
- 卡片标题取第一行 `# [P?] ...`，正文取 `---` 以下内容；[`../../scripts/create_issues.py`](../../scripts/create_issues.py) 按这个格式解析，不要改格式。
- 发布后仍需手动补：给 5 个 Issue 打 `stage/P?` 标签、挂到对应 Milestone；建议值见 [`../../docs/06_仓库协作规范.md`](../../docs/06_仓库协作规范.md) 第 5、7 节。

## 为什么用脚本发布（历史记录）

GitHub App 集成创建 Issue 返回 `403 Resource not accessible by integration`，即该 App 没有被授予 `Issues: Read and write`。App 的权限范围是**注册时**由平台方勾选的，安装者只能批准已列出的权限——因此**重新授权补不了这项权限**，不要在这上面反复尝试。改用个人 fine-grained PAT + 脚本发布。

需要重建或补发时（脚本会跳过同名 Issue，可重复执行）：

```bash
python scripts/create_issues.py --dry-run            # 先预览
python scripts/create_issues.py --links             # 不用 token，输出预填链接
GITHUB_TOKEN=xxx python scripts/create_issues.py    # Git Bash / macOS / Linux
```

Windows PowerShell：

```powershell
$env:GITHUB_TOKEN = "xxx"; python scripts/create_issues.py
```

- 生成 fine-grained PAT：https://github.com/settings/personal-access-tokens/new —— Expiration 选最短（如 7 天，用完删除）；Repository access → **Only select repositories** → 只勾本仓库；Permissions → **Issues: Read and write**，其余保持 No access。
- token 只从环境变量读取，不写进任何文件、不提交；用完立刻在 PAT 页面 Delete。
- 本机实测 Python 标准库访问 `api.github.com` 可直连（HTTP 200），**不需要**像 `git push` 那样临时关闭证书校验。
