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
 * ProgressSteps - Horizontal progress bar with numbered step labels.
 * Good for workflow stages, pipeline visualization.
 */
export const ProgressSteps: React.FC<{ scene: Scene; theme: ThemePalette }> = ({
  scene,
  theme,
}) => {
  const frame = useCurrentFrame();
  const content = scene.progressSteps ?? {
    title: scene.title ?? '',
    steps: [],
  };

  const steps = content.steps ?? [];
  const stepAnims = useStaggeredAnimation({ itemCount: steps.length, staggerDelay: 6, startFrame: 15 });

  const chapterMatch = content.chapterBadge?.match(/^(\d+)\s*(.*)$/);
  const chapterNum = chapterMatch?.[1];
  const chapterTitle = chapterMatch?.[2];

  // Find active step index
  const activeIdx = steps.findIndex((s) => s.active);
  const completedCount = steps.filter((s) => s.completed).length;

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
        <h1 style={{ margin: 0, fontSize: 48, fontWeight: FONT_WEIGHT.bold as number, letterSpacing: 2 }}>
          {content.title}
        </h1>
      </div>

      {/* Steps container */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: 80,
          right: 80,
          bottom: 120,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          gap: 32,
        }}
      >
        {/* Progress bar */}
        <div
          style={{
            position: 'relative',
            height: 8,
            borderRadius: 4,
            background: 'rgba(255,255,255,0.08)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              height: '100%',
              borderRadius: 4,
              background: `linear-gradient(90deg, ${theme.accentOrange ?? '#FF6B35'}, ${theme.accentCyan ?? '#00D4FF'})`,
              width: `${steps.length > 0 ? ((completedCount + (activeIdx >= 0 ? 0.5 : 0)) / steps.length) * 100 : 0}%`,
              transition: 'width 0.5s ease',
            }}
          />
        </div>

        {/* Step nodes */}
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          {steps.map((step, i) => {
            const anim = stepAnims[i] ?? { opacity: 0, transformY: 20 };
            const isCompleted = step.completed || i < completedCount;
            const isActive = step.active || i === activeIdx;
            const nodeColor = isCompleted
              ? (theme.accentGreen ?? '#2ED573')
              : isActive
              ? (theme.accentOrange ?? '#FF6B35')
              : 'rgba(255,255,255,0.3)';

            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 12,
                  opacity: anim.opacity,
                  transform: `translateY(${anim.transformY}px)`,
                  flex: 1,
                }}
              >
                <GlassyPanel
                  theme={theme}
                  padding={0}
                  borderRadius={24}
                  glow={isActive}
                  accent={isActive ? 'orange' : undefined}
                  style={{
                    width: 52,
                    height: 52,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <span
                    style={{
                      fontSize: 20,
                      fontWeight: FONT_WEIGHT.bold as number,
                      color: nodeColor,
                    }}
                  >
                    {isCompleted ? '✓' : step.num}
                  </span>
                </GlassyPanel>
                <span
                  style={{
                    fontSize: 15,
                    fontWeight: isActive ? FONT_WEIGHT.semibold : FONT_WEIGHT.regular,
                    color: isActive ? theme.text : theme.textSecondary,
                    textAlign: 'center',
                    maxWidth: 120,
                  }}
                >
                  {step.label}
                </span>
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
