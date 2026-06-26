/* Scene type definitions for CAP Remotion landscape videos (16:9, 1920×1080) */

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
  type: SceneType;
  duration: number; // seconds (driven by audio timing)

  // Common content fields
  title?: string;
  subtitle?: string;
  lines?: string[];
  items?: string[];
  body?: string;

  // Highlight scene
  highlight?: string;
  highlightValue?: string;

  // Quote scene
  quote?: string;
  quoteAuthor?: string;

  // Data scene
  dataPoints?: DataPoint[];

  // Comparison scene
  leftTitle?: string;
  leftItems?: string[];
  rightTitle?: string;
  rightItems?: string[];

  // Timeline scene
  timelineItems?: TimelineItem[];

  // Image assets (populated by asset-manager / local HTTP server)
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
