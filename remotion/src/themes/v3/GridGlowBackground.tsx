import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ThemePalette } from '../../themes';
import { usePulseAnimation } from '../../components/hooks/usePulseAnimation';

export interface GridGlowBackgroundProps {
  theme: ThemePalette;
  gridSize?: number;
  showBeams?: boolean;
  beamCount?: number;
}

/**
 * Grid background with vertical light beams and center glow.
 * Creates a high-tech sci-fi atmosphere.
 */
export const GridGlowBackground: React.FC<GridGlowBackgroundProps> = ({
  theme,
  gridSize = 48,
  showBeams = true,
  beamCount = 3,
}) => {
  const frame = useCurrentFrame();
  const pulse = usePulseAnimation({ frequency: 0.2, intensity: 0.5 });

  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      {/* Grid lines */}
      <svg
        width="100%"
        height="100%"
        style={{ position: 'absolute' }}
      >
        {/* Horizontal lines */}
        {Array.from({ length: Math.ceil(1080 / gridSize) + 1 }, (_, i) => (
          <line
            key={`h-${i}`}
            x1={0}
            y1={i * gridSize}
            x2={1920}
            y2={i * gridSize}
            stroke="rgba(255,255,255,0.03)"
            strokeWidth={1}
          />
        ))}
        {/* Vertical lines */}
        {Array.from({ length: Math.ceil(1920 / gridSize) + 1 }, (_, i) => (
          <line
            key={`v-${i}`}
            x1={i * gridSize}
            y1={0}
            x2={i * gridSize}
            y2={1080}
            stroke="rgba(255,255,255,0.03)"
            strokeWidth={1}
          />
        ))}
      </svg>

      {/* Center radial glow */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          width: 800,
          height: 800,
          transform: 'translate(-50%, -50%)',
          background: `radial-gradient(ellipse, ${theme.accentCyan ?? '#00D4FF'}15 0%, transparent 70%)`,
          opacity: pulse.opacity * 0.5,
          pointerEvents: 'none',
        }}
      />

      {/* Vertical light beams */}
      {showBeams && Array.from({ length: beamCount }, (_, i) => {
        const baseX = 300 + i * 600;
        const animOffset = Math.sin((frame + i * 50) * 0.01) * 30;

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: baseX + animOffset,
              width: 2,
              background: `linear-gradient(
                to bottom,
                transparent 0%,
                ${theme.beamColor ?? 'rgba(0,212,255,0.08)'} 30%,
                ${theme.beamColor ?? 'rgba(0,212,255,0.12)'} 50%,
                ${theme.beamColor ?? 'rgba(0,212,255,0.08)'} 70%,
                transparent 100%
              )`,
              boxShadow: `0 0 ${40 * pulse.opacity}px ${theme.beamColor ?? 'rgba(0,212,255,0.1)'}`,
            }}
          />
        );
      })}

      {/* Subtle vignette */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.4) 100%)',
          pointerEvents: 'none',
        }}
      />
    </AbsoluteFill>
  );
};
