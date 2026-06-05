# CAP - Content Auto Pipeline 需求规格说明书

## 1. 项目概述

### 1.1 项目名称
CAP - Content Auto Pipeline（内容自动生产线）

### 1.2 项目目标
构建一套自动化内容运营工具，实现"热点监控 → AI 内容生成 → 多平台发布"全流程自动化，降低内容创作成本，提高发布效率。

### 1.3 目标用户
- 自媒体运营者
- 内容创作者
- AI 领域内容账号运营者

---

## 2. 功能需求

### 2.1 热点采集模块 (Monitor)

#### FR-2.1.1 今日头条热榜采集
- **描述**: 自动抓取今日头条热榜数据
- **数据源**: `https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc`
- **采集字段**: 标题(Title)、链接(Url)、热度值(HotValue)
- **采集数量**: 可配置，默认最多 10 条
- **去重机制**: 基于标题去重，已采集的话题不重复入库

#### FR-2.1.2 手动话题输入
- **描述**: 支持通过 CLI 参数手动添加热点话题
- **参数**: `--topic` / `-t`，支持多次指定
- **示例**: `python main.py monitor -t "AI编程" -t "ChatGPT"`

#### FR-2.1.3 话题持久化
- **描述**: 采集的话题存储到 SQLite 数据库
- **存储字段**: 来源、标题、链接、热度、状态、采集时间
- **状态流转**: new → processing → completed

---

### 2.2 AI 内容生成模块 (Generator)

#### FR-2.2.1 多平台内容生成
- **描述**: 基于热点话题，调用 MiMo API 为各平台生成适配内容
- **支持平台**: 小红书、微信公众号、抖音
- **API**: MiMo API（OpenAI 兼容格式）
- **模型**: mimo-v2.5-pro（可配置）
- **模板**: 每个平台独立的 prompt 模板（`templates/` 目录）

#### FR-2.2.2 内容格式要求

**小红书**:
- 标题: 20字以内，带 emoji
- 正文: 300-500字，口语化
- 标签: 5-8 个话题标签
- 输出: JSON `{title, body, tags}`

**微信公众号**:
- 标题: 不超过 32 字
- 摘要: 50 字以内
- 正文: 1500-2500字，Markdown 格式
- 输出: JSON `{title, summary, body}`

**抖音**:
- 标题: 15-20字，带话题标签
- 脚本: 15-60秒口播文案
- 输出: JSON `{title, script, duration_seconds, tags}`

#### FR-2.2.3 AI 配图生成
- **描述**: 自动识别正文中的 `[IMAGE:description]` 占位符，调用 DashScope SDK 生成配图
- **模型**: qwen-image-2.0-pro（可配置）
- **图片分辨率**: 1472x1104（可配置）
- **图片风格**: 立体/创意/2.5D 插画风格
- **处理流程**: 识别占位符 → 生成图片 → 保存到 `output/{platform}/media/` → 替换为 `![配图](media/xxx.png)`
- **可选开关**: `config.yaml` 中 `generation.auto_image: true/false`

#### FR-2.2.4 内容文件存储
- **描述**: 生成的内容以 Markdown + YAML frontmatter 保存到文件系统
- **存储路径**: `output/{platform}/{序号:03d}_{标题}.md`
- **Frontmatter 字段**:
  - `platform`: 平台名称
  - `status`: 状态（approved/published）
  - `tags`: 标签列表
  - `media_urls`: 配图路径列表
  - `created_at`: 创建时间
  - `topic_id`: 关联话题 ID
- **默认状态**: 生成后直接为 `approved`（待发布）

---

### 2.3 内容发布模块 (Publisher)

#### FR-2.3.1 发布确认机制
- **描述**: 发布前展示待发布内容列表，用户确认后才执行发布
- **取消**: 用户可取消发布操作
- **试运行**: 支持 `--dry-run` 模式，不实际发布

#### FR-2.3.2 微信公众号发布
- **API**: 微信公众号草稿箱 API
- **功能**:
  - 上传内容图片到微信永久素材库
  - 上传首图作为封面（thumb_media_id）
  - Markdown → 微信排版 HTML 转换
  - 创建草稿（draft/add）
- **限制**:
  - 标题: ≤ 32 字
  - 作者: ≤ 16 字
  - 摘要: ≤ 128 字
- **编码**: `json.dumps(ensure_ascii=False)` 确保中文正确显示

#### FR-2.3.3 微信排版引擎
- **描述**: 移植自 WeChat-Markdown 开源项目，将 Markdown 转换为微信公众号兼容的 HTML
- **核心功能**:
  - Markdown 解析（markdown-it-py）
  - 主题样式注入（内联 CSS）
  - 图片网格布局（连续图片并排显示）
  - 列表修复（转为手动编号段落，避免 WeChat 渲染 bug）
  - 字体继承强制（WeChat 会覆盖继承字体）
  - CJK 标点粘连处理
- **内置主题**: claude、apple、wechat、notion
- **配置**: `config.yaml` 中 `platforms.wechat.theme` 指定主题

#### FR-2.3.4 小红书发布
- **方式**: Playwright 浏览器自动化
- **前提**: 已登录的 cookie 文件（`db/xhs_cookies.json`）
- **流程**: 加载 cookie → 打开创作者页面 → 填写标题/正文/标签 → 上传图片 → 发布

#### FR-2.3.5 抖音发布
- **方式**: Playwright 浏览器自动化
- **前提**: 已登录的 cookie 文件（`db/douyin_cookies.json`）
- **流程**: 加载 cookie → 打开创作者页面 → 填写内容 → 发布

#### FR-2.3.6 发布状态更新
- **描述**: 发布成功后，更新内容文件的 status 为 `published`

---

### 2.4 流水线控制 (CLI)

#### FR-2.4.1 一键全流程
- **命令**: `python main.py run`
- **流程**: 热点采集 → AI 内容生成 → 发布确认 → 执行发布
- **参数**:
  - `--topic` / `-t`: 手动添加话题
  - `--limit` / `-l`: 最大处理数（默认 5）
  - `--dry-run`: 试运行

#### FR-2.4.2 分步执行
- `python main.py monitor`: 仅采集热点
- `python main.py generate`: 仅生成内容
- `python main.py publish`: 仅发布内容

#### FR-2.4.3 状态查看
- **命令**: `python main.py status`
- **显示**: 热点总数、待处理热点数、内容文件总数、待发布数、已发布数

#### FR-2.4.4 内容查看
- **命令**: `python main.py show`
- **参数**: `--platform` 筛选平台，`--status` 筛选状态

#### FR-2.4.5 内容编辑
- **命令**: `python main.py edit {platform} {index}`
- **功能**: 用系统默认编辑器打开内容文件

---

## 3. 非功能需求

### 3.1 性能要求
- 热点采集: ≤ 10 秒
- 单条内容生成: ≤ 30 秒
- 单张配图生成: ≤ 60 秒
- 微信发布: ≤ 15 秒

### 3.2 可靠性
- API 调用失败时记录日志，不中断整个流程
- 图片生成失败时移除占位符，不影响正文发布
- 数据库操作异常时回滚

### 3.3 可配置性
所有关键参数通过 `config.yaml` 配置:
- AI 模型 API Key、模型名称、生成参数
- 配图模型、分辨率
- 各平台发布配置
- 采集数量限制
- 日志级别

### 3.4 可扩展性
- 新增平台: 实现 `publish(content) -> dict` 接口，在 `publisher.py` 注册即可
- 新增热点源: 在 `monitor.py` 添加新的 `fetch_xxx()` 方法
- 新增排版主题: 在 `wechat_renderer.py` 的 `THEMES` 字典中添加

### 3.5 兼容性
- Python 3.10+
- Windows / macOS / Linux
- 微信公众号 API v2

---

## 4. 技术架构

### 4.1 技术栈

| 组件 | 技术选型 |
|------|----------|
| CLI 框架 | Typer + Rich |
| AI 内容生成 | MiMo API（OpenAI 兼容） |
| AI 配图 | 阿里云百炼 DashScope SDK |
| Markdown 渲染 | markdown-it-py |
| HTML 处理 | BeautifulSoup4 |
| 浏览器自动化 | Playwright |
| 数据库 | SQLite |
| 文件存储 | Markdown + YAML frontmatter |
| HTTP 请求 | requests |

### 4.2 数据流

```
今日头条热榜
     │
     ▼
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Monitor  │────▶│  Generator   │────▶│  Publisher   │
│ (热点采集) │     │ (AI内容生成)  │     │ (多平台发布)  │
└──────────┘     └──────────────┘     └──────────────┘
     │                  │                     │
     ▼                  ▼                     ▼
  SQLite DB        output/*.md           微信/小红书/抖音
                + media/*.png
```

### 4.3 存储设计

**SQLite (db/pipeline.db)** - 仅用于热点去重:
- `topics` 表: id, source, title, url, heat, status, created_at

**文件系统 (output/)** - 内容存储:
```
output/
  xiaohongshu/
    001_标题.md
    media/
      content_1_1.png
  wechat/
    001_标题.md
    media/
      content_1_1.png
  douyin/
    001_标题.md
```

---

## 5. 配置说明

### 5.1 config.yaml 结构

```yaml
mimo:               # MiMo API 配置
  api_key:          # API 密钥
  base_url:         # API 地址
  model:            # 模型名称

generation:         # 内容生成参数
  max_tokens:       # 最大 token 数
  temperature:      # 温度参数
  platforms:        # 生成的平台列表
  auto_image:       # 是否自动生成配图

dashscope:          # 阿里云百炼配置
  api_key:          # API 密钥
  model:            # 生图模型
  size:             # 图片分辨率
  media_dir:        # 图片保存目录

monitor:            # 热点采集配置
  max_topics:       # 最大采集数

platforms:          # 发布平台配置
  wechat:           # 微信公众号
    app_id:
    app_secret:
    author:
    mode:           # draft/publish
    theme:          # 排版主题
  xiaohongshu:      # 小红书
    cookie_file:
    headless:
    channel:
  douyin:           # 抖音
    cookie_file:
    headless:
    channel:

database:           # 数据库配置
  path:

logging:            # 日志配置
  level:
  file:
```

---

## 6. 依赖清单

### 6.1 Python 依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| openai | ≥1.0.0 | MiMo API 调用 |
| typer[all] | ≥0.12.0 | CLI 框架 |
| rich | ≥13.0 | 终端美化输出 |
| playwright | ≥1.40.0 | 浏览器自动化 |
| requests | ≥2.31.0 | HTTP 请求 |
| pyyaml | ≥6.0 | YAML 解析 |
| feedparser | ≥6.0 | RSS 解析 |
| Pillow | ≥10.0 | 图片处理 |
| dashscope | ≥1.20.0 | 阿里云百炼 SDK |
| markdown-it-py | ≥3.0.0 | Markdown 解析 |
| beautifulsoup4 | ≥4.12.0 | HTML 处理 |

### 6.2 外部服务

| 服务 | 用途 | 配置项 |
|------|------|--------|
| MiMo API | AI 内容生成 | `mimo.api_key` |
| 阿里云百炼 | AI 配图生成 | `dashscope.api_key` |
| 微信公众号 API | 草稿发布 | `platforms.wechat.app_id/secret` |
| 今日头条 | 热点数据源 | 无需配置 |

---

## 7. 约束与限制

### 7.1 微信公众号 API 限制
- 标题长度 ≤ 32 字
- 作者长度 ≤ 16 字
- 摘要长度 ≤ 128 字
- 需要配置 IP 白名单
- 图片需上传为永久素材

### 7.2 WeChat HTML 渲染限制
- 不支持 `<ol>/<li>` 有序列表（渲染异常，已转为手动编号段落）
- 不支持 flex 布局（已转为 table 布局）
- 字体会被覆盖（已强制内联继承）
- 图片不支持外部 URL（已上传为微信素材）

### 7.3 浏览器自动化限制
- 小红书/抖音发布依赖 Playwright cookie
- Cookie 过期需重新登录获取
- headless 模式下可能被平台检测

---

## 8. 未来扩展（待定）

- [ ] 定时任务（cron / APScheduler）
- [ ] 更多平台支持（微博、知乎等）
- [ ] 内容数据分析与效果追踪
- [ ] 多账号管理
- [ ] Web 管理界面
- [ ] 内容审核（AI 自审）
