import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Scene, ThemePalette, LayoutType } from '../../types';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { SceneFrame } from './_shared';

/**
 * CardGrid — 3-column glass card grid (sample 6: "能力包出现").
 * Title on top, 3 cards below each with title bar, header badge, item list, and run button.
 * Center callout text under the cards.
 */
export const CardGridScene: React.FC<{ scene: Scene; theme: ThemePalette }> = ({ scene, theme }) => {
  const frame = useCurrentFrame();

  const content = scene.cardGrid ?? {
    title: scene.title ?? '',
    englishLabel: scene.englishLabel,
    cards: (scene.items ?? []).map((t) => ({ title: t, items: [] as string[] })),
    calloutText: '',
    sceneSubtitle: scene.sceneSubtitle,
  };

  // Title scale-in
  const titleProgress = Math.min(Math.max((frame / 24 - 0.1) / 0.5, 0), 1);
  const titleEase = 1 - Math.pow(1 - titleProgress, 3);
  const titleScale = 0.92 + titleEase * 0.08;

  return (
    <SceneFrame theme={theme} englishLabel={content.englishLabel}>
      {/* Title block */}
      <div
        style={{
          position: 'absolute',
          top: 96,
          left: 0,
          right: 0,
          textAlign: 'center',
          fontFamily: FONT_FAMILY,
          color: theme.text,
          opacity: titleEase,
          transform: `scale(${titleScale})`,
        }}
      >
        <div
          style={{
            fontSize: 56,
            fontWeight: FONT_WEIGHT.bold,
            letterSpacing: 3,
          }}
        >
          {content.title}
        </div>
        {content.calloutSubtext && (
          <div
            style={{
              marginTop: 12,
              fontSize: 22,
              color: theme.textSecondary,
              letterSpacing: 2,
            }}
          >
            {content.calloutSubtext}
          </div>
        )}
      </div>

      {/* 3-column card grid */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: 80,
          right: 80,
          display: 'grid',
          gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
          gap: 32,
        }}
      >
        {content.cards.map((card, idx) => {
          // Stagger each card
          const cardStart = 12 + idx * 8;
          const cardProgress = Math.min(Math.max((frame - cardStart) / 18, 0), 1);
          const cardEase = 1 - Math.pow(1 - cardProgress, 3);

          return (
            <div
              key={idx}
              style={{
                background: theme.glassSurface ?? 'rgba(255,255,255,0.05)',
                border: `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.10)'}`,
                borderRadius: 18,
                padding: 24,
                backdropFilter: 'blur(12px)',
                WebkitBackdropFilter: 'blur(12px)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.25)',
                fontFamily: FONT_FAMILY,
                color: theme.text,
                opacity: cardEase,
                transform: `translateY(${(1 - cardEase) * 20}px)`,
                minHeight: 320,
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              {/* Card title bar with optional badge */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 16,
                }}
              >
                <div
                  style={{
                    fontSize: 18,
                    fontWeight: FONT_WEIGHT.bold,
                    letterSpacing: 1,
                  }}
                >
                  {card.title}
                </div>
                {card.badge && (
                  <div
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 6,
                      padding: '4px 12px',
                      borderRadius: 999,
                      background:
                        card.badge.variant === 'orange' ? 'rgba(255,107,53,0.15)'
                        : card.badge.variant === 'cyan' ? 'rgba(0,212,255,0.15)'
                        : 'rgba(255,255,255,0.06)',
                      border: `1px solid ${
                        card.badge.variant === 'orange' ? 'rgba(255,107,53,0.4)'
                        : card.badge.variant === 'cyan' ? 'rgba(0,212,255,0.4)'
                        : 'rgba(255,255,255,0.12)'
                      }`,
                      color:
                        card.badge.variant === 'orange' ? (theme.accentOrange ?? '#FF6B35')
                        : card.badge.variant === 'cyan' ? (theme.accentCyan ?? '#00D4FF')
                        : theme.textSecondary,
                      fontSize: 13,
                      fontWeight: FONT_WEIGHT.medium,
                    }}
                  >
                    {card.badge.icon && <span>{card.badge.icon}</span>}
                    <span>{card.badge.text}</span>
                  </div>
                )}
              </div>

              {/* Card items (checklist) */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
                {(card.items ?? []).map((item, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: '8px 12px',
                      background: 'rgba(255,255,255,0.04)',
                      borderRadius: 8,
                      fontSize: 16,
                      color: theme.text,
                    }}
                  >
                    <span
                      style={{
                        color: theme.accentGreen ?? '#2ED573',
                        fontSize: 14,
                      }}
                    >
                      ✓
                    </span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>

              {/* Optional footer button */}
              {card.buttonText && (
                <div
                  style={{
                    marginTop: 16,
                    padding: '8px 16px',
                    background: 'linear-gradient(90deg, rgba(255,107,53,0.3), rgba(0,212,255,0.2))',
                    border: '1px solid rgba(255,107,53,0.4)',
                    borderRadius: 8,
                    textAlign: 'center',
                    fontSize: 15,
                    fontWeight: FONT_WEIGHT.medium,
                    color: theme.text,
                  }}
                >
                  {card.buttonText}
                </div>
              )}
              {card.footerText && !card.buttonText && (
                <div
                  style={{
                    marginTop: 16,
                    fontSize: 13,
                    color: theme.textSecondary,
                    textAlign: 'center',
                  }}
                >
                  {card.footerText}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Callout text under cards */}
      {content.calloutText && (
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: 100,
            textAlign: 'center',
            fontFamily: FONT_FAMILY,
            fontSize: 20,
            color: theme.textSecondary,
            letterSpacing: 1.5,
            opacity: Math.min(Math.max((frame - 60) / 20, 0), 1),
          }}
        >
          {content.calloutText}
        </div>
      )}
    </SceneFrame>
  );
};

(CardGridScene as any).layoutType = LayoutType.CardGrid;
