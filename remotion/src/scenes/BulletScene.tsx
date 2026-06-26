import React from 'react';
import { useCurrentFrame } from 'remotion';
import { SceneWrapper } from './SceneWrapper';
import { AnimatedText } from '../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../styles/typography';
import { SceneComponentProps } from './types';

/**
 * BulletScene — Key points list slide.
 * Title at top-left + bullet points that fly in from right one by one.
 * Current point is highlighted to sync with narration.
 */
export const BulletScene: React.FC<SceneComponentProps> = ({ scene, theme, frame, fps }) => {
  const items = scene.items || scene.lines || [];
  const title = scene.title || '';
  const staggerDelay = 0.3;
  const itemInterval = 0.35;

  // Determine which item is currently "active" based on elapsed time
  const elapsed = frame / fps;
  const activeIndex = Math.min(
    Math.floor((elapsed - staggerDelay) / itemInterval),
    items.length - 1
  );

  return (
    <SceneWrapper
      scene={scene}
      theme={theme}
      verticalAlign="center"
      horizontalAlign="left"
      padding={120}
      overlayOpacity={0.45}
    >
      <div style={{ width: '100%', maxWidth: 1600 }}>
        {/* Title */}
        {title && (
          <AnimatedText
            text={title}
            animation="slideUp"
            delay={0.1}
            duration={0.4}
            fontSize={FONT_SIZE.subtitle}
            fontWeight={FONT_WEIGHT.bold}
            color={theme.accent}
            style={{ display: 'block', marginBottom: 40 }}
          />
        )}

        {/* Bullet points */}
        {items.map((item, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              marginBottom: 20,
            }}
          >
            <AnimatedText
              text={item}
              animation="slideRight"
              delay={staggerDelay + i * itemInterval}
              duration={0.4}
              fontSize={FONT_SIZE.bullet}
              fontWeight={
                i === activeIndex
                  ? FONT_WEIGHT.semibold
                  : FONT_WEIGHT.regular
              }
              color={
                i === activeIndex
                  ? theme.accent
                  : theme.text
              }
              lineHeight={1.6}
              style={{
                display: 'block',
                paddingLeft: 36,
                borderLeft: i === activeIndex
                  ? `3px solid ${theme.accent}`
                  : `3px solid ${theme.textSecondary}44`,
                textShadow: i === activeIndex
                  ? `0 0 30px ${theme.accent}33`
                  : 'none',
              }}
            />
          </div>
        ))}
      </div>
    </SceneWrapper>
  );
};
