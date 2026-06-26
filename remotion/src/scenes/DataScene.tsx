import React from 'react';
import { SceneWrapper } from './SceneWrapper';
import { AnimatedText } from '../components/AnimatedText';
import { BarChart, AnimatedCounter } from '../components/DataChart';
import { FONT_SIZE, FONT_WEIGHT } from '../styles/typography';
import { SceneComponentProps } from './types';

/**
 * DataScene — Data visualization slide.
 * Title + Animated counter/bar chart + description.
 * All visualizations are SVG (no image needed).
 */
export const DataScene: React.FC<SceneComponentProps> = ({ scene, theme, frame, fps }) => {
  const title = scene.title || '';
  const body = scene.body || '';
  const dataPoints = scene.dataPoints || [];

  const primaryDataPoint = dataPoints[0];

  return (
    <SceneWrapper
      scene={scene}
      theme={theme}
      verticalAlign="center"
      horizontalAlign="center"
      overlayOpacity={0.35}
      padding={60}
    >
      <div style={{ textAlign: 'center', width: '100%', maxWidth: 1600 }}>
        {/* Title */}
        {title && (
          <AnimatedText
            text={title}
            animation="slideUp"
            delay={0.1}
            duration={0.4}
            fontSize={FONT_SIZE.subtitle}
            fontWeight={FONT_WEIGHT.bold}
            color={theme.text}
            style={{ display: 'block', marginBottom: 40 }}
          />
        )}

        {/* Primary data point: big number */}
        {primaryDataPoint && (
          <div style={{ marginBottom: 40 }}>
            <AnimatedCounter
              value={primaryDataPoint.value}
              delay={0.3}
              duration={0.8}
              fontSize={FONT_SIZE.dataValue}
              fontWeight={FONT_WEIGHT.extrabold}
              color={theme.accent}
              unit={primaryDataPoint.unit || ''}
            />
            <AnimatedText
              text={primaryDataPoint.label}
              animation="fade"
              delay={0.5}
              duration={0.4}
              fontSize={FONT_SIZE.dataLabel}
              fontWeight={FONT_WEIGHT.medium}
              color={theme.textSecondary}
              style={{ display: 'block', marginTop: 8 }}
            />
          </div>
        )}

        {/* Bar chart */}
        {dataPoints.length > 1 && (
          <div style={{ marginTop: 20 }}>
            <BarChart
              data={dataPoints}
              theme={theme}
              delay={0.5}
              drawDuration={0.8}
            />
          </div>
        )}

        {/* Body text */}
        {body && (
          <AnimatedText
            text={body}
            animation="fade"
            delay={0.8}
            duration={0.4}
            fontSize={FONT_SIZE.body}
            fontWeight={FONT_WEIGHT.regular}
            color={theme.textSecondary}
            style={{ display: 'block', marginTop: 24 }}
          />
        )}
      </div>
    </SceneWrapper>
  );
};
