import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { AnimatedText } from '../../components/AnimatedText';
import { FONT_FAMILY, FONT_SIZE, FONT_WEIGHT } from '../../styles/typography';
import { SceneComponentProps } from '../types';
import { ParticleBackground } from '../../themes/v3/ParticleBackground';
import { GridGlowBackground } from '../../themes/v3/GridGlowBackground';
import { EnglishLabel } from '../layouts/_shared';
import { ChapterBadge } from '../../components/v3/ChapterBadge';
import { GlowEffect } from '../../components/v3/GlowEffect';
import { Subtitle } from '../../components/Subtitle';

export const HighlightScene: React.FC<SceneComponentProps> = ({ scene, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Handle highlight as either string or {text, subtext} object from LLM plans
  const rawHighlight = scene.highlight;
  let highlight = '';
  let subtext = '';
  if (typeof rawHighlight === 'string') {
    highlight = rawHighlight;
  } else if (rawHighlight && typeof rawHighlight === 'object') {
    highlight = (rawHighlight as any).text || '';
    subtext = (rawHighlight as any).subtext || '';
  }
  const highlightValue = scene.highlightValue || '';
  const body = scene.body || subtext;

  // Parse chapter badge from scene metadata if present
  const chapterMatch = (scene.chapterBadge ?? '').match(/^(\d+)\s*(.*)$/);
  const chapterNum = chapterMatch?.[1];
  const chapterTitle = chapterMatch?.[2];

  // Fade in animations
  const valueOpacity = Math.min(Math.max((frame - 10) / 15, 0), 1);
  const titleOpacity = Math.min(Math.max((frame - 25) / 15, 0), 1);
  const bodyOpacity = Math.min(Math.max((frame - 40) / 15, 0), 1);

  return (
    <AbsoluteFill style={{ fontFamily: FONT_FAMILY, color: theme.text }}>
      {/* v3 Background effects */}
      <ParticleBackground theme={theme} particleCount={40} />
      <GridGlowBackground theme={theme} showBeams={false} />

      {/* Navigation */}
      <ChapterBadge
        chapterNum={chapterNum}
        chapterTitle={chapterTitle}
        theme={theme}
        showDecorDots
      />
      <EnglishLabel text={scene.englishLabel} theme={theme} />

      {/* Centered highlight content */}
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ position: 'relative', textAlign: 'center', maxWidth: 1400 }}>
          {highlightValue && (
            <GlowEffect
              color={theme.accentOrange ?? theme.accent ?? '#FF6B35'}
              intensity={0.4}
              pulse
            >
              <div style={{ opacity: valueOpacity }}>
                <AnimatedText
                  text={highlightValue}
                  animation="slideUp"
                  delay={0}
                  duration={0.5}
                  fontSize={72}
                  fontWeight={FONT_WEIGHT.extrabold}
                  color={theme.accentOrange ?? theme.accent ?? '#FF6B35'}
                  style={{ display: 'block', lineHeight: 1.1, marginBottom: 16 }}
                />
              </div>
            </GlowEffect>
          )}

          {highlight && (
            <div style={{ opacity: titleOpacity }}>
              <AnimatedText
                text={highlight}
                animation="slideUp"
                delay={0}
                duration={0.5}
                fontSize={FONT_SIZE.title}
                fontWeight={FONT_WEIGHT.bold}
                color={theme.text}
                lineHeight={1.3}
                style={{ display: 'block' }}
              />
            </div>
          )}

          {body && (
            <div style={{ opacity: bodyOpacity, marginTop: 24 }}>
              <AnimatedText
                text={body}
                animation="fade"
                delay={0}
                duration={0.4}
                fontSize={24}
                fontWeight={FONT_WEIGHT.regular}
                color={theme.textSecondary}
                style={{ display: 'block', lineHeight: 1.6 }}
              />
            </div>
          )}
        </div>
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
