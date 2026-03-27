# YouTube Follower Tracking

每日自动追踪订阅 YouTube 频道的最新视频，抓取字幕存入 `feed.json`，配合 Claude Code skill 实时生成中文总结。

---

## 工作原理

```
GitHub Actions (每天 15:00 北京时间)
    └── 抓取各频道最新视频字幕
    └── 写入 feed.json 并推送到仓库

Claude Code /YoutuberPointTracking skill
    └── 读取 feed.json
    └── 用中文总结每个视频核心内容
    └── 保存为每日 .md 文件 / 推送到 Notion
```

**数据逻辑：**
- 频道有新视频 → 更新该频道数据
- 频道无新视频 → 保留上次数据
- 频道从未有数据 → 自动抓取最新一条做初始填充

---

## 追踪频道

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

---

## 数据格式

`feed.json` 结构：

```json
{
  "generated_at": "2026-03-28T07:00:00Z",
  "videos": [
    {
      "channel": "频道名",
      "title": "视频标题",
      "url": "https://www.youtube.com/watch?v=xxx",
      "transcript": "视频字幕全文..."
    }
  ]
}
```

---

## 自行部署

### 1. Fork 本仓库

### 2. 申请 API Key

| 服务 | 用途 | 获取方式 |
|------|------|---------|
| YouTube Data API v3 | 查询频道和视频 | [Google Cloud Console](https://console.cloud.google.com/) |
| Supadata | 抓取视频字幕 | [supadata.ai](https://supadata.ai/) |

### 3. 配置 GitHub Secrets

在仓库 `Settings → Secrets and variables → Actions` 中添加：

```
YOUTUBE_API_KEY=你的 YouTube API Key
SUPADATA_API_KEY=你的 Supadata API Key
```

### 4. 启用 GitHub Actions

Actions 会在每天 UTC 7:00（北京时间 15:00）自动运行。也可在 Actions 页面手动触发。

### 5. 配置 Claude Code Skill（可选）

将 `YoutuberPointTracking` skill 安装到 Claude Code，即可用 `/YoutuberPointTracking` 指令实时总结当日内容。

---

## API 配额说明

YouTube Data API v3 每日免费配额 **10,000 单位**。本项目使用 Playlist API 查询视频（1单位/次），配额消耗极低，日常使用完全够用。

---

## 致谢

灵感来自 [zarazhangrui/follow-builder](https://github.com/zarazhangrui/follow-builder)
