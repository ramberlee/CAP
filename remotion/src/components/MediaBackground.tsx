import React from 'react';
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { GradientOverlay } from './GradientOverlay';
import { ThemePalette } from '../themes';

interface MediaBackgroundProps {
  /** Image URL (from local HTTP server) */
  imageUrl?: string;
  /** Theme for overlay colors */
  theme: ThemePalette;
  /** Whether to apply a vignette */
  vignette?: boolean;
  /** Ken Burns effect: 'zoomIn' (default), 'zoomOut', 'none' */
  kenBurns?: 'zoomIn' | 'zoomOut' | 'none';
  /** Overlay opacity (0-1) */
  overlayOpacity?: number;
  /** Whether to blur the image */
  blur?: number;
}

/**
 * Background image component with Ken Burns effect and gradient overlay.
 * Used by all scene components for consistent background treatment.
 */
export const MediaBackground: React.FC<MediaBackgroundProps> = ({
  imageUrl,
  theme,
  vignette = true,
  kenBurns = 'zoomIn',
  overlayOpacity = 0.5,
  blur = 0,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  if (!imageUrl) {
    // Pure gradient background
    return (
      <AbsoluteFill
        style={{
          background: theme.backgroundGradient || theme.background,
        }}
      />
    );
  }

  const progress = durationInFrames > 0 ? frame / durationInFrames : 0;

  const getTransform = () => {
    if (kenBurns === 'none') return 'none';
    const scale = kenBurns === 'zoomIn'
      ? interpolate(progress, [0, 1], [1.0, 1.08])
      : interpolate(progress, [0, 1], [1.08, 1.0]);
    return `scale(${scale})`;
  };

  return (
    <AbsoluteFill>
      <AbsoluteFill
        style={{
          transform: getTransform(),
          filter: blur > 0 ? `blur(${blur}px)` : undefined,
        }}
      >
        <Img
          src={imageUrl}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </AbsoluteFill>
      <GradientOverlay theme={theme} opacity={overlayOpacity} />
      {vignette && (
        <AbsoluteFill
          style={{
            background: 'radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.4) 100%)',
          }}
        />
      )}
    </AbsoluteFill>
  );
};

/**
 * Fallback geometric background when no image is available.
 * Pure Remotion/CSS — no external assets needed.
 */
export const GeometricBackground: React.FC<{
  theme: ThemePalette;
  accent?: string;
}> = ({ theme, accent }) => {
  const frame = useCurrentFrame();
  const accentColor = accent || theme.accent;

  return (
    <AbsoluteFill
      style={{
        background: theme.backgroundGradient || theme.background,
      }}
    >
      {/* Decorative circles */}
      <AbsoluteFill
        style={{
          position: 'absolute',
          top: '10%',
          right: '5%',
          width: 300,
          height: 300,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${accentColor}22 0%, transparent 70%)`,
          opacity: 0.5,
          transform: `translate(${Math.sin(frame * 0.01) * 10}px, ${Math.cos(frame * 0.015) * 8}px)`,
        }}
      />
      <AbsoluteFill
        style={{
          position: 'absolute',
          bottom: '15%',
          left: '8%',
          width: 200,
          height: 200,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${accentColor}15 0%, transparent 70%)`,
          opacity: 0.4,
          transform: `translate(${Math.cos(frame * 0.012) * 8}px, ${Math.sin(frame * 0.01) * 10}px)`,
        }}
      />
    </AbsoluteFill>
  );
};
