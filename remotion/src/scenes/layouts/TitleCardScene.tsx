import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { Scene, ThemePalette, LayoutType } from '../../types';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { SceneFrame } from './_shared';

/**
 * TitleCard — generic cover / section title.
 * Big centered title with optional subtitle. Top-right English label.
 */
export const TitleCardScene: React.FC<{ scene: Scene; theme: ThemePalette }> = ({ scene, theme }) => {
  const { durationInFrames } = useVideoConfig();
  const frame = useCurrentFrame();

  const content = scene.titleCard ?? {
    title: scene.title ?? '',
    subtitle: scene.subtitle,
    englishLabel: scene.englishLabel,
    sceneSubtitle: scene.sceneSubtitle,
  };

  // Title entry scale-in
  const titleProgress = Math.min(Math.max((frame / 24 - 0.1) / 0.6, 0), 1);
  const titleEase = 1 - Math.pow(1 - titleProgress, 3);
  const titleScale = 0.85 + titleEase * 0.15;
  const titleOpacity = titleEase;

  const subProgress = Math.min(Math.max((frame / 24 - 0.5) / 0.5, 0), 1);
  const subEase = 1 - Math.pow(1 - subProgress, 3);

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
              fontSize: 96,
              fontWeight: FONT_WEIGHT.bold,
              letterSpacing: 4,
              lineHeight: 1.1,
              color: theme.text,
              opacity: titleOpacity,
              transform: `scale(${titleScale})`,
            }}
          >
            {content.title}
          </div>
        )}

        {content.subtitle && (
          <div
            style={{
              marginTop: 24,
              fontSize: 28,
              fontWeight: FONT_WEIGHT.regular,
              color: theme.textSecondary,
              letterSpacing: 6,
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
