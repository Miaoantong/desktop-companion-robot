# 桌面陪伴机器人 · Desktop Companion Robot

一个不拍你脸、会在该闭嘴时闭嘴的桌面学习搭档。

> 个人实践项目，也是我学嵌入式 / 机器人开发的主线载体。
> 技术主张：**慢脑 - 快反射** —— AI 只做"建议"，实时性留在 MCU 上。
> 当前阶段：**P0**（2026.11 – 2027.01） · 许可证：[MIT](LICENSE) · 仓库目前以文档为主，固件工程处于骨架阶段

---

## 它是什么

不是"会聊天的桌面玩具"，而是：

> **一个隐私优先、慢脑 - 快反射架构的桌面具身智能体，聚焦学习场景下的在场感知与主动干预。**

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

## 阶段

| 阶段 | 时间 | 内容 | 状态 | 追踪 |
|---|---|---|---|---|
| **P0** | 2026.11 – 2027.01 | 表情脸 + 转头收尾；参数化表情渲染；延迟测量框架 | 进行中 | [#1](https://github.com/Miaoantong/desktop-companion-robot/issues/1) |
| **P1** | 2027.02 – 2027.04 | **电流感知触觉**：摸头分级、柔顺退让、堵转保护 | 计划中 | [#2](https://github.com/Miaoantong/desktop-companion-robot/issues/2) |
| **P2** | 2027.05 – 2027.08 | ESP32-S3 接入；UART 协议；雷达在场感知 | 计划中 | [#3](https://github.com/Miaoantong/desktop-companion-robot/issues/3) |
| **P3** | 2027.09 – 2028.01 | 边缘侧行为识别；主动干预策略；记忆系统 | 计划中 | [#4](https://github.com/Miaoantong/desktop-companion-robot/issues/4) |
| **P4** | 2028.02 – 2028.05 | 外壳、benchmark、开源整理；对话模块（可选） | 计划中 | [#5](https://github.com/Miaoantong/desktop-companion-robot/issues/5) |

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

> 标注「骨架」的目录已建立但还没有工程代码；进度以 [`docs/01_项目规划.md`](docs/01_项目规划.md) 的验收清单为准。

```
desktop-companion-robot
├── README.md                  # 项目总览（本文件）
├── LICENSE                    # MIT
├── CONTRIBUTING.md            # 分支、提交、协作约定
├── .gitignore
├── .github/
│   ├── ISSUE_TEMPLATE/        # Bug / 功能 / 里程碑追踪模板
│   ├── ISSUES/                # P0~P4 追踪卡，已发布为 Issue #1~#5
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/ci.yml       # 文档链接检查
├── scripts/
│   ├── check_docs.py          # 校验 Markdown 相对链接（CI 同一套）
│   └── create_issues.py       # 从追踪卡发布 / 预填阶段 Issue
├── docs/                      # 01~06：规划、硬件、方案、路线、协作规范
├── hardware/                  # 接线说明（原理图 / 结构待补）
└── firmware/
    ├── README.md              # 工程编号规则与约定
    ├── 里程碑01_表情脸/        # 骨架 · P0
    ├── 里程碑02_会转头/        # 骨架 · P0
    ├── 10_电流触觉/            # 骨架 · P1 实验工程
    ├── 20_表情引擎v2/          # 骨架 · P1 参数化渲染
    ├── 90_v1_整合/             # 骨架 · P2 起最终产品工程
    └── shared/                 # 骨架 · 跨工程协议定义
```

---

## 开发环境

- Keil MDK（D:\Keil_v5）
- STM32CubeMX（D:\ST）
- 采用 **HAL 库**开发，工程由 CubeMX 生成，逻辑写在 `USER CODE` 区
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
| [`06_仓库协作规范.md`](docs/06_仓库协作规范.md) | 分支、提交、里程碑、发布 |

- 接线 → [`hardware/接线说明.md`](hardware/接线说明.md)
- 固件工程约定 → [`firmware/README.md`](firmware/README.md)

---

## 参与协作

分支与提交规范见 [`CONTRIBUTING.md`](CONTRIBUTING.md)，阶段与里程碑映射见
[`docs/06_仓库协作规范.md`](docs/06_仓库协作规范.md)。提交前跑一次 `python scripts/check_docs.py`，CI 会做同一项检查。

阶段进度以 [Issue #1–#5](https://github.com/Miaoantong/desktop-companion-robot/issues) 为准，验收清单在 Issue 里逐项打勾；正文的单一来源是 `.github/ISSUES/P0.md`–`P4.md`，改动验收标准时两处要同步更新。

---

## 许可证

[MIT](LICENSE) © 2026 Miaoantong
