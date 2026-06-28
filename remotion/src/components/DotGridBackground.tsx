import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { ThemePalette } from '../themes';

interface DotGridBackgroundProps {
  theme: ThemePalette;
  /** Cell spacing in pixels. Defaults to 48. */
  spacing?: number;
  /** Dot radius in pixels. Defaults to 1.2. */
  radius?: number;
  /** Scene duration in frames — used for entry fade. */
  sceneDurationInFrames: number;
}

/**
 * Subtle SVG dot grid background used in dark_glass scenes.
 * Renders a pattern of low-opacity dots. Fades in with the scene and out near the end.
 */
export const DotGridBackground: React.FC<DotGridBackgroundProps> = ({
  theme,
  spacing = 48,
  radius = 1.2,
  sceneDurationInFrames,
}) => {
  const frame = useCurrentFrame();
  const dotColor = theme.dotGridColor ?? 'rgba(255,255,255,0.05)';

  // Soft entry fade: dots appear in the first 30 frames, fade out in the last 10.
  const opacity = interpolate(
    frame,
    [0, 30, Math.max(30, sceneDurationInFrames - 10), sceneDurationInFrames],
    [0, 0.85, 0.85, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );

  // Use a fixed SVG canvas; the pattern repeats from 0,0 to 1920×1080.
  // Render via CSS background-image (more efficient than thousands of <circle> nodes).
  return (
    <AbsoluteFill style={{ opacity, pointerEvents: 'none' }}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `radial-gradient(${dotColor} ${radius}px, transparent ${radius + 0.5}px)`,
          backgroundSize: `${spacing}px ${spacing}px`,
        }}
      />
    </AbsoluteFill>
  );
};

/**
 * Vertical / horizontal line grid variant (used in some dark_glass scenes).
 */
export const LineGridBackground: React.FC<DotGridBackgroundProps> = ({
  theme,
  spacing = 80,
  sceneDurationInFrames,
}) => {
  const frame = useCurrentFrame();
  const lineColor = theme.dotGridColor ?? 'rgba(255,255,255,0.04)';

  const opacity = interpolate(
    frame,
    [0, 30, Math.max(30, sceneDurationInFrames - 10), sceneDurationInFrames],
    [0, 0.6, 0.6, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );

  return (
    <AbsoluteFill style={{ opacity, pointerEvents: 'none' }}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(to right, ${lineColor} 1px, transparent 1px),
            linear-gradient(to bottom, ${lineColor} 1px, transparent 1px)
          `,
          backgroundSize: `${spacing}px ${spacing}px`,
        }}
      />
    </AbsoluteFill>
  );
};
