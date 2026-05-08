# Personal Reading Assistant

一个为**英文有声书学习者**设计的最小可运行项目结构，帮助你把每日听书记录整理为中英双语复盘。

## 项目目标

- 记录每日英文有声书输入（章节、时长、难点、感想）；
- 结构化提取关键内容，输出可复习的双语 review；
- 积累生词并整理为 CSV 词汇表；
- 全流程只使用本地文件，不调用外部 API。

## 目录结构

```text
personal-reading-assistant/
├── README.md
├── notes/
│   ├── daily_log_template.md
│   └── chapter_review_template.md
├── scripts/
│   └── build_daily_review.py
└── vocabulary/
    ├── raw_words.txt
    └── vocab_sheet_template.csv
```

## 使用方式（最小流程）

### 1) 新建当天听书笔记

复制模板：

```bash
cp notes/daily_log_template.md notes/2026-05-08-log.md
```

然后填写：书名、章节、摘要、生词、反思等内容。

### 2) 生成结构化复盘文件

运行脚本：

```bash
python3 scripts/build_daily_review.py notes/2026-05-08-log.md
```

脚本会在同目录生成：

```text
notes/2026-05-08-log.review.md
```

### 3) 维护词汇表

- 临时生词先记到 `vocabulary/raw_words.txt`；
- 每周手动整理到 `vocabulary/vocab_sheet_template.csv`；
- 可按 `word / meaning_zh / example_en / example_zh / source` 维护。

## 面向英语学习者的建议

- **每天 15~30 分钟**固定输入，优先稳定节奏；
- 每次听书后写 3~5 句英文 summary，再补中文理解；
- 生词只挑“高频且可复用”的，避免一次性背太多；
- 章节复盘时关注：人物关系、核心冲突、表达方式。

## 脚本说明

`scripts/build_daily_review.py` 当前是最小可运行版本：

- 输入：一个 Markdown 日志文件；
- 解析：按标题抓取关键板块（如 Summary EN/ZH、Vocabulary 等）；
- 输出：一个新的 Markdown 复盘文件，包含原始内容和结构化块；
- 不读取或写入任何个人敏感信息字段。

## 注意

- 本项目不处理真实个人隐私数据；
- 所有内容均保存在本地 Markdown/CSV 文件中；
- 若模板字段名称修改，请同步更新脚本中的标题映射。
