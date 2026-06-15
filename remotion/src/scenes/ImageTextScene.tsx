import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SceneWrapper } from "./SceneWrapper";
import { ThemePalette, AnimationStyle } from "../types";

interface ImageTextSceneProps {
  theme: ThemePalette;
  text: string;
  imagePath?: string;
  duration: number;
  animation?: AnimationStyle;
}

const ImageTextScene: React.FC<ImageTextSceneProps> = ({
  theme,
  text,
  imagePath,
  animation = "fade_in",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // Split text and hashtags
  const lines = text.split("\n").filter(Boolean);
  const mainLines = lines.filter((l) => !l.startsWith("#"));
  const hashtags = lines.filter((l) => l.startsWith("#"));

  return (
    <SceneWrapper theme={theme} animation={animation}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          width: "100%",
          height: "100%",
          padding: 0,
        }}
      >
        {/* Image area (top 55%) */}
        <div
          style={{
            flex: "0 0 55%",
            background: imagePath
              ? `url(${imagePath}) center/cover no-repeat`
              : `linear-gradient(135deg, ${theme.accent}40, ${theme.accentSecondary}40)`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            borderRadius: 0,
            margin: 0,
            position: "relative",
          }}
        >
          {!imagePath && (
            <div
              style={{
                fontSize: 80,
                opacity: 0.6,
                color: theme.text,
              }}
            >
              🖼
            </div>
          )}
          {/* Gradient overlay at bottom of image */}
          <div
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
              height: 80,
              background: `linear-gradient(transparent, ${theme.background})`,
            }}
          />
        </div>

        {/* Text area (bottom 45%) */}
        <div
          style={{
            flex: "0 0 45%",
            background: theme.background,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            padding: "20px 40px",
          }}
        >
          {mainLines.map((line, i) => {
            const lineDelay = i * 0.15;
            const lineT = Math.max(0, Math.min(1, (t - lineDelay) * 3));

            return (
              <div
                key={i}
                style={{
                  fontSize: i === 0 ? 40 : 32,
                  fontWeight: i === 0 ? 700 : 400,
                  color: i === 0 ? theme.text : theme.textSecondary,
                  opacity: lineT,
                  transform: `translateY(${(1 - lineT) * 20}px)`,
                  lineHeight: 1.4,
                }}
              >
                {line}
              </div>
            );
          })}

          {hashtags.length > 0 && (
            <div
              style={{
                marginTop: 16,
                display: "flex",
                gap: 12,
                flexWrap: "wrap",
              }}
            >
              {hashtags.map((tag, i) => (
                <span
                  key={i}
                  style={{
                    fontSize: 22,
                    color: theme.accent,
                    opacity: Math.min(1, (t - 0.5) * 2),
                  }}
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </SceneWrapper>
  );
};

export default ImageTextScene;
