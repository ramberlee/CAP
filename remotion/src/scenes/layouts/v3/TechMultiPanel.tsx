import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Scene } from '../../../types';
import { ThemePalette } from '../../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../../styles/typography';
import { ParticleBackground } from '../../../themes/v3/ParticleBackground';
import { GridGlowBackground } from '../../../themes/v3/GridGlowBackground';
import { EnglishLabel } from '../_shared';
import { GlassyPanel } from '../../../components/v3/GlassyPanel';
import { StatusBadge } from '../../../components/v3/StatusBadge';
import { StateDot } from '../../../components/v3/StateDot';
import { ChapterBadge } from '../../../components/v3/ChapterBadge';
import { ProgressBar, SimpleProgressBar } from '../../../components/v3/ProgressBar';
import { useStaggeredAnimation } from '../../../components/hooks/useStaggeredAnimation';
import { Subtitle } from '../../../components/Subtitle';

/**
 * TechMultiPanel - 3-column tech dashboard layout (sample screenshot 6).
 * Left panel: feature list with status badges.
 * Center: main content area with title and progress.
 * Right panel: document list with loaded indicators.
 */
export const TechMultiPanel: React.FC<{ scene: Scene; theme: ThemePalette }> = ({
  scene,
  theme,
}) => {
  const frame = useCurrentFrame();
  const content = scene.techMultiPanel ?? {
    title: scene.title ?? '',
    leftPanel: { items: [] },
    centerPanel: { body: '' },
    rightPanel: { items: [] },
  };

  const leftItems = content.leftPanel.items ?? [];
  const rightItems = content.rightPanel.items ?? [];
  const leftAnims = useStaggeredAnimation({ itemCount: leftItems.length, staggerDelay: 5, startFrame: 10 });
  const rightAnims = useStaggeredAnimation({ itemCount: rightItems.length, staggerDelay: 5, startFrame: 25 });

  // Parse chapter badge (e.g., "02 问题" -> num="02", title="问题")
  const chapterMatch = content.chapterBadge?.match(/^(\d+)\s*(.*)$/);
  const chapterNum = chapterMatch?.[1];
  const chapterTitle = chapterMatch?.[2];

  return (
    <AbsoluteFill style={{ fontFamily: FONT_FAMILY, color: theme.text }}>
      {/* v3 Background effects */}
      <ParticleBackground theme={theme} />
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
          top: 140,
          left: 80,
          right: 80,
          opacity: Math.min(Math.max((frame - 5) / 15, 0), 1),
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: 56,
            fontWeight: FONT_WEIGHT.bold as number,
            letterSpacing: 2,
            color: theme.text,
          }}
        >
          {content.title}
        </h1>
      </div>

      {/* 3-Column Layout */}
      <div
        style={{
          position: 'absolute',
          top: 240,
          left: 80,
          right: 80,
          bottom: 120,
          display: 'grid',
          gridTemplateColumns: '1fr 1.6fr 1fr',
          gap: 24,
        }}
      >
        {/* Left Panel - Feature List */}
        <GlassyPanel theme={theme} padding={20} borderRadius={16}>
          <div
            style={{
              fontSize: 13,
              color: theme.textSecondary,
              letterSpacing: 1,
              marginBottom: 16,
              opacity: Math.min(Math.max((frame - 8) / 12, 0), 1),
            }}
          >
            {content.leftPanel.title ?? 'FEATURES'}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {leftItems.map((item, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 14px',
                  background: item.state === 'active' ? 'rgba(255,107,53,0.10)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${item.state === 'active' ? 'rgba(255,107,53,0.30)' : 'rgba(255,255,255,0.06)'}`,
                  borderRadius: 10,
                  opacity: leftAnims[i]?.opacity ?? 0,
                  transform: `translateY(${leftAnims[i]?.transformY ?? 10}px)`,
                }}
              >
                <StateDot state={item.state ?? 'idle'} size={8} />
                <span style={{ flex: 1, fontSize: 14 }}>{item.text}</span>
                {item.badge && (
                  <StatusBadge
                    text={item.badge.text}
                    variant={item.badge.variant === 'orange' ? 'loading' : item.badge.variant === 'green' ? 'loaded' : 'one-off'}
                    size="sm"
                  />
                )}
              </div>
            ))}
          </div>
          {content.leftPanel.progress && (
            <div style={{ marginTop: 20 }}>
              <SimpleProgressBar
                value={content.leftPanel.progress.current}
                max={content.leftPanel.progress.total}
                color={theme.accentOrange ?? '#FF6B35'}
                showPercent
              />
            </div>
          )}
        </GlassyPanel>

        {/* Center Panel - Main Content */}
        <GlassyPanel
          theme={theme}
          padding={28}
          borderRadius={16}
          accent="orange"
          glow={content.centerPanel.glow}
        >
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {content.centerPanel.title && (
              <h2
                style={{
                  margin: '0 0 16px 0',
                  fontSize: 28,
                  fontWeight: FONT_WEIGHT.bold as number,
                  color: theme.text,
                  opacity: Math.min(Math.max((frame - 15) / 12, 0), 1),
                }}
              >
                {content.centerPanel.title}
              </h2>
            )}
            {content.centerPanel.subtitle && (
              <p
                style={{
                  margin: '0 0 20px 0',
                  fontSize: 16,
                  color: theme.textSecondary,
                  opacity: Math.min(Math.max((frame - 20) / 12, 0), 1),
                }}
              >
                {content.centerPanel.subtitle}
              </p>
            )}
            <div
              style={{
                flex: 1,
                fontSize: 16,
                lineHeight: 1.8,
                color: theme.text,
                opacity: Math.min(Math.max((frame - 25) / 15, 0), 1),
              }}
            >
              {content.centerPanel.body}
            </div>
            {content.centerPanel.progressBar && (
              <div style={{ marginTop: 20 }}>
                <ProgressBar
                  segments={content.centerPanel.progressBar}
                  animated
                  showLabels
                  height={36}
                />
              </div>
            )}
          </div>
        </GlassyPanel>

        {/* Right Panel - Documents */}
        <GlassyPanel theme={theme} padding={20} borderRadius={16}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 16,
              opacity: Math.min(Math.max((frame - 18) / 12, 0), 1),
            }}
          >
            <span
              style={{
                fontSize: 13,
                color: theme.textSecondary,
                letterSpacing: 1,
              }}
            >
              {content.rightPanel.title ?? 'DOCUMENTS'}
            </span>
            {content.rightPanel.pagination && (
              <div style={{ display: 'flex', gap: 6 }}>
                {Array.from({ length: content.rightPanel.pagination.total }, (_, i) => (
                  <div
                    key={i}
                    style={{
                      width: i === content.rightPanel.pagination!.current ? 20 : 6,
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: i === content.rightPanel.pagination!.current
                        ? theme.accentOrange ?? '#FF6B35'
                        : 'rgba(255,255,255,0.2)',
                    }}
                  />
                ))}
              </div>
            )}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {rightItems.map((item, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 14px',
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: 10,
                  opacity: rightAnims[i]?.opacity ?? 0,
                  transform: `translateY(${rightAnims[i]?.transformY ?? 10}px)`,
                }}
              >
                <span style={{ flex: 1, fontSize: 14 }}>📄 {item.name}</span>
                {item.badge && (
                  <StatusBadge
                    text={item.badge.text}
                    variant={item.badge.variant === 'green' ? 'loaded' : item.badge.variant === 'orange' ? 'loading' : 'one-off'}
                    size="sm"
                  />
                )}
              </div>
            ))}
          </div>
        </GlassyPanel>
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
