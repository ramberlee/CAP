import React from 'react';
import { AbsoluteFill } from 'remotion';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { ThemePalette } from '../../themes';
import { useDelayedAnimation } from '../hooks/useStaggeredAnimation';

export interface ChapterBadgeProps {
  chapterNum?: string;
  chapterTitle?: string;
  theme: ThemePalette;
  position?: 'top-left' | 'top-right';
  showDecorDots?: boolean;
}

/**
 * Chapter identifier badge shown in the corner.
 * Includes decorative window-control-style dots.
 */
export const ChapterBadge: React.FC<ChapterBadgeProps> = ({
  chapterNum,
  chapterTitle,
  theme,
  position = 'top-left',
  showDecorDots = true,
}) => {
  const anim = useDelayedAnimation({ delay: 0, duration: 15 });

  const positionStyles: React.CSSProperties = position === 'top-left'
    ? { top: 60, left: 80 }
    : { top: 60, right: 80 };

  return (
    <AbsoluteFill
      style={{
        pointerEvents: 'none',
        opacity: anim.opacity,
        transform: `translateY(${anim.transformY * 0.5}px)`,
      }}
    >
      <div
        style={{
          position: 'absolute',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          fontFamily: FONT_FAMILY,
          ...positionStyles,
        }}
      >
        {/* Window-control style decorative dots (close/min/max) */}
        {showDecorDots && (
          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#FF5F56' }} />
            <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#FFBD2E' }} />
            <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#27C93F' }} />
          </div>
        )}

        {/* Chapter text */}
        {(chapterNum || chapterTitle) && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 16px',
              background: theme.glassSurface ?? 'rgba(255,255,255,0.05)',
              border: `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.12)'}`,
              borderRadius: 8,
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)',
            }}
          >
            {chapterNum && (
              <span
                style={{
                  fontSize: 16,
                  fontWeight: FONT_WEIGHT.bold as number,
                  color: theme.accentOrange ?? '#FF6B35',
                }}
              >
                {chapterNum}
              </span>
            )}
            {chapterNum && chapterTitle && (
              <span style={{ color: theme.textSecondary, fontSize: 14 }}>•</span>
            )}
            {chapterTitle && (
              <span
                style={{
                  fontSize: 14,
                  fontWeight: FONT_WEIGHT.medium as number,
                  color: theme.text,
                }}
              >
                {chapterTitle}
              </span>
            )}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
