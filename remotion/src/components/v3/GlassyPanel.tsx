import React from 'react';
import { ThemePalette } from '../../themes';
import { usePulseAnimation } from '../hooks/usePulseAnimation';

export interface GlassyPanelProps {
  theme: ThemePalette;
  variant?: 'glass' | 'outlined' | 'filled';
  accent?: 'orange' | 'cyan' | 'red' | 'green' | 'yellow';
  glow?: boolean;
  children: React.ReactNode;
  style?: React.CSSProperties;
  padding?: number | string;
  borderRadius?: number;
}

/**
 * Glass-morphism panel container used by all v3 layouts.
 * Features backdrop blur, gradient borders, and optional glow effect.
 */
export const GlassyPanel: React.FC<GlassyPanelProps> = ({
  theme,
  variant = 'glass',
  accent,
  glow = false,
  children,
  style,
  padding = 24,
  borderRadius = 16,
}) => {
  const pulse = usePulseAnimation({ intensity: glow ? 0.8 : 0 });

  // Get accent color
  const accentColors: Record<string, string> = {
    orange: theme.accentOrange ?? '#FF6B35',
    cyan: theme.accentCyan ?? '#00D4FF',
    red: theme.accentRed ?? '#FF4757',
    green: theme.accentGreen ?? '#2ED573',
    yellow: theme.accentYellow ?? '#FFA502',
  };
  const accentColor = accent ? accentColors[accent] : undefined;

  // Variant-specific styles
  const variantStyles: React.CSSProperties = variant === 'outlined'
    ? {
        background: 'transparent',
        border: `1px solid ${accentColor ?? theme.glassBorder ?? 'rgba(255,255,255,0.12)'}`,
      }
    : variant === 'filled'
    ? {
        background: accentColor
          ? `${accentColor}20` // 12% opacity
          : theme.glassSurfaceStrong ?? 'rgba(255,255,255,0.09)',
        border: `1px solid ${accentColor ?? theme.glassBorder ?? 'rgba(255,255,255,0.12)'}`,
      }
    : { // glass (default)
        background: theme.glassSurface ?? 'rgba(255,255,255,0.05)',
        border: `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.12)'}`,
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
      };

  // Glow effect
  const glowStyle: React.CSSProperties = glow && accentColor
    ? {
        boxShadow: `
          0 0 ${30 * pulse.glowIntensity}px ${accentColor}30,
          0 0 ${60 * pulse.glowIntensity}px ${accentColor}15,
          inset 0 0 ${20 * pulse.glowIntensity}px ${accentColor}08
        `,
        borderColor: `${accentColor}${Math.round(pulse.borderBrightness * 100 + 60).toString(16).padStart(2, '0')}`,
      }
    : {};

  return (
    <div
      style={{
        position: 'relative',
        borderRadius,
        padding: typeof padding === 'number' ? `${padding}px` : padding,
        ...variantStyles,
        ...glowStyle,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
