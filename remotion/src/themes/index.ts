// ===== 类型导出 =====
export * from './themeTypes';

// ===== 主题预设 =====
export * from './presets';

// ===== Hooks 工具 =====
export * from './useTheme';

// ===== 背景组件 =====
export * from './v3/ParticleBackground';
export * from './v3/GridGlowBackground';
export * from './v3/DataFlowCurves';

// ===== 向后兼容 =====
import { ThemePalette, ThemeId, getTheme, themePresets } from './presets';

// 兼容旧版导出
export { ThemePalette, ThemeId, getTheme, themePresets as themes };

// 检测是否是玻璃主题（兼容旧代码）
export function isDarkGlassTheme(theme: ThemePalette): boolean {
  return theme.id === 'dark_glass' || theme.id === 'dark_tech_v3';
}
