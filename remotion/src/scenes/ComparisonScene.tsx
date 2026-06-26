import React from 'react';
import { SceneWrapper } from './SceneWrapper';
import { AnimatedText } from '../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../styles/typography';
import { SceneComponentProps } from './types';
import { hexToRgba } from '../styles/colors';

/**
 * ComparisonScene — Side-by-side comparison slide.
 * Left panel (old/before) vs Right panel (new/after) with VS divider.
 */
export const ComparisonScene: React.FC<SceneComponentProps> = ({ scene, theme, frame, fps }) => {
  const leftTitle = scene.leftTitle || '';
  const rightTitle = scene.rightTitle || '';
  const leftItems = scene.leftItems || [];
  const rightItems = scene.rightItems || [];

  return (
    <SceneWrapper
      scene={scene}
      theme={theme}
      verticalAlign="center"
      horizontalAlign="center"
      overlayOpacity={0.4}
      padding={60}
    >
      <div style={{ display: 'flex', width: '100%', maxWidth: 1700, gap: 40, alignItems: 'stretch' }}>
        {/* Left panel */}
        <div style={{ flex: 1 }}>
          {leftTitle && (
            <AnimatedText
              text={leftTitle}
              animation="slideRight"
              delay={0.15}
              duration={0.4}
              fontSize={FONT_SIZE.subtitle}
              fontWeight={FONT_WEIGHT.bold}
              color={theme.textSecondary}
              style={{
                display: 'block',
                marginBottom: 20,
                textAlign: 'center',
                textTransform: 'uppercase',
                letterSpacing: 3,
              }}
            />
          )}
          <div
            style={{
              background: hexToRgba(theme.surface, 0.6),
              borderRadius: 16,
              padding: '30px 24px',
              border: `1px solid ${theme.surfaceBorder}`,
            }}
          >
            {leftItems.map((item, i) => (
              <AnimatedText
                key={i}
                text={item}
                animation="slideRight"
                delay={0.3 + i * 0.2}
                duration={0.4}
                fontSize={FONT_SIZE.bullet}
                fontWeight={FONT_WEIGHT.regular}
                color={theme.textSecondary}
                lineHeight={1.8}
                style={{ display: 'block', paddingLeft: 16, borderLeft: `2px solid ${theme.textSecondary}44` }}
              />
            ))}
          </div>
        </div>

        {/* VS divider */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 60,
            flexShrink: 0,
          }}
        >
          <AnimatedText
            text="VS"
            animation="scaleIn"
            delay={0.3}
            duration={0.5}
            fontSize={28}
            fontWeight={FONT_WEIGHT.extrabold}
            color={theme.accent}
          />
        </div>

        {/* Right panel */}
        <div style={{ flex: 1 }}>
          {rightTitle && (
            <AnimatedText
              text={rightTitle}
              animation="slideRight"
              delay={0.35}
              duration={0.4}
              fontSize={FONT_SIZE.subtitle}
              fontWeight={FONT_WEIGHT.bold}
              color={theme.accent}
              style={{
                display: 'block',
                marginBottom: 20,
                textAlign: 'center',
                textTransform: 'uppercase',
                letterSpacing: 3,
              }}
            />
          )}
          <div
            style={{
              background: hexToRgba(theme.surface, 0.6),
              borderRadius: 16,
              padding: '30px 24px',
              border: `1px solid ${theme.accent}44`,
              boxShadow: `0 0 30px ${theme.accent}22`,
            }}
          >
            {rightItems.map((item, i) => (
              <AnimatedText
                key={i}
                text={item}
                animation="slideRight"
                delay={0.5 + i * 0.2}
                duration={0.4}
                fontSize={FONT_SIZE.bullet}
                fontWeight={FONT_WEIGHT.medium}
                color={theme.text}
                lineHeight={1.8}
                style={{ display: 'block', paddingLeft: 16, borderLeft: `2px solid ${theme.accent}` }}
              />
            ))}
          </div>
        </div>
      </div>
    </SceneWrapper>
  );
};
