import React from 'react';
import { SceneWrapper } from '../SceneWrapper';
import { AnimatedText } from '../../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../../styles/typography';
import { SceneComponentProps } from '../types';
import { hexToRgba } from '../../styles/colors';

export const EndingScene: React.FC<SceneComponentProps> = ({ scene, theme }) => {
  const items = scene.items || scene.lines || [];
  const title = scene.title || '感谢观看';
  const body = scene.body || '';

  return (
    <SceneWrapper
      scene={scene}
      theme={theme}
      verticalAlign="center"
      horizontalAlign="center"
      overlayOpacity={0.4}
    >
      <div style={{ textAlign: 'center', maxWidth: 1400 }}>
        <AnimatedText
          text={title}
          animation="slideUp"
          delay={0.15}
          duration={0.5}
          fontSize={FONT_SIZE.title}
          fontWeight={FONT_WEIGHT.bold}
          color={theme.text}
          style={{ display: 'block', marginBottom: 32 }}
        />

        <div
          style={{
            background: hexToRgba(theme.surface, 0.4),
            borderRadius: 16,
            padding: '28px 36px',
            border: `1px solid ${theme.surfaceBorder}`,
            textAlign: 'left',
            maxWidth: 900,
            margin: '0 auto 28px',
          }}
        >
          {items.map((item, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                marginBottom: i < items.length - 1 ? 10 : 0,
              }}
            >
              <span style={{ color: theme.accent, fontSize: 18, fontWeight: 700 }}>✓</span>
              <AnimatedText
                text={item}
                animation="slideUp"
                delay={0.4 + i * 0.15}
                duration={0.35}
                fontSize={FONT_SIZE.body}
                fontWeight={FONT_WEIGHT.regular}
                color={theme.text}
                lineHeight={1.7}
                style={{ display: 'block' }}
              />
            </div>
          ))}
        </div>

        {body && (
          <AnimatedText
            text={body}
            animation="fade"
            delay={0.6 + items.length * 0.15}
            duration={0.4}
            fontSize={FONT_SIZE.body}
            fontWeight={FONT_WEIGHT.medium}
            color={theme.textSecondary}
            style={{ display: 'block' }}
          />
        )}

        {scene.subtitle && (
          <AnimatedText
            text={scene.subtitle}
            animation="slideUp"
            delay={0.8 + items.length * 0.15}
            duration={0.4}
            fontSize={FONT_SIZE.button}
            fontWeight={FONT_WEIGHT.semibold}
            color="#FFFFFF"
            style={{
              display: 'inline-block',
              marginTop: 32,
              padding: '12px 36px',
              background: `linear-gradient(135deg, ${theme.accent}, ${theme.accentSecondary})`,
              borderRadius: 40,
              letterSpacing: 2,
            }}
          />
        )}
      </div>
    </SceneWrapper>
  );
};
