import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { Scene } from '../../../types';
import { ThemePalette } from '../../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../../styles/typography';
import { ParticleBackground } from '../../../themes/v3/ParticleBackground';
import { GridGlowBackground } from '../../../themes/v3/GridGlowBackground';
import { EnglishLabel } from '../_shared';
import { ChapterBadge } from '../../../components/v3/ChapterBadge';
import { Subtitle } from '../../../components/Subtitle';

const COLOR_MAP: Record<string, string> = {
  orange: '#FF6B35',
  cyan: '#00D4FF',
  green: '#2ED573',
  red: '#FF4757',
};

/**
 * DataCompare — animated horizontal bars with multiplication effects.
 * Matches the reference video style: "底子 50 ×3 → 150"
 */
export const DataCompare: React.FC<{ scene: Scene; theme: ThemePalette }> = ({
  scene,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const content = scene.dataCompare ?? {
    title: '',
    items: [],
  };

  const items = content.items ?? [];

  // Title animation
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Find max result value for bar scaling
  const maxValue = Math.max(...items.map((item) => item.resultValue), 1);

  // Chapter badge parsing
  const chapterMatch = content.chapterBadge?.match(/^(\d+)\s*(.*)$/);
  const chapterNum = chapterMatch?.[1];
  const chapterTitle = chapterMatch?.[2];

  return (
    <AbsoluteFill style={{ fontFamily: FONT_FAMILY, color: theme.text }}>
      <ParticleBackground theme={theme} particleCount={35} />
      <GridGlowBackground theme={theme} showBeams={false} />

      <ChapterBadge chapterNum={chapterNum} chapterTitle={chapterTitle} theme={theme} showDecorDots />
      <EnglishLabel text={content.englishLabel ?? scene.englishLabel} theme={theme} />

      {/* Title */}
      <div
        style={{
          position: 'absolute',
          top: 100,
          left: 80,
          right: 80,
          opacity: titleOpacity,
        }}
      >
        <div style={{ fontSize: 14, color: theme.accentOrange ?? '#FF6B35', fontWeight: FONT_WEIGHT.semibold, marginBottom: 8, letterSpacing: 2 }}>
          {content.chapterBadge ?? ''}
        </div>
        <h1 style={{ margin: 0, fontSize: 52, fontWeight: FONT_WEIGHT.bold as number, letterSpacing: 2, color: theme.text }}>
          {content.title}
        </h1>
      </div>

      {/* Data bars */}
      <div
        style={{
          position: 'absolute',
          top: 260,
          left: 120,
          right: 120,
          bottom: 160,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          gap: 48,
        }}
      >
        {items.map((item, i) => {
          const itemDelay = 15 + i * 12;
          const barProgress = interpolate(frame, [itemDelay, itemDelay + 25], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          // Cubic ease out
          const barEase = 1 - Math.pow(1 - barProgress, 3);

          const numberProgress = interpolate(frame, [itemDelay + 10, itemDelay + 30], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          const labelOpacity = interpolate(frame, [itemDelay, itemDelay + 10], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          const color = COLOR_MAP[item.color ?? 'orange'] ?? theme.accentOrange ?? '#FF6B35';
          const barWidth = (item.resultValue / maxValue) * 100;
          const baseWidth = (item.baseValue / maxValue) * 100;

          const displayResult = Math.round(item.resultValue * numberProgress);
          const displayBase = Math.round(item.baseValue * Math.min(numberProgress * 2, 1));

          return (
            <div key={i} style={{ opacity: labelOpacity }}>
              {/* Label row */}
              <div style={{ display: 'flex', alignItems: 'baseline', marginBottom: 12, gap: 12 }}>
                <span style={{ fontSize: 24, fontWeight: FONT_WEIGHT.semibold as number, color: theme.text }}>
                  {item.label}
                </span>
                {item.baseLabel && (
                  <span style={{ fontSize: 16, color: theme.textSecondary }}>
                    {item.baseLabel}
                  </span>
                )}
              </div>

              {/* Bar row */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
                {/* Base value */}
                <div style={{ fontSize: 40, fontWeight: FONT_WEIGHT.extrabold as number, color: theme.textSecondary, minWidth: 60, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                  {displayBase}
                </div>

                {/* Multiplier */}
                {item.multiplier && (
                  <div style={{ fontSize: 24, fontWeight: FONT_WEIGHT.bold as number, color: theme.textSecondary, minWidth: 40, textAlign: 'center' }}>
                    ×{item.multiplier}
                  </div>
                )}

                {/* Progress bar */}
                <div style={{ flex: 1, height: 40, background: 'rgba(255,255,255,0.06)', borderRadius: 8, overflow: 'hidden', position: 'relative' }}>
                  {/* Base bar (darker) */}
                  <div
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      height: '100%',
                      width: `${baseWidth * barEase}%`,
                      background: `${color}40`,
                      borderRadius: 8,
                    }}
                  />
                  {/* Result bar (bright) */}
                  <div
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      height: '100%',
                      width: `${barWidth * barEase}%`,
                      background: `linear-gradient(90deg, ${color}90, ${color})`,
                      borderRadius: 8,
                      boxShadow: `0 0 20px ${color}40`,
                    }}
                  />
                </div>

                {/* Result value */}
                <div style={{ fontSize: 48, fontWeight: FONT_WEIGHT.extrabold as number, color, minWidth: 80, textAlign: 'left', fontVariantNumeric: 'tabular-nums' }}>
                  {displayResult}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Center text */}
      {content.centerText && (
        <div
          style={{
            position: 'absolute',
            bottom: 140,
            left: 0,
            right: 0,
            textAlign: 'center',
            opacity: interpolate(frame, [40, 55], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
          }}
        >
          <span style={{ fontSize: 22, color: theme.accentOrange ?? '#FF6B35', fontWeight: FONT_WEIGHT.medium as number, letterSpacing: 1 }}>
            {content.centerText}
          </span>
        </div>
      )}

      <Subtitle
        text={content.sceneSubtitle ?? scene.sceneSubtitle}
        theme={theme}
        sceneDurationInFrames={Math.round((scene.duration ?? 5) * fps)}
        glassBackground
      />
    </AbsoluteFill>
  );
};
