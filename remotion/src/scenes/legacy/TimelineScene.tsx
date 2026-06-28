import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { SceneWrapper } from '../SceneWrapper';
import { AnimatedText } from '../../components/AnimatedText';
import { FONT_FAMILY, FONT_SIZE, FONT_WEIGHT } from '../../styles/typography';
import { SceneComponentProps } from '../types';

export const TimelineScene: React.FC<SceneComponentProps> = ({ scene, theme, frame, fps }) => {
  const title = scene.title || '';
  const items = scene.timelineItems || [];

  if (items.length <= 1) {
    const displayText = items.length === 1 ? items[0].title : (title || 'Timeline');
    return (
      <SceneWrapper scene={scene} theme={theme} verticalAlign="center" horizontalAlign="center">
        <AnimatedText text={displayText} animation="fade" fontSize={FONT_SIZE.title} fontWeight={FONT_WEIGHT.bold} color={theme.text} />
      </SceneWrapper>
    );
  }

  const t = frame / fps;
  const totalWidth = 1400;
  const startX = (1920 - totalWidth) / 2;
  const nodeSpacing = totalWidth / (items.length - 1);
  const lineY = 320;

  const lineDrawDelay = 0.3;
  const lineDrawDuration = 0.8;
  const lineProgress = Math.min(Math.max((t - lineDrawDelay) / lineDrawDuration, 0), 1);
  const lineEndX = startX + lineProgress * totalWidth;

  return (
    <SceneWrapper
      scene={scene}
      theme={theme}
      verticalAlign="top"
      horizontalAlign="center"
      overlayOpacity={0.3}
      padding={80}
    >
      <div style={{ textAlign: 'center', width: '100%' }}>
        {title && (
          <AnimatedText
            text={title}
            animation="slideUp"
            delay={0.1}
            duration={0.4}
            fontSize={FONT_SIZE.subtitle}
            fontWeight={FONT_WEIGHT.bold}
            color={theme.text}
            style={{ display: 'block', marginBottom: 50 }}
          />
        )}

        <svg width="1920" height={380} style={{ overflow: 'visible' }}>
          <line
            x1={startX}
            y1={lineY}
            x2={Math.max(lineEndX, startX)}
            y2={lineY}
            stroke={theme.accent}
            strokeWidth={3}
            strokeLinecap="round"
          />

          {items.map((item, i) => {
            const x = startX + i * nodeSpacing;
            const nodeDelay = 0.4 + i * 0.2;
            const nodeProgress = Math.min(Math.max((t - nodeDelay) / 0.35, 0), 1);
            const nodeOpacity = interpolate(nodeProgress, [0, 0.5], [0, 1]);
            const nodeScale = interpolate(nodeProgress, [0, 1], [0.5, 1]);
            const isActive = i === Math.min(Math.max(Math.floor((t - 0.4) / 0.2), 0), items.length - 1);

            return (
              <g key={i} opacity={nodeOpacity}>
                <circle
                  cx={x}
                  cy={lineY}
                  r={isActive ? 10 : 7}
                  fill={isActive ? theme.accent : theme.background}
                  stroke={theme.accent}
                  strokeWidth={2.5}
                  style={{ transform: `scale(${nodeScale})`, transformOrigin: `${x}px ${lineY}px` }}
                />

                <text
                  x={x}
                  y={lineY - 24}
                  textAnchor="middle"
                  fill={theme.textSecondary}
                  fontFamily={FONT_FAMILY}
                  fontSize={FONT_SIZE.timeline}
                  fontWeight={FONT_WEIGHT.medium}
                >
                  {item.date}
                </text>

                <text
                  x={x}
                  y={lineY + 34}
                  textAnchor="middle"
                  fill={isActive ? theme.accent : theme.text}
                  fontFamily={FONT_FAMILY}
                  fontSize={FONT_SIZE.timeline}
                  fontWeight={isActive ? FONT_WEIGHT.semibold : FONT_WEIGHT.regular}
                >
                  {item.title}
                </text>

                {item.description && (
                  <text
                    x={x}
                    y={lineY + 54}
                    textAnchor="middle"
                    fill={theme.textSecondary}
                    fontFamily={FONT_FAMILY}
                    fontSize={13}
                  >
                    {item.description}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>
    </SceneWrapper>
  );
};
