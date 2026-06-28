import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Scene } from '../../../types';
import { ThemePalette } from '../../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../../styles/typography';
import { ParticleBackground } from '../../../themes/v3/ParticleBackground';
import { GridGlowBackground } from '../../../themes/v3/GridGlowBackground';
import { EnglishLabel } from '../_shared';
import { GlassyPanel } from '../../../components/v3/GlassyPanel';
import { GlowEffect } from '../../../components/v3/GlowEffect';
import { ChapterBadge } from '../../../components/v3/ChapterBadge';
import { Subtitle } from '../../../components/Subtitle';

/**
 * QuoteCard - Large centered quote with author attribution.
 * Good for expert opinions, impactful statements, testimonials.
 */
export const QuoteCard: React.FC<{ scene: Scene; theme: ThemePalette }> = ({
  scene,
  theme,
}) => {
  const frame = useCurrentFrame();
  const content = scene.quoteCard ?? {
    quote: scene.quote ?? scene.title ?? '',
    author: scene.quoteAuthor,
  };

  const chapterMatch = content.chapterBadge?.match(/^(\d+)\s*(.*)$/);
  const chapterNum = chapterMatch?.[1];
  const chapterTitle = chapterMatch?.[2];

  const quoteOpacity = Math.min(Math.max((frame - 10) / 20, 0), 1);
  const authorOpacity = Math.min(Math.max((frame - 30) / 15, 0), 1);

  return (
    <AbsoluteFill style={{ fontFamily: FONT_FAMILY, color: theme.text }}>
      <ParticleBackground theme={theme} particleCount={50} />
      <GridGlowBackground theme={theme} showBeams={false} />

      <ChapterBadge chapterNum={chapterNum} chapterTitle={chapterTitle} theme={theme} showDecorDots />
      <EnglishLabel text={content.englishLabel ?? scene.englishLabel} theme={theme} />

      {/* Centered Quote */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 160px',
        }}
      >
        <GlowEffect color={theme.accentOrange ?? '#FF6B35'} intensity={0.4} pulse>
          <GlassyPanel
            theme={theme}
            padding={48}
            borderRadius={24}
            accent="orange"
            style={{ maxWidth: 1200, textAlign: 'center' }}
          >
            {/* Decorative quote mark */}
            <div
              style={{
                fontSize: 80,
                fontWeight: FONT_WEIGHT.extrabold as number,
                color: theme.accentOrange ?? '#FF6B35',
                opacity: 0.3,
                lineHeight: 0.6,
                marginBottom: 16,
              }}
            >
              {"“"}
            </div>

            {/* Quote text */}
            <div
              style={{
                fontSize: 36,
                fontWeight: FONT_WEIGHT.bold as number,
                lineHeight: 1.5,
                color: theme.text,
                opacity: quoteOpacity,
                letterSpacing: 1,
              }}
            >
              {content.quote}
            </div>

            {/* Author */}
            {(content.author || content.source) && (
              <div
                style={{
                  marginTop: 32,
                  opacity: authorOpacity,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 12,
                }}
              >
                {content.author && (
                  <span
                    style={{
                      fontSize: 18,
                      fontWeight: FONT_WEIGHT.medium as number,
                      color: theme.accentOrange ?? '#FF6B35',
                    }}
                  >
                    {content.author}
                  </span>
                )}
                {content.author && content.source && (
                  <span style={{ color: theme.textSecondary }}>|</span>
                )}
                {content.source && (
                  <span style={{ fontSize: 16, color: theme.textSecondary }}>
                    {content.source}
                  </span>
                )}
              </div>
            )}
          </GlassyPanel>
        </GlowEffect>
      </div>

      <Subtitle
        text={content.sceneSubtitle ?? scene.sceneSubtitle}
        theme={theme}
        sceneDurationInFrames={Math.round((scene.duration ?? 5) * 30)}
        glassBackground
      />
    </AbsoluteFill>
  );
};
