import React from 'react';
import { usePulseAnimation } from '../hooks/usePulseAnimation';

export type DotState = 'idle' | 'active' | 'completed' | 'error';

export interface StateDotProps {
  state: DotState;
  size?: number;
}

const stateStyles: Record<DotState, { color: string; pulse?: boolean; opacity?: number }> = {
  idle: { color: 'rgba(255,255,255,0.3)', opacity: 0.3 },
  active: { color: '#FF6B35', pulse: true },
  completed: { color: '#2ED573' },
  error: { color: '#FF4757', pulse: true },
};

const DEFAULT_STYLE = stateStyles.idle;

/**
 * Small circular state indicator used in lists and panels.
 * Shows idle/active/completed/error states with optional pulse animation.
 */
export const StateDot: React.FC<StateDotProps> = ({
  state,
  size = 8,
}) => {
  const style = stateStyles[state] ?? DEFAULT_STYLE;
  const pulse = usePulseAnimation({ intensity: style.pulse ? 0.8 : 0 });

  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        backgroundColor: style.color,
        opacity: style.pulse ? pulse.opacity : (style.opacity ?? 1),
        boxShadow: style.pulse
          ? `0 0 ${size * pulse.glowIntensity}px ${style.color}80`
          : 'none',
        flexShrink: 0,
      }}
    />
  );
};
