import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { SceneWrapper } from '../SceneWrapper';
import { AnimatedText } from '../../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../../styles/typography';
import { SceneComponentProps } from '../types';

export const ImageCaptionScene: React.FC<SceneComponentProps> = ({ scene, theme }) => {
  const frame = useCurrentFrame();
  const title = scene.title || '';
  const body = scene.body || '';
  const lines = scene.lines || [];
  const hasImage = !!scene.imageUrl;
  const t = frame / 30;

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
          display: 'flex',
          width: '100%',
          maxWidth: 1700,
          gap: 50,
          alignItems: 'center',
        }}
      >
        {hasImage && (
          <div
            style={{
              flex: '0 0 560px',
              height: 420,
              borderRadius: 12,
              overflow: 'hidden',
              boxShadow: `0 6px 24px rgba(0,0,0,0.25)`,
            }}
          >
            <img
              src={scene.imageUrl!}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                transform: `scale(${interpolate(t, [0, 3], [1.0, 1.03])})`,
              }}
            />
          </div>
        )}

        <div style={{ flex: 1 }}>
          {title && (
            <AnimatedText
              text={title}
              animation="slideUp"
              delay={0.2}
              duration={0.4}
              fontSize={FONT_SIZE.subtitle}
              fontWeight={FONT_WEIGHT.bold}
              color={theme.text}
              style={{ display: 'block', marginBottom: 14 }}
            />
          )}

          {body && (
            <AnimatedText
              text={body}
              animation="slideUp"
              delay={0.35}
              duration={0.4}
              fontSize={FONT_SIZE.body}
              fontWeight={FONT_WEIGHT.regular}
              color={theme.textSecondary}
              lineHeight={1.7}
              style={{ display: 'block' }}
            />
          )}

          {lines.map((line, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                marginTop: 8,
              }}
            >
              <div
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  backgroundColor: theme.accent,
                  flexShrink: 0,
                }}
              />
              <AnimatedText
                text={line}
                animation="slideUp"
                delay={0.4 + i * 0.12}
                duration={0.3}
                fontSize={FONT_SIZE.body}
                fontWeight={FONT_WEIGHT.regular}
                color={theme.textSecondary}
                lineHeight={1.6}
                style={{ display: 'block' }}
              />
            </div>
          ))}
        </div>
      </div>
    </SceneWrapper>
  );
};
