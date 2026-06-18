import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";
import { computeStyle, getStaggerDelay, easeOutCubic } from "../components/VisualInterpreter";

interface BulletPointsSceneProps {
  theme: ThemePalette; items: string[]; duration: number;
  animation?: AnimationStyle; icon?: string;
  visualStyle?: string; mood?: string; layoutHint?: string;
  imagePath?: string;
}

const BulletPointsScene: React.FC<BulletPointsSceneProps> = ({
  theme, items, duration, icon, animation = "slide_up",
  visualStyle, mood, layoutHint, imagePath,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const cs = computeStyle(visualStyle, mood, layoutHint, theme);
  const accent = cs.accentOverride || theme.accent;
  const itemInterval = duration / Math.max(items.length, 1);

  return (
    <SceneWrapper theme={theme} animation={animation} icon={icon}
      visualStyle={visualStyle} mood={mood} layoutHint={layoutHint}
      imagePath={imagePath}>
      <div style={{ display: "flex", flexDirection: "column", gap: 20, padding: "0 60px", width: "100%", maxWidth: 680, height: "100%", justifyContent: "center" }}>
        {icon && (
          <div style={{ fontSize: 80, textAlign: "center", marginBottom: 10, filter: `drop-shadow(0 0 20px ${accent}30)` }}>{icon}</div>
        )}

        {items.map((item, i) => {
          const delay = getStaggerDelay(i, items.length, cs.entrancePattern, itemInterval * 0.6 / items.length);
          const appearAt = i * itemInterval * 0.6;
          const itemT = easeOutCubic(Math.max(0, Math.min(1, (t - appearAt) * 3)));
          const barStart = appearAt;
          const barEnd = appearAt + itemInterval * 0.85;
          const barProgress = Math.max(0, Math.min(1, (t - barStart) / (barEnd - barStart)));

          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{
                display: "flex", alignItems: "center", gap: 20,
                opacity: itemT, transform: `translateX(${(1 - itemT) * (cs.motionStyle === "bold" ? 50 : 30)}px)`,
              }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 12, flexShrink: 0,
                  background: itemT > 0.8 ? accent : theme.surfaceBorder,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 22, fontWeight: 700,
                  color: itemT > 0.8 ? theme.background : theme.textSecondary,
                  boxShadow: itemT > 0.8 && cs.glowIntensity > 0.3 ? `0 0 ${cs.glowIntensity * 25}px ${accent}40` : "none",
                }}>{i + 1}</div>
                <div style={{
                  fontSize: cs.fontSize * 0.85, fontWeight: cs.fontWeight,
                  color: cs.textColorOverride || theme.text,
                  lineHeight: cs.lineHeight, letterSpacing: cs.letterSpacing,
                }}>{item}</div>
              </div>
              <div style={{ height: 3, borderRadius: 2, background: theme.surfaceBorder, overflow: "hidden", marginLeft: 68, opacity: itemT }}>
                <div style={{ height: "100%", width: `${barProgress * 100}%`, background: `linear-gradient(90deg, ${accent}, ${theme.accentSecondary})`, borderRadius: 2 }} />
              </div>
            </div>
          );
        })}
      </div>
    </SceneWrapper>
  );
};

export default BulletPointsScene;
