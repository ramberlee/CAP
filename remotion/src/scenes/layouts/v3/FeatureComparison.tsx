import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Scene } from '../../../types';
import { ThemePalette } from '../../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../../styles/typography';
import { ParticleBackground } from '../../../themes/v3/ParticleBackground';
import { GridGlowBackground } from '../../../themes/v3/GridGlowBackground';
import { EnglishLabel } from '../_shared';
import { GlassyPanel } from '../../../components/v3/GlassyPanel';
import { ChapterBadge } from '../../../components/v3/ChapterBadge';
import { useStaggeredAnimation } from '../../../components/hooks/useStaggeredAnimation';
import { Subtitle } from '../../../components/Subtitle';

/**
 * FeatureComparison - Side-by-side feature matrix with checkmarks/crosses.
 * Good for before/after, pros/cons, product comparison.
 */
export const FeatureComparison: React.FC<{ scene: Scene; theme: ThemePalette }> = ({
  scene,
  theme,
}) => {
  const frame = useCurrentFrame();
  const content = scene.featureComparison ?? {
    title: scene.title ?? '',
    leftTitle: '',
    rightTitle: '',
    features: [],
  };

  const features = content.features ?? [];
  const rowAnims = useStaggeredAnimation({ itemCount: features.length, staggerDelay: 4, startFrame: 15 });

  const chapterMatch = content.chapterBadge?.match(/^(\d+)\s*(.*)$/);
  const chapterNum = chapterMatch?.[1];
  const chapterTitle = chapterMatch?.[2];

  return (
    <AbsoluteFill style={{ fontFamily: FONT_FAMILY, color: theme.text }}>
      <ParticleBackground theme={theme} particleCount={40} />
      <GridGlowBackground theme={theme} showBeams={false} />

      <ChapterBadge chapterNum={chapterNum} chapterTitle={chapterTitle} theme={theme} showDecorDots />
      <EnglishLabel text={content.englishLabel ?? scene.englishLabel} theme={theme} />

      {/* Title */}
      <div
        style={{
          position: 'absolute',
          top: 140,
          left: 0,
          right: 0,
          textAlign: 'center',
          opacity: Math.min(Math.max((frame - 5) / 15, 0), 1),
        }}
      >
        <h1 style={{ margin: 0, fontSize: 48, fontWeight: FONT_WEIGHT.bold as number, letterSpacing: 2 }}>
          {content.title}
        </h1>
      </div>

      {/* Comparison table */}
      <div
        style={{
          position: 'absolute',
          top: 240,
          left: 120,
          right: 120,
          bottom: 120,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header row */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1.5fr 1fr 1fr',
            gap: 16,
            marginBottom: 16,
            opacity: Math.min(Math.max((frame - 10) / 12, 0), 1),
          }}
        >
          <div /> {/* empty corner */}
          <GlassyPanel theme={theme} padding={14} borderRadius={12} accent="orange" glow={false} style={{ textAlign: 'center' }}>
            <span style={{ fontSize: 18, fontWeight: FONT_WEIGHT.bold as number, color: theme.accentOrange ?? '#FF6B35' }}>
              {content.leftTitle}
            </span>
          </GlassyPanel>
          <GlassyPanel theme={theme} padding={14} borderRadius={12} accent="cyan" glow={false} style={{ textAlign: 'center' }}>
            <span style={{ fontSize: 18, fontWeight: FONT_WEIGHT.bold as number, color: theme.accentCyan ?? '#00D4FF' }}>
              {content.rightTitle}
            </span>
          </GlassyPanel>
        </div>

        {/* Feature rows */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
          {features.map((feat, i) => {
            const anim = rowAnims[i] ?? { opacity: 0, transformY: 20 };

            return (
              <div
                key={i}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1.5fr 1fr 1fr',
                  gap: 16,
                  opacity: anim.opacity,
                  transform: `translateY(${anim.transformY}px)`,
                }}
              >
                {/* Feature name */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '12px 16px',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.06)',
                    borderRadius: 10,
                    fontSize: 16,
                    fontWeight: FONT_WEIGHT.medium as number,
                  }}
                >
                  {feat.name}
                </div>
                {/* Left value */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '12px 16px',
                    background: feat.left ? 'rgba(255,107,53,0.06)' : 'rgba(255,255,255,0.02)',
                    border: `1px solid ${feat.left ? 'rgba(255,107,53,0.15)' : 'rgba(255,255,255,0.04)'}`,
                    borderRadius: 10,
                    fontSize: 15,
                    color: feat.left ? theme.text : theme.textSecondary,
                    textAlign: 'center',
                  }}
                >
                  {feat.left ?? '—'}
                </div>
                {/* Right value */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '12px 16px',
                    background: feat.right ? 'rgba(0,212,255,0.06)' : 'rgba(255,255,255,0.02)',
                    border: `1px solid ${feat.right ? 'rgba(0,212,255,0.15)' : 'rgba(255,255,255,0.04)'}`,
                    borderRadius: 10,
                    fontSize: 15,
                    color: feat.right ? theme.text : theme.textSecondary,
                    textAlign: 'center',
                  }}
                >
                  {feat.right ?? '—'}
                </div>
              </div>
            );
          })}
        </div>
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
