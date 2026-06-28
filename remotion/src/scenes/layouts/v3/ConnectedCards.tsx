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
import { CurvedConnector } from '../../../components/v3/ConnectorLine';
import { useStaggeredAnimation } from '../../../components/hooks/useStaggeredAnimation';
import { Subtitle } from '../../../components/Subtitle';

/**
 * ConnectedCards - 3 horizontal cards with curved connecting lines (sample screenshot 7).
 * Shows sequential steps or categories with numbered lists inside each card.
 */
export const ConnectedCards: React.FC<{ scene: Scene; theme: ThemePalette }> = ({
  scene,
  theme,
}) => {
  const frame = useCurrentFrame();
  const content = scene.connectedCards ?? {
    title: scene.title ?? '',
    cards: [],
  };

  const cards = content.cards ?? [];
  const cardAnims = useStaggeredAnimation({ itemCount: cards.length, staggerDelay: 6, startFrame: 10 });

  // Parse chapter badge
  const chapterMatch = content.chapterBadge?.match(/^(\d+)\s*(.*)$/);
  const chapterNum = chapterMatch?.[1];
  const chapterTitle = chapterMatch?.[2];

  // Card positions for connectors
  const cardWidth = (1920 - 160 - 48) / 3; // 1920 - padding - gap
  const cardTop = 320;
  const cardHeight = 400;
  const getCardCenterX = (index: number) => 80 + cardWidth / 2 + index * (cardWidth + 24);

  const accentColors: Array<'orange' | 'cyan' | 'green'> = ['orange', 'cyan', 'green'];

  return (
    <AbsoluteFill style={{ fontFamily: FONT_FAMILY, color: theme.text }}>
      {/* v3 Background effects */}
      <ParticleBackground theme={theme} particleCount={50} />
      <GridGlowBackground theme={theme} />

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
          top: 150,
          left: 80,
          right: 80,
          textAlign: 'center',
          opacity: Math.min(Math.max((frame - 5) / 15, 0), 1),
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: 52,
            fontWeight: FONT_WEIGHT.bold as number,
            letterSpacing: 3,
            color: theme.text,
          }}
        >
          {content.title}
        </h1>
      </div>

      {/* Cards Container */}
      <div
        style={{
          position: 'absolute',
          top: cardTop,
          left: 80,
          right: 80,
          display: 'grid',
          gridTemplateColumns: `repeat(${cards.length}, 1fr)`,
          gap: 24,
        }}
      >
        {cards.map((card, i) => {
          const accent = card.accentColor ?? accentColors[i % 3];
          const anim = cardAnims[i] ?? { opacity: 0, transformY: 20 };
          const isHighlighted = card.state === 'highlighted';
          const isDimmed = card.state === 'dimmed';

          return (
            <GlassyPanel
              key={i}
              theme={theme}
              padding={24}
              borderRadius={16}
              accent={accent}
              glow={isHighlighted}
              style={{
                opacity: isDimmed ? 0.4 : anim.opacity,
                transform: `translateY(${anim.transformY}px)`,
              }}
            >
              {/* Card Header */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  marginBottom: 20,
                  paddingBottom: 16,
                  borderBottom: '1px solid rgba(255,255,255,0.08)',
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: FONT_WEIGHT.bold as number,
                    color: accent === 'orange' ? theme.accentOrange : accent === 'cyan' ? theme.accentCyan : theme.accentGreen,
                    fontVariantNumeric: 'tabular-nums',
                  }}
                >
                  {card.num}
                </span>
                <span
                  style={{
                    fontSize: 20,
                    fontWeight: FONT_WEIGHT.semibold as number,
                    color: theme.text,
                  }}
                >
                  {card.title}
                </span>
              </div>

              {/* Card Items */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {card.items.map((item, j) => (
                  <div
                    key={j}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: '10px 14px',
                      background: j === 0 && isHighlighted ? 'rgba(255,107,53,0.12)' : 'rgba(255,255,255,0.03)',
                      border: `1px solid ${j === 0 && isHighlighted ? 'rgba(255,107,53,0.35)' : 'rgba(255,255,255,0.06)'}`,
                      borderRadius: 10,
                      opacity: Math.min(Math.max((frame - 25 - i * 5 - j * 3) / 10, 0), 1),
                    }}
                  >
                    <span style={{ fontSize: 14, color: theme.text }}>
                      {item}
                    </span>
                  </div>
                ))}
              </div>
            </GlassyPanel>
          );
        })}
      </div>

      {/* Curved Connectors Between Cards */}
      {cards.length > 1 && cards.slice(0, -1).map((_, i) => {
        const fromX = getCardCenterX(i);
        const toX = getCardCenterX(i + 1);
        const connectorY = cardTop - 20;
        const showConnector = frame > 30 + i * 8;

        if (!showConnector) return null;

        return (
          <CurvedConnector
            key={i}
            fromX={fromX}
            fromY={connectorY}
            toX={toX}
            toY={connectorY}
            curveHeight={-30}
            color={theme.accentOrange ?? '#FF6B35'}
            dashed
          />
        );
      })}

      {/* Center Text Below Cards */}
      {content.centerText && (
        <div
          style={{
            position: 'absolute',
            top: cardTop + cardHeight + 30,
            left: 0,
            right: 0,
            textAlign: 'center',
            opacity: Math.min(Math.max((frame - 45) / 15, 0), 1),
          }}
        >
          <span
            style={{
              fontSize: 18,
              color: theme.accentOrange ?? '#FF6B35',
              fontWeight: FONT_WEIGHT.medium as number,
              letterSpacing: 1.5,
            }}
          >
            {content.centerText}
          </span>
        </div>
      )}

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
