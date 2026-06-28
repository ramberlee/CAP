import { ThemePalette, ThemeId } from './themeTypes';

// ===== 基础常量 =====
const BASE_SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 40,
  xxl: 60,
};

const BASE_RADIUS = {
  sm: 4,
  md: 8,
  lg: 16,
  xl: 24,
  full: 9999,
};

const BASE_TYPOGRAPHY = {
  fontFamily: '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
  fontWeights: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  fontSize: {
    xs: 12,
    sm: 14,
    md: 18,
    lg: 24,
    xl: 32,
    xxl: 48,
    hero: 72,
  },
  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.8,
  },
};

const BASE_ANIMATION = {
  fast: 8,
  normal: 15,
  slow: 30,
  stagger: 4,
};

// ===== 主题预设 =====
export const DARK_GLASS: ThemePalette = {
  id: 'dark_glass',
  name: '深色玻璃质感',
  background: '#0A0A0F',
  backgroundGradient: 'linear-gradient(135deg, #0A0A0F 0%, #161B2E 50%, #0A0A0F 100%)',
  text: '#FFFFFF',
  textSecondary: '#A0A0B8',
  textMuted: '#6B7280',
  accent: '#FF6B35',
  accentSecondary: '#00D4FF',
  surface: 'rgba(255,255,255,0.06)',
  surfaceBorder: 'rgba(255,255,255,0.12)',
  glassSurface: 'rgba(255,255,255,0.05)',
  glassSurfaceStrong: 'rgba(255,255,255,0.09)',
  glassBorder: 'rgba(255,255,255,0.12)',
  accentOrange: '#FF6B35',
  accentCyan: '#00D4FF',
  accentRed: '#FF4757',
  accentGreen: '#2ED573',
  accentYellow: '#FFA502',
  accentPurple: '#A855F7',
  dotGridColor: 'rgba(255,255,255,0.05)',
  particleColor: 'rgba(255,255,255,0.6)',
  beamColor: 'rgba(0,212,255,0.08)',
  flowCurveColor: 'rgba(255,107,53,0.4)',
  glowIntensity: 0.6,
  spacing: BASE_SPACING,
  radius: BASE_RADIUS,
  typography: BASE_TYPOGRAPHY,
  animation: BASE_ANIMATION,
};

export const DARK_TECH_V3: ThemePalette = {
  id: 'dark_tech_v3',
  name: '科技风 v3',
  background: '#06060B',
  backgroundGradient: 'linear-gradient(135deg, #06060B 0%, #0D1021 40%, #06060B 100%)',
  text: '#FFFFFF',
  textSecondary: '#7A7A9E',
  textMuted: '#5A5A7E',
  accent: '#FF6B35',
  accentSecondary: '#00D4FF',
  surface: 'rgba(255,255,255,0.04)',
  surfaceBorder: 'rgba(255,255,255,0.08)',
  glassSurface: 'rgba(255,255,255,0.04)',
  glassSurfaceStrong: 'rgba(255,255,255,0.08)',
  glassBorder: 'rgba(255,255,255,0.10)',
  accentOrange: '#FF6B35',
  accentCyan: '#00D4FF',
  accentRed: '#FF4757',
  accentGreen: '#2ED573',
  accentYellow: '#FFA502',
  accentPurple: '#A855F7',
  dotGridColor: 'rgba(255,255,255,0.04)',
  particleColor: 'rgba(255,255,255,0.5)',
  beamColor: 'rgba(0,212,255,0.06)',
  flowCurveColor: 'rgba(255,107,53,0.35)',
  glowIntensity: 0.7,
  spacing: BASE_SPACING,
  radius: BASE_RADIUS,
  typography: BASE_TYPOGRAPHY,
  animation: BASE_ANIMATION,
};

export const DARK_TECH: ThemePalette = {
  id: 'dark_tech',
  name: '深色技术风',
  background: '#0D1117',
  backgroundGradient: 'linear-gradient(135deg, #0D1117 0%, #161B22 50%, #0D1117 100%)',
  text: '#FFFFFF',
  textSecondary: '#8B949E',
  textMuted: '#6E7681',
  accent: '#58A6FF',
  accentSecondary: '#FFD700',
  surface: '#161B22',
  surfaceBorder: '#30363D',
  accentOrange: '#F0883E',
  accentCyan: '#39D353',
  accentRed: '#F85149',
  accentGreen: '#3FB950',
  accentYellow: '#D29922',
  accentPurple: '#A371F7',
  spacing: BASE_SPACING,
  radius: BASE_RADIUS,
  typography: BASE_TYPOGRAPHY,
  animation: BASE_ANIMATION,
};

export const LIGHT_CLEAN: ThemePalette = {
  id: 'light_clean',
  name: '明亮清爽',
  background: '#FFFFFF',
  backgroundGradient: 'linear-gradient(135deg, #FFFFFF 0%, #F6F8FA 50%, #FFFFFF 100%)',
  text: '#1F2937',
  textSecondary: '#6B7280',
  textMuted: '#9CA3AF',
  accent: '#0969DA',
  accentSecondary: '#BF3989',
  surface: '#F6F8FA',
  surfaceBorder: '#D1D5DB',
  accentOrange: '#D97706',
  accentCyan: '#0891B2',
  accentRed: '#DC2626',
  accentGreen: '#059669',
  accentYellow: '#CA8A04',
  accentPurple: '#7C3AED',
  spacing: BASE_SPACING,
  radius: BASE_RADIUS,
  typography: BASE_TYPOGRAPHY,
  animation: BASE_ANIMATION,
};

export const VIBRANT: ThemePalette = {
  id: 'vibrant',
  name: '活力撞色',
  background: '#1A0A2E',
  backgroundGradient: 'linear-gradient(135deg, #1A0A2E 0%, #1A1A3E 50%, #2D1B4E 100%)',
  text: '#FFFFFF',
  textSecondary: '#C4B5D4',
  textMuted: '#9D8BB4',
  accent: '#FF6B35',
  accentSecondary: '#F7C948',
  surface: '#1A1A3E',
  surfaceBorder: '#3A2A5E',
  accentOrange: '#FF6B35',
  accentCyan: '#00D4FF',
  accentRed: '#FF4757',
  accentGreen: '#2ED573',
  accentYellow: '#F7C948',
  accentPurple: '#A855F7',
  spacing: BASE_SPACING,
  radius: BASE_RADIUS,
  typography: BASE_TYPOGRAPHY,
  animation: BASE_ANIMATION,
};

// ===== 主题注册表 =====
export const themePresets: Record<ThemeId, ThemePalette> = {
  dark_tech: DARK_TECH,
  light_clean: LIGHT_CLEAN,
  vibrant: VIBRANT,
  minimal: {
    ...DARK_TECH,
    id: 'minimal',
    name: '极简黑白',
    background: '#000000',
    backgroundGradient: undefined,
    text: '#FFFFFF',
    textSecondary: '#888888',
    textMuted: '#666666',
    accent: '#FFFFFF',
    accentSecondary: '#888888',
    surface: '#111111',
    surfaceBorder: '#333333',
  },
  news: {
    ...LIGHT_CLEAN,
    id: 'news',
    name: '新闻杂志',
    background: '#F0F2F5',
    backgroundGradient: 'linear-gradient(135deg, #F0F2F5 0%, #FFFFFF 50%, #F0F2F5 100%)',
    accent: '#E63946',
    accentSecondary: '#1D3557',
  },
  dark_glass: DARK_GLASS,
  dark_tech_v3: DARK_TECH_V3,
};

// ===== 默认主题 =====
export const DEFAULT_THEME_ID: ThemeId = 'dark_tech_v3';

// ===== 辅助函数 =====
export function getTheme(id: ThemeId | string | undefined): ThemePalette {
  if (id && id in themePresets) {
    return themePresets[id as ThemeId];
  }
  return themePresets[DEFAULT_THEME_ID];
}

export function isDarkTheme(theme: ThemePalette): boolean {
  const bg = theme.background.replace('#', '');
  const r = parseInt(bg.slice(0, 2), 16);
  const g = parseInt(bg.slice(2, 4), 16);
  const b = parseInt(bg.slice(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance < 0.5;
}

export function isGlassTheme(theme: ThemePalette): boolean {
  return theme.id === 'dark_glass' || theme.id === 'dark_tech_v3';
}
