import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';
import { useBlockEntry } from './useBlockEntry';

interface Props {
  block: Extract<Block, { type: 'connector' }>;
  theme: ThemePalette;
}

/**
 * SVG-based decorative connector lines. Renders an SVG that occupies its
 * parent (use inside a relatively positioned container). Supports:
 * - dashed_curve: a dashed S-curve from top-left to bottom-right
 * - arrow: a horizontal arrow with arrowhead
 * - line: a simple horizontal line
 * - dashed_horizontal: a dashed horizontal line
 *
 * Note: connector positions are stylized — the layout scenes are responsible
 * for placing connectors between named anchors. This block draws a generic
 * decorative connector for visual richness in escape-hatch block trees.
 */
export const ConnectorBlock: React.FC<Props> = ({ block, theme }) => {
  const { opacity, transform } = useBlockEntry(undefined, 0);
  const stroke = theme.accentOrange ?? theme.accent;

  return (
    <div
      style={{
        width: '100%',
        height: 60,
        opacity,
        transform,
        pointerEvents: 'none',
      }}
    >
      <svg width="100%" height="60" viewBox="0 0 600 60" preserveAspectRatio="none">
        {block.variant === 'dashed_curve' && (
          <path
            d="M 0 30 C 200 0, 400 60, 600 30"
            stroke={stroke}
            strokeWidth="2"
            strokeDasharray="6 6"
            fill="none"
            opacity="0.7"
          />
        )}
        {block.variant === 'arrow' && (
          <>
            <line
              x1="0" y1="30" x2="580" y2="30"
              stroke={stroke}
              strokeWidth="2"
              strokeDasharray="6 6"
              opacity="0.7"
            />
            <polygon
              points="580,30 565,22 565,38"
              fill={stroke}
              opacity="0.8"
            />
          </>
        )}
        {block.variant === 'line' && (
          <line
            x1="0" y1="30" x2="600" y2="30"
            stroke={stroke}
            strokeWidth="2"
            opacity="0.7"
          />
        )}
        {block.variant === 'dashed_horizontal' && (
          <line
            x1="0" y1="30" x2="600" y2="30"
            stroke={stroke}
            strokeWidth="2"
            strokeDasharray="6 6"
            opacity="0.7"
          />
        )}
      </svg>
    </div>
  );
};
