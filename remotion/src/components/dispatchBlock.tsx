import React from 'react';
import { Block } from '../types';
import { ThemePalette } from '../themes';
import { HeadingBlock } from './blocks/HeadingBlock';
import { TextBlock } from './blocks/TextBlock';
import { CardBlock } from './blocks/CardBlock';
import { GridBlock } from './blocks/GridBlock';
import { ColumnBlock } from './blocks/ColumnBlock';
import { RowBlock } from './blocks/RowBlock';
import { NumberedListBlock } from './blocks/NumberedListBlock';
import { BadgeBlock } from './blocks/BadgeBlock';
import { CodeBlockBlock } from './blocks/CodeBlockBlock';
import { FileTreeBlock } from './blocks/FileTreeBlock';
import { ProgressBarBlock } from './blocks/ProgressBarBlock';
import { CalloutBlock } from './blocks/CalloutBlock';
import { ConnectorBlock } from './blocks/ConnectorBlock';
import { DividerBlock } from './blocks/DividerBlock';
import { SpacerBlock } from './blocks/SpacerBlock';
import { BlockRenderer } from './BlockRenderer';

/**
 * Dispatch a single Block to its component. Container blocks recursively
 * re-enter via BlockRenderer, which is imported here to avoid the block
 * files importing this module (avoids circular import).
 *
 * `indexInParent` is the block's position among its siblings — used by
 * container blocks to compute a stagger delay for the child.
 */
export const BlockDispatch: React.FC<{
  block: Block;
  theme: ThemePalette;
  staggerOffset?: number;
  indexInParent?: number;
}> = ({ block, theme, staggerOffset = 0, indexInParent = 0 }) => {
  const childStagger =
    block.type === 'grid' || block.type === 'column' || block.type === 'row'
      ? (block.animation?.stagger ?? 0.1) * indexInParent
      : 0;

  switch (block.type) {
    case 'heading':
      return <HeadingBlock block={block} theme={theme} staggerOffset={staggerOffset} />;
    case 'text':
      return <TextBlock block={block} theme={theme} staggerOffset={staggerOffset} />;
    case 'card':
      return <CardBlock block={block} theme={theme} staggerOffset={staggerOffset} />;
    case 'grid':
      return (
        <GridBlock block={block} theme={theme} staggerOffset={staggerOffset}>
          <BlockRenderer
            blocks={block.items}
            theme={theme}
            staggerOffset={staggerOffset + childStagger}
          />
        </GridBlock>
      );
    case 'column':
      return (
        <ColumnBlock block={block} theme={theme} staggerOffset={staggerOffset}>
          <BlockRenderer
            blocks={block.items}
            theme={theme}
            staggerOffset={staggerOffset + childStagger}
          />
        </ColumnBlock>
      );
    case 'row':
      return (
        <RowBlock block={block} theme={theme} staggerOffset={staggerOffset}>
          <BlockRenderer
            blocks={block.items}
            theme={theme}
            staggerOffset={staggerOffset + childStagger}
          />
        </RowBlock>
      );
    case 'numbered_list':
      return <NumberedListBlock block={block} theme={theme} staggerOffset={staggerOffset} />;
    case 'badge':
    case 'tag':
      return <BadgeBlock block={block} theme={theme} staggerOffset={staggerOffset} />;
    case 'code_block':
      return <CodeBlockBlock block={block} theme={theme} staggerOffset={staggerOffset} />;
    case 'file_tree':
      return <FileTreeBlock block={block} theme={theme} staggerOffset={staggerOffset} />;
    case 'progress_bar':
      return <ProgressBarBlock block={block} theme={theme} staggerOffset={staggerOffset} />;
    case 'callout':
      return <CalloutBlock block={block} theme={theme} staggerOffset={staggerOffset} />;
    case 'connector':
      return <ConnectorBlock block={block} theme={theme} />;
    case 'divider':
      return <DividerBlock block={block} theme={theme} />;
    case 'spacer':
      return <SpacerBlock block={block} theme={theme} />;
    default:
      // subtitle, english_label are rendered at the scene level.
      return null;
  }
};
