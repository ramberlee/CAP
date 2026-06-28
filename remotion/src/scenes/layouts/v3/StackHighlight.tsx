import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Scene } from '../../../types';
import { ThemePalette } from '../../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../../styles/typography';
import { ParticleBackground } from '../../../themes/v3/ParticleBackground';
import { GridGlowBackground } from '../../../themes/v3/GridGlowBackground';
import { DataFlowCurves } from '../../../themes/v3/DataFlowCurves';
import { EnglishLabel } from '../_shared';
import { GlassyPanel } from '../../../components/v3/GlassyPanel';
import { StatusBadge } from '../../../components/v3/StatusBadge';
import { StateDot } from '../../../components/v3/StateDot';
import { ChapterBadge } from '../../../components/v3/ChapterBadge';
import { CurvedConnector } from '../../../components/v3/ConnectorLine';
import { GlowEffect } from '../../../components/v3/GlowEffect';
import { useStaggeredAnimation } from '../../../components/hooks/useStaggeredAnimation';
import { Subtitle } from '../../../components/Subtitle';

/**
 * StackHighlight - Left vertical list with right highlighted card.
 * (Sample screenshot 10 - System capability stack).
 * Dashed curved lines connect list items to the right card.
 * Current highlighted item has orange background, others are dimmed.
 */
export const StackHighlight: React.FC<{ scene: Scene; theme: ThemePalette }> = ({
  scene,
  theme,
}) => {
  const frame = useCurrentFrame();
  const content = scene.stackHighlight ?? {
    title: scene.title ?? '',
    leftItems: [],
    rightCard: { title: '', body: '' },
  };

  const leftItems = content.leftItems ?? [];
  const itemAnims = useStaggeredAnimation({ itemCount: leftItems.length, staggerDelay: 4, startFrame: 8 });

  // Parse chapter badge
  const chapterMatch = content.chapterBadge?.match(/^(\d+)\s*(.*)$/);
  const chapterNum = chapterMatch?.[1];
  const chapterTitle = chapterMatch?.[2];

  // Find the active (highlighted) item index
  const activeIndex = leftItems.findIndex((item) => item.highlighted);

  return (
    <AbsoluteFill style={{ fontFamily: FONT_FAMILY, color: theme.text }}>
      {/* v3 Background effects */}
      <ParticleBackground theme={theme} particleCount={50} />
      <GridGlowBackground theme={theme} />
      <DataFlowCurves theme={theme} curveCount={2} />

      {/* Navigation */}
      <ChapterBadge
        chapterNum={chapterNum}
        chapterTitle={chapterTitle}
        theme={theme}
        showDecorDots
      />
      <EnglishLabel text={content.englishLabel ?? scene.englishLabel} theme={theme} />

      {/* Main Title */}
      <div
        style={{
          position: 'absolute',
          top: 140,
          left: 80,
          opacity: Math.min(Math.max((frame - 5) / 15, 0), 1),
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: 48,
            fontWeight: FONT_WEIGHT.bold as number,
            letterSpacing: 2,
            color: theme.text,
          }}
        >
          {content.title}
        </h1>
      </div>

      {/* 2-Column Layout */}
      <div
        style={{
          position: 'absolute',
          top: 240,
          left: 80,
          right: 80,
          bottom: 120,
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 60,
        }}
      >
        {/* Left - Vertical Item List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {leftItems.map((item, i) => {
            const anim = itemAnims[i] ?? { opacity: 0, transformY: 20 };
            const isHighlighted = item.highlighted || i === activeIndex;
            const isDimmed = activeIndex >= 0 && !isHighlighted;

            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '14px 18px',
                  background: isHighlighted
                    ? 'rgba(255,107,53,0.15)'
                    : 'rgba(255,255,255,0.04)',
                  border: `1px solid ${isHighlighted
                    ? 'rgba(255,107,53,0.40)'
                    : 'rgba(255,255,255,0.08)'}`,
                  borderRadius: 12,
                  opacity: isDimmed ? 0.35 : anim.opacity,
                  transform: `translateY(${anim.transformY}px)`,
                  transition: 'all 0.2s ease',
                }}
              >
                <StateDot
                  state={item.state ?? (isHighlighted ? 'active' : 'idle')}
                  size={10}
                />
                <span
                  style={{
                    flex: 1,
                    fontSize: 16,
                    fontWeight: isHighlighted
                      ? (FONT_WEIGHT.semibold as number)
                      : (FONT_WEIGHT.regular as number),
                    color: isHighlighted ? theme.text : theme.textSecondary,
                  }}
                >
                  {item.text}
                </span>
                {item.badge && (
                  <StatusBadge
                    text={item.badge.text}
                    variant={
                      item.badge.variant === 'orange'
                        ? 'loading'
                        : item.badge.variant === 'green'
                        ? 'loaded'
                        : item.badge.variant === 'cyan'
                        ? 'one-off'
                        : 'reusable'
                    }
                    size="sm"
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Right - Highlighted Card */}
        <div
          style={{
            opacity: Math.min(Math.max((frame - 10) / 12, 0), 1),
            transform: `translateY(${Math.max(0, (15 - frame) * 0.5)}px)`,
          }}
        >
          <GlowEffect
            color={theme.accentOrange ?? '#FF6B35'}
            intensity={0.5}
            pulse
          >
            <GlassyPanel
              theme={theme}
              padding={32}
              borderRadius={20}
              accent="orange"
              glow
              style={{ height: '100%' }}
            >
              <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                {content.rightCard.subtitle && (
                  <div
                    style={{
                      fontSize: 14,
                      color: theme.textSecondary,
                      letterSpacing: 1,
                      marginBottom: 8,
                    }}
                  >
                    {content.rightCard.subtitle}
                  </div>
                )}
                <h2
                  style={{
                    margin: '0 0 16px 0',
                    fontSize: 32,
                    fontWeight: FONT_WEIGHT.bold as number,
                    color: theme.accentOrange ?? '#FF6B35',
                  }}
                >
                  {content.rightCard.title}
                </h2>
                <div
                  style={{
                    flex: 1,
                    fontSize: 16,
                    lineHeight: 1.8,
                    color: theme.text,
                  }}
                >
                  {content.rightCard.body}
                </div>
                {content.rightCard.pills && content.rightCard.pills.length > 0 && (
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: 8,
                      marginTop: 20,
                    }}
                  >
                    {content.rightCard.pills.map((pill, i) => (
                      <span
                        key={i}
                        style={{
                          padding: '6px 14px',
                          background: 'rgba(255,255,255,0.08)',
                          border: '1px solid rgba(255,255,255,0.12)',
                          borderRadius: 999,
                          fontSize: 13,
                          color: theme.textSecondary,
                        }}
                      >
                        {pill}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </GlassyPanel>
          </GlowEffect>
        </div>

        {/* Curved Connectors from left items to right card */}
        {leftItems.slice(0, 3).map((_, i) => {
          // Simple approximate positions for connector lines
          const itemY = 260 + i * 58;
          const cardCenterY = 400;

          return (
            <CurvedConnector
              key={i}
              fromX={850} // Right edge of left column
              fromY={itemY}
              toX={980} // Left edge of right card
              toY={cardCenterY}
              curveHeight={-30 + i * 15}
              color="rgba(255,107,53,0.25)"
              dashed
            />
          );
        })}
      </div>

      {/* Bottom Subtitle */}
      <Subtitle
        text={content.sceneSubtitle ?? scene.sceneSubtitle}
        theme={theme}
        sceneDurationInFrames={Math.round((scene.duration ?? 5) * 30)}
        glassBackground
      />
    </AbsoluteFill>
  );
};
