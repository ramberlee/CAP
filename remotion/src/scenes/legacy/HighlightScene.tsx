import React from 'react';
import { SceneWrapper } from '../SceneWrapper';
import { AnimatedText } from '../../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../../styles/typography';
import { SceneComponentProps } from '../types';
import { hexToRgba } from '../../styles/colors';

export const HighlightScene: React.FC<SceneComponentProps> = ({ scene, theme }) => {
  // Handle highlight as either string or {text, subtext} object from LLM plans
  const rawHighlight = scene.highlight;
  let highlight = '';
  let subtext = '';
  if (typeof rawHighlight === 'string') {
    highlight = rawHighlight;
  } else if (rawHighlight && typeof rawHighlight === 'object') {
    highlight = (rawHighlight as any).text || '';
    subtext = (rawHighlight as any).subtext || '';
  }
  const highlightValue = scene.highlightValue || '';
  const body = scene.body || subtext;

  return (
    <SceneWrapper
      scene={scene}
      theme={theme}
      verticalAlign="center"
      horizontalAlign="center"
      overlayOpacity={0}
      padding={80}
    >
      <div
        style={{
          textAlign: 'center',
          maxWidth: 1400,
          background: hexToRgba(theme.surface, 0.4),
          borderRadius: 20,
          padding: '50px 60px',
          border: `1px solid ${theme.surfaceBorder}`,
        }}
      >
        {highlightValue && (
          <AnimatedText
            text={highlightValue}
            animation="slideUp"
            delay={0.2}
            duration={0.5}
            fontSize={FONT_SIZE.highlight}
            fontWeight={FONT_WEIGHT.extrabold}
            color={theme.accent}
            style={{ display: 'block', lineHeight: 1.1 }}
          />
        )}

        {highlight && (
          <AnimatedText
            text={highlight}
            animation="slideUp"
            delay={highlightValue ? 0.4 : 0.2}
            duration={0.5}
            fontSize={FONT_SIZE.title}
            fontWeight={FONT_WEIGHT.bold}
            color={theme.text}
            lineHeight={1.3}
            style={{ display: 'block', marginTop: highlightValue ? 12 : 0 }}
          />
        )}

        {body && (
          <AnimatedText
            text={body}
            animation="fade"
            delay={0.6}
            duration={0.4}
            fontSize={FONT_SIZE.body}
            fontWeight={FONT_WEIGHT.regular}
            color={theme.textSecondary}
            style={{ display: 'block', marginTop: 16 }}
          />
        )}
      </div>
    </SceneWrapper>
  );
};
