# YouTube Follower Tracking

每日自动追踪订阅 YouTube 频道的最新视频，抓取字幕存入 `feed.json`，配合 Claude Code skill 实时生成中文总结，并自动推送到 Notion。

---

## 效果预览

每天在 Notion 中自动生成一篇日报，格式如下：

```
📺 硅谷101播客 — OpenAI 发布 o3 模型，AGI 还有多远？
🔗 https://www.youtube.com/watch?v=xxx

💬 一句话核心观点
博主认为 o3 在数学和编程基准上已超越人类专家水平，但距离通用 AGI 仍差"常识推理"这一关键能力。

🧭 背景与前提
- 背景：OpenAI 在 2025 年底发布 o3，各项 benchmark 刷新纪录
- 立场：博主持乐观但审慎态度，认为 benchmark 不等于真实世界能力

📌 核心论点
- o3 在 ARC-AGI 测试得分 87.5%（人类均值 85%），首次超越人类
- 训练成本约 $1000/任务，推理成本过高是商业化瓶颈
- ...

🎯 结论 / 建议
关注 OpenAI 后续降本路线，2026 年是关键节点

⚠️ 风险 / 不确定因素
- benchmark 存在过拟合风险，实际能力可能被高估

🔍 延伸线索
- ARC-AGI 测试设计理念值得深入了解
```

---

## 架构设计

```
┌─────────────────────────────────────────────────────┐
│                   第一层：数据抓取                    │
│                                                     │
│  GitHub Actions（每天 15:00 北京时间自动触发）         │
│      ↓                                              │
│  fetch.py                                           │
│      ├── YouTube Data API  →  获取频道最新视频        │
│      ├── Supadata API      →  抓取视频字幕            │
│      └── 写入 feed.json 并推送到仓库                  │
└─────────────────────────────────────────────────────┘
                          ↓ feed.json（公开可访问）
┌─────────────────────────────────────────────────────┐
│                   第二层：内容总结                    │
│                                                     │
│  方式 A：手动触发                                     │
│      Claude Code /YoutuberPointTracking             │
│          └── 读取 feed.json → 总结 → 保存本地 .md    │
│                                                     │
│  方式 B：自动触发（Claude Code /schedule）            │
│      Remote Agent（每天 15:30 自动运行）              │
│          └── 读取 feed.json → 总结 → 推送到 Notion   │
└─────────────────────────────────────────────────────┘
```

**数据更新逻辑：**
- 频道今日有新视频 → 用新数据覆盖该频道
- 频道今日无新视频 → 保留上次数据，不清空
- 频道首次运行且无历史数据 → 自动抓取最新一条做初始填充

这样 `feed.json` 中始终有内容，不会因为某天博主没更新而出现空白。

---

## 追踪频道（27个）

| 频道 | 领域 |
|------|------|
| 海伦子 Hellen | 美股 / 投资 |
| 硅谷101播客 | 科技 / 创业 |
| 美投讲美股 | 美股分析 |
| 美股先锋 | 美股分析 |
| 美股博士 | 美股分析 |
| 老石谈芯 | 芯片 / 科技 |
| 股市咖啡屋 Stock Cafe | 美股 / 港股 |
| 视野环球财经 | 宏观财经 |
| LEI | 市场分析 |
| PowerUpGammas | 期权策略 |
| Sober 聊期权 CFA | 期权 / 投资 |
| SpaceX | 航天科技 |
| 一口新饭 | 财经 / 生活 |
| 华尔街阿宝 | 美股 / 财经 |
| 富翁電視 MTTV | 港台财经 |
| 小Lin说 | 财经科普 |
| 小岛大浪吹 | 财经 / 时事 |
| 投资TALK君 | 美股投资 |
| BWB - Business With Brian | 商业 / 投资 |
| 猴哥财经 HG Finance | 美股财经 |
| 美股查理 | 美股分析 |
| 美投侃新闻 | 财经新闻 |
| Nick 美股咖啡館 | 美股分析 |
| Terry Chen 泰瑞 | 美股 / 投资 |
| Couch Investor | 投资 |
| Future Investing | 投资 |
| 美股投资网 | 美股资讯 |

想追踪其他频道？在 `fetch.py` 的 `CHANNELS` 列表中添加即可：
```python
{"name": "频道显示名", "handle": "YouTube handle（@后面的部分）"},
```
如果不知道 handle，留空则自动按名称搜索。

---

## 自行部署

### 第一步：Fork 本仓库

点击右上角 Fork，克隆到你自己的 GitHub 账号。

### 第二步：申请 API Key

**YouTube Data API v3**
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建项目 → 启用 YouTube Data API v3
3. 创建 API 密钥，应用限制选「无」，API 限制选「YouTube Data API v3」

**Supadata**
1. 前往 [supadata.ai](https://supadata.ai/) 注册账号
2. 免费额度：每月 100 次字幕抓取
3. 在 Dashboard 获取 API Key

### 第三步：配置 GitHub Secrets

进入你的仓库 `Settings → Secrets and variables → Actions → New repository secret`，添加两个 Secret：

| Name | Value |
|------|-------|
| `YOUTUBE_API_KEY` | 你的 YouTube API Key |
| `SUPADATA_API_KEY` | 你的 Supadata API Key |

### 第四步：启用 GitHub Actions

进入仓库的 `Actions` 标签页，点击启用 Workflows。

之后每天 UTC 7:00（北京时间 15:00）会自动运行，也可以手动点击 `Run workflow` 立即触发。

### 第五步：安装 Claude Code Skill

将 `SKILL.md` 放入 Claude Code 的 skills 目录：

```bash
# 创建 skill 文件夹
mkdir -p ~/.claude/skills/YoutuberPointTracking

# 复制 SKILL.md
cp SKILL.md ~/.claude/skills/YoutuberPointTracking/SKILL.md
```

之后在 Claude Code 中输入 `/YoutuberPointTracking` 即可触发每日总结。

### 第六步：配置自动推送到 Notion（可选）

使用 Claude Code 的 `/schedule` 功能，创建一个每天 15:30 自动运行的远程 Agent，读取 `feed.json` 并将总结写入 Notion 指定页面。具体配置参考 `SKILL.md`。

---

## feed.json 数据格式

```json
{
  "generated_at": "2026-03-28T07:00:00Z",
  "videos": [
    {
      "channel": "硅谷101播客",
      "title": "视频标题",
      "url": "https://www.youtube.com/watch?v=xxx",
      "transcript": "视频字幕全文（最多 50000 字符）..."
    }
  ]
}
```

`feed.json` 托管在 GitHub 上，可通过以下地址直接访问：
```
https://raw.githubusercontent.com/你的用户名/YouTube-Follower-Tracking/main/feed.json
```

---

## API 配额说明

YouTube Data API v3 每日免费配额 **10,000 单位**：

| 操作 | 接口 | 消耗 |
|------|------|------|
| 通过 handle 查频道 ID | Channels API | 1 单位 |
| 查询频道最新视频 | PlaylistItems API | 1 单位 |
| 通过名称搜索频道 | Search API | 100 单位（尽量避免） |

27 个频道每日正常运行约消耗 **54 单位**，远低于 10,000 上限。

---

## 致谢

灵感来自 [zarazhangrui/follow-builder](https://github.com/zarazhangrui/follow-builder)
