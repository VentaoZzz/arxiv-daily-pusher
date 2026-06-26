# arXiv Daily Paper Pusher

自动获取昨日 arXiv 论文，按研究组关键词匹配评分，推送至飞书群。

## ✨ 功能特性

- 📚 **多研究组** — 可配置多个研究组，每组独立关键词
- 🔍 **智能评分** — 标题匹配权重 2x，摘要匹配权重 1x，归一化到 [0, 1]
- 🚀 **双模式 API** — arxiv 库优先，超时自动降级到 HTTP API
- 📤 **飞书推送** — 支持按组分批推送或合并单条推送
- ⏰ **内置定时** — `--schedule` 一键挂起，每天定时运行
- 💻 **全平台** — Windows / Linux / macOS 均可运行

---

## 🚀 快速开始

### 方式一：纯 Python 运行（推荐，全平台通用）

适合所有用户，Windows / Linux / macOS 都行，不依赖任何外部调度工具。

```bash
# 1. 克隆项目
git clone https://github.com/VentaoZzz/arxiv-daily-pusher.git
cd arxiv-daily-pusher

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置
cp config.example.yaml config.yaml
# 编辑 config.yaml，填入你的飞书 Webhook URL 和关键词

# 4. 测试运行（单次执行）
python main.py

# 5. 定时运行（每天 10:30 自动执行，进程常驻）
python main.py --schedule 10:30
```

> 💡 `--schedule` 模式启动后会**立即执行一次**，之后每天在指定时间重复运行。按 `Ctrl+C` 停止。

**后台运行建议：**

```bash
# Linux / macOS — 用 nohup 挂后台
nohup python main.py --schedule 10:30 > cron.log 2>&1 &

# Windows — 用 pythonw 或 start 命令
start /b python main.py --schedule 10:30 > cron.log 2>&1

# 或者用 screen / tmux（Linux）
screen -dmS arxiv python main.py --schedule 10:30
```

---

### 方式二：OpenClaw / Claude Code 自动部署

如果你使用 [OpenClaw](https://github.com/openclaw/openclaw) 或 Claude Code，可以把下面这段提示词直接粘贴给 AI 助手，它会自动完成安装和定时任务配置：

<summary>📋 点击复制提示词</summary>

```
请帮我部署 arxiv-daily-pusher 项目，步骤如下：

1. 克隆仓库：git clone https://github.com/YOUR_USERNAME/arxiv-daily-pusher.git
2. 进入目录：cd arxiv-daily-pusher
3. 安装 Python 依赖：pip install -r requirements.txt
4. 复制配置模板：cp config.example.yaml config.yaml
5. 编辑 config.yaml，我需要配置以下内容：
   - feishu_webhook: （我会提供）
   - groups: （我会提供研究组名称和关键词）
   - top_k: 6
   - timezone_offset: 8
   - api_mode: auto
   - push_strategy: per_group
6. 先运行一次测试：python main.py
7. 如果测试成功，设置每天 10:30 的定时任务（用 cron 或 --schedule 均可）

我的飞书 Webhook URL 是：[在这里填你的 URL]
我的研究组和关键词是：
- 组1名称: [名称]，关键词: [keyword1, keyword2, ...]
- 组2名称: [名称]，关键词: [keyword1, keyword2, ...]
```


或者直接通过ClawHub一键命令安装
```
# 通过 ClawHub 安装
clawhub install arxiv-daily-pusher

```

---

### 方式三：系统级定时任务（可选）

如果你不想让 Python 进程常驻，可以用系统自带的定时任务来调度。

**Linux / macOS — crontab：**

```bash
# 编辑 crontab
crontab -e

# 每天 10:30（北京时间 = UTC 02:30）执行
30 2 * * * cd /path/to/arxiv-daily-pusher && /usr/bin/python3 main.py >> cron.log 2>&1
```

**Windows — 任务计划程序：**

```powershell
# 用 PowerShell 创建定时任务（每天 10:30 运行）
$action = New-ScheduledTaskAction `
    -Execute "python" `
    -Argument "main.py" `
    -WorkingDirectory "C:\path\to\arxiv-daily-pusher"

$trigger = New-ScheduledTaskTrigger -Daily -At "10:30"

Register-ScheduledTask `
    -TaskName "arXiv Daily Pusher" `
    -Action $action `
    -Trigger $trigger `
    -Description "Daily arXiv paper fetch and push"
```

或者通过 GUI：`Win+R` → `taskschd.msc` → 创建基本任务 → 设置每日触发。

**OpenClaw Cron（适合已有 OpenClaw 的用户）：**

```bash
openclaw cron add --name "arXiv Daily" --schedule "30 2 * * *" --command "cd /path/to/arxiv-daily-pusher && python main.py"
```

---

## 📝 配置说明

### 配置文件

复制模板并编辑：

```bash
cp config.example.yaml config.yaml
```

```yaml
# 研究组配置
groups:
  - name: "Group A - Memory & RL"
    keywords:
      - "memory"
      - "reinforcement learning"
      - "agent"

  - name: "Group B - Electronic Design"
    keywords:
      - "Verilog generation"
      - "Electronic Design"

# 飞书 Webhook URL（必填）
feishu_webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_TOKEN"

# 全局设置
top_k: 6                    # 每组推送论文数
timezone_offset: 8          # 时区偏移（北京时间=8）
api_mode: "auto"            # auto | arxiv_only | http_only
push_strategy: "per_group"  # per_group | single
```

### 获取飞书 Webhook

1. 在飞书群聊中点击 **设置** → **群机器人** → **添加机器人**
2. 选择 **自定义机器人**
3. 复制 **Webhook 地址** 填入 `config.yaml`

> 📖 **详细图文教程**请参考项目内的 `arxiv-daily-pusher-feishu-demo.pdf`，有手把手保姆级飞书配置指南。

### 研究组配置

```yaml
groups:
  - name: "显示名称"       # 推送消息中的标题
    keywords:              # 关键词列表（OR 关系）
      - "keyword1"
      - "keyword2"
```

### API 模式

| 模式 | 说明 |
|------|------|
| `auto` | 优先 arxiv 库，15 秒超时自动降级到 HTTP API（推荐） |
| `arxiv_only` | 仅使用 arxiv 库 |
| `http_only` | 仅使用 HTTP API |

### 推送策略

| 策略 | 说明 |
|------|------|
| `per_group` | 每个研究组单独推送一条消息 |
| `single` | 所有组合并为一条消息推送 |

---

## 📐 评分算法

论文相关性得分计算：
- 标题匹配关键词：**+2 分**
- 摘要匹配关键词：**+1 分**
- 最终得分归一化到 **[0, 1]**

```
关键词: ["memory", "reinforcement learning", "agent"]
最大可能得分: 3 keywords × 3 points = 9

论文 A: 标题含 "memory"，摘要含 "agent"
得分: (2 + 1) / 9 = 0.333
```

---

## 📁 项目结构

```
arxiv-daily-pusher/
├── main.py                           # 入口（支持 --schedule 定时）
├── fetch_papers.py                   # arXiv 论文获取（双模式 API + 跨平台超时）
├── rank_papers.py                    # 相关性评分排序
├── push_feishu.py                    # 飞书推送
├── config.example.yaml               # 配置模板
├── requirements.txt                  # Python 依赖
├── arxiv-daily-pusher-feishu-demo.pdf # 飞书配置保姆级教程
├── SKILL.md                          # OpenClaw Skill 描述
└── README.md
```

---

## 🔧 命令行参数

```
python main.py [--schedule HH:MM]

参数:
  --schedule HH:MM    每天定时运行（本地时间），进程常驻
                      省略则单次执行后退出

示例:
  python main.py                  # 立即执行一次
  python main.py --schedule 10:30 # 每天 10:30 执行，首次启动也会立即运行
```

---

## ❓ 故障排查

| 问题 | 解决方案 |
|------|----------|
| 无论文返回 | 检查关键词是否过于具体；尝试 `http_only` 模式；确认 arXiv 昨日有更新 |
| 推送失败 | 检查 Webhook URL 是否正确；确认机器人未被移除；查看控制台错误 |
| API 超时 | 北京时间下午14:00-20:00进行测试的话非常容易遇到API超时问题，**建议北京时间上午进行测试**。使用 `http_only` 模式绕过 arxiv 库；检查网络 |
| Windows 报错 | 确保 Python 3.10+；旧版本有 `signal.SIGALRM` 兼容问题，已在新版修复 |

---

## 📦 依赖

- Python 3.10+
- arxiv >= 2.1.0
- PyYAML >= 6.0
- requests >= 2.31.0
- schedule >= 1.2.0

---

## 📄 开源协议

MIT License

## 🤝 贡献

欢迎 Issue 和 PR！
