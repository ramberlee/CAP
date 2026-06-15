import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";

interface EndingSceneProps {
  theme: ThemePalette;
  text: string;
  duration: number;
  animation?: AnimationStyle;
}

const EndingScene: React.FC<EndingSceneProps> = ({
  theme,
  text,
  animation = "fade_out",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const lines = text.split("\n").filter(Boolean);

  return (
    <SceneWrapper theme={theme} animation={animation}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 16,
          padding: 40,
        }}
      >
        {/* Logo/avatar placeholder */}
        <div
          style={{
            width: 80,
            height: 80,
            borderRadius: "50%",
            background: theme.accent,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 32,
            color: theme.background,
            fontWeight: 700,
            marginBottom: 10,
          }}
        >
          AI
        </div>

        {lines.map((line, i) => (
          <div
            key={i}
            style={{
              fontSize: i === 0 ? 44 : 28,
              fontWeight: i === 0 ? 700 : 400,
              color: i === 0 ? theme.text : theme.textSecondary,
              textAlign: "center",
              lineHeight: 1.4,
              maxWidth: "80%",
            }}
          >
            {line}
          </div>
        ))}

        {/* Call to action button */}
        <div
          style={{
            marginTop: 20,
            padding: "14px 40px",
            borderRadius: 50,
            background: theme.accent,
            fontSize: 26,
            fontWeight: 600,
            color: theme.background,
            opacity: Math.min(1, (t - 0.5) * 3),
          }}
        >
          关注获取更多
        </div>
      </div>
    </SceneWrapper>
  );
};

export default EndingScene;
