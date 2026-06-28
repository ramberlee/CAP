// ===== 动画曲线配置 =====
export interface AnimationTimings {
  fast: number;    // 8 frames
  normal: number;  // 15 frames
  slow: number;    // 30 frames
  stagger: number; // 4 frames per item
}

// ===== 间距配置 =====
export interface Spacing {
  xs: number;  // 4
  sm: number;  // 8
  md: number;  // 16
  lg: number;  // 24
  xl: number;  // 40
  xxl: number; // 60
}

// ===== 圆角配置 =====
export interface Radius {
  sm: number;  // 4
  md: number;  // 8
  lg: number;  // 16
  xl: number;  // 24
  full: number; // 9999
}

// ===== 字体配置 =====
export interface Typography {
  fontFamily: string;
  fontWeights: {
    regular: number;
    medium: number;
    semibold: number;
    bold: number;
  };
  fontSize: {
    xs: number;  // 12
    sm: number;  // 14
    md: number;  // 18
    lg: number;  // 24
    xl: number;  // 32
    xxl: number; // 48
    hero: number; // 72
  };
  lineHeight: {
    tight: number; // 1.2
    normal: number; // 1.5
    relaxed: number; // 1.8
  };
}

// ===== 颜色配置 =====
export interface ColorPalette {
  background: string;
  backgroundGradient?: string;
  text: string;
  textSecondary: string;
  textMuted: string;
  accent: string;
  accentSecondary: string;
  surface: string;
  surfaceBorder: string;

  // 玻璃拟态专属
  glassSurface?: string;
  glassBorder?: string;
  glassSurfaceStrong?: string;

  // 颜色变量
  accentOrange: string;
  accentCyan: string;
  accentRed: string;
  accentGreen: string;
  accentYellow: string;
  accentPurple: string;

  // v3 科技风专属
  dotGridColor?: string;
  particleColor?: string;
  beamColor?: string;
  flowCurveColor?: string;
  glowIntensity?: number;
}

// ===== 完整主题配置 =====
export interface ThemePalette extends ColorPalette {
  id?: string;
  name?: string;
  spacing: Spacing;
  radius: Radius;
  typography: Typography;
  animation: AnimationTimings;
}

export type ThemeId =
  | 'dark_tech'
  | 'light_clean'
  | 'vibrant'
  | 'minimal'
  | 'news'
  | 'dark_glass'
  | 'dark_tech_v3';
