# Personal Knowledge Archive

这是一个本地优先（local-first）的个人知识归档仓库，包含两大模块：

1. **英文阅读助手（English Audiobook Reading Assistant）**
2. **周/月晨报归档系统（Weekly/Monthly Briefing Archive）**

全流程使用本地 Markdown/CSV 文件，不调用外部 API。

## 项目目标

- 记录并复盘英文有声书输入（章节、时长、难点、感想）；
- 累积可复用词汇，维护个人词汇表；
- 将晨报信息按**周**与**月**沉淀为结构化知识资产；
- 不保存每日原始晨报，仅保留周/月归档结果。

## 目录结构

```text
reading-assistant/
├── README.md
├── notes/
│   ├── daily_log_template.md
│   └── chapter_review_template.md
├── vocabulary/
│   ├── raw_words.txt
│   └── vocab_sheet_template.csv
├── scripts/
│   ├── build_daily_review.py
│   └── create_digest_file.py
├── briefings/
│   ├── weekly/
│   └── monthly/
├── health-science/
│   ├── weekly-digest/
│   └── monthly-review/
└── templates/
    ├── weekly_digest_template.md
    └── monthly_digest_template.md
```

## 模块 A：英文阅读助手

### 最小流程

1) 新建当天听书笔记

```bash
cp notes/daily_log_template.md notes/2026-05-08-log.md
```

2) 生成结构化复盘

```bash
python3 scripts/build_daily_review.py notes/2026-05-08-log.md
```

输出示例：

```text
notes/2026-05-08-log.review.md
```

3) 维护词汇表

- 临时生词先记录到 `vocabulary/raw_words.txt`；
- 每周手动整理到 `vocabulary/vocab_sheet_template.csv`。

## 模块 B：周/月晨报归档系统

> 本仓库不保存每日原始晨报（即不提供 `briefings/daily/`）。

### 创建周报归档文件

```bash
python scripts/create_digest_file.py weekly 2026-W19
```

会创建：

```text
briefings/weekly/2026-W19.md
```

内容来源：`templates/weekly_digest_template.md`。

### 创建月报归档文件

```bash
python scripts/create_digest_file.py monthly 2026-05
```

会创建：

```text
briefings/monthly/2026-05.md
```

内容来源：`templates/monthly_digest_template.md`。

## 模板字段说明

### Weekly 模板

- Week
- 高频主题
- 重要事件时间线
- 趋势判断
- 值得继续跟踪的问题
- 个人知识卡片
- 下周观察重点

### Monthly 模板

- Month
- 本月核心趋势
- AI & Technology
- Geopolitics
- Economy
- Education & Work Relevance
- Health / Neuroscience Notes
- Things I Changed My Mind About
- Questions for Next Month

## 注意事项

- 不调用外部 API；
- 不处理真实隐私数据；
- 若模板字段发生调整，请同步更新相应脚本。

## Website Preview Plan

This repository is now being prepared for a MkDocs-based knowledge archive website.

- The first version uses MkDocs + Material for Markdown-first browsing.
- GitHub Pages deployment is **not enabled yet**.
- The site can be published to GitHub Pages in a future step when ready.

## Website Deployment

This repository is deployed as a static website using **MkDocs Material + GitHub Pages**.

- Every merge/push to `main` will automatically trigger the GitHub Actions deployment workflow.
- The workflow builds the site with `mkdocs build` and deploys it through GitHub Pages official actions.
- In your repository settings, go to **Settings → Pages** and set **Source** to **GitHub Actions**.

## OpenRouter Free Daily Briefing Test

This workflow uses GitHub Actions + OpenRouter API to generate a daily Morning Intelligence Briefing.

- It requires repository secret: `OPENROUTER_API_KEY`.
- It currently uses a free model for pipeline testing.
- Quality may be lower than paid models.
- After testing, `MODEL_NAME` can be changed to `openai/gpt-4.1-mini` or another paid model.
- Public repo must never contain API keys.
The OpenRouter daily briefing workflow now builds and deploys the MkDocs site directly after generating or updating the daily briefing, because commits made with GITHUB_TOKEN do not trigger the separate deploy workflow automatically.
