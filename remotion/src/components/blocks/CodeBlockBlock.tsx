import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { useBlockEntry } from './useBlockEntry';

interface Props {
  block: Extract<Block, { type: 'code_block' }>;
  theme: ThemePalette;
  staggerOffset?: number;
}

/**
 * Monospace code block. Optional `title` renders as a small label above the code.
 * Used in the doc_tree layout for the right-hand code panel.
 */
export const CodeBlockBlock: React.FC<Props> = ({ block, theme, staggerOffset = 0 }) => {
  const { opacity, transform } = useBlockEntry(block.animation, staggerOffset);

  return (
    <div
      style={{
        background: 'rgba(0,0,0,0.45)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 12,
        padding: 16,
        fontFamily: '"Cascadia Code", "JetBrains Mono", Consolas, Monaco, monospace',
        fontSize: 14,
        lineHeight: 1.6,
        color: theme.text,
        opacity,
        transform,
      }}
    >
      {block.title && (
        <div
          style={{
            fontFamily: FONT_FAMILY,
            fontSize: 13,
            fontWeight: FONT_WEIGHT.semibold,
            color: theme.textSecondary,
            marginBottom: 10,
            letterSpacing: 0.5,
          }}
        >
          {block.title}
        </div>
      )}
      <pre
        style={{
          margin: 0,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          color: '#A8B3CF',
        }}
      >
        {block.code}
      </pre>
    </div>
  );
};
