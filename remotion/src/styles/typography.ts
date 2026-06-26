/* Typography constants for 1920×1080 landscape videos */

export const FONT_FAMILY = '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif';
export const FONT_FAMILY_MONO = '"JetBrains Mono", "Fira Code", monospace';

export const FONT_WEIGHT = {
  regular: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
  extrabold: 800,
} as const;

/* Font sizes in px for 1920×1080 canvas */
export const FONT_SIZE = {
  title: 48,
  subtitle: 32,
  sectionTitle: 56,
  body: 26,
  bullet: 28,
  dataValue: 72,
  dataLabel: 22,
  quote: 36,
  quoteAuthor: 20,
  caption: 18,
  small: 16,
  highlight: 80,
  timeline: 22,
  button: 24,
} as const;

export const LINE_HEIGHT = {
  tight: 1.2,
  normal: 1.5,
  relaxed: 1.75,
} as const;
