import React from 'react';
import { Img, interpolate, useCurrentFrame } from 'remotion';
import { SceneWrapper } from './SceneWrapper';
import { AnimatedText } from '../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../styles/typography';
import { SceneComponentProps } from './types';

/**
 * ImageCaptionScene — Image + text side-by-side slide.
 * Image on left (40%) with rounded corners, text on right (60%).
 * If no image, falls back to full-width text layout.
 */
export const ImageCaptionScene: React.FC<SceneComponentProps> = ({ scene, theme, frame, fps }) => {
  const title = scene.title || '';
  const body = scene.body || '';
  const lines = scene.lines || [];
  const hasImage = !!scene.imageUrl;
  const t = frame / fps;

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
        {/* Image side (40%) */}
        {hasImage && (
          <div
            style={{
              flex: '0 0 600px',
              height: 450,
              borderRadius: 16,
              overflow: 'hidden',
              boxShadow: `0 8px 32px rgba(0,0,0,0.3)`,
            }}
          >
            <Img
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

        {/* Text side */}
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
              style={{ display: 'block', marginBottom: 16 }}
            />
          )}

          {body && (
            <AnimatedText
              text={body}
              animation="slideUp"
              delay={0.4}
              duration={0.4}
              fontSize={FONT_SIZE.body}
              fontWeight={FONT_WEIGHT.regular}
              color={theme.textSecondary}
              lineHeight={1.7}
              style={{ display: 'block' }}
            />
          )}

          {lines.map((line, i) => (
            <AnimatedText
              key={i}
              text={line}
              animation="slideUp"
              delay={0.4 + i * 0.2}
              duration={0.3}
              fontSize={FONT_SIZE.body}
              fontWeight={FONT_WEIGHT.regular}
              color={theme.textSecondary}
              lineHeight={1.7}
              style={{ display: 'block' }}
            />
          ))}
        </div>
      </div>
    </SceneWrapper>
  );
};
