# Floraputation Backend API

> 植物品种网络口碑智能分析平台 — 后端数据管道

## 概述

Floraputation Backend 是一个基于 FastAPI 的后端服务，为植物品种声誉分析提供完整的数据管道：

1. **品种管理** — 连接 Supabase 数据库，提供品种 CRUD API
2. **多平台数据抓取** — 从 Reddit、YouTube、Web 抓取品种相关讨论和评论
3. **AI 声誉分析** — 使用 GPT-4.1-mini 进行情感分析和声誉评分
4. **自动化调度** — 定时自动抓取和分析，持续积累数据

## 技术栈

- **Python 3.11+** + **FastAPI** — Web 框架
- **Supabase** (PostgreSQL) — 数据库
- **OpenAI GPT-4.1-mini** — AI 情感分析
- **Firecrawl** — 网页抓取
- **PullPush.io** — Reddit 数据
- **Docker** — 容器化部署

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 3. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Docker 部署

```bash
docker-compose up -d
```

## API 端点 (23 个)

### 品种管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/varieties | 品种列表（分页/搜索/筛选/排序） |
| POST | /api/varieties | 创建品种 |
| GET | /api/varieties/{id} | 品种详情 |
| PUT | /api/varieties/{id} | 全量更新 |
| PATCH | /api/varieties/{id} | 部分更新 |
| DELETE | /api/varieties/{id} | 删除品种 |
| POST | /api/varieties/batch-delete | 批量删除 |
| GET | /api/varieties/crops/list | 作物类型列表 |
| GET | /api/varieties/companies/list | 公司列表 |

### 数据抓取

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/scraping/scrape | 抓取单个品种（Crop + Series + Variety） |
| POST | /api/scraping/scrape/batch | 批量抓取 |
| GET | /api/scraping/stats | 抓取统计 |
| GET | /api/scraping/posts | 查看帖子 |
| GET | /api/scraping/comments | 查看评论 |
| GET | /api/scraping/jobs | 抓取任务历史 |

### AI 分析

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/analysis/analyze | AI 声誉分析 |
| POST | /api/analysis/full-pipeline | 一键抓取+分析 |
| GET | /api/analysis/history | 分析历史 |

### 自动化调度

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/scheduler/auto-scrape | 自动抓取待更新品种 |
| POST | /api/scheduler/incremental-scrape | 增量抓取 |
| GET | /api/scheduler/candidates | 查看待抓取品种 |

## 搜索字段

所有搜索 API 使用三个结构化字段：

- **crop** (必填) — 作物名称，如 Petunia、Begonia、Rose
- **variety** (必填) — 品种名称，如 Galaxy、Nonstop、Iceberg
- **series** (选填) — 系列名称，如 Wave、Surfinia、Knock Out

搜索查询自动组合为：`{crop} {series} {variety}`

## 数据库表

| 表名 | 用途 |
|------|------|
| varieties | 品种主数据 (3789 条) |
| scraped_posts | 抓取的帖子/视频 |
| scraped_comments | 抓取的评论 |
| scrape_jobs | 抓取任务历史 |
| analysis_results | AI 分析结果 |

## 开发进度

- [x] Day 1-2: 项目初始化 + Supabase 连接
- [x] Day 3-4: 品种管理 API (CRUD)
- [x] Day 5: 多平台爬虫 (Reddit/YouTube/Firecrawl)
- [x] Day 6: AI 声誉分析引擎
- [x] Day 7-8: 三字段搜索 + 分数回写 + 自动化调度 + 部署配置
- [ ] Day 9-10: 评论质量过滤 + 多语言支持
- [ ] Day 11-12: 前端集成优化
- [ ] Day 13-15: 端到端测试 + 文档完善 + GitHub 推送

## License

Private — Floraputation Project
