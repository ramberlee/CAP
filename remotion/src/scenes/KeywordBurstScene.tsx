import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";
import { computeStyle } from "../components/VisualInterpreter";

interface KeywordBurstSceneProps {
  theme: ThemePalette;
  duration: number;
  animation?: AnimationStyle;
  icon?: string;
  visualStyle?: string;
  mood?: string;
  layoutHint?: string;
  imagePath?: string;
  /** Keywords to burst onto screen */
  visual_keywords?: string[];
}

const KeywordBurstScene: React.FC<KeywordBurstSceneProps> = ({
  theme, duration, icon, animation = "zoom_in",
  visualStyle, mood, layoutHint, imagePath,
  visual_keywords,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const cs = computeStyle(visualStyle, mood, layoutHint, theme);
  const accent = cs.accentOverride || theme.accent;

  const keywords = visual_keywords?.length ? visual_keywords : [];
  const totalItems = Math.max(keywords.length, 1);

  // Each keyword appears at a staggered time
  const itemDelay = duration / (totalItems + 2);

  // Grid positions for keywords — spread across the screen
  const positions = keywords.map((_, i) => {
    const angle = (i / totalItems) * Math.PI * 2 + 0.3;
    const radius = 0.25 + (i % 3) * 0.12;
    return {
      x: 50 + Math.cos(angle) * 40,
      y: 45 + Math.sin(angle) * 35,
      rotate: -10 + (i / totalItems) * 20,
      fromAngle: angle + Math.PI, // come from opposite direction
    };
  });

  return (
    <SceneWrapper
      theme={theme} animation={animation} icon={icon}
      visualStyle={visualStyle} mood={mood} layoutHint={layoutHint}
      imagePath={imagePath}
    >
      {icon && (
        <div style={{
          position: "absolute", top: "8%", fontSize: 50,
          opacity: Math.min(1, t * 2),
          filter: `drop-shadow(0 0 ${cs.glowIntensity * 20}px ${accent}30)`,
        }}>{icon}</div>
      )}

      {keywords.map((kw, i) => {
        const pos = positions[i];
        const appearAt = i * itemDelay * 0.7;
        const kwT = Math.max(0, Math.min(1, (t - appearAt) / 0.4));
        // Ease-out back
        const easeOutBack = (x: number) => {
          const c1 = 1.2;
          return 1 + c1 * Math.pow(x - 1, 3) + (c1 - 1) * Math.pow(x - 1, 2);
        };
        const scale = kwT > 0 ? easeOutBack(Math.min(1, kwT * 1.05)) : 0;
        const driftX = (1 - kwT) * 60 * Math.cos(pos.fromAngle);
        const driftY = (1 - kwT) * 60 * Math.sin(pos.fromAngle);

        // Glow pulse after appearing
        const glowPulse = kwT >= 0.9
          ? Math.round((0.15 + 0.08 * Math.sin((t - appearAt - 0.4) * 8)) * 100) / 100
          : kwT * 0.15;

        // Decide color: alternate between accent and text
        const kwColor = i % 3 === 0 ? accent
          : i % 3 === 1 ? (cs.textColorOverride || theme.text)
          : theme.accentSecondary;

        return (
          <div key={i} style={{
            position: "absolute",
            left: `${pos.x}%`, top: `${pos.y}%`,
            transform: `translate(-50%, -50%) translate(${driftX}px, ${driftY}px) scale(${Math.max(0, scale)}) rotate(${pos.rotate * (1 - kwT)}deg)`,
            opacity: Math.min(1, kwT * 1.5),
            fontSize: cs.fontSize * (0.7 + (i % 3) * 0.15),
            fontWeight: cs.fontWeight + (i % 2 === 0 ? 200 : 0),
            color: kwColor,
            textAlign: "center",
            padding: "12px 28px",
            borderRadius: 32,
            background: kwT > 0.3
              ? `${kwColor}${Math.round(glowPulse * 25).toString(16).padStart(2, "0")}`
              : "transparent",
            border: kwT > 0.15 && kwT < 0.5
              ? `2px solid ${kwColor}${Math.round(kwT * 60).toString(16).padStart(2, "0")}`
              : kwT >= 0.5
                ? `2px solid ${kwColor}30`
                : "2px solid transparent",
            textShadow: cs.glowIntensity > 0.3 && kwColor === accent
              ? `0 0 ${cs.glowIntensity * 30}px ${accent}40` : "none",
            letterSpacing: cs.letterSpacing,
            lineHeight: cs.lineHeight,
            whiteSpace: "nowrap",
            zIndex: i + 1,
          }}>
            {kw}
          </div>
        );
      })}
    </SceneWrapper>
  );
};

export default KeywordBurstScene;
