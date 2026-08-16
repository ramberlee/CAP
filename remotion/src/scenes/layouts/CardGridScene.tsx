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

  // Callout fade-in (kept for the new in-column callout)
  const calloutOpacity = Math.min(Math.max((frame - 60) / 20, 0), 1);

  return (
    <SceneFrame theme={theme} englishLabel={content.englishLabel}>
      {/* Vertically-centered column: title → cards → callout.
          Replaces the old fixed `top:` offsets that crammed content into the
          upper 40% and left the lower half dead. Cards now size to their
          content instead of a forced minHeight, so a sparse card no longer
          leaves a giant empty box. */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'stretch',
          padding: '96px 80px 120px',
          fontFamily: FONT_FAMILY,
          color: theme.text,
        }}
      >
        {/* Title block */}
        <div style={{ textAlign: 'center', opacity: titleEase, transform: `scale(${titleScale})` }}>
          <div
            style={{
              fontSize: 56,
              fontWeight: FONT_WEIGHT.bold,
              letterSpacing: 3,
            }}
          >
            {content.title}
          </div>
          {(content as any).calloutSubtext && (
            <div
              style={{
                marginTop: 12,
                fontSize: 22,
                color: theme.textSecondary,
                letterSpacing: 2,
              }}
            >
              {(content as any).calloutSubtext}
            </div>
          )}
        </div>

        {/* 3-column card grid — flex: 1 so it expands into available vertical space */}
        <div
          style={{
            marginTop: 48,
            flex: 1,
            display: 'grid',
            gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
            gap: 32,
            alignItems: 'stretch',
          }}
        >
        {content.cards.map((cardOrig, idx) => {
          // Stagger each card
          const cardStart = 12 + idx * 8;
          const cardProgress = Math.min(Math.max((frame - cardStart) / 18, 0), 1);
          const cardEase = 1 - Math.pow(1 - cardProgress, 3);

          // Type assertion: card accepts both schema format and simplified LLM format
          const card = cardOrig as any;

          return (
            <div
              key={idx}
              style={{
                background: theme.glassSurface ?? 'rgba(255,255,255,0.05)',
                border: `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.10)'}`,
                borderRadius: 18,
                padding: 28,
                minHeight: 220,
                backdropFilter: 'blur(12px)',
                WebkitBackdropFilter: 'blur(12px)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.25)',
                fontFamily: FONT_FAMILY,
                color: theme.text,
                opacity: cardEase,
                transform: `translateY(${(1 - cardEase) * 20}px)`,
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
                    fontSize: 20,
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

              {/* Card items (checklist) OR description text (simplified format).
                  Items use flex:1 to expand and fill the card evenly when sparse. */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, flex: 1, justifyContent: 'flex-start' }}>
                {(card.items ?? []).length > 0 ? (
                  (card.items ?? []).map((item: string, i: number) => (
                    <div
                      key={i}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 12,
                        padding: '12px 16px',
                        background: 'rgba(255,255,255,0.04)',
                        borderRadius: 10,
                        fontSize: 18,
                        color: theme.text,
                        lineHeight: 1.4,
                      }}
                    >
                      <span
                        style={{
                          color: theme.accentGreen ?? '#2ED573',
                          fontSize: 16,
                        }}
                      >
                        ✓
                      </span>
                      <span>{item}</span>
                    </div>
                  ))
                ) : (
                  // Fallback: show icon + description (simplified format from LLM)
                  <>
                    {card.icon && (
                      <div style={{ fontSize: 48, textAlign: 'center', marginBottom: 16 }}>
                        {card.icon}
                      </div>
                    )}
                    {(card as any).desc && (
                      <div style={{
                        fontSize: 16,
                        color: theme.textSecondary,
                        textAlign: 'center',
                        lineHeight: 1.6,
                      }}>
                        {(card as any).desc}
                      </div>
                    )}
                  </>
                )}
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

      {/* Callout text under cards — kept inside the centered column so it
          sits right below the grid instead of floating detached at the bottom. */}
      {content.calloutText && (
        <div
          style={{
            marginTop: 40,
            textAlign: 'center',
            fontFamily: FONT_FAMILY,
            fontSize: 20,
            color: theme.textSecondary,
            letterSpacing: 1.5,
            opacity: calloutOpacity,
          }}
        >
          {content.calloutText}
        </div>
      )}
      </div>
    </SceneFrame>
  );
};

(CardGridScene as any).layoutType = LayoutType.CardGrid;
