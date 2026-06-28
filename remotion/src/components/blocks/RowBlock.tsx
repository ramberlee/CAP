import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';
import { useBlockEntry } from './useBlockEntry';

interface Props {
  block: Extract<Block, { type: 'row' }>;
  theme: ThemePalette;
  staggerOffset?: number;
  children: React.ReactNode;
}

const JUSTIFY: Record<string, string> = {
  left: 'flex-start',
  center: 'center',
  right: 'flex-end',
  between: 'space-between',
};

/**
 * Horizontal row. Use `align` to control horizontal distribution.
 */
export const RowBlock: React.FC<Props> = ({ block, theme, staggerOffset = 0, children }) => {
  const { opacity, transform } = useBlockEntry(block.animation, staggerOffset);
  const gap = block.gap ?? 12;
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: JUSTIFY[block.align ?? 'left'],
        gap,
        width: '100%',
        opacity,
        transform,
      }}
    >
      {children}
    </div>
  );
};
