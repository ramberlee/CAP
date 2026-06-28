import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Scene, ThemePalette, LayoutType } from '../../types';
import { FONT_FAMILY, FONT_WEIGHT } from '../../styles/typography';
import { SceneFrame } from './_shared';

/**
 * DocTree — 3-column document view (sample 11: "专业工作手册").
 * Left: file tree. Center: numbered TOC. Right: code block.
 */
export const DocTreeScene: React.FC<{ scene: Scene; theme: ThemePalette }> = ({ scene, theme }) => {
  const frame = useCurrentFrame();

  const content = scene.docTree ?? {
    title: scene.title ?? '',
    englishLabel: scene.englishLabel,
    rootName: 'SKILL.md',
    files: [],
    tocTitle: 'SKILL.md',
    toc: [],
    codeTitle: '类代码实现',
    codeContent: '',
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
          top: 80,
          left: 80,
          fontFamily: FONT_FAMILY,
          color: theme.text,
          opacity: titleEase,
        }}
      >
        <div
          style={{
            fontSize: 48,
            fontWeight: FONT_WEIGHT.bold,
            letterSpacing: 2,
          }}
        >
          {content.title}
        </div>
      </div>

      {/* 3-column layout */}
      <div
        style={{
          position: 'absolute',
          top: 220,
          left: 80,
          right: 80,
          bottom: 130,
          display: 'grid',
          gridTemplateColumns: 'minmax(280px, 1fr) 1.4fr 1.4fr',
          gap: 24,
        }}
      >
        {/* LEFT: file tree */}
        <div
          style={{
            background: theme.glassSurface ?? 'rgba(255,255,255,0.04)',
            border: `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.10)'}`,
            borderRadius: 14,
            padding: 16,
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            fontFamily: FONT_FAMILY,
            color: theme.text,
            opacity: Math.min(Math.max((frame - 8) / 16, 0), 1),
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          <div
            style={{
              fontSize: 11,
              color: theme.textSecondary,
              letterSpacing: 1.5,
              marginBottom: 8,
            }}
          >
            SKILL outline / task-manual-system
          </div>

          {/* Root file entry */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 12px',
              background: 'rgba(255,107,53,0.10)',
              border: '1px solid rgba(255,107,53,0.30)',
              borderRadius: 8,
            }}
          >
            <span style={{ fontSize: 14 }}>📄</span>
            <span style={{ flex: 1, fontSize: 15, fontWeight: FONT_WEIGHT.semibold }}>{content.rootName}</span>
            {content.rootBadge && (
              <span
                style={{
                  fontSize: 11,
                  color: theme.accentCyan ?? '#00D4FF',
                  background: 'rgba(0,212,255,0.10)',
                  border: '1px solid rgba(0,212,255,0.25)',
                  padding: '2px 8px',
                  borderRadius: 999,
                  fontWeight: FONT_WEIGHT.medium,
                }}
              >
                {content.rootBadge}
              </span>
            )}
          </div>

          {/* File list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginTop: 4 }}>
            {(content.files ?? []).map((file, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '6px 10px 6px 18px',
                  borderRadius: 6,
                  color: theme.textSecondary,
                  fontSize: 13,
                }}
              >
                <span style={{ fontSize: 12, opacity: 0.7 }}>{file.icon ?? '·'}</span>
                <span style={{ flex: 1, color: theme.text }}>{file.name}</span>
                {file.badge && (
                  <span
                    style={{
                      fontSize: 10,
                      color: theme.accentCyan ?? '#00D4FF',
                      background: 'rgba(0,212,255,0.10)',
                      padding: '2px 6px',
                      borderRadius: 999,
                    }}
                  >
                    {file.badge}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* CENTER: numbered TOC */}
        <div
          style={{
            background: theme.glassSurface ?? 'rgba(255,255,255,0.04)',
            border: `1px solid ${theme.glassBorder ?? 'rgba(255,255,255,0.10)'}`,
            borderRadius: 14,
            padding: 20,
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            fontFamily: FONT_FAMILY,
            color: theme.text,
            opacity: Math.min(Math.max((frame - 12) / 18, 0), 1),
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 16,
              fontWeight: FONT_WEIGHT.semibold,
              color: theme.text,
              marginBottom: 4,
            }}
          >
            <span style={{ color: theme.accentCyan ?? '#00D4FF' }}>📄</span>
            <span>{content.tocTitle}</span>
          </div>

          {(content.toc ?? []).map((entry, i) => {
            const itemStart = 20 + i * 4;
            const itemEase = Math.min(Math.max((frame - itemStart) / 10, 0), 1);
            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '8px 12px',
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: 8,
                  fontSize: 14,
                  opacity: itemEase,
                  transform: `translateX(${(1 - itemEase) * 12}px)`,
                }}
              >
                <span
                  style={{
                    minWidth: 22,
                    fontWeight: FONT_WEIGHT.bold,
                    color: theme.accentCyan ?? '#00D4FF',
                    fontVariantNumeric: 'tabular-nums',
                    fontSize: 13,
                  }}
                >
                  {entry.num}
                </span>
                <span style={{ flex: 1, color: theme.text }}>{entry.name}</span>
                {(entry.badges ?? []).map((b, j) => (
                  <span
                    key={j}
                    style={{
                      fontSize: 11,
                      color: theme.textSecondary,
                      padding: '2px 8px',
                      background: 'rgba(255,255,255,0.05)',
                      borderRadius: 999,
                    }}
                  >
                    {b}
                  </span>
                ))}
              </div>
            );
          })}
        </div>

        {/* RIGHT: code block */}
        <div
          style={{
            opacity: Math.min(Math.max((frame - 18) / 18, 0), 1),
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
          }}
        >
          {/* Code block title pill */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 14px',
              background: 'rgba(255,107,53,0.10)',
              border: '1px solid rgba(255,107,53,0.25)',
              borderRadius: 8,
              fontFamily: FONT_FAMILY,
              fontSize: 13,
              color: theme.accentOrange ?? '#FF6B35',
              fontWeight: FONT_WEIGHT.semibold,
              letterSpacing: 0.5,
            }}
          >
            <span>{content.codeTitle}</span>
          </div>

          {/* Code body */}
          <pre
            style={{
              flex: 1,
              margin: 0,
              padding: 16,
              background: 'rgba(0,0,0,0.45)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 12,
              fontFamily: '"Cascadia Code", "JetBrains Mono", Consolas, Monaco, monospace',
              fontSize: 13,
              lineHeight: 1.6,
              color: '#A8B3CF',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {content.codeContent}
          </pre>
        </div>
      </div>
    </SceneFrame>
  );
};

(DocTreeScene as any).layoutType = LayoutType.DocTree;
