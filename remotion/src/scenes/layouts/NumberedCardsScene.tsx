import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Scene, ThemePalette, LayoutType } from '../../types';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { SceneFrame } from './_shared';

/**
 * NumberedCards — 3 numbered cards with dashed connector curves between them
 * (sample 7: "重复任务"). Includes a centered callout text and dashed lines
 * linking the three cards.
 */
export const NumberedCardsScene: React.FC<{ scene: Scene; theme: ThemePalette }> = ({ scene, theme }) => {
  const frame = useCurrentFrame();

  const content = scene.numberedCards ?? {
    title: scene.title ?? '',
    englishLabel: scene.englishLabel,
    cards: (scene.items ?? []).map((t) => ({ name: t, items: [] })),
    centerText: '',
    sceneSubtitle: scene.sceneSubtitle,
  };

  const titleProgress = Math.min(Math.max((frame / 24 - 0.1) / 0.5, 0), 1);
  const titleEase = 1 - Math.pow(1 - titleProgress, 3);

  return (
    <SceneFrame theme={theme} englishLabel={content.englishLabel}>
      {/* Title (top-left) */}
      <div
        style={{
          position: 'absolute',
          top: 96,
          left: 80,
          fontFamily: FONT_FAMILY,
          color: theme.text,
          opacity: titleEase,
        }}
      >
        <div
          style={{
            fontSize: 60,
            fontWeight: FONT_WEIGHT.bold,
            letterSpacing: 3,
          }}
        >
          {content.title}
        </div>
      </div>

      {/* Dashed connectors between cards (SVG behind cards) */}
      <svg
        style={{
          position: 'absolute',
          top: 340,
          left: 0,
          right: 0,
          width: '100%',
          height: 100,
          pointerEvents: 'none',
          opacity: Math.min(Math.max((frame - 30) / 25, 0), 1),
        }}
        viewBox="0 0 1920 100"
        preserveAspectRatio="none"
      >
        <path
          d="M 380 0 C 600 100, 1320 100, 1540 0"
          stroke={theme.accentOrange ?? '#FF6B35'}
          strokeWidth="2"
          strokeDasharray="6 6"
          fill="none"
          opacity="0.7"
        />
      </svg>

      {/* 3-column card grid */}
      <div
        style={{
          position: 'absolute',
          top: 300,
          left: 80,
          right: 80,
          display: 'grid',
          gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
          gap: 40,
        }}
      >
        {content.cards.map((card, idx) => {
          const cardStart = 18 + idx * 8;
          const cardProgress = Math.min(Math.max((frame - cardStart) / 18, 0), 1);
          const cardEase = 1 - Math.pow(1 - cardProgress, 3);

          return (
            <div
              key={idx}
              style={{
                background: theme.glassSurface ?? 'rgba(255,255,255,0.05)',
                border: `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.10)'}`,
                borderRadius: 18,
                padding: 28,
                backdropFilter: 'blur(12px)',
                WebkitBackdropFilter: 'blur(12px)',
                fontFamily: FONT_FAMILY,
                color: theme.text,
                opacity: cardEase,
                transform: `translateY(${(1 - cardEase) * 24}px)`,
              }}
            >
              {/* Card header */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginBottom: 18,
                  paddingBottom: 12,
                  borderBottom: '1px solid rgba(255,255,255,0.08)',
                }}
              >
                <span
                  style={{
                    color: theme.accentCyan ?? '#00D4FF',
                    fontSize: 14,
                    opacity: 0.7,
                  }}
                >
                  ●
                </span>
                <span
                  style={{
                    fontSize: 18,
                    fontWeight: FONT_WEIGHT.bold,
                    color: theme.text,
                    letterSpacing: 1,
                  }}
                >
                  {card.name}
                </span>
              </div>

              {/* Numbered items */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {card.items.map((item, i) => {
                  const itemStart = cardStart + 18 + i * 6;
                  const itemEase = Math.min(Math.max((frame - itemStart) / 14, 0), 1);
                  return (
                    <div
                      key={i}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        fontSize: 16,
                        color: theme.text,
                        opacity: itemEase,
                        transform: `translateX(${(1 - itemEase) * 12}px)`,
                      }}
                    >
                      <span
                        style={{
                          minWidth: 28,
                          fontWeight: FONT_WEIGHT.bold,
                          color: theme.accentCyan ?? '#00D4FF',
                          fontVariantNumeric: 'tabular-nums',
                          fontSize: 15,
                        }}
                      >
                        {item.num || String(i + 1).padStart(2, '0')}
                      </span>
                      <span style={{ flex: 1 }}>{item.text}</span>
                      {item.suffix && (
                        <span
                          style={{
                            fontSize: 13,
                            color: theme.textSecondary,
                            padding: '2px 8px',
                            background: 'rgba(255,255,255,0.05)',
                            borderRadius: 6,
                          }}
                        >
                          {item.suffix}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Center callout text */}
      {content.centerText && (
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: 110,
            textAlign: 'center',
            fontFamily: FONT_FAMILY,
            fontSize: 22,
            color: theme.text,
            fontWeight: FONT_WEIGHT.medium,
            letterSpacing: 1.5,
            opacity: Math.min(Math.max((frame - 50) / 20, 0), 1),
          }}
        >
          {content.centerText}
        </div>
      )}
    </SceneFrame>
  );
};

(NumberedCardsScene as any).layoutType = LayoutType.NumberedCards;
