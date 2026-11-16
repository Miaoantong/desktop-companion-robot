# 桌面机器人平台 · Force-Sensing Desk Robot

[![持续集成](https://github.com/Miaoantong/desktop-companion-robot/actions/workflows/ci.yml/badge.svg)](https://github.com/Miaoantong/desktop-companion-robot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个**带力觉反馈的桌面机器人平台**：用舵机电流反推外力，在一颗 STM32 上跑 1kHz 实时闭环与端侧推理，断网时依然活着。

> 主线是嵌入式实时系统与力觉交互；应用示例是"一个不拍你脸、会在该闭嘴时闭嘴的桌面学习搭档"。
> 技术主张：**慢脑 - 快反射** —— AI 只写状态槽，实时性留在 MCU 上。
> 关键词：`sensorless force estimation` · `on-device inference` · `real-time contract with graceful degradation`
> 当前：**C1 起步** · 能力阶梯见 [`docs/01`](docs/01_项目规划.md) 第 3 节 · 许可证：[MIT](LICENSE)
> 已有可运行代码：协议层（CRC8 + 帧编解码）**63 项断言、零外部依赖**，`make -C firmware test` 秒级验证

---

## 它是什么

**技术定义**：一个双自由度、带力觉反馈的桌面机器人平台，四项核心能力——

1. **实时控制环**：1kHz 舵机环，微秒级确定性
2. **无传感器力估计**：不装触摸传感器，用舵机电流反推外力
3. **端侧推理**：20KB RAM 的 M3 上部署 int8 模型
4. **故障降级**：断连、断网、传感器失效时不失控

**应用示例**：把它摆在学习桌上，它就是一个不拍你脸的桌面学习搭档。

| 传统做法 | 本项目 |
|---|---|
| 评测它"聊得好不好" | 评测它"**能不能在该沉默时沉默**" |
| 摄像头拍脸做情绪识别 | 毫米波雷达 + 声学，**默认不采集图像** |
| 大模型直接驱动表情 | AI 只写"情绪状态槽"，执行层保证 <50ms 反射 |
| 加个触摸模块做互动 | **用舵机电流反推外力**，零额外传感器 |

---

## 技术主张：慢脑 - 快反射

AI 推理是秒级且抖动的，而"转头看你"必须在 150ms 内完成。所以三级分工：

| 层 | 硬件 | 职责 | 时间尺度 |
|---|---|---|---|
| **L0 反射层** | STM32F103C8T6 | 1kHz 舵机环、电流采样、参数化表情、情绪状态槽 | 微秒 ~ 10ms，硬实时 |
| **L1 感知层** | ESP32-S3 | 唤醒词、雷达在场检测、声学 | 10 ~ 300ms |
| **L2 认知层** | 边缘算力（先用笔记本） | 行为识别、记忆、主动策略 | 秒级，允许抖动 |

**硬约束：AI 断连时机器人必须依然"活着"** —— 表情、摸头、转头全部在 L0 本地闭环，只是不"思考"。

---

## 能力阶梯

按**依赖关系**推进，不绑日历。每一级都能独立演示、独立写进简历，中途停下来不会烂尾。
详细定义与验收见 [`docs/01_项目规划.md`](docs/01_项目规划.md) 第 3 节。

| 级 | 能力 | 最小可演示 | 追踪 |
|---|---|---|---|
| **C1** | 会点灯说话 | 舵机转到指定角 + 串口命令行 | [#1](https://github.com/Miaoantong/desktop-companion-robot/issues/1) |
| **C2** | 会画脸 | 眨眼 + 表情切换，帧率可见 | [#1](https://github.com/Miaoantong/desktop-companion-robot/issues/1) |
| **C3** | 会测电流 | 4 类波形可复现 + 分类准确率 | [#2](https://github.com/Miaoantong/desktop-companion-robot/issues/2) |
| **C4** | 会闭环 ★分水岭 | 轻拍 / 重按 / 推动 / 堵转 四种反应 | [#2](https://github.com/Miaoantong/desktop-companion-robot/issues/2) |
| **C5** | 会想事 | 断连仍能自主表情 + 推理耗时数据 | [#2](https://github.com/Miaoantong/desktop-companion-robot/issues/2)–[#3](https://github.com/Miaoantong/desktop-companion-robot/issues/3) |
| **C6** | 会做系统 | 6 类故障注入全过 + benchmark 表 | [#3](https://github.com/Miaoantong/desktop-companion-robot/issues/3) |

> P3（认知层）与 P4（作品集）不在这条阶梯上——它们是**加在完整产品之上**的能力，砍掉不影响演示。

---

## 验收指标

| 指标 | 目标 |
|---|---|
| 电流 4 类分类准确率 | ≥ 85%（自采 500 样本） |
| 触摸 → 表情响应 | ≤ 50 ms |
| 堵转检测 → 卸力 | ≤ 200 ms |
| 表情帧率 | ≥ 35 fps |
| 在场检测误报率 | ≤ 10% |

---

## 硬件

- **主控**：STM32F103C8T6 最小系统板
- **显示**：0.96 寸 I2C OLED（SSD1306，128×64）
- **动作**：SG90 舵机 ×2
- **触觉**：0.1Ω 采样电阻 + MCP6002 差分放大（**不用触摸模块**）
- **P2 起**：ESP32-S3、INMP441、LD2410C 毫米波雷达

详见 [`docs/02_硬件清单.md`](docs/02_硬件清单.md)。

---

## 目录结构

> 进度以 [`docs/01_项目规划.md`](docs/01_项目规划.md) 的能力阶梯为准。
> `app/` 与 `tests/` 已有代码并通过 CI；`bsp/`、`platform/`、`tools/` 在 C1 接线时按 [`firmware/README.md`](firmware/README.md) 建立。

```
desktop-companion-robot
├── README.md                  # 项目总览（本文件）
├── LICENSE                    # MIT
├── CONTRIBUTING.md            # 分支、提交、协作约定
├── .gitignore
├── .github/
│   ├── ISSUE_TEMPLATE/        # Bug / 功能 / 里程碑追踪模板
│   ├── ISSUES/                # P0~P4 追踪卡，已发布为 Issue #1~#5
│   ├── repo-meta.json         # 非代码配置（描述 / topics / 标签 / 里程碑 / 分支保护）
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/ci.yml       # 文档链接 + 配置校验
├── scripts/
│   ├── check_docs.py          # 校验 Markdown 相对链接（CI 同一套）
│   └── create_issues.py       # 发布 Issue；--setup 同步配置；--check-config 校验
├── docs/                      # 01~07：规划、硬件、方案、路线、协作规范、亮点与证据
├── hardware/                  # 接线说明（原理图 / 结构待补）
└── firmware/                  # 单一工程，分层规则见 firmware/README.md
    ├── README.md              # 分层规则与构建约定
    ├── app/protocol/          # 业务逻辑（禁止依赖 HAL）：CRC8、帧编解码
    ├── bsp/                   # 板级支持（唯一允许碰 HAL 的层）— C1 起创建
    ├── platform/              # CubeMX 生成，不手改 — C1 起生成
    ├── tests/                 # host 端单元测试（gcc 直接编，无需板子）
    ├── tools/                 # 上位机与数据分析脚本 — C3 起创建
    └── Makefile               # make test：与 CI 完全同一条命令
```

---

## 30 秒验证

不需要板子、不需要 Keil、不需要任何第三方库：

```bash
make -C firmware test
```

```
host tests

[ RUN  ] suite_crc8
[  OK  ] suite_crc8
[ RUN  ] suite_frame
[  OK  ] suite_frame

63 checks, 0 failure(s)
RESULT: PASS
```

之所以能在 PC 上跑，是因为 `app/` 不 include 任何 HAL 头文件。这条规则由 CI 双重把关：
**编译器**（host 编译时根本没有 HAL 的 include 路径）+ **文本检查**（`grep` 反向依赖，报错比编译器直白）。

---

## 开发环境

- Keil MDK（D:\Keil_v5）
- STM32CubeMX（D:\ST）
- 采用 **HAL 库**开发，工程由 CubeMX 生成，逻辑写在 `USER CODE` 区
- 逻辑层验证：任意 C99 编译器 + make，命令见上一节；**Keil 只用于下载与断点调试**
- 文档检查脚本：`python scripts/check_docs.py`（仅需 Python 3，无第三方依赖）

---

## 文档

| 文档 | 回答什么问题 |
|---|---|
| [`01_项目规划.md`](docs/01_项目规划.md) | 做什么、不做什么、各阶段验收 |
| [`02_硬件清单.md`](docs/02_硬件清单.md) | 买什么、怎么供电、主控怎么分工 |
| [`03_学习日志.md`](docs/03_学习日志.md) | 每天学了什么、踩了什么坑 |
| [`04_技术方案.md`](docs/04_技术方案.md) | 怎么做、为什么这样选型 |
| [`05_学习路线.md`](docs/05_学习路线.md) | 18 周怎么学、每周验收题 |
| [`06_仓库协作规范.md`](docs/06_仓库协作规范.md) | 分支、提交、里程碑、发布、工程化差距 |
| [`07_技术亮点与证据链.md`](docs/07_技术亮点与证据链.md) | 亮点凭什么成立、拿什么证明、面试怎么答 |

- 接线 → [`hardware/接线说明.md`](hardware/接线说明.md)
- 固件工程约定 → [`firmware/README.md`](firmware/README.md)

---

## 参与协作

分支与提交规范见 [`CONTRIBUTING.md`](CONTRIBUTING.md)，阶段与里程碑映射见
[`docs/06_仓库协作规范.md`](docs/06_仓库协作规范.md)。提交前跑一次 `python scripts/check_docs.py` 和 `make -C firmware test`，CI 会做同样的事。

阶段进度以 [Issue #1–#5](https://github.com/Miaoantong/desktop-companion-robot/issues) 为准，验收清单在 Issue 里逐项打勾；正文的单一来源是 `.github/ISSUES/P0.md`–`P4.md`，改完跑 `python scripts/create_issues.py --update-bodies` 同步到远端（`--dry-run` 先预览）。

仓库非代码配置（description / topics / 标签 / 里程碑 / Issue 挂载 / main 分支保护）集中在 [`.github/repo-meta.json`](.github/repo-meta.json)：改完执行 `python scripts/create_issues.py --setup` 即可同步，远端被误改也会按配置修回；`--setup --dry-run` 预览变更、`--check-config` 校验配置（CI 同款）。凭据自动复用本机 Git 登录态，**不需要新建 PAT**。

---

## 许可证

[MIT](LICENSE) © 2026 Miaoantong
