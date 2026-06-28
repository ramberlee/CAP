import { CompositionPlan } from '../types';
import {
  createTitleScene,
  createTechMultiPanel,
  createConnectedCards,
  createStackHighlight,
  createArchitectureFlow,
  createCardGrid,
  createEndingScene,
} from './sceneTemplates';

// ===== 视频模板类型 =====
export interface VideoTemplateOptions {
  theme?: string;
  title?: string;
  subtitle?: string;
  audioPath?: string;
  tags?: string[];
}

// ===== 科技展示视频模板 (v3) =====
export function createTechShowcaseVideo(
  options: VideoTemplateOptions = {}
): CompositionPlan {
  const {
    theme = 'dark_tech_v3',
    title = '科技产品展示',
    subtitle = '创新 · 高效 · 智能',
    audioPath,
    tags = ['科技', '产品', 'AI'],
  } = options;

  return {
    theme,
    title,
    audioPath,
    tags,
    scenes: [
      // 封面
      createTitleScene(title, subtitle, {
        duration: 4,
        englishLabel: 'INTRO',
        sceneSubtitle: subtitle,
      }),

      // 多面板概览
      createTechMultiPanel({
        duration: 6,
        englishLabel: 'OVERVIEW',
        sceneSubtitle: '全方位能力展示',
        centerTitle: '产品核心能力',
        centerSubtitle: '领先一代的技术架构',
        centerBody: '采用最新的技术栈，结合人工智能算法，为您提供前所未有的使用体验。从数据处理到智能分析，每一个环节都经过精心优化。',
      }),

      // 流程步骤
      createConnectedCards({
        duration: 5,
        englishLabel: 'WORKFLOW',
        sceneSubtitle: '三步完成工作',
        cards: [
          { num: '01', title: '数据接入', items: ['多源导入', '自动清洗', '格式标准化'], state: 'highlighted' },
          { num: '02', title: '智能分析', items: ['AI 处理', '特征提取', '模式识别'], state: 'normal' },
          { num: '03', title: '结果输出', items: ['可视化展示', '报告生成', '推送通知'], state: 'dimmed' },
        ],
      }),

      // 特性列表高亮
      createStackHighlight('核心特性', {
        duration: 5,
        englishLabel: 'FEATURES',
        sceneSubtitle: '六大核心竞争力',
        items: [
          { text: '高性能计算引擎', highlighted: true, state: 'active', badge: { text: 'CORE', variant: 'orange' } },
          { text: '分布式架构', highlighted: false, state: 'completed', badge: { text: 'SCALE', variant: 'cyan' } },
          { text: '实时数据同步', highlighted: false, state: 'completed', badge: { text: 'REAL-TIME', variant: 'green' } },
          { text: '智能预警系统', highlighted: false, state: 'idle', badge: { text: 'AI', variant: 'neutral' } },
          { text: '多端适配', highlighted: false, state: 'idle', badge: { text: 'CROSS', variant: 'neutral' } },
          { text: '企业级安全', highlighted: false, state: 'idle', badge: { text: 'SECURE', variant: 'neutral' } },
        ],
        rightCard: {
          title: '产品优势',
          subtitle: '为什么选择我们',
          body: '我们的产品经过多年技术积累，在性能、稳定性、易用性方面都达到了行业领先水平。服务于全球数千家企业客户。',
          pills: ['高性能', '可扩展', '高可用', '安全', '便捷', '智能'],
        },
      }),

      // 架构图
      createArchitectureFlow('系统架构', {
        duration: 6,
        englishLabel: 'ARCHITECTURE',
        sceneSubtitle: '模块化设计 · 弹性扩展',
        nodes: [
          { id: 'user', label: '用户端', x: 40, y: 220, w: 120, h: 60, color: 'cyan' },
          { id: 'api', label: 'API 网关', x: 220, y: 160, w: 140, h: 60, color: 'neutral' },
          { id: 'auth', label: '认证服务', x: 220, y: 280, w: 140, h: 60, color: 'neutral' },
          { id: 'core', label: '核心服务', x: 420, y: 220, w: 160, h: 80, color: 'orange', glow: true },
          { id: 'data', label: '数据层', x: 640, y: 160, w: 140, h: 60, color: 'green' },
          { id: 'cache', label: '缓存层', x: 640, y: 280, w: 140, h: 60, color: 'green' },
        ],
        connections: [
          { from: 'user', to: 'api', flowing: true },
          { from: 'user', to: 'auth', flowing: true },
          { from: 'api', to: 'core', flowing: true },
          { from: 'auth', to: 'core', flowing: true },
          { from: 'core', to: 'data', flowing: true },
          { from: 'core', to: 'cache', flowing: true },
        ],
      }),

      // 功能卡片网格
      createCardGrid({
        duration: 5,
        title: '更多功能',
        englishLabel: 'MODULES',
        sceneSubtitle: '持续迭代，功能越来越强',
        cards: [
          { title: '用户管理', badge: { text: 'USER', variant: 'orange' }, items: ['权限控制', '角色划分', '审计日志'], buttonText: '详情' },
          { title: '数据分析', badge: { text: 'ANALYTICS', variant: 'cyan' }, items: ['多维度报表', '趋势分析', '导出功能'], buttonText: '详情' },
          { title: '系统集成', badge: { text: 'OPEN API', variant: 'green' }, items: ['RESTful API', 'Webhook', 'SDK支持'], buttonText: '详情' },
        ],
      }),

      // 结尾
      createEndingScene('感谢观看', '期待与您的合作', {
        duration: 4,
        englishLabel: 'THANKS',
        sceneSubtitle: '让我们一起创造未来',
      }),
    ],
  };
}

// ===== 产品介绍视频模板 =====
export function createProductIntroVideo(
  productName: string,
  options: VideoTemplateOptions = {}
): CompositionPlan {
  const { theme = 'dark_tech_v3' } = options;

  return {
    theme,
    title: `${productName} 产品介绍`,
    tags: ['产品介绍', '科技', '演示'],
    scenes: [
      createTitleScene(productName, '重新定义行业标准', {
        duration: 4,
        englishLabel: 'INTRO',
      }),

      createStackHighlight('核心优势', {
        duration: 5,
        englishLabel: 'ADVANTAGES',
        items: [
          { text: '技术领先一代', highlighted: true, badge: { text: '领先', variant: 'orange' } },
          { text: '部署简单快捷', highlighted: false, badge: { text: '快捷', variant: 'cyan' } },
          { text: '成本大幅降低', highlighted: false, badge: { text: '经济', variant: 'green' } },
          { text: '7×24 小时支持', highlighted: false, badge: { text: '可靠', variant: 'neutral' } },
        ],
        rightCard: {
          title: '为什么选择我们',
          subtitle: '行业领先的技术优势',
          body: `通过多年技术积累，${productName} 在多个关键指标上都超越了竞争对手。客户满意度高达 98%，续费率超过 95%。`,
          pills: ['技术领先', '部署简单', '成本节约', '优质服务'],
        },
      }),

      createConnectedCards({
        duration: 5,
        englishLabel: 'HOW IT WORKS',
        cards: [
          { num: '01', title: '接入', items: ['API 对接', '配置设定', '测试验证'], state: 'highlighted' },
          { num: '02', title: '运行', items: ['自动运转', '智能调优', '监控告警'], state: 'normal' },
          { num: '03', title: '收益', items: ['效率提升', '成本下降', '数据洞察'], state: 'dimmed' },
        ],
      }),

      createEndingScene('立即开始试用', '30 天免费试用', {
        duration: 4,
        englishLabel: 'CTA',
      }),
    ],
  };
}

// ===== 极简模板 (3 场景) =====
export function createMinimalVideo(
  title: string,
  items: string[],
  options: VideoTemplateOptions = {}
): CompositionPlan {
  const { theme = 'dark_tech_v3' } = options;

  return {
    theme,
    title,
    scenes: [
      createTitleScene(title, '', { duration: 3 }),

      createCardGrid({
        duration: Math.max(4, items.length * 1.5),
        cards: items.map((text, i) => ({
          title: text,
          items: [],
          badge: { text: `0${i + 1}`, variant: i === 0 ? 'orange' : i === 1 ? 'cyan' : 'green' },
        })),
      }),

      createEndingScene('谢谢观看', '', { duration: 3 }),
    ],
  };
}

// ===== 模板导出 =====
export const videoTemplates = {
  techShowcase: createTechShowcaseVideo,
  productIntro: createProductIntroVideo,
  minimal: createMinimalVideo,
};

export type VideoTemplateType = keyof typeof videoTemplates;
