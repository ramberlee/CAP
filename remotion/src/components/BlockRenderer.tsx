import React from 'react';
import { Block } from '../types';
import { ThemePalette } from '../themes';
import { BlockDispatch } from './dispatchBlock';

interface BlockRendererProps {
  blocks: Block[];
  theme: ThemePalette;
  /** Stagger offset (seconds) — used when container block applies staggered entry to its children. */
  staggerOffset?: number;
}

/**
 * Central dispatcher that walks a Block[] tree and renders each block with the
 * appropriate component. Container blocks (grid, column, row) propagate a
 * stagger offset to their children automatically.
 *
 * Per-block dispatch is in `./dispatchBlock` to avoid circular imports
 * (block components like CardBlock may render their own body via BlockRenderer).
 */
export const BlockRenderer: React.FC<BlockRendererProps> = ({
  blocks,
  theme,
  staggerOffset = 0,
}) => {
  return (
    <>
      {blocks.map((block, idx) => (
        <BlockDispatch
          key={idx}
          block={block}
          theme={theme}
          staggerOffset={staggerOffset}
          indexInParent={idx}
        />
      ))}
    </>
  );
};
