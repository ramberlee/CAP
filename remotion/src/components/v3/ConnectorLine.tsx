import React, { useMemo } from 'react';
import { useCurrentFrame } from 'remotion';
import { useFlowAnimation } from '../hooks/useFlowAnimation';

export type ConnectorVariant = 'straight' | 'curve' | 'arrow' | 'dashed';

export interface ConnectorLineProps {
  from: { x: number; y: number };
  to: { x: number; y: number };
  variant?: ConnectorVariant;
  color?: string;
  width?: number;
  flowing?: boolean;
  dotColor?: string;
  dotCount?: number;
  dotSize?: number;
}

/**
 * Connecting line between UI elements with optional flowing dots animation.
 * Supports straight lines, curves, arrows, and dashed styles.
 */
export const ConnectorLine: React.FC<ConnectorLineProps> = ({
  from,
  to,
  variant = 'straight',
  color = 'rgba(255,107,53,0.5)',
  width = 2,
  flowing = false,
  dotColor,
  dotCount = 3,
  dotSize = 4,
}) => {
  const frame = useCurrentFrame();

  // Calculate path length for animation
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const pathLength = Math.sqrt(dx * dx + dy * dy);

  const flow = useFlowAnimation({
    pathLength,
    speed: 4,
    dotCount,
    dotSpacing: pathLength / dotCount,
  });

  // Generate path SVG
  const pathD = useMemo(() => {
    if (variant === 'curve') {
      // Create a gentle curve
      const midX = (from.x + to.x) / 2;
      const midY = (from.y + to.y) / 2 - 30;
      return `M ${from.x} ${from.y} Q ${midX} ${midY} ${to.x} ${to.y}`;
    }
    return `M ${from.x} ${from.y} L ${to.x} ${to.y}`;
  }, [from, to, variant]);

  // Get point along path (simplified for straight lines)
  const getPointAtLength = (t: number) => ({
    x: from.x + (to.x - from.x) * t,
    y: from.y + (to.y - from.y) * t,
  });

  const strokeDasharray = variant === 'dashed' ? '6 6' : undefined;

  return (
    <svg
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        overflow: 'visible',
      }}
    >
      {/* Main line */}
      <path
        d={pathD}
        stroke={color}
        strokeWidth={width}
        fill="none"
        strokeDasharray={strokeDasharray}
        strokeDashoffset={flowing ? flow.dashOffset : undefined}
        strokeLinecap="round"
      />

      {/* Flowing dots */}
      {flowing && flow.dots.map((dot, i) => {
        const point = getPointAtLength(dot.position);
        return (
          <circle
            key={i}
            cx={point.x}
            cy={point.y}
            r={dotSize}
            fill={dotColor ?? color}
            opacity={dot.opacity}
            style={{
              filter: `drop-shadow(0 0 ${dotSize}px ${dotColor ?? color})`,
            }}
          />
        );
      })}

      {/* Arrow head */}
      {variant === 'arrow' && (
        <polygon
          points={`${to.x},${to.y} ${to.x - 10},${to.y - 5} ${to.x - 10},${to.y + 5}`}
          fill={color}
        />
      )}
    </svg>
  );
};

/**
 * Curved connector with fixed control point for consistent styling.
 */
export const CurvedConnector: React.FC<{
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
  curveHeight?: number;
  color?: string;
  dashed?: boolean;
}> = ({
  fromX,
  fromY,
  toX,
  toY,
  curveHeight = -40,
  color = 'rgba(255,107,53,0.5)',
  dashed = true,
}) => {
  const midX = (fromX + toX) / 2;
  const midY = (fromY + toY) / 2 + curveHeight;

  return (
    <svg
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        overflow: 'visible',
      }}
    >
      <path
        d={`M ${fromX} ${fromY} Q ${midX} ${midY} ${toX} ${toY}`}
        stroke={color}
        strokeWidth={2}
        fill="none"
        strokeDasharray={dashed ? '8 8' : undefined}
        strokeLinecap="round"
      />
    </svg>
  );
};
