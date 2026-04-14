# arXiv Daily Paper Pusher

自动获取昨日 arXiv 论文，按研究组关键词匹配并排序，推送至飞书群。

## 功能特性

- 📚 **多研究组支持** - 可配置多个研究组，每组独立关键词
- 🔍 **智能匹配** - 标题匹配权重 2x，摘要匹配权重 1x
- 🚀 **双模式 API** - arxiv 库优先，超时自动降级到 HTTP API
- 📤 **飞书推送** - 支持按组分批推送或合并单条推送
- ⏰ **定时任务** - 建议每日上午运行，获取昨日论文

## 快速开始

### 1. 安装

```bash
# 通过 ClawHub 安装
clawhub install arxiv-daily-pusher

# 或手动克隆
git clone https://github.com/YOUR_USERNAME/arxiv-daily-pusher.git
cd arxiv-daily-pusher
pip install -r requirements.txt
```

### 2. 配置

复制配置模板并修改：

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`：

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

### 3. 获取飞书 Webhook

1. 在飞书群聊中点击 **设置** → **群机器人** → **添加机器人**
2. 选择 **自定义机器人**
3. 复制 **Webhook 地址** 填入 `config.yaml`

### 4. 运行测试

```bash
python main.py
```

成功后会看到：
```
🚀 arXiv Daily Pusher started for 2025-01-14
⏳ Fetching: Group A - Memory & RL
   Candidates: 12
📤 Pushing to Feishu (strategy: per_group)...
   ✅ Successfully pushed Group A - Memory & RL
✅ Phase 2 complete.
```

### 5. 设置定时任务

**OpenClaw Cron（推荐）：**

```bash
openclaw cron add --name "arXiv Daily" --schedule "30 2 * * *" --command "python main.py"
```

**Linux Crontab：**

```bash
# 每天上午 10:30 运行（北京时间）
30 2 * * * cd /path/to/arxiv-daily-pusher && /usr/bin/python3 main.py >> cron.log 2>&1
```

## 配置详解

### 研究组配置

```yaml
groups:
  - name: "研究组名称"      # 显示在推送消息中的名称
    keywords:               # 关键词列表，OR 关系
      - "keyword1"
      - "keyword2"
```

### API 模式

| 模式 | 说明 |
|------|------|
| `auto` | 优先使用 arxiv 库，15秒超时后自动降级到 HTTP API |
| `arxiv_only` | 仅使用 arxiv 库 |
| `http_only` | 仅使用 HTTP API（无超时保护） |

### 推送策略

| 策略 | 说明 |
|------|------|
| `per_group` | 每个研究组单独推送一条消息 |
| `single` | 所有组合并成一条长消息推送 |

## 项目结构

```
arxiv-daily-pusher/
├── main.py              # 入口脚本
├── fetch_papers.py      # arXiv 论文获取（含双模式 API）
├── rank_papers.py       # 相关性评分排序
├── push_feishu.py       # 飞书推送
├── config.example.yaml  # 配置模板
├── requirements.txt     # Python 依赖
├── SKILL.md             # OpenClaw Skill 描述
└── README.md            # 本文件
```

## 评分算法

论文相关性得分计算：
- 标题匹配关键词：+2 分
- 摘要匹配关键词：+1 分
- 最终得分归一化到 [0, 1]

示例：
```
关键词: ["memory", "reinforcement learning", "agent"]
最大可能得分: 3 × 3 = 9

论文A: 标题含 "memory", 摘要含 "agent"
得分: (2 + 1) / 9 = 0.3333
```

## 故障排查

### 无论文返回
- 检查关键词是否过于具体
- 尝试使用 `http_only` 模式
- 确认 arXiv 昨日确实有相关论文

### 推送失败
- 检查 Webhook URL 是否正确
- 确认飞书机器人未被移除
- 查看 `execution.log` 详细错误

### API 超时
- 使用 `http_only` 模式绕过 arxiv 库
- 检查网络连接
- 增加超时时间（修改 `fetch_papers.py`）

## 依赖

- Python 3.10+
- arxiv >= 2.1.0
- PyYAML >= 6.0
- requests >= 2.31.0

## 开源协议

MIT License

## 贡献

欢迎 Issue 和 PR！
