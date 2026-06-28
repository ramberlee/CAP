import React from 'react';
import { SceneWrapper } from '../SceneWrapper';
import { AnimatedText } from '../../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../../styles/typography';
import { SceneComponentProps } from '../types';

export const SectionTitleScene: React.FC<SceneComponentProps> = ({ scene, theme }) => {
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
        {subtitle && (
          <AnimatedText
            text={subtitle}
            animation="fade"
            delay={0.15}
            duration={0.4}
            fontSize={FONT_SIZE.caption}
            fontWeight={FONT_WEIGHT.medium}
            color={theme.textSecondary}
            letterSpacing={6}
            style={{ display: 'block', marginBottom: 14, textTransform: 'uppercase' }}
          />
        )}

        <AnimatedText
          text={title}
          animation="slideUp"
          delay={0.35}
          duration={0.5}
          fontSize={FONT_SIZE.sectionTitle}
          fontWeight={FONT_WEIGHT.bold}
          color={theme.text}
          letterSpacing={4}
          style={{ display: 'block', lineHeight: 1.3 }}
        />

        <div
          style={{
            height: 2,
            width: 60,
            background: `linear-gradient(90deg, ${theme.accent}, transparent)`,
            margin: '24px auto 0',
            borderRadius: 1,
          }}
        />
      </div>
    </SceneWrapper>
  );
};
