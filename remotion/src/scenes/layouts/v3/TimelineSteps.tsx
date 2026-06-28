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

const COLOR_MAP: Record<string, string> = {
  orange: '#FF6B35',
  cyan: '#00D4FF',
  green: '#2ED573',
  red: '#FF4757',
};

/**
 * TimelineSteps - Vertical timeline with numbered nodes and connecting lines.
 * Good for step-by-step processes, tutorials, roadmaps.
 */
export const TimelineSteps: React.FC<{ scene: Scene; theme: ThemePalette }> = ({
  scene,
  theme,
}) => {
  const frame = useCurrentFrame();
  const content = scene.timelineSteps ?? {
    title: scene.title ?? '',
    items: [],
  };

  const items = content.items ?? [];
  const itemAnims = useStaggeredAnimation({ itemCount: items.length, staggerDelay: 8, startFrame: 15 });

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
          left: 80,
          right: 80,
          opacity: Math.min(Math.max((frame - 5) / 15, 0), 1),
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: 48,
            fontWeight: FONT_WEIGHT.bold as number,
            letterSpacing: 2,
          }}
        >
          {content.title}
        </h1>
      </div>

      {/* Timeline */}
      <div
        style={{
          position: 'absolute',
          top: 240,
          left: 120,
          right: 120,
          bottom: 120,
          display: 'flex',
          flexDirection: 'column',
          gap: 0,
        }}
      >
        {items.map((item, i) => {
          const anim = itemAnims[i] ?? { opacity: 0, transformY: 20 };
          const color = COLOR_MAP[item.color ?? 'cyan'] ?? theme.accentCyan ?? '#00D4FF';
          const isLast = i === items.length - 1;

          return (
            <div key={i} style={{ display: 'flex', gap: 24, opacity: anim.opacity, transform: `translateY(${anim.transformY}px)` }}>
              {/* Left: number node + connecting line */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 48, flexShrink: 0 }}>
                {/* Node */}
                <GlassyPanel theme={theme} padding={0} borderRadius={24} style={{ width: 48, height: 48, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontSize: 18, fontWeight: FONT_WEIGHT.bold as number, color }}>
                    {item.num}
                  </span>
                </GlassyPanel>
                {/* Connecting line */}
                {!isLast && (
                  <div
                    style={{
                      width: 2,
                      flex: 1,
                      minHeight: 20,
                      background: `linear-gradient(to bottom, ${color}60, ${color}20)`,
                      marginTop: 4,
                    }}
                  />
                )}
              </div>

              {/* Right: content */}
              <div style={{ flex: 1, paddingBottom: isLast ? 0 : 24 }}>
                <div style={{ fontSize: 22, fontWeight: FONT_WEIGHT.semibold as number, marginBottom: 4 }}>
                  {item.title}
                </div>
                {item.description && (
                  <div style={{ fontSize: 16, color: theme.textSecondary, lineHeight: 1.6 }}>
                    {item.description}
                  </div>
                )}
              </div>
            </div>
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
