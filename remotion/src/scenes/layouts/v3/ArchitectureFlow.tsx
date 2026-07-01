import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { Scene } from '../../../types';
import { ThemePalette } from '../../../themes';
import { FONT_FAMILY, FONT_WEIGHT } from '../../../styles/typography';
import { ParticleBackground } from '../../../themes/v3/ParticleBackground';
import { GridGlowBackground } from '../../../themes/v3/GridGlowBackground';
import { EnglishLabel } from '../_shared';
import { GlassyPanel } from '../../../components/v3/GlassyPanel';
import { ChapterBadge } from '../../../components/v3/ChapterBadge';
import { ConnectorLine } from '../../../components/v3/ConnectorLine';
import { GlowEffect } from '../../../components/v3/GlowEffect';
import { useStaggeredAnimation } from '../../../components/hooks/useStaggeredAnimation';
import { Subtitle } from '../../../components/Subtitle';

const COLOR_MAP: Record<string, string> = {
  orange: '#FF6B35',
  cyan: '#00D4FF',
  red: '#FF4757',
  green: '#2ED573',
  neutral: 'rgba(255,255,255,0.7)',
};

/**
 * ArchitectureFlow - System architecture diagram with nodes and flowing connections.
 * (Sample screenshot 9 - AI system architecture).
 * Nodes can have custom positions, colors, and glow effects.
 * Connections support flowing dots animation.
 */
export const ArchitectureFlow: React.FC<{ scene: Scene; theme: ThemePalette }> = ({
  scene,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const content = scene.architectureFlow ?? {
    title: scene.title ?? '',
    nodes: [],
    connections: [],
  };

  // Diagram area mirrors the absolutely-positioned container below:
  // top:220, bottom:100 → height = height - 320; spans the full width.
  const DIAGRAM_W = width;
  const DIAGRAM_H = height - 320;
  const NODE_W = 220;
  const NODE_H = 80;

  // Normalize nodes. Two positioning modes:
  //  1. Explicit coords (percentage 0-100, or raw pixels) — used as given.
  //  2. No coords — auto-laid-out as a horizontal left→right flow.
  // Mode 2 is the common case (the planner emits nodes without x/y). Without
  // it, positionless nodes all fall back to `left/top: undefined` and stack
  // at (0,0), overlapping into a single clump in the top-left while the rest
  // of the diagram stays empty — exactly the "one pill top-left, empty
  // center" frame that was flagged as low quality.
  const rawNodes = (content.nodes ?? []).map((node) => ({
    ...node,
    w: node.w ?? NODE_W,
    h: node.h ?? NODE_H,
    x:
      node.x > 0 && node.x <= 100
        ? 80 + (node.x / 100) * (width - 240) - ((node.w ?? NODE_W) / 2) // center-align
        : node.x,
    y: node.y > 0 && node.y <= 100 ? (node.y / 100) * DIAGRAM_H : node.y,
  }));

  const needsAutoLayout = rawNodes.some(
    (n) => n.x == null || Number.isNaN(n.x as number),
  );
  let nodes = rawNodes;
  if (needsAutoLayout && rawNodes.length > 0) {
    const gap = 120;
    const totalWidth =
      rawNodes.length * NODE_W + Math.max(0, rawNodes.length - 1) * gap;
    const startX = Math.max(0, (DIAGRAM_W - totalWidth) / 2);
    const centerY = Math.max(0, (DIAGRAM_H - NODE_H) / 2);
    nodes = rawNodes.map((n, i) => ({
      ...n,
      x: startX + i * (NODE_W + gap),
      y: n.y ?? centerY,
      w: NODE_W,
      h: NODE_H,
    }));
  }
  const connections = content.connections ?? [];

  const nodeAnims = useStaggeredAnimation({
    itemCount: nodes.length,
    staggerDelay: 6,
    startFrame: 20,
  });

  // Parse chapter badge
  const chapterMatch = content.chapterBadge?.match(/^(\d+)\s*(.*)$/);
  const chapterNum = chapterMatch?.[1];
  const chapterTitle = chapterMatch?.[2];

  return (
    <AbsoluteFill style={{ fontFamily: FONT_FAMILY, color: theme.text }}>
      {/* v3 Background effects */}
      <ParticleBackground theme={theme} particleCount={40} />
      <GridGlowBackground theme={theme} showBeams={false} />

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
          opacity: Math.min(Math.max((frame - 5) / 15, 0), 1),
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: 48,
            fontWeight: FONT_WEIGHT.bold as number,
            letterSpacing: 2,
            color: theme.text,
          }}
        >
          {content.title}
        </h1>
      </div>

      {/* Diagram Area */}
      <div
        style={{
          position: 'absolute',
          top: 220,
          left: 0,
          right: 0,
          bottom: 100,
        }}
      >
        {/* Connections (render first, behind nodes) */}
        {connections.map((conn, i) => {
          const fromNode = nodes.find((n) => n.id === conn.from);
          const toNode = nodes.find((n) => n.id === conn.to);
          if (!fromNode || !toNode) return null;

          const fromX = fromNode.x + fromNode.w / 2;
          const fromY = fromNode.y + fromNode.h / 2;
          const toX = toNode.x + toNode.w / 2;
          const toY = toNode.y + toNode.h / 2;

          const showConn = frame > 35 + i * 4;
          if (!showConn) return null;

          return (
            <ConnectorLine
              key={i}
              from={{ x: fromX, y: fromY }}
              to={{ x: toX, y: toY }}
              variant={conn.variant ?? 'straight'}
              color={conn.color ?? 'rgba(255,107,53,0.4)'}
              flowing={conn.flowing}
              dotSize={4}
            />
          );
        })}

        {/* Nodes */}
        {nodes.map((node, i) => {
          const anim = nodeAnims[i] ?? { opacity: 0, transformY: 20 };
          const nodeColor = COLOR_MAP[node.color] ?? COLOR_MAP.neutral;
          // The planner emits `desc` for node descriptions; older specs used
          // `sublabel`. Accept either so the description actually renders.
          const sublabel = node.sublabel ?? (node as any).desc;

          const nodeContent = (
            <div
              style={{
                position: 'absolute',
                left: node.x,
                top: node.y,
                width: node.w,
                height: node.h,
                opacity: anim.opacity,
                transform: `translateY(${anim.transformY}px)`,
              }}
            >
              <GlassyPanel
                theme={theme}
                padding={16}
                borderRadius={12}
                style={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textAlign: 'center',
                  borderColor: node.glow ? nodeColor : undefined,
                  borderWidth: node.glow ? 2 : 1,
                }}
              >
                <div
                  style={{
                    fontSize: 20,
                    fontWeight: FONT_WEIGHT.bold as number,
                    color: nodeColor,
                    marginBottom: sublabel ? 4 : 0,
                  }}
                >
                  {node.label}
                </div>
                {sublabel && (
                  <div
                    style={{
                      fontSize: 13,
                      color: theme.textSecondary,
                    }}
                  >
                    {sublabel}
                  </div>
                )}
              </GlassyPanel>
              {node.glow && (
                <GlowEffect color={nodeColor} intensity={0.4} pulse>
                  <div style={{ position: 'absolute', inset: 0, borderRadius: 12 }} />
                </GlowEffect>
              )}
            </div>
          );

          return node.glow ? (
            <GlowEffect key={i} color={nodeColor} intensity={0.3} pulse>
              {nodeContent}
            </GlowEffect>
          ) : (
            <React.Fragment key={i}>{nodeContent}</React.Fragment>
          );
        })}
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
