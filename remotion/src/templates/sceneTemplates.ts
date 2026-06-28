import { Scene } from '../types';
import { TransitionType } from '../VideoComposition';

// ===== 场景模板类型 =====
export interface SceneTemplateOptions {
  duration?: number;
  englishLabel?: string;
  sceneSubtitle?: string;
  transition?: {
    type: TransitionType;
    duration: number;
  };
}

// ===== 封面场景模板 =====
export function createTitleScene(
  title: string,
  subtitle?: string,
  options: SceneTemplateOptions = {}
): Scene {
  return {
    layout: 'title_card',
    duration: options.duration || 4,
    englishLabel: options.englishLabel || 'TITLE',
    sceneSubtitle: options.sceneSubtitle || '',
    titleCard: {
      title,
      subtitle,
    },
  };
}

// ===== 多面板科技场景模板 =====
export interface TechPanelOptions extends SceneTemplateOptions {
  leftItems?: Array<{
    text: string;
    state?: 'idle' | 'active' | 'completed' | 'error';
    badge?: { text: string; variant: string };
  }>;
  centerTitle?: string;
  centerSubtitle?: string;
  centerBody?: string;
  rightItems?: Array<{
    name: string;
    badge?: { text: string; variant: string };
  }>;
}

export function createTechMultiPanel(
  options: TechPanelOptions = {}
): Scene {
  return {
    layout: 'tech_multi_panel',
    duration: options.duration || 6,
    englishLabel: options.englishLabel || 'OVERVIEW',
    sceneSubtitle: options.sceneSubtitle || '',
    techMultiPanel: {
      title: '',
      leftPanel: {
        title: 'FEATURES',
        items: options.leftItems || [
          { text: 'AI 智能分析', state: 'completed', badge: { text: 'loaded', variant: 'green' } },
          { text: '实时数据处理', state: 'active', badge: { text: 'running', variant: 'orange' } },
          { text: '多端同步', state: 'idle', badge: { text: 'ready', variant: 'cyan' } },
        ],
      },
      centerPanel: {
        title: options.centerTitle || '核心能力',
        subtitle: options.centerSubtitle || '从这里开始',
        body: options.centerBody || '强大的技术能力支撑，为您的业务提供全方位保障。',
        glow: true,
      },
      rightPanel: {
        title: 'MODULES',
        items: options.rightItems || [
          { name: 'core.md', badge: { text: 'v2.0', variant: 'green' } },
          { name: 'utils.ts', badge: { text: 'stable', variant: 'cyan' } },
          { name: 'config.yml', badge: { text: 'ready', variant: 'neutral' } },
        ],
      },
    },
  };
}

// ===== 卡片流场景模板 =====
export interface ConnectedCardsOptions extends SceneTemplateOptions {
  cards?: Array<{
    num: string;
    title: string;
    items: string[];
    state?: 'normal' | 'highlighted' | 'dimmed';
    accent?: 'orange' | 'cyan' | 'green' | 'red';
  }>;
}

export function createConnectedCards(
  options: ConnectedCardsOptions = {}
): Scene {
  return {
    layout: 'connected_cards',
    duration: options.duration || 5,
    englishLabel: options.englishLabel || 'STEPS',
    sceneSubtitle: options.sceneSubtitle || '三步完成',
    connectedCards: {
      title: '',
      cards: options.cards || [
        { num: '01', title: '准备阶段', items: ['数据导入', '环境检查', '配置确认'], state: 'highlighted' },
        { num: '02', title: '执行处理', items: ['核心计算', '结果校验', '异常处理'], state: 'normal' },
        { num: '03', title: '输出结果', items: ['报告生成', '数据导出', '完成通知'], state: 'dimmed' },
      ],
    },
  };
}

// ===== 架构图场景模板 =====
export interface ArchitectureOptions extends SceneTemplateOptions {
  nodes?: Array<{
    id: string;
    label: string;
    sublabel?: string;
    x: number;
    y: number;
    color: 'orange' | 'cyan' | 'red' | 'green' | 'neutral';
    glow?: boolean;
  }>;
  connections?: Array<{
    from: string;
    to: string;
    flowing?: boolean;
  }>;
}

export function createArchitectureFlow(
  title: string,
  options: ArchitectureOptions = {}
): Scene {
  return {
    layout: 'architecture_flow',
    duration: options.duration || 6,
    englishLabel: options.englishLabel || 'ARCHITECTURE',
    sceneSubtitle: options.sceneSubtitle || '系统架构',
    architectureFlow: {
      title,
      nodes: options.nodes || [
        { id: 'input', label: '输入层', x: 60, y: 200, w: 140, h: 60, color: 'cyan' },
        { id: 'process', label: '处理层', x: 300, y: 260, w: 180, h: 80, color: 'orange', glow: true },
        { id: 'output', label: '输出层', x: 580, y: 200, w: 140, h: 60, color: 'green' },
      ],
      connections: options.connections || [
        { from: 'input', to: 'process', flowing: true },
        { from: 'process', to: 'output', flowing: true },
      ],
    },
  };
}

// ===== 列表高亮场景模板 =====
export interface StackHighlightOptions extends SceneTemplateOptions {
  items?: Array<{
    text: string;
    highlighted?: boolean;
    state?: 'idle' | 'active' | 'completed' | 'error';
    badge?: { text: string; variant: string };
  }>;
  rightCard?: {
    title?: string;
    subtitle?: string;
    body?: string;
    pills?: string[];
  };
}

export function createStackHighlight(
  leftTitle: string,
  options: StackHighlightOptions = {}
): Scene {
  return {
    layout: 'stack_highlight',
    duration: options.duration || 5,
    englishLabel: options.englishLabel || 'FEATURES',
    sceneSubtitle: options.sceneSubtitle || leftTitle,
    stackHighlight: {
      title: leftTitle,
      leftItems: options.items || [
        { text: '高性能计算引擎', highlighted: true, state: 'active', badge: { text: 'CORE', variant: 'orange' } },
        { text: '智能路由分配', highlighted: false, state: 'completed', badge: { text: 'DONE', variant: 'green' } },
        { text: '实时监控告警', highlighted: false, state: 'idle', badge: { text: 'READY', variant: 'cyan' } },
        { text: '数据持久化', highlighted: false, state: 'idle', badge: { text: 'WAIT', variant: 'neutral' } },
      ],
      rightCard: options.rightCard || {
        title: '核心特性',
        subtitle: '深入了解',
        body: '每个功能模块都经过精心设计和优化，确保最佳性能表现。采用现代化技术栈，支持水平扩展。',
        pills: ['高性能', '可扩展', '高可用', '安全', '便捷'],
      },
    },
  };
}

// ===== 数据网格场景模板 =====
export interface CardGridOptions extends SceneTemplateOptions {
  title?: string;
  cards?: Array<{
    title: string;
    badge?: { text: string; variant: string };
    items: string[];
    buttonText?: string;
  }>;
}

export function createCardGrid(
  options: CardGridOptions = {}
): Scene {
  return {
    layout: 'card_grid',
    duration: options.duration || 5,
    englishLabel: options.englishLabel || 'FEATURES',
    sceneSubtitle: options.sceneSubtitle || '核心功能',
    cardGrid: {
      title: options.title || '核心功能',
      cards: options.cards || [
        { title: '智能分析', badge: { text: 'AI', variant: 'orange' }, items: ['NLP 处理', '模式识别', '预测分析'] },
        { title: '数据处理', badge: { text: 'BIG DATA', variant: 'cyan' }, items: ['流式处理', '批量计算', '实时同步'] },
        { title: '可视化', badge: { text: 'CHARTS', variant: 'green' }, items: ['动态图表', '交互仪表盘', '自动报告'] },
      ],
    },
  };
}

// ===== 结尾场景模板 =====
export function createEndingScene(
  mainTitle: string,
  subtitle?: string,
  options: SceneTemplateOptions = {}
): Scene {
  return {
    type: 'ending',
    duration: options.duration || 4,
    englishLabel: options.englishLabel || 'THANK YOU',
    sceneSubtitle: options.sceneSubtitle || '',
    title: mainTitle,
    subtitle,
    items: subtitle ? [subtitle] : [],
  };
}
