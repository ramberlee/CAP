# CAP - Content Auto Pipeline (内容自动生产线)

热点监控 → AI 内容生成 → 多平台发布，一站式自动化内容运营工具。

## 功能特性

- **热点采集** - 自动抓取今日头条热榜，支持手动添加话题
- **AI 内容生成** - 基于 MiMo 大模型，一键生成小红书、微信公众号、抖音三平台内容
- **AI 配图生成** - 集成阿里云百炼 Qwen-Image，自动为文章生成配图
- **文件化存储** - 内容以 Markdown 文件保存在 `output/` 目录，可直接用编辑器修改
- **微信公众号发布** - 支持草稿箱发布，内置 WeChat-Markdown 排版引擎，多主题切换
- **多平台发布** - 微信公众号、小红书、抖音，逐平台确认后发布

## 项目结构

```
CAP/
├── main.py                      # CLI 入口
├── config.yaml.example          # 配置文件模板
├── config.yaml                  # 配置文件（从 example 复制，不入库）
├── requirements.txt             # Python 依赖
├── templates/                   # 各平台内容模板
│   ├── xiaohongshu.md
│   ├── wechat.md
│   └── douyin.md
├── modules/
│   ├── config.py                # 配置加载
│   ├── database.py              # SQLite 数据库（热点去重）
│   ├── content_store.py         # 文件化内容存储
│   ├── monitor.py               # 热点采集（今日头条）
│   ├── generator.py             # AI 内容生成（MiMo API）
│   ├── imager.py                # AI 配图生成（DashScope SDK）
│   ├── publisher.py             # 发布调度器
│   └── platforms/
│       ├── wechat.py            # 微信公众号发布
│       ├── wechat_renderer.py   # 微信排版引擎（移植自 WeChat-Markdown）
│       ├── xiaohongshu.py       # 小红书发布（Playwright）
│       └── douyin.py            # 抖音发布（Playwright）
├── output/                      # 生成的内容文件
│   ├── xiaohongshu/
│   ├── wechat/
│   └── douyin/
└── db/                          # 数据库和日志
    ├── pipeline.db
    └── pipeline.log
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install
```

### 2. 初始化配置

复制配置模板，然后编辑填入你的 API Key 等信息：

```bash
cp config.yaml.example config.yaml
```

编辑 `config.yaml`，填入以下关键配置：

```yaml
# MiMo API（内容生成）
mimo:
  api_key: "your-mimo-api-key"
  base_url: "https://token-plan-cn.xiaomimimo.com/v1"
  model: "mimo-v2.5-pro"

# 阿里云百炼（配图生成）
dashscope:
  api_key: "your-dashscope-api-key"
  model: "qwen-image-2.0-pro"

# 发布平台配置（enabled 控制是否启用该平台的内容生成和发布）
platforms:
  wechat:
    enabled: true
    app_id: "your-app-id"
    app_secret: "your-app-secret"
    author: "作者名"
    mode: "draft"
    theme: "claude"
  xiaohongshu:
    enabled: true
    cookie_file: "db/xhs_cookies.json"
    headless: false
    channel: "msedge"
  douyin:
    enabled: true
    cookie_file: "db/douyin_cookies.json"
    headless: false
    channel: "msedge"
```

### 3. 使用

```bash
# 一键全流程（采集 → 生成 → 发布）
python main.py run

# 分步执行
python main.py monitor              # 采集热点
python main.py generate -l 3        # 生成内容（最多3条）
python main.py publish -p wechat    # 发布到微信

# 手动指定话题
python main.py run -t "AI编程" -t "ChatGPT"

# 查看状态
python main.py status

# 查看内容
python main.py show -p wechat

# 编辑内容
python main.py edit wechat 1
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `monitor` | 采集热点话题 |
| `generate` | AI 生成内容，保存到 output/ |
| `publish` | 发布已生成的内容（发布前确认） |
| `run` | 一键全流程 |
| `status` | 查看流水线状态 |
| `show` | 查看内容列表 |
| `edit` | 用编辑器打开内容文件 |

## 内容文件格式

生成的内容以 Markdown + YAML frontmatter 保存：

```markdown
---
platform: wechat
status: approved
tags: [AI, 油价, 经济]
media_urls: [media/content_1_1.png]
created_at: "2026-06-05T12:00:00"
topic_id: 1
---

# 文章标题

正文内容...

![配图](media/content_1_1.png)
```

- `status: approved` → 待发布
- `status: published` → 已发布
- 可直接用任何编辑器修改文件内容

## 微信排版主题

内置 4 个主题，可在 `config.yaml` 中切换：

| 主题 | 说明 |
|------|------|
| `claude` | 燕麦卡其底色，橙棕标题（默认） |
| `apple` | 极致留白，黑白灰 |
| `wechat` | 微信公众号原生绿 |
| `notion` | 黑白灰极简 |

## 技术栈

- **CLI**: Typer + Rich
- **AI 内容生成**: MiMo API（OpenAI 兼容）
- **AI 配图**: 阿里云百炼 DashScope SDK（Qwen-Image）
- **Markdown 渲染**: markdown-it-py + BeautifulSoup4
- **浏览器自动化**: Playwright（小红书/抖音发布）
- **数据库**: SQLite（热点去重）
- **文件存储**: Markdown + YAML frontmatter
