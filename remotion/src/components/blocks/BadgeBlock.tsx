import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { useBlockEntry } from './useBlockEntry';

interface Props {
  block: Extract<Block, { type: 'badge' | 'tag' }>;
  theme: ThemePalette;
  staggerOffset?: number;
}

const VARIANT_COLOR: Record<string, { bg: string; fg: string; border: string }> = {
  orange:  { bg: 'rgba(255,107,53,0.15)',  fg: '#FF6B35', border: 'rgba(255,107,53,0.4)' },
  cyan:    { bg: 'rgba(0,212,255,0.15)',   fg: '#00D4FF', border: 'rgba(0,212,255,0.4)' },
  green:   { bg: 'rgba(46,213,115,0.15)',  fg: '#2ED573', border: 'rgba(46,213,115,0.4)' },
  red:     { bg: 'rgba(255,71,87,0.15)',   fg: '#FF4757', border: 'rgba(255,71,87,0.4)' },
  neutral: { bg: 'rgba(255,255,255,0.08)', fg: '#FFFFFF', border: 'rgba(255,255,255,0.18)' },
};

/**
 * Small status pill. Used for tags, "loading" indicators, run buttons.
 * Pulls colors from the theme if available, else uses VARIANT_COLOR.
 */
export const BadgeBlock: React.FC<Props> = ({ block, theme, staggerOffset = 0 }) => {
  const variant = block.variant ?? 'neutral';
  const { opacity, transform } = useBlockEntry(block.animation, staggerOffset);

  // Prefer theme color when available, fall back to hardcoded palette.
  const fallback = VARIANT_COLOR[variant] ?? VARIANT_COLOR.neutral;
  const themeColor = variant === 'orange' ? theme.accentOrange
                   : variant === 'cyan'   ? theme.accentCyan
                   : variant === 'red'    ? theme.accentRed
                   : variant === 'green'  ? theme.accentGreen
                   : null;
  const fg = themeColor ?? fallback.fg;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: block.type === 'tag' ? '4px 10px' : '6px 14px',
        borderRadius: 999,
        background: fallback.bg,
        border: `1px solid ${fallback.border}`,
        color: fg,
        fontFamily: FONT_FAMILY,
        fontSize: block.type === 'tag' ? 14 : 16,
        fontWeight: FONT_WEIGHT.medium,
        opacity,
        transform,
        whiteSpace: 'nowrap',
      }}
    >
      {block.icon && <span style={{ fontSize: '0.95em' }}>{block.icon}</span>}
      <span>{block.text}</span>
    </span>
  );
};
