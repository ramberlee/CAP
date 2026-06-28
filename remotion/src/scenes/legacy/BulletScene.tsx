import React from 'react';
import { SceneWrapper } from '../SceneWrapper';
import { FONT_SIZE, FONT_WEIGHT } from '../../styles/typography';
import { SceneComponentProps } from '../types';
import { hexToRgba } from '../../styles/colors';

export const BulletScene: React.FC<SceneComponentProps> = ({ scene, theme }) => {
  const items = scene.items || scene.lines || [];
  const title = scene.title || '';

  return (
    <SceneWrapper
      scene={scene}
      theme={theme}
      verticalAlign="center"
      horizontalAlign="left"
      padding={100}
      overlayOpacity={0.4}
    >
      <div style={{ width: '100%', maxWidth: 1600 }}>
        {title && (
          <AnimatedText
            text={title}
            animation="slideUp"
            delay={0.1}
            duration={0.4}
            fontSize={FONT_SIZE.subtitle}
            fontWeight={FONT_WEIGHT.bold}
            color={theme.accent}
            style={{ display: 'block', marginBottom: 36 }}
          />
        )}

        {items.map((item, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              marginBottom: 14,
              background: i % 2 === 0 ? hexToRgba(theme.surface, 0.3) : 'transparent',
              borderRadius: 8,
              padding: '10px 16px',
            }}
          >
            <span
              style={{
                minWidth: 28,
                height: 28,
                borderRadius: 6,
                backgroundColor: hexToRgba(theme.accent, 0.15),
                color: theme.accent,
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 14,
                fontWeight: FONT_WEIGHT.bold,
                marginRight: 14,
                marginTop: 3,
                flexShrink: 0,
              }}
            >
              {i + 1}
            </span>
            <AnimatedText
              text={item}
              animation="slideUp"
              delay={0.3 + i * 0.15}
              duration={0.35}
              fontSize={FONT_SIZE.bullet}
              fontWeight={FONT_WEIGHT.regular}
              color={theme.text}
              lineHeight={1.6}
              style={{ display: 'block', flex: 1 }}
            />
          </div>
        ))}
      </div>
    </SceneWrapper>
  );
};
