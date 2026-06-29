import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Scene, ThemePalette, LayoutType } from '../../types';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { SceneFrame } from './_shared';

/**
 * SplitCompare — left problem list (with red ✕) + right probability bar
 * (sample 8: "方法会遗漏" / "hidden cost"). Dashed curve connector between them.
 */
export const SplitCompareScene: React.FC<{ scene: Scene; theme: ThemePalette }> = ({ scene, theme }) => {
  const frame = useCurrentFrame();

  const content = scene.splitCompare ?? {
    title: scene.title ?? '',
    englishLabel: scene.englishLabel,
    leftTitle: '',
    leftItems: (scene.leftItems ?? []).map((t) => ({ text: t })),
    rightHeader: scene.rightTitle ?? '',
    barSegments: [],
    bottomText: '',
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

      {/* 2-column layout */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: 80,
          right: 80,
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 80,
        }}
      >
        {/* LEFT: Problem list */}
        <div
          style={{
            background: theme.glassSurface ?? 'rgba(255,255,255,0.05)',
            border: `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.10)'}`,
            borderRadius: 18,
            padding: 28,
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            fontFamily: FONT_FAMILY,
            color: theme.text,
            opacity: Math.min(Math.max((frame - 12) / 20, 0), 1),
          }}
        >
          <div
            style={{
              fontSize: 18,
              fontWeight: FONT_WEIGHT.semibold,
              color: theme.text,
              marginBottom: 18,
              paddingBottom: 12,
              borderBottom: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            {content.leftTitle}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {content.leftItems.map((item, i) => {
              const itemStart = 18 + i * 5;
              const itemEase = Math.min(Math.max((frame - itemStart) / 12, 0), 1);
              return (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '10px 14px',
                    background: 'rgba(255,71,87,0.06)',
                    border: '1px solid rgba(255,71,87,0.18)',
                    borderRadius: 10,
                    fontSize: 16,
                    color: theme.text,
                    opacity: itemEase,
                    transform: `translateX(${(1 - itemEase) * -16}px)`,
                  }}
                >
                  <span
                    style={{
                      color: theme.accentRed ?? '#FF4757',
                      fontWeight: FONT_WEIGHT.bold,
                      fontSize: 16,
                    }}
                  >
                    {item.icon ?? '✕'}
                  </span>
                  <span style={{ flex: 1 }}>{item.text}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* RIGHT: Cost analysis with probability bar */}
        <div
          style={{
            background: theme.glassSurface ?? 'rgba(255,255,255,0.05)',
            border: `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.10)'}`,
            borderRadius: 18,
            padding: 28,
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            fontFamily: FONT_FAMILY,
            color: theme.text,
            opacity: Math.min(Math.max((frame - 24) / 20, 0), 1),
          }}
        >
          <div
            style={{
              display: 'inline-block',
              padding: '8px 18px',
              background: 'linear-gradient(90deg, rgba(255,107,53,0.25), rgba(255,71,87,0.20))',
              border: '1px solid rgba(255,107,53,0.4)',
              borderRadius: 8,
              fontSize: 18,
              fontWeight: FONT_WEIGHT.bold,
              color: theme.accentOrange ?? '#FF6B35',
              marginBottom: 22,
            }}
          >
            {content.rightHeader}
          </div>

          {/* Probability bar */}
          <div
            style={{
              display: 'flex',
              height: 44,
              borderRadius: 8,
              overflow: 'hidden',
              border: '1px solid rgba(255,255,255,0.10)',
              marginBottom: 12,
            }}
          >
            {(content.barSegments ?? []).map((seg, i) => {
              const segs = content.barSegments ?? [];
              const total = content.barTotal ?? segs.reduce((s, x) => s + x.value, 0);
              const w = total > 0 ? (seg.value / total) * 100 : 0;
              return (
                <div
                  key={i}
                  style={{
                    width: `${w}%`,
                    background: seg.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 15,
                    fontWeight: FONT_WEIGHT.bold,
                    color: '#FFFFFF',
                    textShadow: '0 1px 2px rgba(0,0,0,0.4)',
                  }}
                >
                  {seg.label}
                </div>
              );
            })}
          </div>

          {content.barInlineLabel && (
            <div
              style={{
                fontSize: 14,
                color: theme.textSecondary,
                marginBottom: 14,
                textAlign: 'center',
              }}
            >
              {content.barInlineLabel}
            </div>
          )}

          {content.bottomText && (
            <div
              style={{
                marginTop: 18,
                padding: '12px 16px',
                background: 'rgba(0,0,0,0.30)',
                borderRadius: 8,
                fontSize: 15,
                color: theme.textSecondary,
                lineHeight: 1.6,
              }}
            >
              {content.bottomText}
            </div>
          )}
        </div>
      </div>

      {/* Dashed curve connector */}
      <svg
        style={{
          position: 'absolute',
          top: 460,
          left: 0,
          right: 0,
          width: '100%',
          height: 80,
          pointerEvents: 'none',
          opacity: Math.min(Math.max((frame - 35) / 18, 0), 0.7),
        }}
        viewBox="0 0 1920 80"
        preserveAspectRatio="none"
      >
        <path
          d="M 800 0 C 920 80, 1000 80, 1100 0"
          stroke={theme.accentOrange ?? '#FF6B35'}
          strokeWidth="2"
          strokeDasharray="6 6"
          fill="none"
        />
      </svg>
    </SceneFrame>
  );
};

(SplitCompareScene as any).layoutType = LayoutType.SplitCompare;
