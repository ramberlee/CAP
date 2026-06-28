import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { ThemePalette } from '../../types';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { isDarkGlassTheme } from '../../themes';

/**
 * Top-right "english label" pill (e.g. "SKILL", "repeatable tasks").
 * Renders absolute-positioned in the top-right corner of the scene.
 * Fades in at scene start, fades out at scene end.
 */
export const EnglishLabel: React.FC<{ text?: string; theme: ThemePalette }> = ({ text, theme }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  if (!text) return null;

  const fadeIn = interpolate(frame, [0, 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const fadeOutStart = Math.max(0, durationInFrames - 10);
  const fadeOut = interpolate(frame, [fadeOutStart, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const opacity = Math.min(fadeIn, fadeOut);

  const useGlass = isDarkGlassTheme(theme);

  return (
    <div
      style={{
        position: 'absolute',
        top: 48,
        right: 64,
        padding: '8px 18px',
        background: useGlass ? (theme.glassSurface ?? 'rgba(255,255,255,0.06)') : 'rgba(0,0,0,0.4)',
        border: useGlass ? `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.12)'}` : '1px solid rgba(255,255,255,0.15)',
        borderRadius: 999,
        backdropFilter: useGlass ? 'blur(8px)' : 'none',
        WebkitBackdropFilter: useGlass ? 'blur(8px)' : 'none',
        fontFamily: FONT_FAMILY,
        fontSize: 16,
        fontWeight: FONT_WEIGHT.medium,
        color: theme.textSecondary,
        letterSpacing: 1.2,
        opacity,
        zIndex: 10,
      }}
    >
      {text}
    </div>
  );
};

/**
 * Standard scene frame: background + dot grid (for dark_glass) + english label slot.
 * Children render inside.
 */
export const SceneFrame: React.FC<{
  theme: ThemePalette;
  englishLabel?: string;
  children: React.ReactNode;
  showGrid?: boolean;
}> = ({ theme, englishLabel, children, showGrid = true }) => {
  const { durationInFrames } = useVideoConfig();
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: theme.backgroundGradient ?? theme.background,
        fontFamily: FONT_FAMILY,
        color: theme.text,
      }}
    >
      {showGrid && isDarkGlassTheme(theme) && (
        <DotGridBackgroundInline durationInFrames={durationInFrames} theme={theme} />
      )}
      <EnglishLabel text={englishLabel} theme={theme} />
      {children}
    </div>
  );
};

// Inline dot grid (avoids an extra import)
const DotGridBackgroundInline: React.FC<{ theme: ThemePalette; durationInFrames: number }> = ({
  theme,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const dotColor = theme.dotGridColor ?? 'rgba(255,255,255,0.05)';
  const opacity = interpolate(
    frame,
    [0, 30, Math.max(30, durationInFrames - 10), durationInFrames],
    [0, 0.85, 0.85, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: `radial-gradient(${dotColor} 1.2px, transparent 1.7px)`,
        backgroundSize: '48px 48px',
        opacity,
        pointerEvents: 'none',
      }}
    />
  );
};
