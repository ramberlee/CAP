import React from 'react';
import { useCurrentFrame } from 'remotion';
import { SceneWrapper } from './SceneWrapper';
import { AnimatedText } from '../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../styles/typography';
import { SceneComponentProps } from './types';

/**
 * EndingScene — Closing slide.
 * Thank you message + key takeaways summary + CTA button.
 */
export const EndingScene: React.FC<SceneComponentProps> = ({ scene, theme, frame, fps }) => {
  const items = scene.items || scene.lines || [];
  const title = scene.title || '感谢观看';
  const body = scene.body || '';
  const t = frame / fps;

  return (
    <SceneWrapper
      scene={scene}
      theme={theme}
      verticalAlign="center"
      horizontalAlign="center"
      overlayOpacity={0.5}
    >
      <div style={{ textAlign: 'center', maxWidth: 1400 }}>
        {/* Thank you */}
        <AnimatedText
          text={title}
          animation="scaleIn"
          delay={0.2}
          duration={0.5}
          fontSize={FONT_SIZE.title}
          fontWeight={FONT_WEIGHT.bold}
          color={theme.text}
          style={{ display: 'block', marginBottom: 40 }}
        />

        {/* Key takeaways */}
        {items.map((item, i) => (
          <AnimatedText
            key={i}
            text={item}
            animation="slideUp"
            delay={0.6 + i * 0.3}
            duration={0.4}
            fontSize={FONT_SIZE.body}
            fontWeight={FONT_WEIGHT.regular}
            color={theme.textSecondary}
            lineHeight={1.8}
            style={{ display: 'block' }}
          />
        ))}

        {/* Body */}
        {body && (
          <AnimatedText
            text={body}
            animation="fade"
            delay={0.8 + items.length * 0.3}
            duration={0.4}
            fontSize={FONT_SIZE.body}
            fontWeight={FONT_WEIGHT.medium}
            color={theme.accent}
            style={{ display: 'block', marginTop: 24 }}
          />
        )}

        {/* CTA Button — driven by scene.subtitle, falls back to a default */}
        {scene.subtitle && (
          <AnimatedText
            text={scene.subtitle}
            animation="scaleIn"
            delay={1.2 + items.length * 0.3}
            duration={0.5}
            fontSize={FONT_SIZE.button}
            fontWeight={FONT_WEIGHT.semibold}
            color="#FFFFFF"
            style={{
              display: 'inline-block',
              marginTop: 40,
              padding: '14px 40px',
              background: `linear-gradient(135deg, ${theme.accent}, ${theme.accentSecondary})`,
              borderRadius: 50,
              boxShadow: `0 4px 20px ${theme.accent}44`,
              letterSpacing: 2,
            }}
          />
        )}
      </div>
    </SceneWrapper>
  );
};
