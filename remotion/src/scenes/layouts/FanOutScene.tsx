import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Scene, ThemePalette, LayoutType } from '../../types';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { SceneFrame } from './_shared';

/**
 * FanOut — left column fanning out to a single right "Skill" card
 * (sample 10: "系统能力叠加"). Includes curved dashed lines connecting
 * left items to the right card and bottom status pills.
 */
export const FanOutScene: React.FC<{ scene: Scene; theme: ThemePalette }> = ({ scene, theme }) => {
  const frame = useCurrentFrame();

  const content = scene.fanOut ?? {
    title: scene.title ?? '',
    englishLabel: scene.englishLabel,
    leftItems: (scene.items ?? []).map((t) => ({ text: t })),
    rightCardTitle: '',
    rightCardBody: '',
    rightPills: [],
    sceneSubtitle: scene.sceneSubtitle,
  };

  const titleProgress = Math.min(Math.max((frame / 24 - 0.1) / 0.5, 0), 1);
  const titleEase = 1 - Math.pow(1 - titleProgress, 3);

  return (
    <SceneFrame theme={theme} englishLabel={content.englishLabel}>
      {/* Title */}
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
            fontSize: 56,
            fontWeight: FONT_WEIGHT.bold,
            letterSpacing: 3,
          }}
        >
          {content.title}
        </div>
      </div>

      {/* Layout: left list + right card */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: 80,
          right: 80,
          display: 'grid',
          gridTemplateColumns: 'minmax(360px, 1fr) 1.4fr',
          gap: 80,
        }}
      >
        {/* LEFT: vertical list of items */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {(content.leftItems ?? []).map((item, i) => {
            const itemStart = 12 + i * 4;
            const itemEase = Math.min(Math.max((frame - itemStart) / 14, 0), 1);
            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '14px 20px',
                  background: theme.glassSurface ?? 'rgba(255,255,255,0.04)',
                  border: `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.08)'}`,
                  borderRadius: 12,
                  fontFamily: FONT_FAMILY,
                  color: theme.text,
                  opacity: itemEase,
                  transform: `translateX(${(1 - itemEase) * -16}px)`,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {item.badge && (
                    <span
                      style={{
                        display: 'inline-block',
                        minWidth: 8,
                        height: 8,
                        borderRadius: 999,
                        background:
                          item.badge.variant === 'orange' ? (theme.accentOrange ?? '#FF6B35')
                          : item.badge.variant === 'cyan' ? (theme.accentCyan ?? '#00D4FF')
                          : 'rgba(255,255,255,0.5)',
                      }}
                    />
                  )}
                  <span style={{ fontSize: 17, fontWeight: FONT_WEIGHT.medium }}>{item.text}</span>
                </div>
                {item.badge && (
                  <span
                    style={{
                      fontSize: 12,
                      color: theme.textSecondary,
                      padding: '2px 10px',
                      background: 'rgba(255,255,255,0.05)',
                      borderRadius: 999,
                    }}
                  >
                    {item.badge.text}
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {/* RIGHT: Highlighted card */}
        <div
          style={{
            position: 'relative',
            background: 'linear-gradient(135deg, rgba(255,107,53,0.10), rgba(0,212,255,0.05))',
            border: '1.5px solid rgba(255,107,53,0.3)',
            borderRadius: 18,
            padding: 32,
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            fontFamily: FONT_FAMILY,
            color: theme.text,
            boxShadow: '0 12px 48px rgba(255,107,53,0.10)',
            opacity: Math.min(Math.max((frame - 30) / 18, 0), 1),
            transform: `translateY(${Math.max(0, 1 - Math.min(Math.max((frame - 30) / 18, 0), 1)) * 16}px)`,
          }}
        >
          <div
            style={{
              fontSize: 14,
              color: theme.accentOrange ?? '#FF6B35',
              fontWeight: FONT_WEIGHT.semibold,
              letterSpacing: 2,
              marginBottom: 12,
            }}
          >
            叠加之后 →
          </div>
          <div
            style={{
              fontSize: 56,
              fontWeight: FONT_WEIGHT.bold,
              letterSpacing: 4,
              marginBottom: 18,
              background: 'linear-gradient(135deg, #FF6B35, #00D4FF)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            {content.rightCardTitle}
          </div>
          {content.rightCardSubtitle && (
            <div
              style={{
                fontSize: 14,
                color: theme.textSecondary,
                letterSpacing: 1,
                marginBottom: 16,
              }}
            >
              {content.rightCardSubtitle}
            </div>
          )}
          <div
            style={{
              fontSize: 17,
              color: theme.text,
              lineHeight: 1.6,
              marginBottom: 22,
            }}
          >
            {content.rightCardBody}
          </div>
          {(content.rightPills ?? []).length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
              {content.rightPills.map((pill, i) => (
                <div
                  key={i}
                  style={{
                    padding: '6px 14px',
                    background: 'rgba(255,255,255,0.06)',
                    border: '1px solid rgba(255,255,255,0.12)',
                    borderRadius: 999,
                    fontSize: 13,
                    color: theme.text,
                    letterSpacing: 0.5,
                  }}
                >
                  {pill}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Curved dashed connectors from left items to right card */}
      <svg
        style={{
          position: 'absolute',
          top: 280,
          left: '40%',
          right: '5%',
          width: '55%',
          height: 520,
          pointerEvents: 'none',
          opacity: Math.min(Math.max((frame - 30) / 18, 0), 0.7),
        }}
        viewBox="0 0 1000 520"
        preserveAspectRatio="none"
      >
        <path d="M 0 60 C 200 80, 400 100, 950 240" stroke={theme.accentOrange ?? '#FF6B35'} strokeWidth="2" strokeDasharray="6 6" fill="none" />
        <path d="M 0 240 C 250 240, 500 240, 950 250" stroke={theme.accentOrange ?? '#FF6B35'} strokeWidth="2" strokeDasharray="6 6" fill="none" />
        <path d="M 0 420 C 250 380, 500 340, 950 260" stroke={theme.accentOrange ?? '#FF6B35'} strokeWidth="2" strokeDasharray="6 6" fill="none" />
      </svg>
    </SceneFrame>
  );
};

(FanOutScene as any).layoutType = LayoutType.FanOut;
