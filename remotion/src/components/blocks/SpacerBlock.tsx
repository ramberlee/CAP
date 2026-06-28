import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';

interface Props {
  block: Extract<Block, { type: 'spacer' }>;
  theme: ThemePalette;
}

/** Empty vertical spacer. Height in pixels. */
export const SpacerBlock: React.FC<Props> = ({ block }) => {
  return <div style={{ height: block.height, width: '100%' }} />;
};
