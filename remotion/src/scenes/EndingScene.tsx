import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";
import { computeStyle, getStaggerDelay } from "../components/VisualInterpreter";

interface EndingSceneProps {
  theme: ThemePalette; text: string; duration: number;
  animation?: AnimationStyle; icon?: string;
  visualStyle?: string; mood?: string; layoutHint?: string;
  imagePath?: string;
}

const EndingScene: React.FC<EndingSceneProps> = ({
  theme, text, icon, animation = "fade_out",
  visualStyle, mood, layoutHint, imagePath,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const cs = computeStyle(visualStyle, mood, layoutHint, theme);
  const accent = cs.accentOverride || theme.accent;
  const lines = text.split("\n").filter(Boolean);
  const avatarPulse = 1 + 0.03 * Math.sin(t * 2);

  return (
    <SceneWrapper theme={theme} animation={animation}
      visualStyle={visualStyle} mood={mood} layoutHint={layoutHint}
      imagePath={imagePath}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16, padding: 40, width: "100%", height: "100%", justifyContent: "center" }}>
        <div style={{ position: "relative", marginBottom: 10 }}>
          <div style={{
            position: "absolute", inset: cs.glowIntensity > 0.5 ? -16 : -12, borderRadius: "50%",
            border: `${cs.glowIntensity > 0.5 ? 3 : 2}px solid ${accent}30`,
            transform: `scale(${avatarPulse})`,
          }} />
          <div style={{
            width: cs.glowIntensity > 0.5 ? 90 : 80,
            height: cs.glowIntensity > 0.5 ? 90 : 80, borderRadius: "50%",
            background: cs.glowIntensity > 0.3
              ? `linear-gradient(135deg, ${accent}, ${theme.accentSecondary})`
              : accent,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: icon ? 36 : 32, color: theme.background, fontWeight: 700,
            boxShadow: `0 0 ${cs.glowIntensity * 40}px ${accent}50`,
          }}>{icon || "AI"}</div>
        </div>

        {lines.map((line, i) => {
          const delay = getStaggerDelay(i, lines.length, cs.entrancePattern, 0.2);
          const lineT = Math.max(0, Math.min(1, (t - delay) * 2));
          return (
            <div key={i} style={{
              fontSize: i === 0 ? cs.fontSize * 0.9 : cs.fontSize * 0.6,
              fontWeight: i === 0 ? cs.fontWeight : Math.max(300, cs.fontWeight - 300),
              color: i === 0 ? (cs.textColorOverride || theme.text) : theme.textSecondary,
              textAlign: "center", lineHeight: cs.lineHeight,
              maxWidth: "80%", opacity: lineT,
              transform: `translateY(${(1 - lineT) * 15}px)`,
              letterSpacing: cs.letterSpacing,
            }}>{line}</div>
          );
        })}

        <div style={{
          marginTop: 20, padding: "14px 40px", borderRadius: 50,
          background: `linear-gradient(135deg, ${accent}, ${theme.accentSecondary})`,
          fontSize: 26, fontWeight: 600, color: theme.background,
          opacity: Math.min(1, (t - 0.5) * 3),
          boxShadow: `0 0 ${cs.glowIntensity * 35}px ${accent}40`,
          transform: `scale(${1 + 0.02 * Math.sin(t * 3)})`,
        }}>关注获取更多</div>
      </div>
    </SceneWrapper>
  );
};

export default EndingScene;
