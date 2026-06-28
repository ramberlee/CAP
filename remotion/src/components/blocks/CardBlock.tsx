import React from 'react';
import { Block } from '../../types';
import { ThemePalette } from '../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { useBlockEntry } from './useBlockEntry';
import { BlockRenderer } from '../BlockRenderer';
import { BadgeBlock } from './BadgeBlock';
import { isDarkGlassTheme } from '../../themes';

interface Props {
  block: Extract<Block, { type: 'card' }>;
  theme: ThemePalette;
  staggerOffset?: number;
}

/**
 * Glass / outlined / filled card. Renders an optional title, a header badge,
 * a body region containing nested blocks, and an optional footer.
 *
 * This is the workhorse container for the dark_glass visual style.
 */
export const CardBlock: React.FC<Props> = ({ block, theme, staggerOffset = 0 }) => {
  const { opacity, transform } = useBlockEntry(block.animation, staggerOffset);
  const useGlass = isDarkGlassTheme(theme) && (block.variant === 'glass' || !block.variant);

  const styles: React.CSSProperties = useGlass
    ? {
        background: theme.glassSurface,
        border: `1px solid ${theme.glassBorder}`,
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderRadius: 16,
        boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
        padding: 24,
      }
    : block.variant === 'outlined'
    ? {
        background: 'transparent',
        border: `1px solid ${theme.surfaceBorder}`,
        borderRadius: 16,
        padding: 24,
      }
    : {
        background: theme.surface,
        border: `1px solid ${theme.surfaceBorder}`,
        borderRadius: 16,
        padding: 24,
      };

  return (
    <div style={{ ...styles, opacity, transform }}>
      {(block.title || block.headerBadge) && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 16,
            gap: 12,
          }}
        >
          {block.title && (
            <div
              style={{
                fontFamily: FONT_FAMILY,
                fontSize: 22,
                fontWeight: FONT_WEIGHT.bold,
                color: theme.text,
                letterSpacing: 0.5,
              }}
            >
              {block.title}
            </div>
          )}
          {block.headerBadge && (
            <BadgeBlock
              block={{ type: 'badge', text: block.headerBadge.text, variant: block.headerBadge.variant, icon: block.headerBadge.icon }}
              theme={theme}
            />
          )}
        </div>
      )}

      {block.subtitle && (
        <div
          style={{
            fontFamily: FONT_FAMILY,
            fontSize: 15,
            color: theme.textSecondary,
            marginBottom: 14,
            lineHeight: 1.4,
          }}
        >
          {block.subtitle}
        </div>
      )}

      <BlockRenderer blocks={block.body} theme={theme} />

      {block.footer && block.footer.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <BlockRenderer blocks={block.footer} theme={theme} />
        </div>
      )}
    </div>
  );
};
