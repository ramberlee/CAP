import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { useBlockEntry } from './useBlockEntry';

interface Props {
  block: Extract<Block, { type: 'callout' }>;
  theme: ThemePalette;
  staggerOffset?: number;
}

/**
 * Highlighted text callout. Three variants:
 * - inline: small inline pill
 * - center: large centered text (used in sample 7 for "当 AI 面对一类重复出现的任务时")
 * - banner: full-width banner with icon
 */
export const CalloutBlock: React.FC<Props> = ({ block, theme, staggerOffset = 0 }) => {
  const { opacity, transform } = useBlockEntry(block.animation, staggerOffset);
  const variant = block.variant ?? 'inline';

  if (variant === 'center') {
    return (
      <div
        style={{
          textAlign: 'center',
          fontFamily: FONT_FAMILY,
          fontSize: 26,
          fontWeight: FONT_WEIGHT.semibold,
          color: theme.text,
          letterSpacing: 1,
          lineHeight: 1.4,
          padding: '12px 20px',
          opacity,
          transform,
        }}
      >
        {block.icon && <span style={{ marginRight: 8 }}>{block.icon}</span>}
        {block.text}
      </div>
    );
  }

  if (variant === 'banner') {
    return (
      <div
        style={{
          background: 'linear-gradient(90deg, rgba(255,107,53,0.15), rgba(0,212,255,0.10))',
          border: '1px solid rgba(255,107,53,0.3)',
          borderRadius: 12,
          padding: '16px 24px',
          fontFamily: FONT_FAMILY,
          fontSize: 22,
          fontWeight: FONT_WEIGHT.semibold,
          color: theme.text,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          opacity,
          transform,
        }}
      >
        {block.icon && <span style={{ fontSize: 24 }}>{block.icon}</span>}
        <span>{block.text}</span>
      </div>
    );
  }

  // inline
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '4px 12px',
        background: 'rgba(255,107,53,0.12)',
        border: '1px solid rgba(255,107,53,0.3)',
        borderRadius: 6,
        color: theme.accentOrange ?? theme.accent,
        fontFamily: FONT_FAMILY,
        fontSize: 15,
        fontWeight: FONT_WEIGHT.medium,
        opacity,
        transform,
      }}
    >
      {block.icon && <span>{block.icon}</span>}
      <span>{block.text}</span>
    </span>
  );
};
