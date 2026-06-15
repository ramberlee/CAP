import React, { useMemo } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";

interface TitleSceneProps {
  theme: ThemePalette;
  text: string;
  duration: number;
  animation?: AnimationStyle;
}

const TitleScene: React.FC<TitleSceneProps> = ({
  theme,
  text,
  animation = "scale_in",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // Line-by-line animation
  const lines = text.split("\n").filter(Boolean);

  return (
    <SceneWrapper theme={theme} animation={animation}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 20,
          padding: 40,
        }}
      >
        {lines.map((line, i) => {
          const lineDelay = i * 0.3;
          const lineT = Math.max(0, Math.min(1, (t - lineDelay) * 2));
          const isMain = i === 0;

          return (
            <div
              key={i}
              style={{
                fontSize: isMain ? 72 : 36,
                fontWeight: isMain ? 800 : 400,
                color: isMain ? theme.accent : theme.textSecondary,
                textAlign: "center",
                opacity: lineT,
                transform: lineT > 0 ? "translateY(0)" : "translateY(30px)",
                transition: "opacity 0.5s, transform 0.5s",
                textShadow:
                  isMain
                    ? `0 0 40px ${theme.accent}40, 0 0 80px ${theme.accent}20`
                    : "none",
                lineHeight: 1.3,
                maxWidth: "90%",
              }}
            >
              {line}
            </div>
          );
        })}
      </div>

      {/* Decorative accent line */}
      <div
        style={{
          position: "absolute",
          bottom: "25%",
          width: "60%",
          height: 2,
          background: `linear-gradient(90deg, transparent, ${theme.accent}, transparent)`,
          opacity: Math.min(1, (t - 0.5) * 2),
        }}
      />
    </SceneWrapper>
  );
};

export default TitleScene;
