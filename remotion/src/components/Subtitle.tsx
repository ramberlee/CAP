import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { SubtitleChunk } from '../types';
import { ThemePalette } from '../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../styles/typography';
import { isDarkGlassTheme } from '../themes';

interface SubtitleProps {
  /** Either a single static text (simple caption) or timed chunks (animated reveals). */
  text?: string;
  chunks?: SubtitleChunk[];
  /** Theme palette (used to pick glass / classic styling). */
  theme: ThemePalette;
  /** Scene duration in frames. */
  sceneDurationInFrames: number;
  /** Whether to render a glass-pill background (true for dark_glass). */
  glassBackground?: boolean;
  /** Position from the bottom, in pixels. */
  bottomOffset?: number;
}

/**
 * Bottom-center caption that mirrors the look in the reference samples.
 *
 * Behaviour:
 * - If `chunks` is provided, displays only the chunk whose [start, end] interval
 *   contains the current scene time (with a 0.25s crossfade between chunks).
 * - Otherwise, displays `text` for the full scene duration.
 * - Always fades in at the start (first 15 frames) and out at the end (last 10).
 */
export const Subtitle: React.FC<SubtitleProps> = ({
  text,
  chunks,
  theme,
  sceneDurationInFrames,
  glassBackground = true,
  bottomOffset = 56,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // Pick the currently active chunk, if any.
  let activeText: string | undefined;
  if (chunks && chunks.length > 0) {
    const active = chunks.find((c) => t >= c.start && t < c.end);
    activeText = active?.text;
  }
  if (!activeText) activeText = text;

  // Entry / exit fade for the whole caption.
  const fadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fadeOutStart = Math.max(0, sceneDurationInFrames - 10);
  const fadeOut = interpolate(frame, [fadeOutStart, sceneDurationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const opacity = Math.min(fadeIn, fadeOut);

  if (!activeText) return null;

  const useGlass = glassBackground && isDarkGlassTheme(theme);

  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: bottomOffset,
          display: 'flex',
          justifyContent: 'center',
          opacity,
        }}
      >
        <div
          style={{
            maxWidth: 1400,
            padding: useGlass ? '14px 32px' : '10px 24px',
            borderRadius: 999,
            background: useGlass
              ? (theme.glassSurfaceStrong ?? 'rgba(255,255,255,0.08)')
              : 'rgba(0,0,0,0.55)',
            border: useGlass
              ? `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.12)'}`
              : 'none',
            boxShadow: useGlass ? '0 6px 24px rgba(0,0,0,0.35)' : 'none',
            backdropFilter: useGlass ? 'blur(12px)' : 'none',
            WebkitBackdropFilter: useGlass ? 'blur(12px)' : 'none',
            color: theme.text,
            fontFamily: FONT_FAMILY,
            fontSize: 26,
            fontWeight: FONT_WEIGHT.medium,
            letterSpacing: 1,
            textAlign: 'center',
            lineHeight: 1.4,
          }}
        >
          {activeText}
        </div>
      </div>
    </AbsoluteFill>
  );
};
