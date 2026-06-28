/* Color themes for CAP Remotion landscape videos (16:9, 1920×1080) */

export interface ThemePalette {
  id?: string;
  background: string;
  backgroundGradient?: string;
  text: string;
  textSecondary: string;
  accent: string;
  accentSecondary: string;
  surface: string;
  surfaceBorder: string;

  // Optional tokens for the dark_glass visual system. Other themes leave them unset.
  glassSurface?: string;
  glassBorder?: string;
  glassSurfaceStrong?: string;
  dotGridColor?: string;
  accentOrange?: string;
  accentCyan?: string;
  accentRed?: string;
  accentGreen?: string;
  accentYellow?: string;

  // v3 theme tokens for advanced tech visuals
  particleColor?: string;
  beamColor?: string;
  flowCurveColor?: string;
  glowIntensity?: number;
}

export type ThemeId =
  | 'dark_tech'
  | 'light_clean'
  | 'vibrant'
  | 'minimal'
  | 'news'
  | 'dark_glass'
  | 'dark_tech_v3';

const themes: Record<ThemeId, ThemePalette> = {
  dark_tech: {
    id: 'dark_tech',
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
    id: 'light_clean',
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
    id: 'vibrant',
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
    id: 'minimal',
    background: '#000000',
    text: '#FFFFFF',
    textSecondary: '#888888',
    accent: '#FFFFFF',
    accentSecondary: '#888888',
    surface: '#111111',
    surfaceBorder: '#333333',
  },
  news: {
    id: 'news',
    background: '#F0F2F5',
    backgroundGradient: 'linear-gradient(135deg, #F0F2F5 0%, #FFFFFF 50%, #F0F2F5 100%)',
    text: '#1D3557',
    textSecondary: '#6B7280',
    accent: '#E63946',
    accentSecondary: '#1D3557',
    surface: '#FFFFFF',
    surfaceBorder: '#D1D5DB',
  },
  dark_glass: {
    id: 'dark_glass',
    background: '#0A0A0F',
    backgroundGradient:
      'linear-gradient(135deg, #0A0A0F 0%, #161B2E 50%, #0A0A0F 100%)',
    text: '#FFFFFF',
    textSecondary: '#A0A0B8',
    accent: '#FF6B35',
    accentSecondary: '#00D4FF',
    surface: 'rgba(255,255,255,0.06)',
    surfaceBorder: 'rgba(255,255,255,0.12)',
    glassSurface: 'rgba(255,255,255,0.05)',
    glassSurfaceStrong: 'rgba(255,255,255,0.09)',
    glassBorder: 'rgba(255,255,255,0.12)',
    dotGridColor: 'rgba(255,255,255,0.05)',
    accentOrange: '#FF6B35',
    accentCyan: '#00D4FF',
    accentRed: '#FF4757',
    accentGreen: '#2ED573',
    accentYellow: '#FFA502',
    // v3 additions
    particleColor: 'rgba(255,255,255,0.6)',
    beamColor: 'rgba(0,212,255,0.08)',
    flowCurveColor: 'rgba(255,107,53,0.4)',
    glowIntensity: 0.6,
  },
  dark_tech_v3: {
    id: 'dark_tech_v3',
    background: '#06060B',
    backgroundGradient:
      'linear-gradient(135deg, #06060B 0%, #0D1021 40%, #06060B 100%)',
    text: '#FFFFFF',
    textSecondary: '#7A7A9E',
    accent: '#FF6B35',
    accentSecondary: '#00D4FF',
    surface: 'rgba(255,255,255,0.04)',
    surfaceBorder: 'rgba(255,255,255,0.08)',
    glassSurface: 'rgba(255,255,255,0.04)',
    glassSurfaceStrong: 'rgba(255,255,255,0.08)',
    glassBorder: 'rgba(255,255,255,0.10)',
    dotGridColor: 'rgba(255,255,255,0.04)',
    accentOrange: '#FF6B35',
    accentCyan: '#00D4FF',
    accentRed: '#FF4757',
    accentGreen: '#2ED573',
    accentYellow: '#FFA502',
    // v3 tokens
    particleColor: 'rgba(255,255,255,0.5)',
    beamColor: 'rgba(0,212,255,0.06)',
    flowCurveColor: 'rgba(255,107,53,0.35)',
    glowIntensity: 0.7,
  },
};

export function getTheme(id: ThemeId | string | undefined): ThemePalette {
  if (id && id in themes) {
    return themes[id as ThemeId];
  }
  return themes.dark_glass;
}

export function isDarkGlassTheme(theme: ThemePalette): boolean {
  return theme.id === 'dark_glass';
}

export default themes;
