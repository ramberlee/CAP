import React from "react";
import { useCurrentFrame, useVideoConfig, Img } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";
import { computeStyle, easeOutCubic } from "../components/VisualInterpreter";

interface ImageTextSceneProps {
  theme: ThemePalette; text: string; imagePath?: string; duration: number;
  animation?: AnimationStyle; icon?: string;
  visualStyle?: string; mood?: string; layoutHint?: string;
}

const ImageTextScene: React.FC<ImageTextSceneProps> = ({
  theme, text, imagePath, icon, animation = "fade_in",
  visualStyle, mood, layoutHint,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const cs = computeStyle(visualStyle, mood, layoutHint, theme);
  const accent = cs.accentOverride || theme.accent;
  const lines = text.split("\n").filter(Boolean);
  const mainLines = lines.filter((l) => !l.startsWith("#"));
  const hashtags = lines.filter((l) => l.startsWith("#"));

  return (
    <SceneWrapper theme={theme} animation={animation}
      visualStyle={visualStyle} mood={mood} layoutHint={layoutHint}>
      <div style={{ display: "flex", flexDirection: "column", width: "100%", height: "100%", padding: 0 }}>
        <div style={{
          flex: "0 0 55%", position: "relative", overflow: "hidden",
        }}>
          {imagePath ? (
            <Img
              src={imagePath}
              style={{
                width: "100%", height: "100%", objectFit: "cover",
              }}
            />
          ) : (
            <ImageFallback theme={theme} t={t} icon={icon} cs={cs} accent={accent} />
          )}
          <div style={{
            position: "absolute", bottom: 0, left: 0, right: 0, height: 80,
            background: `linear-gradient(transparent, ${theme.background})`, zIndex: 2,
          }} />
        </div>

        <div style={{ flex: "0 0 45%", background: theme.background, display: "flex", flexDirection: "column", justifyContent: "center", padding: "20px 40px" }}>
          {mainLines.map((line, i) => {
            const lineDelay = i * 0.15;
            const lineT = easeOutCubic(Math.max(0, Math.min(1, (t - lineDelay) * 3)));
            return (
              <div key={i} style={{
                fontSize: i === 0 ? cs.fontSize * 0.85 : cs.fontSize * 0.65,
                fontWeight: i === 0 ? cs.fontWeight : Math.max(300, cs.fontWeight - 300),
                color: i === 0 ? (cs.textColorOverride || theme.text) : theme.textSecondary,
                opacity: lineT, transform: `translateY(${(1 - lineT) * 20}px)`,
                lineHeight: cs.lineHeight, letterSpacing: cs.letterSpacing,
              }}>{line}</div>
            );
          })}
          {hashtags.length > 0 && (
            <div style={{ marginTop: 16, display: "flex", gap: 12, flexWrap: "wrap" }}>
              {hashtags.map((tag, i) => (
                <span key={i} style={{ fontSize: 22, color: accent, opacity: Math.min(1, (t - 0.5) * 2) }}>{tag}</span>
              ))}
            </div>
          )}
        </div>
      </div>
    </SceneWrapper>
  );
};

const ImageFallback: React.FC<{
  theme: ThemePalette; t: number; icon?: string;
  cs: ReturnType<typeof computeStyle>; accent: string;
}> = ({ theme, t, icon, cs, accent }) => (
  <div style={{ position: "absolute", inset: 0, background: `linear-gradient(135deg, ${accent}25, ${theme.accentSecondary}25, ${accent}15)`, backgroundSize: "400% 400%" }}>
    {(cs.motionStyle === "bold" ? [0, 1, 2, 3, 4] : [0, 1, 2, 3]).map((i) => {
      const angle = (i * Math.PI) / 2 + t * (cs.animationSpeed === "fast" ? 0.6 : 0.4);
      const radius = 120 + i * 30;
      return (
        <div key={i} style={{
          position: "absolute", left: `${50 + Math.cos(angle) * 30}%`, top: `${50 + Math.sin(angle) * 25}%`,
          width: radius, height: radius,
          borderRadius: i % 2 === 0 ? "50%" : "8px",
          border: `2px solid ${accent}20`,
          transform: `translate(-50%, -50%) rotate(${t * 20 * (i % 2 === 0 ? 1 : -1)}deg)`,
          opacity: 0.5,
        }} />
      );
    })}
    <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{
        fontSize: icon ? 100 : 80, opacity: icon ? 0.9 : 0.5, color: theme.text,
        filter: `drop-shadow(0 0 20px ${accent}40)`,
        transform: `scale(${1 + 0.05 * Math.sin(t * 1.5)})`,
      }}>{icon || "🖼"}</div>
    </div>
  </div>
);

export default ImageTextScene;
