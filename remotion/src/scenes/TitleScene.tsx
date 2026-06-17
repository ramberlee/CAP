import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";
import { computeStyle, getStaggerDelay } from "../components/VisualInterpreter";

interface TitleSceneProps {
  theme: ThemePalette;
  text: string;
  duration: number;
  animation?: AnimationStyle;
  icon?: string;
  visualStyle?: string;
  mood?: string;
  layoutHint?: string;
  imagePath?: string;
}

const TitleScene: React.FC<TitleSceneProps> = ({
  theme, text, icon, animation = "scale_in",
  visualStyle, mood, layoutHint, imagePath,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const lines = text.split("\n").filter(Boolean);
  const cs = computeStyle(visualStyle, mood, layoutHint, theme);
  const accent = cs.accentOverride || theme.accent;

  return (
    <SceneWrapper
      theme={theme} animation={animation} icon={icon}
      visualStyle={visualStyle} mood={mood} layoutHint={layoutHint}
      imagePath={imagePath}
    >
      <div style={{ display: "flex", flexDirection: "column", alignItems: cs.textAlign === "center" ? "center" : "flex-start", justifyContent: "center", gap: 20, padding: 40, width: "100%", height: "100%" }}>
        {icon && (
          <div style={{
            fontSize: cs.glowIntensity > 0.6 ? 120 : 90,
            marginBottom: 10,
            transform: `scale(${1 + 0.05 * Math.sin(t * 2)})`,
            filter: `drop-shadow(0 0 ${cs.glowIntensity * 30}px ${accent}40)`,
          }}>{icon}</div>
        )}

        {lines.map((line, i) => {
          const delay = getStaggerDelay(i, lines.length, cs.entrancePattern, 0.3);
          const lineT = Math.max(0, Math.min(1, (t - delay) * 2));
          const isMain = i === 0;

          return (
            <div key={i} style={{
              fontSize: isMain ? Math.round(cs.fontSize * 1.5) : Math.round(cs.fontSize * 0.75),
              fontWeight: isMain ? cs.fontWeight : Math.max(300, cs.fontWeight - 300),
              color: isMain ? accent : cs.textColorOverride || theme.textSecondary,
              textAlign: cs.textAlign,
              opacity: lineT,
              transform: lineT > 0 ? "translateY(0)" : `translateY(${cs.motionStyle === "bold" ? 50 : 30}px)`,
              textShadow: isMain ? cs.textShadow : "none",
              lineHeight: cs.lineHeight,
              letterSpacing: cs.letterSpacing,
              maxWidth: cs.maxWidth,
            }}>{line}</div>
          );
        })}

        <div style={{
          position: "absolute", bottom: "22%",
          width: `${50 + Math.sin(t * 1.5) * 10}%`, height: cs.glowIntensity > 0.5 ? 3 : 2,
          background: `linear-gradient(90deg, transparent, ${accent}, transparent)`,
          opacity: Math.min(1, (t - 0.5) * 2),
          filter: cs.glowIntensity > 0.5 ? `blur(${cs.glowIntensity * 2}px)` : "none",
        }} />
      </div>
    </SceneWrapper>
  );
};

export default TitleScene;
