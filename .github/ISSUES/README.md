# 阶段追踪卡（已发布为 Issue #1–#5）

这 5 个文件是 P0–P4 阶段 Issue 正文的**单一来源**，内容与 [`../../docs/01_项目规划.md`](../../docs/01_项目规划.md) 的验收清单一一对应。2026-11-15 已发布为公开 Issue。

| 文件 | 阶段 | 对应能力级 | 已发布的 Issue |
|---|---|---|---|
| [P0.md](P0.md) | P0 | C1–C2 | [#1 表情脸 + 转头 + 可测量](https://github.com/Miaoantong/desktop-companion-robot/issues/1) |
| [P1.md](P1.md) | P1 | C3–C4 | [#2 电流感知触觉：无传感器力估计](https://github.com/Miaoantong/desktop-companion-robot/issues/2) |
| [P2.md](P2.md) | P2 | C5–C6 | [#3 异构架构 + 隐私在场感知](https://github.com/Miaoantong/desktop-companion-robot/issues/3) |
| [P3.md](P3.md) | P3 | 产品之外 | [#4 认知层：行为识别、主动策略与记忆](https://github.com/Miaoantong/desktop-companion-robot/issues/4) |
| [P4.md](P4.md) | P4 | 作品集收口 | [#5 完整作品与开源整理](https://github.com/Miaoantong/desktop-companion-robot/issues/5) |

阶段不绑日历，标题与正文均不含日期。里程碑上仍有截止日，仅作提醒，不构成交付承诺（见 [`../../docs/06_仓库协作规范.md`](../../docs/06_仓库协作规范.md) 第 4 节）。

## 维护约定

- 改动验收标准时，`docs/01_项目规划.md`、这里的卡片、GitHub 上的 Issue 正文**要同步更新**，否则下次重新发布会把 GitHub 侧的改动覆盖掉。
- 卡片标题取第一行 `# [P?] ...`，正文取 `---` 以下内容；[`../../scripts/create_issues.py`](../../scripts/create_issues.py) 按这个格式解析，不要改格式。
- 仓库非代码配置（description / topics / 标签 / 里程碑 / Issue 挂载 / main 分支保护）统一放在 [`../repo-meta.json`](../repo-meta.json)，改完跑一次 `--setup`，远端被误改也会被修回；详见 [`../../docs/06_仓库协作规范.md`](../../docs/06_仓库协作规范.md) 第 7 节。

## 凭据：不需要新建 PAT

[`../../scripts/create_issues.py`](../../scripts/create_issues.py) 按以下顺序自动解析本机已有的 GitHub 凭据：

1. 环境变量 `GITHUB_TOKEN`（显式覆盖，调试或临时换身份时用）
2. `gh auth token`（本机装了 GitHub CLI 且已登录）
3. `git credential fill`（**复用 `git push` 使用的本机 OAuth 登录态**；本机实测 scopes 含 `repo`）

所以只要 `git push` 能用，脚本就能用。token 只在内存中使用，不写文件、不进命令行参数、不打印、不提交。

## 常用命令

```bash
python scripts/create_issues.py --dry-run                # 预览将创建哪些 Issue
python scripts/create_issues.py                        # 补发缺失的阶段 Issue（跳过同名）
python scripts/create_issues.py --links                 # 不用凭据，输出预填新建 Issue 链接
python scripts/create_issues.py --check-config          # 校验配置结构（CI 同款）
python scripts/create_issues.py --setup --dry-run       # 预览仓库配置变更，不写入
python scripts/create_issues.py --setup                # 按 repo-meta.json 同步全部非代码配置
```

`--setup` 全部幂等：已存在的标签 / 里程碑会跳过；分支保护逐字段比较，只在远端与配置不一致时重写；更新 Issue 时保留它上面已有的其他标签，只补 `stage/P?` 并挂里程碑。重复运行可以当作配置体检，远端被误改也会被修回。

匿名 `--setup --dry-run` 下，分支保护只展示本地目标值（该端点需认证）；显式设置 `GITHUB_TOKEN` 后可获得完整预览。

## 为什么用脚本而不是手动建 Issue

GitHub App 集成创建 Issue 返回 `403 Resource not accessible by integration`：该 App 未被授予 `Issues: Read and write`，而 App 的权限范围在注册时确定，重新授权无法补齐。
因此改为用本机凭据直接调用 REST API，脚本同时承担幂等同步的职责。

> `401` = 凭据无效或已撤销；`403` = 权限不足或触发限流。
