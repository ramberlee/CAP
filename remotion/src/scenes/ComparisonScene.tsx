import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";
import { computeStyle, easeOutCubic } from "../components/VisualInterpreter";

interface ComparisonSceneProps {
  theme: ThemePalette;
  duration: number;
  animation?: AnimationStyle;
  icon?: string;
  visualStyle?: string;
  mood?: string;
  layoutHint?: string;
  imagePath?: string;
  /** Left-side label */
  visual_left?: string;
  /** Right-side label */
  visual_right?: string;
}

const ComparisonScene: React.FC<ComparisonSceneProps> = ({
  theme, duration, icon, animation = "slide_up",
  visualStyle, mood, layoutHint, imagePath,
  visual_left, visual_right,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const cs = computeStyle(visualStyle, mood, layoutHint, theme);
  const accent = cs.accentOverride || theme.accent;

  // Left slides in from left, right slides in from right
  const leftDelay = 0.15;
  const rightDelay = 0.35;
  const animDuration = 0.5;
  const leftT = Math.max(0, Math.min(1, (t - leftDelay) / animDuration));
  const rightT = Math.max(0, Math.min(1, (t - rightDelay) / animDuration));

  // VS divider expands
  const vsT = easeOutCubic(Math.max(0, Math.min(1, (t - 0.2) * 2)));
  const vsPulse = 1 + 0.06 * Math.sin((t - 0.2) * Math.PI * 3);

  const leftX = (1 - easeOutCubic(leftT)) * -150;
  const rightX = (1 - easeOutCubic(rightT)) * 150;

  return (
    <SceneWrapper
      theme={theme} animation={animation} icon={icon}
      visualStyle={visualStyle} mood={mood} layoutHint={layoutHint}
      imagePath={imagePath}
    >
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "center",
        width: "100%", height: "100%", gap: 0, padding: 60,
      }}>
        {/* Left panel */}
        <div style={{
          flex: 1, display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          transform: `translateX(${leftX}px)`,
          opacity: leftT,
        }}>
          <div style={{
            fontSize: cs.fontSize * 0.55, fontWeight: 500,
            color: theme.textSecondary, marginBottom: 12,
            letterSpacing: 2, textTransform: "uppercase",
          }}>BEFORE</div>
          <div style={{
            width: "100%", maxWidth: 350, padding: "24px 20px",
            borderRadius: 16, background: theme.surface,
            border: `2px solid ${theme.surfaceBorder}`,
            textAlign: "center",
          }}>
            <div style={{
              fontSize: cs.fontSize * 0.8, fontWeight: cs.fontWeight,
              color: cs.textColorOverride || theme.textSecondary,
              lineHeight: cs.lineHeight,
            }}>{visual_left || "旧方案"}</div>
          </div>
        </div>

        {/* VS divider */}
        <div style={{
          width: 70, display: "flex", alignItems: "center", justifyContent: "center",
          transform: `scale(${vsT * vsPulse})`,
          opacity: vsT,
        }}>
          <div style={{
            width: 56, height: 56, borderRadius: 28,
            background: `linear-gradient(135deg, ${accent}, ${theme.accentSecondary})`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 22, fontWeight: 800, color: theme.background,
            boxShadow: cs.glowIntensity > 0.3
              ? `0 0 ${cs.glowIntensity * 30}px ${accent}60` : "none",
          }}>VS</div>
        </div>

        {/* Right panel */}
        <div style={{
          flex: 1, display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          transform: `translateX(${rightX}px)`,
          opacity: rightT,
        }}>
          <div style={{
            fontSize: cs.fontSize * 0.55, fontWeight: 500,
            color: accent, marginBottom: 12,
            letterSpacing: 2, textTransform: "uppercase",
          }}>AFTER</div>
          <div style={{
            width: "100%", maxWidth: 350, padding: "24px 20px",
            borderRadius: 16, background: theme.surface,
            border: `2px solid ${accent}40`,
            boxShadow: cs.glowIntensity > 0.3
              ? `0 0 ${cs.glowIntensity * 20}px ${accent}20` : "none",
            textAlign: "center",
          }}>
            <div style={{
              fontSize: cs.fontSize * 0.8, fontWeight: cs.fontWeight,
              color: cs.textColorOverride || theme.text,
              lineHeight: cs.lineHeight,
            }}>{visual_right || "新方案"}</div>
          </div>
        </div>
      </div>
    </SceneWrapper>
  );
};

export default ComparisonScene;
