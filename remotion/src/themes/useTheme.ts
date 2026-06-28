import { useMemo } from 'react';
import { ThemePalette, ThemeId, getTheme, isDarkTheme, isGlassTheme } from './presets';

// ===== 主题 Hook =====
export function useTheme(themeId?: ThemeId | string): {
  theme: ThemePalette;
  isDark: boolean;
  isGlass: boolean;
  colors: ThemePalette;
  spacing: ThemePalette['spacing'];
  radius: ThemePalette['radius'];
  typography: ThemePalette['typography'];
  animation: ThemePalette['animation'];
} {
  const theme = useMemo(() => getTheme(themeId), [themeId]);

  return {
    theme,
    isDark: isDarkTheme(theme),
    isGlass: isGlassTheme(theme),
    colors: theme,
    spacing: theme.spacing,
    radius: theme.radius,
    typography: theme.typography,
    animation: theme.animation,
  };
}

// ===== 颜色操作工具 =====

/**
 * 调整颜色透明度
 */
export function withAlpha(color: string, alpha: number): string {
  // 处理 rgb/rgba 格式
  if (color.startsWith('rgb')) {
    const match = color.match(/(\d+),\s*(\d+),\s*(\d+)/);
    if (match) {
      const [, r, g, b] = match;
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
  }

  // 处理 hex 格式
  if (color.startsWith('#')) {
    const hex = color.slice(1);
    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  return color;
}

/**
 * 加深颜色
 */
export function darken(color: string, amount: number): string {
  if (!color.startsWith('#')) return color;

  const hex = color.slice(1);
  const num = parseInt(hex, 16);
  const r = Math.max(0, ((num >> 16) & 255) - amount * 255);
  const g = Math.max(0, ((num >> 8) & 255) - amount * 255);
  const b = Math.max(0, (num & 255) - amount * 255);

  return `#${Math.round(r).toString(16).padStart(2, '0')}${Math.round(g).toString(16).padStart(2, '0')}${Math.round(b).toString(16).padStart(2, '0')}`;
}

/**
 * 加亮颜色
 */
export function lighten(color: string, amount: number): string {
  if (!color.startsWith('#')) return color;

  const hex = color.slice(1);
  const num = parseInt(hex, 16);
  const r = Math.min(255, ((num >> 16) & 255) + amount * 255);
  const g = Math.min(255, ((num >> 8) & 255) + amount * 255);
  const b = Math.min(255, (num & 255) + amount * 255);

  return `#${Math.round(r).toString(16).padStart(2, '0')}${Math.round(g).toString(16).padStart(2, '0')}${Math.round(b).toString(16).padStart(2, '0')}`;
}

/**
 * 获取对比色（黑/白）
 */
export function getContrastColor(color: string): string {
  if (!color.startsWith('#')) return '#FFFFFF';

  const hex = color.slice(1);
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);

  // YIQ 亮度公式
  const yiq = (r * 299 + g * 587 + b * 114) / 1000;

  return yiq >= 128 ? '#000000' : '#FFFFFF';
}
