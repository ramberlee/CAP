/* Color themes for CAP Remotion landscape videos (16:9, 1920×1080) */

export interface ThemePalette {
  background: string;
  backgroundGradient?: string;
  text: string;
  textSecondary: string;
  accent: string;
  accentSecondary: string;
  surface: string;
  surfaceBorder: string;
}

export type ThemeId = 'dark_tech' | 'light_clean' | 'vibrant' | 'minimal' | 'news';

const themes: Record<ThemeId, ThemePalette> = {
  dark_tech: {
    background: '#0D1117',
    backgroundGradient: 'linear-gradient(135deg, #0D1117 0%, #161B22 50%, #0D1117 100%)',
    text: '#FFFFFF',
    textSecondary: '#8B949E',
    accent: '#58A6FF',
    accentSecondary: '#FFD700',
    surface: '#161B22',
    surfaceBorder: '#30363D',
  },
  light_clean: {
    background: '#FFFFFF',
    backgroundGradient: 'linear-gradient(135deg, #FFFFFF 0%, #F6F8FA 50%, #FFFFFF 100%)',
    text: '#1F2937',
    textSecondary: '#6B7280',
    accent: '#0969DA',
    accentSecondary: '#BF3989',
    surface: '#F6F8FA',
    surfaceBorder: '#D1D5DB',
  },
  vibrant: {
    background: '#1A0A2E',
    backgroundGradient: 'linear-gradient(135deg, #1A0A2E 0%, #1A1A3E 50%, #2D1B4E 100%)',
    text: '#FFFFFF',
    textSecondary: '#C4B5D4',
    accent: '#FF6B35',
    accentSecondary: '#F7C948',
    surface: '#1A1A3E',
    surfaceBorder: '#3A2A5E',
  },
  minimal: {
    background: '#000000',
    text: '#FFFFFF',
    textSecondary: '#888888',
    accent: '#FFFFFF',
    accentSecondary: '#888888',
    surface: '#111111',
    surfaceBorder: '#333333',
  },
  news: {
    background: '#F0F2F5',
    backgroundGradient: 'linear-gradient(135deg, #F0F2F5 0%, #FFFFFF 50%, #F0F2F5 100%)',
    text: '#1D3557',
    textSecondary: '#6B7280',
    accent: '#E63946',
    accentSecondary: '#1D3557',
    surface: '#FFFFFF',
    surfaceBorder: '#D1D5DB',
  },
};

export function getTheme(id: ThemeId | string): ThemePalette {
  return themes[id as ThemeId] || themes.dark_tech;
}

export default themes;
