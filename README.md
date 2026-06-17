# CAP - Content Auto Pipeline (内容自动生产线)

热点监控 → AI 内容生成 → 多平台发布，一站式自动化内容运营工具。

## 功能特性

- **热点采集** - 支持两类热点：「道」社会热点（今日头条）+「术」AI技术热点（36kr、Hacker News），支持分类采集
- **道与术分类** - 社会热点归「道」、AI技术热点归「术」，自动生成不同定位的内容
- **AI 内容生成** - 基于 MiMo 大模型，一键生成小红书、微信公众号、抖音三平台内容
- **AI 配图生成** - 支持阿里云百炼 DashScope 和 Agnes AI 两种后端，自动为文章生成配图
- **抖音视频生成** - 口播脚本经 MiMo TTS 生成音频，再由文生视频模型生成带配音的短视频（支持 DashScope / Agnes / Remotion）
- **Remotion 文字视频** - 基于 React 的程序化视频渲染，免费生成文字动画短视频，时长由内容自动决定
- **文件化存储** - 内容以 Markdown 文件保存在 `output/` 目录，可直接用编辑器修改
- **微信公众号发布** - 支持草稿箱发布，内置 WeChat-Markdown 排版引擎，多主题切换
- **小红书发布** - Playwright + CDP 浏览器自动化，自动上传图片、填写内容、Shadow DOM 穿透点击发布
- **抖音发布** - Playwright 浏览器自动化，支持批量视频发布
- **多平台发布** - 微信公众号、小红书、抖音，逐平台确认后发布

## 项目结构

```
CAP/
├── main.py                      # CLI 入口
├── config.yaml.example          # 配置文件模板
├── config.yaml                  # 配置文件（从 example 复制，不入库）
├── requirements.txt             # Python 依赖
├── templates/                   # 各平台内容模板（按道/术分类）
│   ├── xiaohongshu_dao.md       # 小红书·道（社会热点）
│   ├── xiaohongshu_shu.md       # 小红书·术（AI技术）
│   ├── wechat_dao.md            # 公众号·道
│   ├── wechat_shu.md            # 公众号·术
│   ├── douyin_dao.md            # 抖音·道
│   └── douyin_shu.md            # 抖音·术
├── modules/
│   ├── config.py                # 配置加载
│   ├── database.py              # SQLite 数据库（热点去重）
│   ├── content_store.py         # 文件化内容存储
│   ├── monitor.py               # 热点采集（道：今日头条，术：36kr+HN）
│   ├── generator.py             # AI 内容生成（MiMo API）
│   ├── imager.py                # AI 配图生成（DashScope / Agnes）
│   ├── vgen.py                  # AI 视频生成（DashScope / Agnes / Remotion）
│   ├── remotion_client.py       # Remotion 视频渲染客户端
│   ├── video_planner.py         # 视频构图规划（LLM 生成 Remotion 场景计划）
│   ├── agnes_client.py          # Agnes AI API 统一客户端
│   ├── tts.py                   # TTS 语音合成（MiMo TTS）
│   ├── publisher.py             # 发布调度器
│   └── platforms/
│       ├── wechat.py            # 微信公众号发布
│       ├── wechat_renderer.py   # 微信排版引擎（移植自 WeChat-Markdown）
│       ├── xiaohongshu.py       # 小红书发布（Playwright + CDP Shadow DOM）
│       └── douyin.py            # 抖音发布（Playwright 批量发布）
├── tools/
│   ├── xhs_login.py             # 小红书登录（保存 Cookie）
│   └── douyin_login.py          # 抖音登录（保存 Cookie）
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
# MiMo API（内容生成 + TTS 语音合成）
mimo:
  api_key: "your-mimo-api-key"
  base_url: "https://token-plan-cn.xiaomimimo.com/v1"
  model: "mimo-v2.5-pro"
  tts_model: "mimo-v2.5-tts"
  tts_voice: "zh-female"

# 阿里云百炼（配图 + 视频生成）
dashscope:
  api_key: "your-dashscope-api-key"
  model: "qwen-image-2.0-pro"
  video_model: "wan2.7-t2v-turbo"
  video_size: "1280*720"
  video_duration: 15

# Remotion（文字动画视频，免费推荐）
# video_provider 设为 "remotion" 时生效
remotion:
  project_dir: "remotion"
  fps: 30

# 热点采集数据源
monitor:
  max_topics: 10
  sources:
    dao: [toutiao]            # 道：社会热点源
    shu: [36kr, hackernews]   # 术：AI技术热点源

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
# 默认生成 1篇"道" + 1篇"术"
python main.py run

# 分步执行
python main.py monitor              # 采集全部热点（道+术）
python main.py generate             # 生成内容（默认: 1篇道+1篇术）
python main.py generate -l 3        # 生成内容（3篇道+3篇术）
python main.py publish -p wechat    # 发布到微信
python main.py publish -p xiaohongshu  # 发布到小红书

# 按类别采集和生成
python main.py monitor -c dao       # 只采集社会热点（道）
python main.py monitor -c shu       # 只采集AI技术热点（术）
python main.py run -c shu           # 全流程只处理「术」类

# 手动指定话题
python main.py run -t "AI编程" -t "ChatGPT"

# 查看状态（显示道/术分类统计）
python main.py status

# 查看内容
python main.py show -p wechat

# 编辑内容
python main.py edit wechat 1
```

#### 小红书发布说明

小红书发布需要先登录保存 Cookie：

```bash
# 1. 登录小红书创作者中心（浏览器会自动打开，扫码登录后按 Enter）
python tools/xhs_login.py

# 2. 发布
python main.py publish -p xiaohongshu
```

**内容限制**（自动生成时会自动截断）：
- 标题：≤ 20 字
- 正文：≤ 1000 字
- 图片：必需，支持 .png / .jpg / .jpeg / .webp

**技术细节**：
- 使用 Playwright 浏览器自动化 + CDP（Chrome DevTools Protocol）
- 正文通过 CDP `Input.insertText` 注入 TipTap/ProseMirror 编辑器
- 发布按钮位于 `<xhs-publish-btn>` Shadow DOM (closed) 内，通过 CDP `DOM.getDocument(pierce=True)` 穿透点击

#### 视频生成后端

`config.yaml` 中 `generation.video_provider` 控制抖音视频的生成方式：

| 后端 | 说明 | 费用 |
|------|------|------|
| `dashscope` | 阿里云百炼 Wan2.7-T2V 文生视频 | 按量计费 |
| `agnes` | Agnes AI 文生视频 | 按量计费 |
| `remotion` | **推荐** — 程序化文字动画视频，LLM 自动规划场景 | **免费** |

Remotion 后端会用 LLM 将口播脚本转化为"构图计划"（场景分解 + 动画效果），然后通过 React 组件渲染为竖屏视频。需要 Node.js 环境，首次使用需在 `remotion/` 目录执行 `npm install`。

#### 默认生成数量

- **默认行为**: 每次运行生成 **1篇"道"文章** 和 **1篇"术"文章**
- **自定义数量**: 使用 `--limit` 参数调整，如 `python main.py generate --limit 5`
- **配置文件**: 在 `config.yaml` 中设置 `generation.default_limit` 修改默认值

详细说明请参考 [docs/generation_limit_usage.md](docs/generation_limit_usage.md)

#### 道与术分类说明

| 类别 | 定位 | 数据源 | 内容风格 |
|------|------|--------|----------|
| **道(dao)** | 社会趋势洞察 | 今日头条热榜 | 用AI思维解读社会热点，提供认知升级 |
| **术(shu)** | AI技术解读 | 36kr快讯 + Hacker News | 技术深度分析，工具推荐，实操方法 |

## CLI 命令

| 命令 | 说明 |
|------|------|
| `monitor [-c dao\|shu]` | 采集热点话题，可按道/术分类采集 |
| `generate [-c dao\|shu]` | AI 生成内容，可按类别筛选 |
| `publish [-p platform]` | 发布到指定平台（wechat / xiaohongshu / douyin） |
| `run [-c dao\|shu]` | 一键全流程，可指定类别 |
| `status` | 查看流水线状态（含道/术统计） |
| `show [-p platform]` | 查看内容列表 |
| `edit <platform> <index>` | 用编辑器打开内容文件 |

## 内容模板

模板按平台 × 类别组织，优先加载 `{platform}_{category}.md`，回退到 `{platform}.md`：

| 模板 | 类别 | 说明 |
|------|------|------|
| `xiaohongshu_dao.md` | 道 | 小红书·社会热点洞察 |
| `xiaohongshu_shu.md` | 术 | 小红书·AI技术干货 |
| `wechat_dao.md` | 道 | 公众号·趋势深度解读 |
| `wechat_shu.md` | 术 | 公众号·技术深度分析 |
| `douyin_dao.md` | 道 | 抖音·热点认知洞察 |
| `douyin_shu.md` | 术 | 抖音·技术干货分享 |

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

抖音内容包含视频和音频文件：

```markdown
---
platform: douyin
status: approved
tags: [#AI, #热点]
media_urls: [media/content_102_1.mp4, media/content_102_tts.mp3]
created_at: "2026-06-05T12:00:00"
topic_id: 102
---

# 视频标题

【钩子】一句话hook

---

【价值】核心观点

---

【收尾】引导互动

[视频](media/content_102_1.mp4)
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

## API 文档

详细的模块 API 文档见 [docs/API.md](docs/API.md)，包含：

| 模块 | 说明 |
|------|------|
| `modules.database` | SQLite 数据库层（话题增删改查、分类统计） |
| `modules.monitor` | 热点采集（今日头条/36kr/Hacker News，道/术分类） |
| `modules.generator` | AI 内容生成（MiMo API，分类模板和提示词） |
| `modules.imager` | AI 配图生成（DashScope / Agnes 后端） |
| `modules.vgen` | AI 视频生成（DashScope / Agnes / Remotion 后端，支持音频同步） |
| `modules.remotion_client` | Remotion 视频渲染客户端（npx/ffmpeg 管理、渲染、音频合并） |
| `modules.video_planner` | 视频构图规划（LLM 生成 Remotion 场景计划） |
| `modules.agnes_client` | Agnes AI API 统一客户端 |
| `modules.tts` | TTS 语音合成（MiMo TTS，口播脚本转音频） |
| `modules.content_store` | 文件化内容存储（Markdown + YAML frontmatter） |
| `modules.config` | 配置加载 |

## 技术栈

- **CLI**: Typer + Rich
- **AI 内容生成**: MiMo API（OpenAI 兼容）
- **AI 配图**: 阿里云百炼 DashScope SDK / Agnes AI（可切换）
- **AI 视频生成**: 阿里云百炼 Wan2.7-T2V / Agnes AI / Remotion（可切换）
- **Remotion 视频渲染**: React + Remotion 框架，程序化文字动画视频（免费，推荐）
- **TTS 语音合成**: MiMo TTS（OpenAI 兼容）
- **Markdown 渲染**: markdown-it-py + BeautifulSoup4
- **浏览器自动化**: Playwright + CDP（小红书发布，Shadow DOM 穿透）
- **数据库**: SQLite（热点去重）
- **文件存储**: Markdown + YAML frontmatter
