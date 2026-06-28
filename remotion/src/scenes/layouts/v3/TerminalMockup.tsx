import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { Scene } from '../../../types';
import { ThemePalette } from '../../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../../styles/typography';
import { ParticleBackground } from '../../../themes/v3/ParticleBackground';
import { GridGlowBackground } from '../../../themes/v3/GridGlowBackground';
import { EnglishLabel } from '../_shared';
import { ChapterBadge } from '../../../components/v3/ChapterBadge';
import { GlassyPanel } from '../../../components/v3/GlassyPanel';
import { Subtitle } from '../../../components/Subtitle';

/**
 * TerminalMockup — simulated AI terminal response.
 * Matches the reference video style: "Claude 的一条回复" with highlighted text.
 */
export const TerminalMockup: React.FC<{ scene: Scene; theme: ThemePalette }> = ({
  scene,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const content = scene.terminalMockup ?? {
    title: '',
    lines: [],
  };

  const lines = content.lines ?? [];

  // Title animation
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Terminal window animation
  const terminalOpacity = interpolate(frame, [8, 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const terminalSlideUp = interpolate(frame, [8, 20], [30, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Chapter badge parsing
  const chapterMatch = content.chapterBadge?.match(/^(\d+)\s*(.*)$/);
  const chapterNum = chapterMatch?.[1];
  const chapterTitle = chapterMatch?.[2];

  return (
    <AbsoluteFill style={{ fontFamily: FONT_FAMILY, color: theme.text }}>
      <ParticleBackground theme={theme} particleCount={30} />
      <GridGlowBackground theme={theme} showBeams={false} />

      <ChapterBadge chapterNum={chapterNum} chapterTitle={chapterTitle} theme={theme} showDecorDots />
      <EnglishLabel text={content.englishLabel ?? scene.englishLabel} theme={theme} />

      {/* Title */}
      <div
        style={{
          position: 'absolute',
          top: 80,
          left: 80,
          right: 80,
          opacity: titleOpacity,
        }}
      >
        <h1 style={{ margin: 0, fontSize: 48, fontWeight: FONT_WEIGHT.bold as number, letterSpacing: 2, color: theme.text }}>
          {content.title}
        </h1>
      </div>

      {/* Terminal window */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 120,
          right: 120,
          bottom: 160,
          opacity: terminalOpacity,
          transform: `translateY(${terminalSlideUp}px)`,
        }}
      >
        <GlassyPanel theme={theme} padding={0} borderRadius={16} style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Terminal header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '14px 20px',
              borderBottom: `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.12)'}`,
              gap: 10,
            }}
          >
            {/* macOS traffic lights */}
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#FF5F57' }} />
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#FEBC2E' }} />
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#28C840' }} />
            {/* Terminal title */}
            {content.terminalTitle && (
              <span style={{ marginLeft: 12, fontSize: 15, color: theme.textSecondary, fontWeight: FONT_WEIGHT.medium as number }}>
                {content.terminalTitle}
              </span>
            )}
          </div>

          {/* Terminal content */}
          <div
            style={{
              flex: 1,
              padding: '24px 28px',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              overflow: 'hidden',
            }}
          >
            {lines.map((line, i) => {
              const lineDelay = 20 + i * 8;
              const lineOpacity = interpolate(frame, [lineDelay, lineDelay + 10], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
              const lineSlide = interpolate(frame, [lineDelay, lineDelay + 10], [10, 0], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });

              // Typewriter effect for highlighted lines
              const charCount = line.text.length;
              const typewriterProgress = line.highlight
                ? interpolate(frame, [lineDelay, lineDelay + Math.min(charCount * 1.5, 40)], [0, 1], {
                    extrapolateLeft: 'clamp',
                    extrapolateRight: 'clamp',
                  })
                : 1;
              const visibleChars = Math.floor(charCount * typewriterProgress);

              return (
                <div
                  key={i}
                  style={{
                    opacity: lineOpacity,
                    transform: `translateY(${lineSlide}px)`,
                  }}
                >
                  {line.isUser ? (
                    /* User prompt line */
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                      <span style={{ color: theme.accentOrange ?? '#FF6B35', fontSize: 16, fontWeight: FONT_WEIGHT.bold as number, marginTop: 2 }}>▸</span>
                      <span style={{ fontSize: 20, color: theme.text, fontWeight: FONT_WEIGHT.medium as number }}>
                        {line.text}
                      </span>
                    </div>
                  ) : line.highlight ? (
                    /* Highlighted response line — orange background */
                    <div
                      style={{
                        background: `${theme.accentOrange ?? '#FF6B35'}18`,
                        border: `1px solid ${theme.accentOrange ?? '#FF6B35'}40`,
                        borderRadius: 8,
                        padding: '12px 18px',
                      }}
                    >
                      <span style={{ fontSize: 22, color: theme.accentOrange ?? '#FF6B35', fontWeight: FONT_WEIGHT.semibold as number }}>
                        {line.text.slice(0, visibleChars)}
                        {typewriterProgress < 1 && (
                          <span style={{ opacity: frame % 10 < 5 ? 1 : 0 }}>▋</span>
                        )}
                      </span>
                    </div>
                  ) : (
                    /* Normal response line */
                    <div style={{ fontSize: 18, color: theme.textSecondary, lineHeight: 1.6, paddingLeft: 26 }}>
                      {line.text}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </GlassyPanel>
      </div>

      {/* Callout text */}
      {content.calloutText && (
        <div
          style={{
            position: 'absolute',
            bottom: 120,
            left: 0,
            right: 0,
            textAlign: 'center',
            opacity: interpolate(frame, [50, 65], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
          }}
        >
          <GlassyPanel theme={theme} variant="outlined" accent="orange" padding="12px 32px" borderRadius={999} style={{ display: 'inline-block' }}>
            <span style={{ fontSize: 20, color: theme.accentOrange ?? '#FF6B35', fontWeight: FONT_WEIGHT.semibold as number }}>
              {content.calloutText}
            </span>
          </GlassyPanel>
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
