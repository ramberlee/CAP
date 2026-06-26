import React from 'react';
import { SceneWrapper } from './SceneWrapper';
import { TypewriterText } from '../components/AnimatedText';
import { AnimatedText } from '../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../styles/typography';
import { SceneComponentProps } from './types';

/**
 * QuoteScene — Quote highlight slide.
 * Large quote text with left accent bar + blurred background image + author attribution.
 * Quote appears character by character (typewriter effect).
 */
export const QuoteScene: React.FC<SceneComponentProps> = ({ scene, theme, frame, fps }) => {
  const quote = scene.quote || '';
  const author = scene.quoteAuthor || '';

  return (
    <SceneWrapper
      scene={scene}
      theme={theme}
      verticalAlign="center"
      horizontalAlign="left"
      padding={140}
      blur={6}
      overlayOpacity={0.6}
    >
      <div
        style={{
          maxWidth: 1500,
          paddingLeft: 30,
          borderLeft: `4px solid ${theme.accent}`,
        }}
      >
        {/* Quote text — typewriter */}
        {quote && (
          <div style={{ marginBottom: 24 }}>
            <TypewriterText
              text={quote}
              fontSize={FONT_SIZE.quote}
              fontWeight={FONT_WEIGHT.medium}
              color={theme.text}
              delay={0.3}
              speed={10}
            />
          </div>
        )}

        {/* Author */}
        {author && (
          <AnimatedText
            text={`— ${author}`}
            animation="fade"
            delay={1.5}
            duration={0.5}
            fontSize={FONT_SIZE.quoteAuthor}
            fontWeight={FONT_WEIGHT.regular}
            color={theme.textSecondary}
            style={{ display: 'block', textAlign: 'right', marginTop: 16 }}
          />
        )}
      </div>
    </SceneWrapper>
  );
};
