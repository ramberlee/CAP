import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { useBlockEntry } from './useBlockEntry';

interface Props {
  block: Extract<Block, { type: 'file_tree' }>;
  theme: ThemePalette;
  staggerOffset?: number;
}

/**
 * File-tree view. The root is shown as a folder entry at the top, then each
 * file in `files` is rendered below with optional `badge` text on the right
 * (used for the "load 100%" pill in the doc_tree sample).
 */
export const FileTreeBlock: React.FC<Props> = ({ block, theme, staggerOffset = 0 }) => {
  const { opacity, transform } = useBlockEntry(block.animation, staggerOffset);

  return (
    <div
      style={{
        background: theme.glassSurface ?? 'rgba(255,255,255,0.04)',
        border: `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.1)'}`,
        borderRadius: 12,
        padding: 16,
        fontFamily: FONT_FAMILY,
        opacity,
        transform,
      }}
    >
      {/* Root entry */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 10px',
          background: 'rgba(255,107,53,0.10)',
          border: '1px solid rgba(255,107,53,0.25)',
          borderRadius: 8,
          marginBottom: 12,
        }}
      >
        <span style={{ fontSize: 14 }}>📄</span>
        <span
          style={{
            flex: 1,
            fontSize: 15,
            fontWeight: FONT_WEIGHT.semibold,
            color: theme.text,
            letterSpacing: 0.3,
          }}
        >
          {block.root}
        </span>
      </div>

      {/* File list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {block.files.map((file, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '6px 10px 6px 20px',
              borderRadius: 6,
              color: theme.textSecondary,
              fontSize: 14,
            }}
          >
            <span style={{ fontSize: 13, opacity: 0.8 }}>{file.icon ?? '·'}</span>
            <span style={{ flex: 1, color: theme.text }}>{file.name}</span>
            {file.badge && (
              <span
                style={{
                  fontSize: 11,
                  color: theme.accentCyan ?? theme.accent,
                  background: 'rgba(0,212,255,0.10)',
                  border: '1px solid rgba(0,212,255,0.25)',
                  padding: '2px 8px',
                  borderRadius: 999,
                  fontWeight: FONT_WEIGHT.medium,
                }}
              >
                {file.badge}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
