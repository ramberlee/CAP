import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
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
  const content = scene.architectureFlow ?? {
    title: scene.title ?? '',
    nodes: [],
    connections: [],
  };

  const nodes = content.nodes ?? [];
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
                    marginBottom: node.sublabel ? 4 : 0,
                  }}
                >
                  {node.label}
                </div>
                {node.sublabel && (
                  <div
                    style={{
                      fontSize: 13,
                      color: theme.textSecondary,
                    }}
                  >
                    {node.sublabel}
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
