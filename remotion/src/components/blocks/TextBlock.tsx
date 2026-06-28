import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';
import { FONT_FAMILY } from '../../styles/typography';
import { useBlockEntry } from './useBlockEntry';

interface Props {
  block: Extract<Block, { type: 'text' }>;
  theme: ThemePalette;
  staggerOffset?: number;
}

const SIZE_MAP = { sm: 18, md: 24, lg: 32, xl: 44 } as const;

/**
 * Generic text paragraph. Defaults to md size.
 */
export const TextBlock: React.FC<Props> = ({ block, theme, staggerOffset = 0 }) => {
  const { opacity, transform } = useBlockEntry(block.animation, staggerOffset);
  const fontSize = SIZE_MAP[block.size ?? 'md'];

  return (
    <div
      style={{
        fontFamily: FONT_FAMILY,
        fontSize,
        color: block.color ?? theme.textSecondary,
        lineHeight: 1.5,
        opacity,
        transform,
      }}
    >
      {block.text}
    </div>
  );
};
