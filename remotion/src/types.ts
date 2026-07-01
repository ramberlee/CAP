/* Type definitions for CAP Remotion landscape videos (16:9, 1920×1080).

Two coexisting systems:
*/

// Re-export ThemePalette from themes.ts for backward compatibility
export { ThemePalette } from './themes';

/*

1. Legacy (v1): each Scene has a `type` from SceneType enum → fixed component.
   Kept for backward compatibility with existing plans.

2. Primitive-based (v2): each Scene has a `layout` from LayoutType enum → either
   a named layout (CardGrid, FlowDiagram, …) or a `block_tree` escape hatch
   composed of Block primitives. Themes default to `dark_glass`.

VideoComposition routes by `scene.layout` first, falling back to `scene.type`.
*/

// ───────────────────────────────────────────────────────────────────────
//  Legacy v1 — preserved for backward compatibility
// ───────────────────────────────────────────────────────────────────────

export enum SceneType {
  Title = 'title',
  Bullet = 'bullet',
  SectionTitle = 'section_title',
  DataCard = 'data_card',
  Quote = 'quote',
  Comparison = 'comparison',
  Timeline = 'timeline',
  Highlight = 'highlight',
  ImageCaption = 'image_caption',
  Ending = 'ending',
}

// ───────────────────────────────────────────────────────────────────────
//  v2 — Layout-based scene system
// ───────────────────────────────────────────────────────────────────────

export enum LayoutType {
  TitleCard     = 'title_card',
  CardGrid      = 'card_grid',
  NumberedCards = 'numbered_cards',
  SplitCompare  = 'split_compare',
  FlowDiagram   = 'flow_diagram',
  FanOut        = 'fan_out',
  DocTree       = 'doc_tree',
  BlockTree     = 'block_tree',
  // v3 — Advanced tech layouts
  TechMultiPanel     = 'tech_multi_panel',
  ConnectedCards     = 'connected_cards',
  ArchitectureFlow   = 'architecture_flow',
  StackHighlight     = 'stack_highlight',
  // v3 — New visual layouts
  TimelineSteps      = 'timeline_steps',
  StatsShowcase      = 'stats_showcase',
  QuoteCard          = 'quote_card',
  ProgressSteps      = 'progress_steps',
  FeatureComparison  = 'feature_comparison',
  // v3 — Data & Terminal layouts
  DataCompare        = 'data_compare',
  TerminalMockup     = 'terminal_mockup',
}

// Animation that can be applied to a Block on entry.
export interface BlockAnimation {
  type: 'fade' | 'slideUp' | 'slideRight' | 'scaleIn' | 'typewriter' | 'none';
  delay?: number;     // seconds
  duration?: number;  // seconds
  stagger?: number;   // seconds between children
}

// A timed subtitle chunk (relative to scene start, seconds).
export interface SubtitleChunk {
  text: string;
  start: number;
  end: number;
}

// Small status pill, e.g. { text: "loading", variant: "orange" }.
export interface BadgeSpec {
  text: string;
  variant?: 'orange' | 'cyan' | 'green' | 'red' | 'neutral';
  icon?: string;
}

// Single block — discriminated union over `type`.
// All blocks can carry an optional `animation` for their entry effect.
export type Block =
  | { type: 'heading';       text: string; level?: 1 | 2 | 3; animation?: BlockAnimation }
  | { type: 'text';          text: string; size?: 'sm' | 'md' | 'lg' | 'xl'; color?: string; animation?: BlockAnimation }
  | { type: 'card';
      title?: string;
      subtitle?: string;
      headerBadge?: BadgeSpec;
      body: Block[];
      footer?: Block[];
      variant?: 'glass' | 'outlined' | 'filled';
      animation?: BlockAnimation; }
  | { type: 'grid';          columns: 2 | 3 | 4; gap?: number; items: Block[]; animation?: BlockAnimation }
  | { type: 'column';        width?: string; items: Block[]; animation?: BlockAnimation }
  | { type: 'row';           align?: 'left' | 'center' | 'right' | 'between'; items: Block[]; gap?: number; animation?: BlockAnimation }
  | { type: 'numbered_list'; items: { num: string; text: string; suffix?: string }[]; animation?: BlockAnimation }
  | { type: 'badge';         text: string; variant?: 'orange' | 'cyan' | 'green' | 'red' | 'neutral'; icon?: string; animation?: BlockAnimation }
  | { type: 'tag';           text: string; color?: string; animation?: BlockAnimation }
  | { type: 'code_block';    code: string; language?: string; title?: string; animation?: BlockAnimation }
  | { type: 'file_tree';
      root: string;
      files: { name: string; icon?: string; badge?: string; indent?: number }[];
      animation?: BlockAnimation; }
  | { type: 'progress_bar';
      segments: { label: string; color: string; value: number }[];
      total?: number;
      legend?: string;
      animation?: BlockAnimation; }
  | { type: 'callout';       text: string; icon?: string; variant?: 'inline' | 'center' | 'banner'; animation?: BlockAnimation }
  | { type: 'connector';     variant: 'dashed_curve' | 'arrow' | 'line' | 'dashed_horizontal' }
  | { type: 'subtitle';      chunks: SubtitleChunk[] }                // bottom caption (per-scene)
  | { type: 'english_label'; text: string }                            // top-right pill (per-scene)
  | { type: 'divider';       height?: number }
  | { type: 'spacer';        height: number };

// ───────────────────────────────────────────────────────────────────────
//  Per-layout prop shapes (filled by the LLM in plan JSON)
// ───────────────────────────────────────────────────────────────────────

export interface TitleCardContent {
  title: string;
  subtitle?: string;
  badge?: BadgeSpec;
  englishLabel?: string;
  sceneSubtitle?: string;
}

export interface CardGridCardItem {
  title: string;
  badge?: BadgeSpec;
  items?: string[];
  buttonText?: string;
  footerText?: string;
}

export interface CardGridContent {
  title: string;
  englishLabel?: string;
  cards: CardGridCardItem[];
  calloutText?: string;
  calloutSubtext?: string;
  sceneSubtitle?: string;
}

export interface NumberedCardItem {
  name: string;
  items: { num: string; text: string; suffix?: string }[];
}

export interface NumberedCardsContent {
  title: string;
  englishLabel?: string;
  cards: NumberedCardItem[];
  centerText?: string;
  sceneSubtitle?: string;
}

export interface SplitCompareItem {
  text: string;
  icon?: string;
}

export interface ProgressBarSegment {
  label: string;
  color: string;
  value: number;
}

export interface SplitCompareContent {
  title: string;
  englishLabel?: string;
  leftTitle: string;
  leftItems: SplitCompareItem[];
  rightHeader: string;
  rightHeaderVariant?: 'orange' | 'cyan' | 'green' | 'red';
  barSegments: ProgressBarSegment[];
  barTotal?: number;
  barInlineLabel?: string;
  bottomText: string;
  sceneSubtitle?: string;
}

export interface FlowDiagramContent {
  title: string;
  englishLabel?: string;
  inputs: { label: string; sublabel?: string }[];            // left column inputs
  llmLabel: string;
  llmSublabel?: string;
  harnessContainerTitle?: string;                            // dashed container header
  agentLabel: string;
  agentSublabel?: string;
  harnessLabel: string;
  harnessSublabel?: string;
  toolLabels: { label: string; sublabel?: string }[];         // right column tool nodes
  calloutText?: string;                                      // e.g. "它把 Prompt"
  bottomLegend: { label: string; tone?: 'orange' | 'cyan' | 'neutral' }[]; // bottom pills
  sceneSubtitle?: string;
}

export interface FanOutItem {
  text: string;
  badge?: BadgeSpec;
}

export interface FanOutContent {
  title: string;
  englishLabel?: string;
  leftItems: FanOutItem[];
  rightCardTitle: string;
  rightCardSubtitle?: string;
  rightCardBody: string;
  rightPills?: string[];
  sceneSubtitle?: string;
}

export interface DocTreeFileEntry {
  name: string;
  icon?: string;
  badge?: string;
  indent?: number;
}

export interface DocTreeTocItem {
  num: string;
  name: string;
  badges?: string[];
}

export interface DocTreeContent {
  title: string;
  englishLabel?: string;
  rootName: string;
  rootBadge?: string;
  files: DocTreeFileEntry[];
  tocTitle: string;
  toc: DocTreeTocItem[];
  codeTitle: string;
  codeContent: string;
  codeLanguage?: string;
  sceneSubtitle?: string;
}

// Block-tree escape hatch.
export interface BlockTreeContent {
  title?: string;
  englishLabel?: string;
  blocks: Block[];
  sceneSubtitle?: string;
}

// ───────────────────────────────────────────────────────────────────────
//  v3 — Advanced tech layout content types
// ───────────────────────────────────────────────────────────────────────

export interface TechMultiPanelContent {
  title: string;
  englishLabel?: string;
  chapterBadge?: string;
  leftPanel: {
    title?: string;
    items: {
      text: string;
      state?: 'idle' | 'active' | 'completed' | 'error';
      badge?: BadgeSpec;
      progress?: number;
    }[];
    progress?: { current: number; total: number };
  };
  centerPanel: {
    title?: string;
    subtitle?: string;
    body: string;
    progressBar?: ProgressBarSegment[];
    glow?: boolean;
  };
  rightPanel: {
    title?: string;
    items: { name: string; badge?: BadgeSpec }[];
    pagination?: { current: number; total: number };
  };
  sceneSubtitle?: string;
}

export interface ConnectedCardsContent {
  title: string;
  englishLabel?: string;
  chapterBadge?: string;
  cards: {
    num: string;
    title: string;
    items: string[];
    state?: 'normal' | 'highlighted' | 'dimmed';
    accentColor?: 'orange' | 'cyan' | 'green' | 'red';
  }[];
  centerText?: string;
  sceneSubtitle?: string;
}

export interface ArchitectureFlowContent {
  title: string;
  englishLabel?: string;
  chapterBadge?: string;
  nodes: {
    id: string;
    label: string;
    sublabel?: string;
    x: number; y: number; w: number; h: number;
    color: 'orange' | 'cyan' | 'red' | 'green' | 'neutral';
    glow?: boolean;
  }[];
  connections: {
    from: string;
    to: string;
    label?: string;
    flowing?: boolean;
    color?: string;
    variant?: 'straight' | 'curve' | 'arrow' | 'dashed';
  }[];
  sceneSubtitle?: string;
}

export interface StackHighlightContent {
  title: string;
  englishLabel?: string;
  chapterBadge?: string;
  leftItems: {
    text: string;
    highlighted?: boolean;
    badge?: BadgeSpec;
    state?: 'idle' | 'active' | 'completed' | 'error';
  }[];
  rightCard: {
    title: string;
    subtitle?: string;
    body: string;
    pills?: string[];
  };
  sceneSubtitle?: string;
}

// ───────────────────────────────────────────────────────────────────────
//  v3 — New visual layout content types
// ───────────────────────────────────────────────────────────────────────

export interface TimelineStepsContent {
  title: string;
  englishLabel?: string;
  chapterBadge?: string;
  items: {
    num: string;
    title: string;
    description?: string;
    color?: 'orange' | 'cyan' | 'green' | 'red';
  }[];
  sceneSubtitle?: string;
}

export interface StatsShowcaseContent {
  title: string;
  englishLabel?: string;
  chapterBadge?: string;
  stats: {
    value: string;
    label: string;
    description?: string;
    color?: 'orange' | 'cyan' | 'green' | 'red';
  }[];
  sceneSubtitle?: string;
}

export interface QuoteCardContent {
  quote: string;
  author?: string;
  source?: string;
  englishLabel?: string;
  chapterBadge?: string;
  sceneSubtitle?: string;
}

export interface ProgressStepsContent {
  title: string;
  englishLabel?: string;
  chapterBadge?: string;
  steps: {
    num: string;
    label: string;
    active?: boolean;
    completed?: boolean;
  }[];
  sceneSubtitle?: string;
}

export interface FeatureComparisonContent {
  title: string;
  englishLabel?: string;
  chapterBadge?: string;
  leftTitle: string;
  rightTitle: string;
  features: {
    name: string;
    left?: string;
    right?: string;
  }[];
  sceneSubtitle?: string;
}

// ───────────────────────────────────────────────────────────────────────
//  v3 — Data comparison & Terminal mockup content types
// ───────────────────────────────────────────────────────────────────────

export interface DataCompareItem {
  label: string;          // e.g. "会写代码的人"
  baseValue: number;      // e.g. 50
  baseLabel?: string;     // e.g. "底子"
  multiplier?: number;    // e.g. 3 — shows as "×3"
  resultValue: number;    // e.g. 150
  color?: 'orange' | 'cyan' | 'green' | 'red';
}

export interface DataCompareContent {
  title: string;
  englishLabel?: string;
  chapterBadge?: string;
  items: DataCompareItem[];
  centerText?: string;    // e.g. "越会写代码，越能借上它的力"
  sceneSubtitle?: string;
}

export interface TerminalLine {
  text: string;
  highlight?: boolean;    // orange background highlight
  isUser?: boolean;       // user prompt vs AI response
}

export interface TerminalMockupContent {
  title: string;
  englishLabel?: string;
  chapterBadge?: string;
  terminalTitle?: string; // e.g. "Claude 的一条回复"
  lines: TerminalLine[];
  calloutText?: string;   // bottom callout
  sceneSubtitle?: string;
}

// ───────────────────────────────────────────────────────────────────────
//  Legacy v1 types (unchanged)
// ───────────────────────────────────────────────────────────────────────

export interface DataPoint {
  label: string;
  value: number;
  unit?: string;
  color?: string;
}

export interface TimelineItem {
  date: string;
  title: string;
  description?: string;
}

export interface Scene {
  // v1 routing (legacy)
  type?: SceneType;
  // v2 routing (new)
  layout?: LayoutType;
  blocks?: Block[];

  // Common content
  title?: string;
  subtitle?: string;
  lines?: string[];
  items?: string[];
  body?: string;
  duration: number;

  // v2 per-scene visuals
  englishLabel?: string;
  sceneSubtitle?: string;
  subtitleChunks?: SubtitleChunk[];
  chapterBadge?: string;  // v3 scene chapter badge

  // Layout-specific content (only one will be populated per scene)
  cardGrid?: CardGridContent;
  numberedCards?: NumberedCardsContent;
  splitCompare?: SplitCompareContent;
  flowDiagram?: FlowDiagramContent;
  fanOut?: FanOutContent;
  docTree?: DocTreeContent;
  titleCard?: TitleCardContent;
  // v3 layout content
  techMultiPanel?: TechMultiPanelContent;
  connectedCards?: ConnectedCardsContent;
  architectureFlow?: ArchitectureFlowContent;
  stackHighlight?: StackHighlightContent;
  // v3 new visual layouts
  timelineSteps?: TimelineStepsContent;
  statsShowcase?: StatsShowcaseContent;
  quoteCard?: QuoteCardContent;
  progressSteps?: ProgressStepsContent;
  featureComparison?: FeatureComparisonContent;
  dataCompare?: DataCompareContent;
  terminalMockup?: TerminalMockupContent;

  // Highlight (legacy)
  highlight?: string;
  highlightValue?: string;

  // Quote (legacy)
  quote?: string;
  quoteAuthor?: string;

  // Data (legacy)
  dataPoints?: DataPoint[];

  // Comparison (legacy)
  leftTitle?: string;
  leftItems?: string[];
  rightTitle?: string;
  rightItems?: string[];

  // Timeline (legacy)
  timelineItems?: TimelineItem[];

  // Image assets
  imageUrl?: string;
  imageQuery?: string;

  // Visual control
  theme?: string;
  animation?: string;
}

export interface CompositionPlan {
  title?: string;
  theme: string;
  scenes: Scene[];
  audioPath?: string;
  subtitles?: string;
  tags?: string[];
}
