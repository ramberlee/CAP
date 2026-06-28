import React from 'react';
import { SceneWrapper } from '../SceneWrapper';
import { AnimatedText } from '../../components/AnimatedText';
import { FONT_SIZE, FONT_WEIGHT } from '../../styles/typography';
import { SceneComponentProps } from '../types';
import { hexToRgba } from '../../styles/colors';

export const ComparisonScene: React.FC<SceneComponentProps> = ({ scene, theme }) => {
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
      overlayOpacity={0.3}
      padding={60}
    >
      <div style={{ display: 'flex', width: '100%', maxWidth: 1700, gap: 30, alignItems: 'stretch' }}>
        {/* Left panel */}
        <div style={{ flex: 1 }}>
          {leftTitle && (
            <AnimatedText
              text={leftTitle}
              animation="slideUp"
              delay={0.1}
              duration={0.4}
              fontSize={FONT_SIZE.subtitle}
              fontWeight={FONT_WEIGHT.bold}
              color={theme.textSecondary}
              style={{ display: 'block', marginBottom: 16, textAlign: 'center', letterSpacing: 2 }}
            />
          )}
          <div
            style={{
              background: hexToRgba(theme.surface, 0.5),
              borderRadius: 12,
              padding: '24px 20px',
              border: `1px solid ${theme.surfaceBorder}`,
            }}
          >
            {leftItems.map((item, i) => (
              <AnimatedText
                key={i}
                text={item}
                animation="slideUp"
                delay={0.25 + i * 0.12}
                duration={0.35}
                fontSize={FONT_SIZE.bullet}
                fontWeight={FONT_WEIGHT.regular}
                color={theme.textSecondary}
                lineHeight={1.8}
                style={{ display: 'block', paddingLeft: 12, borderLeft: `2px solid ${theme.textSecondary}44` }}
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
            width: 50,
            flexShrink: 0,
          }}
        >
          <AnimatedText
            text="VS"
            animation="fade"
            delay={0.3}
            duration={0.4}
            fontSize={26}
            fontWeight={FONT_WEIGHT.extrabold}
            color={theme.accent}
          />
        </div>

        {/* Right panel */}
        <div style={{ flex: 1 }}>
          {rightTitle && (
            <AnimatedText
              text={rightTitle}
              animation="slideUp"
              delay={0.15}
              duration={0.4}
              fontSize={FONT_SIZE.subtitle}
              fontWeight={FONT_WEIGHT.bold}
              color={theme.accent}
              style={{ display: 'block', marginBottom: 16, textAlign: 'center', letterSpacing: 2 }}
            />
          )}
          <div
            style={{
              background: hexToRgba(theme.surface, 0.5),
              borderRadius: 12,
              padding: '24px 20px',
              border: `1px solid ${hexToRgba(theme.accent, 0.3)}`,
            }}
          >
            {rightItems.map((item, i) => (
              <AnimatedText
                key={i}
                text={item}
                animation="slideUp"
                delay={0.35 + i * 0.12}
                duration={0.35}
                fontSize={FONT_SIZE.bullet}
                fontWeight={FONT_WEIGHT.medium}
                color={theme.text}
                lineHeight={1.8}
                style={{ display: 'block', paddingLeft: 12, borderLeft: `2px solid ${theme.accent}` }}
              />
            ))}
          </div>
        </div>
      </div>
    </SceneWrapper>
  );
};
