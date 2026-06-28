import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ThemePalette } from '../../themes';
import { useFlowAnimation } from '../../components/hooks/useFlowAnimation';

export interface DataFlowCurvesProps {
  theme: ThemePalette;
  curveCount?: number;
}

/**
 * Flowing colored curves across the background.
 * Represents data flow and creates dynamic tech atmosphere.
 */
export const DataFlowCurves: React.FC<DataFlowCurvesProps> = ({
  theme,
  curveCount = 4,
}) => {
  const frame = useCurrentFrame();

  const curveConfigs = [
    { color: theme.accentOrange ?? '#FF6B35', startY: 200, amplitude: 80, frequency: 0.003 },
    { color: theme.accentCyan ?? '#00D4FF', startY: 400, amplitude: 100, frequency: 0.004 },
    { color: theme.accentYellow ?? '#FFA502', startY: 600, amplitude: 60, frequency: 0.0025 },
    { color: theme.accentGreen ?? '#2ED573', startY: 800, amplitude: 90, frequency: 0.0035 },
  ].slice(0, curveCount);

  const flowAnims = curveConfigs.map((_, i) =>
    useFlowAnimation({
      pathLength: 2000,
      speed: 3 + i,
      dotCount: 4,
      dotSpacing: 500,
    })
  );

  // Generate SVG path for a wavy curve
  const generateCurvePath = (config: typeof curveConfigs[0], index: number): string => {
    const { startY, amplitude, frequency } = config;
    const offset = (frame * (1 + index * 0.3)) % 200;

    let path = `M ${-50} ${startY + Math.sin(frame * frequency) * amplitude}`;

    for (let x = 0; x <= 2000; x += 50) {
      const y = startY + Math.sin((x + offset) * frequency * Math.PI) * amplitude;
      path += ` L ${x} ${y}`;
    }

    return path;
  };

  return (
    <AbsoluteFill style={{ pointerEvents: 'none', overflow: 'hidden' }}>
      <svg width="100%" height="100%" style={{ position: 'absolute' }}>
        {curveConfigs.map((config, i) => {
          const path = generateCurvePath(config, i);
          const flow = flowAnims[i];

          return (
            <g key={i}>
              {/* Curve line */}
              <path
                d={path}
                stroke={config.color}
                strokeWidth={2}
                strokeOpacity={0.15}
                fill="none"
                strokeDasharray="8 16"
                strokeDashoffset={flow.dashOffset}
              />

              {/* Flowing dots */}
              {flow.dots.map((dot, j) => {
                if (!dot.visible) return null;
                // Simple position approximation along path
                const x = dot.position * 2000 - 50;
                const y = config.startY +
                  Math.sin((x + ((frame * (1 + i * 0.3)) % 200)) * config.frequency * Math.PI) * config.amplitude;

                return (
                  <circle
                    key={j}
                    cx={x}
                    cy={y}
                    r={4 + j}
                    fill={config.color}
                    opacity={dot.opacity * 0.6}
                    style={{
                      filter: `drop-shadow(0 0 8px ${config.color})`,
                    }}
                  />
                );
              })}
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
