import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';

interface Props {
  block: Extract<Block, { type: 'divider' }>;
  theme: ThemePalette;
}

/** Thin horizontal divider. Height defaults to 1px. */
export const DividerBlock: React.FC<Props> = ({ block }) => {
  const height = block.height ?? 1;
  return (
    <div
      style={{
        width: '100%',
        height,
        background: 'rgba(255,255,255,0.08)',
      }}
    />
  );
};
