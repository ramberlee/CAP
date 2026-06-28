import React from 'react';
import { Composition, registerRoot } from 'remotion';
import VideoComposition from './VideoComposition';

const FPS = 24;
const WIDTH = 1920;
const HEIGHT = 1080;
// Compute default duration from the plan; the composition must be at least as long
// as the longest plan we expect to render (with audio). 180s covers ~3min videos.
const defaultPlan = {
  "title": "v3 科技风演示",
  "theme": "dark_tech_v3",
  "scenes": [
    {
      "layout": "tech_multi_panel",
      "chapterBadge": "01 概览",
      "englishLabel": "SYSTEM CAP",
      "duration": 6,
      "techMultiPanel": {
        "title": "系统能力全景",
        "leftPanel": {
          "title": "FEATURES",
          "items": [
            {
              "text": "LLM 生成推理",
              "state": "completed",
              "badge": {
                "text": "loaded",
                "variant": "green"
              }
            },
            {
              "text": "Prompt 任务拆解",
              "state": "active",
              "badge": {
                "text": "loading",
                "variant": "orange"
              }
            },
            {
              "text": "Context 上下文注入",
              "state": "idle",
              "badge": {
                "text": "pending",
                "variant": "cyan"
              }
            },
            {
              "text": "Tool 工具调用",
              "state": "idle"
            },
            {
              "text": "Memory 记忆管理",
              "state": "idle"
            }
          ],
          "progress": {
            "current": 2,
            "total": 5
          }
        },
        "centerPanel": {
          "title": "核心能力",
          "subtitle": "AI 从回答到执行的跃迁",
          "body": "传统 LLM 只能回答问题，而 Agent 系统能够理解复杂任务、制定执行计划、调用外部工具、管理上下文记忆，并在多轮对话中持续优化策略。这种从「被动回答」到「主动执行」的转变，是 AI 能力的一次范式革命。",
          "glow": true,
          "progressBar": [
            {
              "label": "理解 40%",
              "color": "#FF6B35",
              "value": 40
            },
            {
              "label": "规划 30%",
              "color": "#FFA502",
              "value": 30
            },
            {
              "label": "执行 30%",
              "color": "#2ED573",
              "value": 30
            }
          ]
        },
        "rightPanel": {
          "title": "DOCUMENTS",
          "items": [
            {
              "name": "skill.md",
              "badge": {
                "text": "loaded",
                "variant": "green"
              }
            },
            {
              "name": "config.yml",
              "badge": {
                "text": "parsing",
                "variant": "cyan"
              }
            },
            {
              "name": "agent.spec",
              "badge": {
                "text": "pending",
                "variant": "neutral"
              }
            }
          ],
          "pagination": {
            "current": 0,
            "total": 3
          }
        },
        "sceneSubtitle": "能力即服务的新范式"
      }
    },
    {
      "layout": "connected_cards",
      "chapterBadge": "02 方案",
      "englishLabel": "SOLUTION",
      "duration": 5,
      "connectedCards": {
        "title": "三步完成转型",
        "cards": [
          {
            "num": "01",
            "title": "视频刷脚本",
            "items": [
              "账号定位",
              "开场节奏",
              "字幕规范"
            ],
            "state": "highlighted",
            "accentColor": "orange"
          },
          {
            "num": "02",
            "title": "投研报告",
            "items": [
              "报告结构",
              "数据口径",
              "风险提示"
            ],
            "state": "normal",
            "accentColor": "cyan"
          },
          {
            "num": "03",
            "title": "代码仓库",
            "items": [
              "项目结构",
              "测试命令",
              "发布流程"
            ],
            "state": "dimmed",
            "accentColor": "green"
          }
        ],
        "centerText": "方法沉淀成可复用资产",
        "sceneSubtitle": "标准化带来的效率革命"
      }
    },
    {
      "layout": "stack_highlight",
      "chapterBadge": "03 能力",
      "englishLabel": "CAPABILITY",
      "duration": 5,
      "stackHighlight": {
        "title": "系统能力叠加",
        "leftItems": [
          {
            "text": "LLM 生成与推理",
            "highlighted": false,
            "state": "completed",
            "badge": {
              "text": "推理",
              "variant": "neutral"
            }
          },
          {
            "text": "Prompt 任务拆解",
            "highlighted": true,
            "state": "active",
            "badge": {
              "text": "核心",
              "variant": "orange"
            }
          },
          {
            "text": "Context 上下文注入",
            "highlighted": false,
            "state": "idle",
            "badge": {
              "text": "记忆",
              "variant": "cyan"
            }
          },
          {
            "text": "Tool 工具调用",
            "highlighted": false,
            "state": "idle",
            "badge": {
              "text": "执行",
              "variant": "green"
            }
          },
          {
            "text": "Memory 记忆管理",
            "highlighted": false,
            "state": "idle",
            "badge": {
              "text": "存储",
              "variant": "neutral"
            }
          },
          {
            "text": "Skill 技能包加载",
            "highlighted": false,
            "state": "idle",
            "badge": {
              "text": "扩展",
              "variant": "orange"
            }
          }
        ],
        "rightCard": {
          "title": "Skill",
          "subtitle": "叠加之后 →",
          "body": "不再是单一能力的简单相加，而是形成了能够处理复杂任务的完整系统。当 LLM 的推理能力与 Prompt 的任务拆解能力相结合，再加上 Tool 的外部执行能力，就产生了 1+1>2 的协同效应。这就是 Skill 的真正价值所在。",
          "pills": [
            "生成",
            "创新",
            "推送",
            "搜索",
            "记忆",
            "执行"
          ]
        },
        "sceneSubtitle": "能力组合的指数效应"
      }
    }
  ]
};
const DEFAULT_DURATION_FRAMES = (() => {
  const totalSec = defaultPlan.scenes.reduce((s, sc) => s + (sc.duration || 0), 0);
  // Pad with a generous margin so test renders (e.g. via --props) can show all
  // scenes even when the runtime plan is longer than the default fallback.
  const padded = Math.max(totalSec || 30, 180);
  return padded * FPS;
})();

const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CAPVideo"
      component={VideoComposition}
      durationInFrames={DEFAULT_DURATION_FRAMES}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      defaultProps={{ plan: defaultPlan }}
    />
  );
};

registerRoot(RemotionRoot);
