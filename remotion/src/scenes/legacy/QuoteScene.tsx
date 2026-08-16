import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { AnimatedText } from '../../components/AnimatedText';
import { FONT_FAMILY, FONT_SIZE, FONT_WEIGHT } from '../../styles/typography';
import { SceneComponentProps } from '../types';
import { ParticleBackground } from '../../themes/v3/ParticleBackground';
import { GridGlowBackground } from '../../themes/v3/GridGlowBackground';
import { EnglishLabel } from '../layouts/_shared';
import { ChapterBadge } from '../../components/v3/ChapterBadge';
import { GlassyPanel } from '../../components/v3/GlassyPanel';
import { Subtitle } from '../../components/Subtitle';

export const QuoteScene: React.FC<SceneComponentProps> = ({ scene, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const quote = scene.quote || '';
  const author = scene.quoteAuthor || '';

  // Parse chapter badge
  const chapterMatch = (scene.chapterBadge ?? '').match(/^(\d+)\s*(.*)$/);
  const chapterNum = chapterMatch?.[1];
  const chapterTitle = chapterMatch?.[2];

  return (
    <AbsoluteFill style={{ fontFamily: FONT_FAMILY, color: theme.text }}>
      {/* v3 Background effects */}
      <ParticleBackground theme={theme} particleCount={35} />
      <GridGlowBackground theme={theme} showBeams={false} />

      {/* Navigation */}
      <ChapterBadge
        chapterNum={chapterNum}
        chapterTitle={chapterTitle}
        theme={theme}
        showDecorDots
      />
      <EnglishLabel text={scene.englishLabel} theme={theme} />

      {/* Quote content */}
      <AbsoluteFill style={{ justifyContent: 'center', padding: '0 140px' }}>
        <GlassyPanel theme={theme} padding={40} borderRadius={24} style={{ maxWidth: 1500 }}>
          <div style={{ paddingLeft: 28, borderLeft: `4px solid ${theme.accentOrange ?? theme.accent ?? '#FF6B35'}` }}>
            {/* Large quotation mark */}
            <div style={{
              fontSize: 80,
              color: theme.accentOrange ?? theme.accent ?? '#FF6B35',
              opacity: 0.3,
              lineHeight: 1,
              marginBottom: -20,
            }}>
              "
            </div>

            {quote && (
              <AnimatedText
                text={quote}
                animation="slideUp"
                delay={0.2}
                duration={0.5}
                fontSize={32}
                fontWeight={FONT_WEIGHT.medium}
                color={theme.text}
                lineHeight={1.6}
                style={{ display: 'block', marginBottom: 24 }}
              />
            )}

            {author && (
              <AnimatedText
                text={`— ${author}`}
                animation="fade"
                delay={0.6}
                duration={0.4}
                fontSize={22}
                fontWeight={FONT_WEIGHT.regular}
                color={theme.textSecondary}
                style={{ display: 'block', textAlign: 'right', marginTop: 12 }}
              />
            )}
          </div>
        </GlassyPanel>
      </AbsoluteFill>

      {/* Bottom Subtitle */}
      <Subtitle
        text={scene.sceneSubtitle}
        theme={theme}
        sceneDurationInFrames={Math.round((scene.duration ?? 5) * fps)}
        glassBackground
      />
    </AbsoluteFill>
  );
};
