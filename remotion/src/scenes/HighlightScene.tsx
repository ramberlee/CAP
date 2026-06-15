import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";

interface HighlightSceneProps {
  theme: ThemePalette;
  text: string;
  duration: number;
  animation?: AnimationStyle;
}

const HighlightScene: React.FC<HighlightSceneProps> = ({
  theme,
  text,
  animation = "pulse",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // Pulsing animation
  const pulse = animation === "pulse"
    ? 1 + 0.04 * Math.sin(t * Math.PI * 2)
    : 1;

  return (
    <SceneWrapper theme={theme} animation={animation}>
      {/* Background glow circle */}
      <div
        style={{
          position: "absolute",
          width: 500,
          height: 500,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${theme.accent}20 0%, transparent 70%)`,
          transform: `scale(${1 + 0.1 * Math.sin(t * Math.PI * 0.5)})`,
        }}
      />

      <div
        style={{
          fontSize: 56,
          fontWeight: 800,
          color: theme.accent,
          textAlign: "center",
          padding: "20px 40px",
          transform: `scale(${pulse})`,
          textShadow: `0 0 30px ${theme.accent}40, 0 0 60px ${theme.accent}20`,
          lineHeight: 1.4,
          maxWidth: "90%",
          zIndex: 1,
        }}
      >
        {text}
      </div>
    </SceneWrapper>
  );
};

export default HighlightScene;
