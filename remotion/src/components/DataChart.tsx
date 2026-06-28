import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { FONT_FAMILY, FONT_SIZE, FONT_WEIGHT } from '../styles/typography';
import { ThemePalette } from '../themes';
import { DataPoint } from '../types';

interface BarChartProps {
  data: DataPoint[];
  theme: ThemePalette;
  /** Delay in seconds before chart starts drawing */
  delay?: number;
  /** Duration of draw animation in seconds */
  drawDuration?: number;
  /** Max bar width in px */
  barWidth?: number;
  /** Bar height in px */
  barHeight?: number;
  /** Gap between bars in px */
  barGap?: number;
}

/**
 * SVG bar chart with draw animation.
 * Each bar rises from bottom sequentially.
 */
export const BarChart: React.FC<BarChartProps> = ({
  data,
  theme,
  delay = 0,
  drawDuration = 0.8,
  barWidth = 180,
  barHeight = 280,
  barGap = 40,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Only treat numeric values as bar magnitudes. String values (e.g. "自动",
  // "智能") are rendered as text labels above zero-height bars so the chart
  // doesn't end up showing NaN.
  const numericValues = data
    .map((d) => Number(d.value))
    .filter((v) => Number.isFinite(v));
  const maxValue = numericValues.length > 0 ? Math.max(...numericValues, 1) : 1;
  const totalWidth = data.length * (barWidth + barGap) - barGap;
  const startX = (1920 - totalWidth) / 2;

  return (
    <svg width="1920" height={barHeight + 80} style={{ overflow: 'visible' }}>
      {data.map((point, i) => {
        const t = Math.max(0, frame / fps - delay - i * 0.15);
        const progress = Math.min(t / drawDuration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const numeric = Number(point.value);
        const ratio = Number.isFinite(numeric) ? numeric / maxValue : 0;
        // Non-numeric values still get a small visible bar so the row doesn't
        // collapse to nothing — it reads as a "data row" even when the LLM
        // returns descriptive strings.
        const barH = easeOut * (ratio > 0 ? ratio : 0.35) * barHeight;
        const x = startX + i * (barWidth + barGap);
        const y = barHeight - barH;
        const color = point.color || theme.accent;

        return (
          <g key={i}>
            {/* Bar */}
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={Math.max(barH, 1)}
              rx={6}
              fill={color}
              opacity={easeOut}
            />
            {/* Value label on top */}
            <text
              x={x + barWidth / 2}
              y={y - 12}
              textAnchor="middle"
              fill={theme.text}
              fontFamily={FONT_FAMILY}
              fontSize={FONT_SIZE.dataLabel}
              fontWeight={FONT_WEIGHT.bold}
              opacity={easeOut}
            >
              {point.value}{point.unit || ''}
            </text>
            {/* Label below */}
            <text
              x={x + barWidth / 2}
              y={barHeight + 30}
              textAnchor="middle"
              fill={theme.textSecondary}
              fontFamily={FONT_FAMILY}
              fontSize={FONT_SIZE.small}
              opacity={easeOut}
            >
              {point.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
};

interface PieChartProps {
  data: DataPoint[];
  theme: ThemePalette;
  delay?: number;
  drawDuration?: number;
  size?: number;
}

/**
 * SVG donut/pie chart with draw animation.
 */
export const PieChart: React.FC<PieChartProps> = ({
  data,
  theme,
  delay = 0,
  drawDuration = 0.8,
  size = 300,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const total = data.reduce((sum, d) => sum + d.value, 0);
  if (total === 0) return null;

  const cx = 960;
  const cy = size / 2 + 40;
  const r = size / 2 - 20;
  const colors = data.map((d) => d.color || theme.accent);

  // Calculate segments
  let currentAngle = -Math.PI / 2;
  const segments = data.map((d, i) => {
    const angle = (d.value / total) * Math.PI * 2;
    const startAngle = currentAngle;
    currentAngle += angle;
    return { startAngle, endAngle: currentAngle, color: colors[i % colors.length], label: d.label, value: d.value };
  });

  return (
    <svg width="1920" height={size + 80} style={{ overflow: 'visible' }}>
      {segments.map((seg, i) => {
        const t = Math.max(0, frame / fps - delay - i * 0.1);
        const progress = Math.min(t / drawDuration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const endAngle = seg.startAngle + (seg.endAngle - seg.startAngle) * easeOut;

        // Arc path
        const x1 = cx + r * Math.cos(seg.startAngle);
        const y1 = cy + r * Math.sin(seg.startAngle);
        const x2 = cx + r * Math.cos(endAngle);
        const y2 = cy + r * Math.sin(endAngle);
        const largeArc = endAngle - seg.startAngle > Math.PI ? 1 : 0;

        const path = `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`;

        return (
          <g key={i} opacity={easeOut}>
            <path d={path} fill={seg.color} stroke={theme.background} strokeWidth={2} />
            {/* Label */}
            {(seg.endAngle - seg.startAngle) / (Math.PI * 2) > 0.08 && (
              <text
                x={cx + (r * 0.65) * Math.cos(seg.startAngle + (seg.endAngle - seg.startAngle) / 2)}
                y={cy + (r * 0.65) * Math.sin(seg.startAngle + (seg.endAngle - seg.startAngle) / 2)}
                textAnchor="middle"
                dominantBaseline="central"
                fill="#FFFFFF"
                fontFamily={FONT_FAMILY}
                fontSize="14"
                fontWeight={FONT_WEIGHT.bold}
              >
                {Math.round((seg.value / total) * 100)}%
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
};

/**
 * Animated counter that rolls from 0 to target value.
 */
export const AnimatedCounter: React.FC<{
  value: number;
  delay?: number;
  duration?: number;
  fontSize?: number;
  fontWeight?: number;
  color?: string;
  unit?: string;
  prefix?: string;
}> = ({
  value,
  delay = 0,
  duration = 1.0,
  fontSize = 72,
  fontWeight = 800,
  color = '#FFFFFF',
  unit = '',
  prefix = '',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const t = Math.max(0, frame / fps - delay);
  const progress = Math.min(t / duration, 1);
  const easeOut = 1 - Math.pow(1 - progress, 3);
  // If value isn't a finite number (e.g. the LLM returned "自动"), fall back
  // to plain text instead of producing NaN.
  const numericValue = Number(value);
  const isNumeric = Number.isFinite(numericValue);
  const displayValue = isNumeric ? Math.round(easeOut * numericValue) : 0;
  const isComplete = progress >= 1;

  return (
    <span
      style={{
        fontSize,
        fontWeight,
        color,
        fontFamily: FONT_FAMILY,
        letterSpacing: 2,
        display: 'inline-block',
        transform: isComplete ? 'none' : undefined,
        textShadow: isComplete ? `0 0 20px ${color}44` : undefined,
      }}
    >
      {prefix}{isNumeric ? displayValue.toLocaleString() : String(value)}{unit}
    </span>
  );
};
