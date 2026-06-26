import React from 'react';
import { AbsoluteFill } from 'remotion';
import { ThemePalette } from '../themes';

interface GradientOverlayProps {
  theme: ThemePalette;
  /** Direction of gradient: 'to-bottom' (default), 'to-top', 'to-right', etc. */
  direction?: string;
  /** Opacity of the overlay, 0-1 */
  opacity?: number;
}

/**
 * Gradient overlay for darkening/brightening backgrounds.
 * Used on top of background images to ensure text readability.
 */
export const GradientOverlay: React.FC<GradientOverlayProps> = ({
  theme,
  direction = 'to-bottom',
  opacity = 0.6,
}) => {
  const isDark = theme.background === '#0D1117' || theme.background === '#000000' || theme.background === '#1A0A2E';

  return (
    <AbsoluteFill
      style={{
        background: isDark
          ? `linear-gradient(${direction}, rgba(0,0,0,${opacity}) 0%, rgba(0,0,0,${opacity * 0.7}) 50%, rgba(0,0,0,${opacity}) 100%)`
          : `linear-gradient(${direction}, rgba(0,0,0,${opacity * 0.4}) 0%, rgba(0,0,0,${opacity * 0.2}) 100%)`,
      }}
    />
  );
};

/**
 * Vignette overlay — darker edges, lighter center.
 */
export const VignetteOverlay: React.FC<{ opacity?: number }> = ({ opacity = 0.5 }) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,${opacity}) 100%)`,
    }}
  />
);
