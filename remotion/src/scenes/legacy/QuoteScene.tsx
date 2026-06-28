import React from 'react';
import { SceneWrapper } from '../SceneWrapper';
import { AnimatedText } from '../../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../../styles/typography';
import { SceneComponentProps } from '../types';

export const QuoteScene: React.FC<SceneComponentProps> = ({ scene, theme }) => {
  const quote = scene.quote || '';
  const author = scene.quoteAuthor || '';

  return (
    <SceneWrapper
      scene={scene}
      theme={theme}
      verticalAlign="center"
      horizontalAlign="left"
      padding={140}
      blur={4}
      overlayOpacity={0.55}
    >
      <div
        style={{
          maxWidth: 1500,
          paddingLeft: 28,
          borderLeft: `4px solid ${theme.accent}`,
        }}
      >
        {quote && (
          <AnimatedText
            text={quote}
            animation="slideUp"
            delay={0.2}
            duration={0.5}
            fontSize={FONT_SIZE.quote}
            fontWeight={FONT_WEIGHT.medium}
            color={theme.text}
            lineHeight={1.6}
            style={{ display: 'block', marginBottom: 20 }}
          />
        )}

        {author && (
          <AnimatedText
            text={`— ${author}`}
            animation="fade"
            delay={0.6}
            duration={0.4}
            fontSize={FONT_SIZE.quoteAuthor}
            fontWeight={FONT_WEIGHT.regular}
            color={theme.textSecondary}
            style={{ display: 'block', textAlign: 'right', marginTop: 12 }}
          />
        )}
      </div>
    </SceneWrapper>
  );
};
