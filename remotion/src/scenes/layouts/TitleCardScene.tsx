import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { Scene, ThemePalette, LayoutType, BadgeSpec } from '../../types';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { SceneFrame } from './_shared';

const BADGE_COLORS: Record<string, { bg: string; fg: string; border: string }> = {
  orange:  { bg: 'rgba(255,107,53,0.18)', fg: '#FF6B35', border: 'rgba(255,107,53,0.45)' },
  cyan:    { bg: 'rgba(0,212,255,0.18)',  fg: '#00D4FF', border: 'rgba(0,212,255,0.45)' },
  green:   { bg: 'rgba(46,213,115,0.18)', fg: '#2ED573', border: 'rgba(46,213,115,0.45)' },
  red:     { bg: 'rgba(255,71,87,0.18)',  fg: '#FF4757', border: 'rgba(255,71,87,0.45)' },
  neutral: { bg: 'rgba(255,255,255,0.10)', fg: '#FFFFFF', border: 'rgba(255,255,255,0.20)' },
};

/**
 * Render an optional badge pill below the title.
 * Animated with a scale-in + fade effect that's staggered after the title.
 */
const BadgePill: React.FC<{ badge: BadgeSpec; frame: number }> = ({
  badge,
  frame,
}) => {
  const badgeProgress = Math.min(Math.max((frame / 24 - 0.7) / 0.4, 0), 1);
  const badgeEase = 1 - Math.pow(1 - badgeProgress, 3);
  const badgeScale = 0.85 + badgeEase * 0.15;

  const variant = badge.variant ?? 'neutral';
  const colors = BADGE_COLORS[variant] ?? BADGE_COLORS.neutral;

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        padding: '10px 24px',
        borderRadius: 999,
        background: colors.bg,
        border: `1.5px solid ${colors.border}`,
        fontFamily: FONT_FAMILY,
        fontSize: 22,
        fontWeight: FONT_WEIGHT.medium,
        color: colors.fg,
        letterSpacing: 1.5,
        opacity: badgeEase,
        transform: `scale(${badgeScale})`,
        marginTop: 28,
      }}
    >
      {badge.icon && <span style={{ fontSize: '1em' }}>{badge.icon}</span>}
      <span>{badge.text}</span>
    </div>
  );
};

/**
 * TitleCard — generic cover / section title with optional badge.
 *
 * When a badge is present, the layout shifts to:
 *   title (big) → badge pill → subtitle (small)
 * to fill the screen and create visual hierarchy.
 *
 * When there's no badge, keeps the classic centered title + subtitle.
 */
export const TitleCardScene: React.FC<{ scene: Scene; theme: ThemePalette }> = ({ scene, theme }) => {
  const frame = useCurrentFrame();

  const content = scene.titleCard ?? {
    title: scene.title ?? '',
    subtitle: scene.subtitle,
    badge: (scene as any).badge,
    englishLabel: scene.englishLabel,
    sceneSubtitle: scene.sceneSubtitle,
  };

  // Also check scene-level badge (LLM may put it outside titleCard)
  const badge = content.badge ?? (scene as any).badge;

  // Title entry scale-in
  const titleProgress = Math.min(Math.max((frame / 24 - 0.1) / 0.6, 0), 1);
  const titleEase = 1 - Math.pow(1 - titleProgress, 3);
  const titleScale = 0.85 + titleEase * 0.15;
  const titleOpacity = titleEase;

  const subProgress = Math.min(Math.max((frame / 24 - 0.5) / 0.5, 0), 1);
  const subEase = 1 - Math.pow(1 - subProgress, 3);

  // Decorative accent line (animates width from 0 to 140px)
  const lineProgress = Math.min(Math.max((frame / 24 - 0.4) / 0.4, 0), 1);
  const lineWidth = interpolate(lineProgress, [0, 1], [0, 140]);

  return (
    <SceneFrame theme={theme} englishLabel={content.englishLabel}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 80px',
          textAlign: 'center',
        }}
      >
        {content.title && (
          <div
            style={{
              fontSize: badge ? 80 : 96,
              fontWeight: FONT_WEIGHT.bold,
              letterSpacing: 4,
              lineHeight: 1.15,
              color: theme.text,
              opacity: titleOpacity,
              transform: `scale(${titleScale})`,
              maxWidth: 1200,
            }}
          >
            {content.title}
          </div>
        )}

        {/* Accent gradient line between title and badge/subtitle */}
        <div
          style={{
            height: 3,
            width: lineWidth,
            background: `linear-gradient(90deg, transparent, ${theme.accent ?? theme.accentOrange ?? '#FF6B35'}, transparent)`,
            margin: badge ? '24px auto 0' : '28px auto',
            borderRadius: 2,
          }}
        />

        {/* Badge pill (if present) */}
        {badge && <BadgePill badge={badge} frame={frame} />}

        {content.subtitle && (
          <div
            style={{
              marginTop: badge ? 20 : 24,
              fontSize: badge ? 24 : 28,
              fontWeight: FONT_WEIGHT.regular,
              color: theme.textSecondary,
              letterSpacing: badge ? 3 : 6,
              opacity: subEase,
            }}
          >
            {content.subtitle}
          </div>
        )}
      </div>
    </SceneFrame>
  );
};

(TitleCardScene as any).layoutType = LayoutType.TitleCard;
