import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';
import { useBlockEntry } from './useBlockEntry';

interface Props {
  block: Extract<Block, { type: 'column' }>;
  theme: ThemePalette;
  staggerOffset?: number;
  children: React.ReactNode;
}

/**
 * Vertical stack. Defaults to 16px gap. Use `width` (CSS length) to constrain.
 */
export const ColumnBlock: React.FC<Props> = ({ block, theme, staggerOffset = 0, children }) => {
  const { opacity, transform } = useBlockEntry(block.animation, staggerOffset);
  // The ColumnBlock itself doesn't carry a gap; the layout scenes that use it
  // wrap children with explicit spacers. We default gap to 0 and let parent
  // styles control spacing.
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        width: block.width ?? '100%',
        opacity,
        transform,
      }}
    >
      {children}
    </div>
  );
};
