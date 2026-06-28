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
import { useStaggeredAnimation } from '../../../components/hooks/useStaggeredAnimation';
import { Subtitle } from '../../../components/Subtitle';

const COLOR_MAP: Record<string, string> = {
  orange: '#FF6B35',
  cyan: '#00D4FF',
  green: '#2ED573',
  red: '#FF4757',
};

/**
 * StatsShowcase - Large metrics/numbers with labels in a grid.
 * Good for data-driven content, KPIs, comparisons.
 */
export const StatsShowcase: React.FC<{ scene: Scene; theme: ThemePalette }> = ({
  scene,
  theme,
}) => {
  const frame = useCurrentFrame();
  const content = scene.statsShowcase ?? {
    title: scene.title ?? '',
    stats: [],
  };

  const stats = content.stats ?? [];
  const statAnims = useStaggeredAnimation({ itemCount: stats.length, staggerDelay: 6, startFrame: 12 });

  const chapterMatch = content.chapterBadge?.match(/^(\d+)\s*(.*)$/);
  const chapterNum = chapterMatch?.[1];
  const chapterTitle = chapterMatch?.[2];

  return (
    <AbsoluteFill style={{ fontFamily: FONT_FAMILY, color: theme.text }}>
      <ParticleBackground theme={theme} particleCount={45} />
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

      {/* Stats Grid */}
      <div
        style={{
          position: 'absolute',
          top: 260,
          left: 80,
          right: 80,
          bottom: 120,
          display: 'grid',
          gridTemplateColumns: `repeat(${Math.min(stats.length, 4)}, 1fr)`,
          gap: 24,
          alignItems: 'center',
        }}
      >
        {stats.map((stat, i) => {
          const anim = statAnims[i] ?? { opacity: 0, transformY: 20 };
          const color = COLOR_MAP[stat.color ?? 'cyan'] ?? theme.accentCyan ?? '#00D4FF';

          return (
            <GlowEffect key={i} color={color} intensity={0.3} pulse={false}>
              <GlassyPanel
                theme={theme}
                padding={28}
                borderRadius={16}
                style={{
                  opacity: anim.opacity,
                  transform: `translateY(${anim.transformY}px)`,
                  textAlign: 'center',
                }}
              >
                <div
                  style={{
                    fontSize: 56,
                    fontWeight: FONT_WEIGHT.extrabold as number,
                    color,
                    lineHeight: 1.1,
                    marginBottom: 12,
                    fontVariantNumeric: 'tabular-nums',
                  }}
                >
                  {stat.value}
                </div>
                <div
                  style={{
                    fontSize: 18,
                    fontWeight: FONT_WEIGHT.semibold as number,
                    color: theme.text,
                    marginBottom: 6,
                  }}
                >
                  {stat.label}
                </div>
                {stat.description && (
                  <div style={{ fontSize: 14, color: theme.textSecondary, lineHeight: 1.5 }}>
                    {stat.description}
                  </div>
                )}
              </GlassyPanel>
            </GlowEffect>
          );
        })}
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
