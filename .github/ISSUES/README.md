# 阶段追踪卡（待发布为 GitHub Issue）

这 5 个文件是 P0–P4 阶段的 Issue 正文草稿，内容与 `docs/01_项目规划.md` 的验收清单一一对应。

**为什么放在仓库里**：GitHub 集成创建 Issue 返回 `403 Resource not accessible by integration`，即该 GitHub App 没有被授予 `Issues: Read and write`。App 的权限范围是**注册时**由平台方勾选的，安装者只能批准已列出的权限——因此**重新授权补不了这项权限**，不要在这上面反复尝试。内容先纳入版本管理，用下面任一种方式发布即可。

## 怎么发布（三选一）

**① 脚本 + 个人 token（推荐，可重复执行）**

1. 生成 fine-grained PAT：https://github.com/settings/personal-access-tokens/new
   - Expiration 选最短（如 7 天，用完删除）
   - Resource owner 选自己的账号；Repository access → **Only select repositories** → 只勾本仓库
   - Permissions → Repository permissions → **Issues: Read and write**（其余保持 No access）
2. 在项目根目录执行（token 只走环境变量，不写进仓库）：

```bash
python scripts/create_issues.py --dry-run            # 先预览
GITHUB_TOKEN=xxx python scripts/create_issues.py    # Git Bash / macOS / Linux
```

Windows PowerShell 写法：

```powershell
$env:GITHUB_TOKEN = "xxx"; python scripts/create_issues.py
```

脚本会读取本目录的 `P0.md`–`P4.md`，自动跳过同名 Issue，成功后打印编号与链接，最后输出 `完成：新建 5 个，跳过 0 个`。

> token 不要写进任何文件、不要提交；有效期设短，用完立刻在 PAT 页面 Delete。
> 本机实测 Python 标准库访问 `api.github.com` 可直连（HTTP 200），**不需要**像 `git push` 那样临时关闭证书校验。

**② 预填链接（不用 token）**

```bash
python scripts/create_issues.py --links
```

会输出 5 个带 title / body 的「新建 Issue」链接，逐个点开确认提交即可。

**③ 手动复制**

打开文件，标题取第一行 `# [P?] ...`，正文取「---」以下内容，粘贴到 Issues → New issue。

> 发布后建议按 `docs/06_仓库协作规范.md` 第 5 节补 `stage/P?` 标签，并在 Settings → Milestones 里建对应里程碑。

| 文件 | 阶段 | 建议标题 |
|---|---|---|
| [P0.md](P0.md) | P0 · 2026.11 – 2027.01 | `[P0] 表情脸 + 转头 + 可测量` |
| [P1.md](P1.md) | P1 · 2027.02 – 2027.04 | `[P1] 电流感知触觉：无传感器力估计` |
| [P2.md](P2.md) | P2 · 2027.05 – 2027.08 | `[P2] 异构架构 + 隐私在场感知` |
| [P3.md](P3.md) | P3 · 2027.09 – 2028.01 | `[P3] 认知层：行为识别、主动策略与记忆` |
| [P4.md](P4.md) | P4 · 2028.02 – 2028.05 | `[P4] 完整作品与开源整理` |

> 验收清单以 [`../../docs/01_项目规划.md`](../../docs/01_项目规划.md) 为准；改动验收标准时，**规划文档和这里的卡片要同一次提交**。
