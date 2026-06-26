import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { SceneWrapper } from './SceneWrapper';
import { AnimatedText } from '../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../styles/typography';
import { SceneComponentProps } from './types';

/**
 * HighlightScene — Emphasis slide for key stats or claims.
 * Large centered text/value with glow/pulse effect.
 * Clean background (no image) — text IS the content.
 */
export const HighlightScene: React.FC<SceneComponentProps> = ({ scene, theme, frame, fps }) => {
  const t = frame / fps;
  const highlight = scene.highlight || '';
  const highlightValue = scene.highlightValue || '';
  const body = scene.body || '';

  // Pulsing glow
  const pulse = 1 + 0.04 * Math.sin(t * Math.PI * 2);
  const glowIntensity = 0.3 + 0.15 * Math.sin(t * Math.PI * 1.5);

  return (
    <SceneWrapper
      scene={scene}
      theme={theme}
      verticalAlign="center"
      horizontalAlign="center"
      overlayOpacity={0}
      padding={80}
    >
      <div style={{ textAlign: 'center', maxWidth: 1600 }}>
        {/* Highlight value (big number) */}
        {highlightValue && (
          <AnimatedText
            text={highlightValue}
            animation="scaleIn"
            delay={0.3}
            duration={0.6}
            fontSize={FONT_SIZE.highlight}
            fontWeight={FONT_WEIGHT.extrabold}
            color={theme.accent}
            style={{
              display: 'block',
              lineHeight: 1.1,
              transform: `scale(${pulse})`,
              textShadow: `0 0 ${40 * glowIntensity}px ${theme.accent}${Math.floor(60 * glowIntensity).toString(16).padStart(2, '0')}`,
            }}
          />
        )}

        {/* Highlight text */}
        {highlight && (
          <AnimatedText
            text={highlight}
            animation="slideUp"
            delay={highlightValue ? 0.6 : 0.3}
            duration={0.5}
            fontSize={FONT_SIZE.title}
            fontWeight={FONT_WEIGHT.bold}
            color={theme.text}
            lineHeight={1.3}
            style={{ display: 'block', marginTop: highlightValue ? 16 : 0 }}
          />
        )}

        {/* Body text */}
        {body && (
          <AnimatedText
            text={body}
            animation="fade"
            delay={0.8}
            duration={0.4}
            fontSize={FONT_SIZE.body}
            fontWeight={FONT_WEIGHT.regular}
            color={theme.textSecondary}
            style={{ display: 'block', marginTop: 20 }}
          />
        )}
      </div>
    </SceneWrapper>
  );
};
