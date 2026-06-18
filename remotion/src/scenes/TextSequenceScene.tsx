import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";
import { computeStyle, getStaggerDelay, easeOutCubic } from "../components/VisualInterpreter";

interface TextSequenceSceneProps {
  theme: ThemePalette; lines: string[]; duration: number;
  animation?: AnimationStyle; icon?: string;
  visualStyle?: string; mood?: string; layoutHint?: string;
  imagePath?: string;
}

const TextSequenceScene: React.FC<TextSequenceSceneProps> = ({
  theme, lines, duration, icon, animation = "fade_in",
  visualStyle, mood, layoutHint, imagePath,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const cs = computeStyle(visualStyle, mood, layoutHint, theme);
  const accent = cs.accentOverride || theme.accent;
  const lineInterval = duration / Math.max(lines.length, 1);

  return (
    <SceneWrapper theme={theme} animation={animation} icon={icon}
      visualStyle={visualStyle} mood={mood} layoutHint={layoutHint}
      imagePath={imagePath}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: cs.textAlign === "center" ? "center" : "flex-start", justifyContent: "center", gap: 0, padding: "0 80px", width: "100%", height: "100%" }}>
        {icon && (
          <div style={{
            fontSize: 70, marginBottom: 30,
            alignSelf: cs.textAlign === "center" ? "center" : "flex-start",
            filter: `drop-shadow(0 0 20px ${accent}30)`,
          }}>{icon}</div>
        )}

        {lines.map((line, i) => {
          const appearAt = i * lineInterval * 0.7;
          const lineT = easeOutCubic(Math.max(0, Math.min(1, (t - appearAt) * 3)));
          const showDot = lineT > 0.3;

          // Highlight the most recently appeared line
          const nextAppearAt = (i + 1) * lineInterval * 0.7;
          const isLatest = t >= appearAt && t < nextAppearAt;
          const highlightPulse = isLatest ? 1 + 0.02 * Math.sin((t - appearAt) * 4) : 1;
          const dotGlow = isLatest ? cs.glowIntensity * 40 : cs.glowIntensity * 20;

          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", width: "100%" }}>
              <div style={{
                display: "flex", alignItems: "center", gap: 20, padding: "18px 0",
                opacity: lineT, transform: `translateX(${(1 - lineT) * (cs.motionStyle === "bold" ? 60 : 40)}px) scale(${highlightPulse})`,
              }}>
                <div style={{
                  width: isLatest ? 18 : (cs.glowIntensity > 0.5 ? 16 : 14),
                  height: isLatest ? 18 : (cs.glowIntensity > 0.5 ? 16 : 14),
                  borderRadius: "50%", flexShrink: 0,
                  background: showDot ? accent : theme.surfaceBorder,
                  boxShadow: showDot ? `0 0 ${dotGlow}px ${accent}60` : "none",
                  transition: "width 0.2s, height 0.2s",
                }} />
                <div style={{
                  fontSize: isLatest ? cs.fontSize * 0.95 : cs.fontSize * 0.9,
                  fontWeight: isLatest ? Math.min(900, cs.fontWeight + 200) : cs.fontWeight,
                  color: lineT > 0.5 ? (cs.textColorOverride || theme.text) : theme.textSecondary,
                  lineHeight: cs.lineHeight, letterSpacing: cs.letterSpacing,
                  maxWidth: cs.maxWidth,
                  textShadow: isLatest && cs.glowIntensity > 0.3 ? `0 0 ${cs.glowIntensity * 15}px ${accent}30` : "none",
                }}>{line}</div>
              </div>
              {i < lines.length - 1 && (
                <div style={{ width: 2, height: 20, background: theme.surfaceBorder, marginLeft: 6, opacity: lineT * 0.6 }} />
              )}
            </div>
          );
        })}
      </div>
    </SceneWrapper>
  );
};

export default TextSequenceScene;
