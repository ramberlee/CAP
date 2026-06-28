import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { useBlockEntry } from './useBlockEntry';

interface Props {
  block: Extract<Block, { type: 'numbered_list' }>;
  theme: ThemePalette;
  staggerOffset?: number;
}

/**
 * Numbered list with optional "num" prefix and "suffix" tag. Items can have
 * a small delay-staggered entry animation via the parent block's animation.
 */
export const NumberedListBlock: React.FC<Props> = ({ block, theme, staggerOffset = 0 }) => {
  const { opacity, transform } = useBlockEntry(block.animation, staggerOffset);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        opacity,
        transform,
      }}
    >
      {block.items.map((item, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '10px 14px',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 10,
          }}
        >
          {item.num && (
            <span
              style={{
                fontFamily: FONT_FAMILY,
                fontSize: 16,
                fontWeight: FONT_WEIGHT.bold,
                color: theme.accentCyan ?? theme.accent,
                minWidth: 36,
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {item.num}
            </span>
          )}
          <span
            style={{
              flex: 1,
              fontFamily: FONT_FAMILY,
              fontSize: 18,
              color: theme.text,
              lineHeight: 1.4,
            }}
          >
            {item.text}
          </span>
          {item.suffix && (
            <span
              style={{
                fontFamily: FONT_FAMILY,
                fontSize: 14,
                color: theme.textSecondary,
                padding: '2px 10px',
                background: 'rgba(255,255,255,0.06)',
                borderRadius: 6,
              }}
            >
              {item.suffix}
            </span>
          )}
        </div>
      ))}
    </div>
  );
};
