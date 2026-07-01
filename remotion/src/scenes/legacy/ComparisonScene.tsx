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

export const ComparisonScene: React.FC<SceneComponentProps> = ({ scene, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const leftTitle = scene.leftTitle || '';
  const rightTitle = scene.rightTitle || '';
  const leftItems = scene.leftItems || [];
  const rightItems = scene.rightItems || [];

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

      {/* Main content */}
      <AbsoluteFill style={{ top: 100, bottom: 80, padding: '0 80px', justifyContent: 'center' }}>
        <div style={{ display: 'flex', width: '100%', maxWidth: 1700, gap: 30, alignItems: 'stretch' }}>
          {/* Left panel */}
          <div style={{ flex: 1, opacity: Math.min(Math.max((frame - 10) / 15, 0), 1), transform: `translateX(${(1 - Math.min(Math.max((frame - 10) / 15, 0), 1)) * -20}px)` }}>
            {leftTitle && (
              <div style={{ marginBottom: 16, textAlign: 'center', letterSpacing: 2, fontSize: FONT_SIZE.subtitle, fontWeight: FONT_WEIGHT.bold, color: theme.textSecondary }}>
                {leftTitle}
              </div>
            )}
            <GlassyPanel theme={theme} padding={24} borderRadius={12} style={{ height: '100%' }}>
              {leftItems.map((item, i) => (
                <AnimatedText
                  key={i}
                  text={item}
                  animation="slideUp"
                  delay={0.25 + i * 0.12}
                  duration={0.35}
                  fontSize={FONT_SIZE.bullet}
                  fontWeight={FONT_WEIGHT.regular}
                  color={theme.textSecondary}
                  lineHeight={1.8}
                  style={{ display: 'block', paddingLeft: 12, borderLeft: `2px solid rgba(255,255,255,0.26)` }}
                />
              ))}
            </GlassyPanel>
          </div>

          {/* VS divider */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 50,
              flexShrink: 0,
            }}
          >
            <AnimatedText
              text="VS"
              animation="fade"
              delay={0.3}
              duration={0.4}
              fontSize={26}
              fontWeight={FONT_WEIGHT.extrabold}
              color={theme.accentOrange ?? theme.accent ?? '#FF6B35'}
            />
          </div>

          {/* Right panel */}
          <div style={{ flex: 1, opacity: Math.min(Math.max((frame - 15) / 15, 0), 1), transform: `translateX(${(1 - Math.min(Math.max((frame - 15) / 15, 0), 1)) * 20}px)` }}>
            {rightTitle && (
              <div style={{ marginBottom: 16, textAlign: 'center', letterSpacing: 2, fontSize: FONT_SIZE.subtitle, fontWeight: FONT_WEIGHT.bold, color: theme.accentOrange ?? theme.accent ?? '#FF6B35' }}>
                {rightTitle}
              </div>
            )}
            <GlassyPanel
              theme={theme}
              padding={24}
              borderRadius={12}
              accent="orange"
              glow
              style={{ height: '100%' }}
            >
              {rightItems.map((item, i) => (
                <AnimatedText
                  key={i}
                  text={item}
                  animation="slideUp"
                  delay={0.35 + i * 0.12}
                  duration={0.35}
                  fontSize={FONT_SIZE.bullet}
                  fontWeight={FONT_WEIGHT.medium}
                  color={theme.text}
                  lineHeight={1.8}
                  style={{ display: 'block', paddingLeft: 12, borderLeft: `2px solid ${theme.accentOrange ?? theme.accent ?? '#FF6B35'}` }}
                />
              ))}
            </GlassyPanel>
          </div>
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
