import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';
import { useBlockEntry } from './useBlockEntry';

interface Props {
  block: Extract<Block, { type: 'grid' }>;
  theme: ThemePalette;
  staggerOffset?: number;
  children: React.ReactNode;
}

/**
 * Multi-column grid. Uses CSS grid with equal-width columns. The block's
 * `stagger` setting (from its animation) propagates to children via the parent.
 */
export const GridBlock: React.FC<Props> = ({ block, theme, staggerOffset = 0, children }) => {
  const { opacity, transform } = useBlockEntry(block.animation, staggerOffset);
  const gap = block.gap ?? 32;

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${block.columns}, minmax(0, 1fr))`,
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
