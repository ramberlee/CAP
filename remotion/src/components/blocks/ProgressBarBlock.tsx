import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { useBlockEntry } from './useBlockEntry';

interface Props {
  block: Extract<Block, { type: 'progress_bar' }>;
  theme: ThemePalette;
  staggerOffset?: number;
}

/**
 * Segmented horizontal probability / progress bar with inline labels.
 * Used in the split_compare layout (sample 8) to show e.g. +70% / 30% splits.
 */
export const ProgressBarBlock: React.FC<Props> = ({ block, theme, staggerOffset = 0 }) => {
  const { opacity, transform } = useBlockEntry(block.animation, staggerOffset);
  const total = block.total ?? block.segments.reduce((s, x) => s + x.value, 0) ?? 100;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        opacity,
        transform,
      }}
    >
      <div
        style={{
          display: 'flex',
          width: '100%',
          height: 36,
          borderRadius: 8,
          overflow: 'hidden',
          border: '1px solid rgba(255,255,255,0.10)',
        }}
      >
        {block.segments.map((seg, i) => {
          const widthPct = (seg.value / total) * 100;
          return (
            <div
              key={i}
              style={{
                width: `${widthPct}%`,
                background: seg.color,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: FONT_FAMILY,
                fontSize: 14,
                fontWeight: FONT_WEIGHT.bold,
                color: '#FFFFFF',
                textShadow: '0 1px 2px rgba(0,0,0,0.4)',
              }}
            >
              {seg.label}
            </div>
          );
        })}
      </div>

      {block.legend && (
        <div
          style={{
            fontFamily: FONT_FAMILY,
            fontSize: 16,
            color: theme.textSecondary,
            textAlign: 'center',
            lineHeight: 1.5,
          }}
        >
          {block.legend}
        </div>
      )}
    </div>
  );
};
