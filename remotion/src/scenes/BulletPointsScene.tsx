import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";

interface BulletPointsSceneProps {
  theme: ThemePalette;
  items: string[];
  duration: number;
  animation?: AnimationStyle;
}

const BulletPointsScene: React.FC<BulletPointsSceneProps> = ({
  theme,
  items,
  duration,
  animation = "slide_up",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const itemInterval = duration / Math.max(items.length, 1);

  return (
    <SceneWrapper theme={theme} animation={animation}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 20,
          padding: "0 60px",
          width: "100%",
          maxWidth: 640,
        }}
      >
        {items.map((item, i) => {
          const appearAt = i * itemInterval * 0.6;
          const itemT = Math.max(0, Math.min(1, (t - appearAt) * 3));

          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 20,
                opacity: itemT,
                transform: `translateX(${(1 - itemT) * 30}px)`,
              }}
            >
              {/* Bullet icon with number */}
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 12,
                  background: theme.accent,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 22,
                  fontWeight: 700,
                  color: theme.background,
                  flexShrink: 0,
                }}
              >
                {i + 1}
              </div>

              {/* Item text */}
              <div
                style={{
                  fontSize: 40,
                  fontWeight: 500,
                  color: theme.text,
                  lineHeight: 1.3,
                }}
              >
                {item}
              </div>
            </div>
          );
        })}
      </div>
    </SceneWrapper>
  );
};

export default BulletPointsScene;
