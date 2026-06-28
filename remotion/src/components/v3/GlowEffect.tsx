import React from 'react';
import { usePulseAnimation } from '../hooks/usePulseAnimation';

export interface GlowEffectProps {
  color: string;
  intensity?: number;
  children: React.ReactNode;
  pulse?: boolean;
  style?: React.CSSProperties;
}

/**
 * Wrapper component that adds a glow effect to its children.
 * Can pulse for attention-grabbing effect.
 */
export const GlowEffect: React.FC<GlowEffectProps> = ({
  color,
  intensity = 0.6,
  children,
  pulse = true,
  style,
}) => {
  const pulseAnim = usePulseAnimation({
    intensity: pulse ? 0.8 : 0,
    minOpacity: 0.4,
    maxOpacity: 1,
  });

  const glowIntensity = pulse
    ? pulseAnim.glowIntensity * intensity
    : intensity;

  return (
    <div
      style={{
        position: 'relative',
        display: 'block',
        ...style,
      }}
    >
      {/* Glow layer */}
      <div
        style={{
          position: 'absolute',
          top: -8,
          left: -8,
          right: -8,
          bottom: -8,
          background: color,
          filter: `blur(${12 + glowIntensity * 20}px)`,
          opacity: 0.15 + glowIntensity * 0.25,
          borderRadius: 'inherit',
          pointerEvents: 'none',
        }}
      />
      {/* Content layer */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        {children}
      </div>
    </div>
  );
};
