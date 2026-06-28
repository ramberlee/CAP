import React from 'react';
import { useCurrentFrame } from 'remotion';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { ProgressBarSegment } from '../../types';

export interface ProgressBarProps {
  segments: ProgressBarSegment[];
  total?: number;
  animated?: boolean;
  showLabels?: boolean;
  height?: number;
  borderRadius?: number;
}

/**
 * Segmented progress bar with optional animation.
 * Supports multiple colored segments and value labels.
 */
export const ProgressBar: React.FC<ProgressBarProps> = ({
  segments,
  total,
  animated = true,
  showLabels = true,
  height = 36,
  borderRadius = 8,
}) => {
  const frame = useCurrentFrame();

  // Calculate actual total if not provided
  const actualTotal = total ?? segments.reduce((sum, s) => sum + s.value, 0);

  // Animation progress (0-1)
  const animProgress = animated
    ? Math.min(1, Math.max(0, (frame - 8) / 20))
    : 1;

  return (
    <div
      style={{
        display: 'flex',
        height,
        borderRadius,
        overflow: 'hidden',
        border: '1px solid rgba(255,255,255,0.10)',
      }}
    >
      {segments.map((seg, i) => {
        const widthPercent = actualTotal > 0
          ? (seg.value / actualTotal) * 100 * animProgress
          : 0;

        return (
          <div
            key={i}
            style={{
              width: `${widthPercent}%`,
              backgroundColor: seg.color,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minWidth: showLabels && seg.label ? 40 : 0,
              transition: 'width 0.3s ease',
            }}
          >
            {showLabels && seg.label && widthPercent > 10 && (
              <span
                style={{
                  fontFamily: FONT_FAMILY,
                  fontWeight: FONT_WEIGHT.bold as number,
                  fontSize: 14,
                  color: '#FFFFFF',
                  textShadow: '0 1px 2px rgba(0,0,0,0.4)',
                  whiteSpace: 'nowrap',
                }}
              >
                {seg.label}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};

/**
 * Simple single-value progress bar (non-segmented).
 */
export const SimpleProgressBar: React.FC<{
  value: number;
  max?: number;
  color?: string;
  height?: number;
  showPercent?: boolean;
}> = ({
  value,
  max = 100,
  color = '#FF6B35',
  height = 8,
  showPercent = false,
}) => {
  const frame = useCurrentFrame();
  const animProgress = Math.min(1, Math.max(0, (frame - 5) / 15));
  const percent = (value / max) * animProgress * 100;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <div
        style={{
          flex: 1,
          height,
          borderRadius: height / 2,
          backgroundColor: 'rgba(255,255,255,0.10)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${percent}%`,
            height: '100%',
            backgroundColor: color,
            borderRadius: height / 2,
            transition: 'width 0.3s ease',
          }}
        />
      </div>
      {showPercent && (
        <span
          style={{
            fontFamily: FONT_FAMILY,
            fontWeight: FONT_WEIGHT.medium as number,
            fontSize: 12,
            color: 'rgba(255,255,255,0.7)',
            minWidth: 40,
            textAlign: 'right',
          }}
        >
          {Math.round(percent)}%
        </span>
      )}
    </div>
  );
};
