import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";

interface TextSequenceSceneProps {
  theme: ThemePalette;
  lines: string[];
  duration: number;
  animation?: AnimationStyle;
}

const TextSequenceScene: React.FC<TextSequenceSceneProps> = ({
  theme,
  lines,
  duration,
  animation = "fade_in",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const lineInterval = duration / Math.max(lines.length, 1);

  return (
    <SceneWrapper theme={theme} animation={animation}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          justifyContent: "center",
          gap: 24,
          padding: "0 60px",
          width: "100%",
        }}
      >
        {lines.map((line, i) => {
          const appearAt = i * lineInterval * 0.7;
          const lineT = Math.max(0, Math.min(1, (t - appearAt) * 3));

          return (
            <div
              key={i}
              style={{
                fontSize: 48,
                fontWeight: 600,
                color: theme.text,
                opacity: lineT,
                transform: `translateX(${(1 - lineT) * 40}px)`,
                lineHeight: 1.4,
                maxWidth: "100%",
                textShadow: `0 2px 10px rgba(0,0,0,0.3)`,
              }}
            >
              {line}
            </div>
          );
        })}
      </div>
    </SceneWrapper>
  );
};

export default TextSequenceScene;
