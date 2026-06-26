import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { SceneWrapper } from './SceneWrapper';
import { AnimatedText } from '../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../styles/typography';
import { SceneComponentProps } from './types';

/**
 * SectionTitleScene — Chapter divider slide.
 * Clean background (no image), large centered section title,
 * subtitle section number, and progress dots.
 */
export const SectionTitleScene: React.FC<SceneComponentProps> = ({ scene, theme, frame, fps }) => {
  const title = scene.title || '';
  const subtitle = scene.subtitle || '';

  return (
    <SceneWrapper
      scene={scene}
      theme={theme}
      verticalAlign="center"
      horizontalAlign="center"
      overlayOpacity={0}
      padding={80}
    >
      <div style={{ textAlign: 'center', maxWidth: 1400 }}>
        {/* Section number / subtitle */}
        {subtitle && (
          <AnimatedText
            text={subtitle}
            animation="fade"
            delay={0.2}
            duration={0.4}
            fontSize={FONT_SIZE.caption}
            fontWeight={FONT_WEIGHT.medium}
            color={theme.textSecondary}
            letterSpacing={6}
            style={{
              display: 'block',
              marginBottom: 16,
              textTransform: 'uppercase',
            }}
          />
        )}

        {/* Title */}
        <AnimatedText
          text={title}
          animation="slideUp"
          delay={0.4}
          duration={0.6}
          fontSize={FONT_SIZE.sectionTitle}
          fontWeight={FONT_WEIGHT.bold}
          color={theme.text}
          letterSpacing={4}
          style={{ display: 'block', lineHeight: 1.3 }}
        />

        {/* Decorative bottom line */}
        <div
          style={{
            height: 2,
            width: 80,
            background: `linear-gradient(90deg, ${theme.accent}, transparent)`,
            margin: '30px auto 0',
            borderRadius: 1,
          }}
        />
      </div>
    </SceneWrapper>
  );
};
