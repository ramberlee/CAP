import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { SceneWrapper } from './SceneWrapper';
import { AnimatedText } from '../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../styles/typography';
import { SceneComponentProps } from './types';

/**
 * TitleScene — Opening cover slide.
 * Large centered title + subtitle + decorative line + tag.
 * Background image (if available) with Ken Burns effect.
 */
export const TitleScene: React.FC<SceneComponentProps> = ({ scene, theme }) => {
  const frame = useCurrentFrame();

  const titleLines = (scene.title || '').split('\n').filter(Boolean);
  const tag = scene.subtitle || '';

  // Decorative line expand from center
  const lineProgress = interpolate(frame, [15, 35], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const lineWidth = interpolate(lineProgress, [0, 1], [0, 200]);

  return (
    <SceneWrapper
      scene={scene}
      theme={theme}
      verticalAlign="center"
      horizontalAlign="center"
      overlayOpacity={0.55}
    >
      <div style={{ textAlign: 'center', maxWidth: 1600 }}>
        {titleLines.map((line, i) => (
          <AnimatedText
            key={i}
            text={line}
            animation="scaleIn"
            delay={0.3 + i * 0.25}
            duration={0.6}
            fontSize={FONT_SIZE.title + (i === 0 ? 8 : 0)}
            fontWeight={i === 0 ? FONT_WEIGHT.bold : FONT_WEIGHT.medium}
            color={i === 0 ? theme.text : theme.textSecondary}
            lineHeight={1.3}
            letterSpacing={i === 0 ? 2 : 0}
            style={{ display: 'block' }}
          />
        ))}

        {/* Decorative line */}
        <div
          style={{
            height: 3,
            width: lineWidth,
            background: `linear-gradient(90deg, transparent, ${theme.accent}, transparent)`,
            margin: '30px auto',
            borderRadius: 2,
          }}
        />

        {/* Tag / subtitle */}
        {tag && (
          <AnimatedText
            text={tag}
            animation="slideUp"
            delay={0.8}
            duration={0.4}
            fontSize={FONT_SIZE.caption}
            fontWeight={FONT_WEIGHT.regular}
            color={theme.textSecondary}
            letterSpacing={4}
            style={{ display: 'block', marginTop: 8, textTransform: 'uppercase' }}
          />
        )}
      </div>
    </SceneWrapper>
  );
};
