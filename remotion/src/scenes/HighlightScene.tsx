import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";
import { computeStyle, getStaggerDelay, easeOutCubic } from "../components/VisualInterpreter";

interface HighlightSceneProps {
  theme: ThemePalette; text: string; duration: number;
  animation?: AnimationStyle; icon?: string;
  visualStyle?: string; mood?: string; layoutHint?: string;
  imagePath?: string;
}

const HighlightScene: React.FC<HighlightSceneProps> = ({
  theme, text, icon, animation = "pulse",
  visualStyle, mood, layoutHint, imagePath,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const cs = computeStyle(visualStyle, mood, layoutHint, theme);
  const accent = cs.accentOverride || theme.accent;
  const pulse = 1 + 0.04 * Math.sin(t * Math.PI * 2);

  return (
    <SceneWrapper theme={theme} animation={animation} icon={icon}
      visualStyle={visualStyle} mood={mood} layoutHint={layoutHint}
      imagePath={imagePath}>
      {/* Concentric rings — more rings for bold styles */}
      {(cs.motionStyle === "bold" ? [1, 2, 3, 4] : [1, 2, 3]).map((ring) => {
        const phase = t * 0.6 + ring * 1.2;
        const scale = 0.5 + ring * 0.3 + 0.15 * Math.sin(phase);
        const alpha = Math.round((0.1 - ring * 0.02) * (0.5 + cs.glowIntensity * 0.5) * 100);
        return (
          <div key={ring} style={{
            position: "absolute", width: cs.glowIntensity > 0.6 ? 600 : 500,
            height: cs.glowIntensity > 0.6 ? 600 : 500, borderRadius: "50%",
            border: `${cs.glowIntensity > 0.5 ? 3 : 2}px solid ${accent}${alpha.toString(16).padStart(2, "0")}`,
            transform: `scale(${scale})`, pointerEvents: "none", zIndex: 0,
          }} />
        );
      })}

      <div style={{
        position: "absolute", width: cs.glowIntensity > 0.6 ? 700 : 600,
        height: cs.glowIntensity > 0.6 ? 700 : 600, borderRadius: "50%",
        background: `radial-gradient(circle, ${accent}${Math.round(cs.glowIntensity * 25).toString(16).padStart(2, "0")} 0%, transparent 70%)`,
        transform: `scale(${1 + 0.1 * Math.sin(t * Math.PI * 0.5)})`, pointerEvents: "none", zIndex: 0,
      }} />

      {icon && (
        <div style={{
          fontSize: cs.glowIntensity > 0.6 ? 140 : 110, marginBottom: 20, zIndex: 1,
          filter: `drop-shadow(0 0 ${cs.glowIntensity * 50}px ${accent}50)`,
          transform: `scale(${1 + 0.03 * Math.sin(t * 2.5)})`,
        }}>{icon}</div>
      )}

      <div style={{
        fontSize: cs.fontSize * 1.15, fontWeight: cs.fontWeight,
        color: accent, textAlign: cs.textAlign, padding: "20px 40px",
        transform: `scale(${pulse})`,
        textShadow: cs.textShadow,
        lineHeight: cs.lineHeight, letterSpacing: cs.letterSpacing,
        maxWidth: cs.maxWidth, zIndex: 1,
      }}>{text}</div>
    </SceneWrapper>
  );
};

export default HighlightScene;
