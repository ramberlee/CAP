import React, { useMemo } from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ThemePalette } from '../../themes';
import { usePulseAnimation } from '../../components/hooks/usePulseAnimation';

export interface ParticleBackgroundProps {
  theme: ThemePalette;
  particleCount?: number;
  particleColors?: string[];
  particleSize?: { min: number; max: number };
  driftSpeed?: number;
}

/**
 * Random floating particle background effect.
 * Particles drift slowly and twinkle with pulse animation.
 */
export const ParticleBackground: React.FC<ParticleBackgroundProps> = ({
  theme,
  particleCount = 60,
  particleColors,
  particleSize = { min: 2, max: 4 },
  driftSpeed = 0.3,
}) => {
  const frame = useCurrentFrame();

  const colors = particleColors ?? [
    theme.particleColor ?? 'rgba(255,255,255,0.5)',
    theme.accentOrange ?? '#FF6B35',
    theme.accentCyan ?? '#00D4FF',
  ];

  // Generate particle positions and properties (stable across renders)
  const particles = useMemo(() => {
    return Array.from({ length: particleCount }, (_, i) => {
      const seed = i * 137.5; // Golden angle for pseudo-random distribution
      const x = ((Math.sin(seed) * 0.5 + 0.5) * 1920 + 100) % 1920;
      const y = ((Math.cos(seed) * 0.5 + 0.5) * 1080 + 100) % 1080;
      const size = particleSize.min + (Math.sin(seed * 2) * 0.5 + 0.5) * (particleSize.max - particleSize.min);
      const colorIndex = Math.floor((Math.sin(seed * 3) * 0.5 + 0.5) * colors.length);
      const phase = (Math.sin(seed * 5) * 0.5 + 0.5); // Phase offset for each particle

      return { x, y, size, color: colors[colorIndex], phase };
    });
  }, [particleCount, particleSize, colors]);

  // Compute all pulse states outside the render loop (hooks must be top-level)
  const pulses = useMemo(
    () =>
      particles.map((p) => {
        const radiansPerFrame = (0.3 * 2 * Math.PI) / 30;
        const phaseOffset = p.phase * 2 * Math.PI;
        // At frame 0 this gives minOpacity; the actual animated value
        // is computed per-frame below using the same formula as usePulseAnimation.
        return { phaseOffset, radiansPerFrame };
      }),
    [particles],
  );

  return (
    <AbsoluteFill style={{ pointerEvents: 'none', overflow: 'hidden' }}>
      {particles.map((p, i) => {
        // Drift animation: slow circular movement
        const driftX = Math.sin((frame + i * 10) * 0.01 * driftSpeed) * 15;
        const driftY = Math.cos((frame + i * 10) * 0.008 * driftSpeed) * 10;

        // Compute pulse opacity inline (no hook call inside map)
        const { phaseOffset, radiansPerFrame } = pulses[i];
        const sineValue = Math.sin(frame * radiansPerFrame + phaseOffset);
        const normalized = (sineValue + 1) / 2;
        const pulseOpacity = 0.2 + normalized * 0.6; // minOpacity=0.2, maxOpacity=0.8

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: p.x + driftX,
              top: p.y + driftY,
              width: p.size,
              height: p.size,
              borderRadius: '50%',
              backgroundColor: p.color,
              opacity: pulseOpacity * 0.6,
              boxShadow: `0 0 ${p.size * 2}px ${p.color}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
