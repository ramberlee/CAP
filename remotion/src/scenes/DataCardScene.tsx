import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";
import { computeStyle } from "../components/VisualInterpreter";

interface DataCardSceneProps {
  theme: ThemePalette;
  duration: number;
  animation?: AnimationStyle;
  icon?: string;
  visualStyle?: string;
  mood?: string;
  layoutHint?: string;
  imagePath?: string;
  /** Label shown above the number */
  visual_label?: string;
  /** Numeric value to animate from 0 */
  visual_value?: number;
  /** Unit text (e.g. "倍", "%", "万") */
  visual_unit?: string;
  /** Trend direction */
  visual_trend?: "up" | "down" | "flat";
}

const DataCardScene: React.FC<DataCardSceneProps> = ({
  theme, duration, icon, animation = "scale_in",
  visualStyle, mood, layoutHint, imagePath,
  visual_label, visual_value, visual_unit, visual_trend,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const cs = computeStyle(visualStyle, mood, layoutHint, theme);
  const accent = cs.accentOverride || theme.accent;

  // Animate number from 0 → target over first 60% of duration
  const countDuration = duration * 0.6;
  const countProgress = Math.min(1, Math.max(0, t / Math.max(countDuration, 0.5)));
  // Ease-out cubic
  const eased = 1 - Math.pow(1 - countProgress, 3);
  const displayValue = visual_value != null
    ? (visual_value > 100 ? Math.round(eased * visual_value).toLocaleString() : Math.round(eased * visual_value * 10) / 10)
    : 0;

  // Scale entrance
  const entranceScale = Math.min(1, (t / 0.4));

  // Trend arrow
  const trendArrow = visual_trend === "up" ? "↑" : visual_trend === "down" ? "↓" : "→";
  const trendColor = visual_trend === "up" ? "#4ade80" : visual_trend === "down" ? "#f87171" : theme.textSecondary;

  // Pulse on completion
  const pulse = 1 + (countProgress >= 0.95 ? 0.03 * Math.sin((t - countDuration) * Math.PI * 6) : 0);

  return (
    <SceneWrapper
      theme={theme} animation={animation} icon={icon}
      visualStyle={visualStyle} mood={mood} layoutHint={layoutHint}
      imagePath={imagePath}
    >
      <div style={{
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        width: "100%", height: "100%", gap: 16, padding: 40,
        transform: `scale(${entranceScale * 0.7 + 0.3})`,
      }}>
        {icon && (
          <div style={{
            fontSize: 80, marginBottom: 10,
            filter: `drop-shadow(0 0 ${cs.glowIntensity * 30}px ${accent}40)`,
            transform: `translateY(${(1 - Math.min(1, t * 3)) * -20}px)`,
          }}>{icon}</div>
        )}

        {visual_label && (
          <div style={{
            fontSize: cs.fontSize * 0.6, fontWeight: 400,
            color: cs.textColorOverride || theme.textSecondary,
            textAlign: "center", opacity: Math.min(1, t * 2),
            letterSpacing: 4, textTransform: "uppercase",
          }}>{visual_label}</div>
        )}

        <div style={{
          display: "flex", alignItems: "baseline", gap: 12,
          transform: `scale(${pulse})`,
        }}>
          <span style={{
            fontSize: cs.fontSize * 2.0, fontWeight: 800,
            color: accent,
            textShadow: cs.glowIntensity > 0.3
              ? `0 0 ${cs.glowIntensity * 40}px ${accent}60` : "none",
            lineHeight: 1,
          }}>{displayValue}</span>

          {visual_unit && (
            <span style={{
              fontSize: cs.fontSize * 0.8, fontWeight: 500,
              color: cs.textColorOverride || theme.text,
              opacity: Math.min(1, (t - 0.3) * 3),
            }}>{visual_unit}</span>
          )}

          {visual_trend && (
            <span style={{
              fontSize: cs.fontSize * 0.9, fontWeight: 700,
              color: trendColor,
              opacity: Math.min(1, (t - 0.5) * 3),
              transform: `translateY(${(1 - Math.min(1, (t - 0.5) * 3)) * 10}px)`,
              textShadow: cs.glowIntensity > 0.3
                ? `0 0 ${cs.glowIntensity * 20}px ${trendColor}40` : "none",
            }}>{trendArrow}</span>
          )}
        </div>

        {/* Progress bar under the number */}
        <div style={{
          width: 200, height: 4, borderRadius: 2,
          background: theme.surfaceBorder, overflow: "hidden",
          opacity: Math.min(1, t * 2), marginTop: 8,
        }}>
          <div style={{
            height: "100%",
            width: `${countProgress * 100}%`,
            background: `linear-gradient(90deg, ${accent}, ${theme.accentSecondary})`,
            borderRadius: 2,
            transition: "width 0.05s linear",
          }} />
        </div>
      </div>
    </SceneWrapper>
  );
};

export default DataCardScene;
