import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { useBlockEntry } from './useBlockEntry';

interface Props {
  block: Extract<Block, { type: 'heading' }>;
  theme: ThemePalette;
  staggerOffset?: number;
}

const SIZE_BY_LEVEL = { 1: 84, 2: 56, 3: 36 } as const;

/**
 * Large heading. Used for scene titles and section labels. Supports three sizes
 * via `level` (1=largest, 3=smallest).
 */
export const HeadingBlock: React.FC<Props> = ({ block, theme, staggerOffset = 0 }) => {
  const level = block.level ?? 1;
  const { opacity, transform } = useBlockEntry(block.animation, staggerOffset);
  const fontSize = SIZE_BY_LEVEL[level];

  return (
    <div
      style={{
        fontFamily: FONT_FAMILY,
        fontSize,
        fontWeight: FONT_WEIGHT.bold,
        color: theme.text,
        lineHeight: 1.15,
        letterSpacing: level === 1 ? 2 : 0,
        opacity,
        transform,
        margin: 0,
      }}
    >
      {block.text}
    </div>
  );
};
