import React from "react";
import { AbsoluteFill, useVideoConfig, useCurrentFrame } from "remotion";
import { ThemePalette, AnimationStyle } from "../types";

interface SceneWrapperProps {
  theme: ThemePalette;
  children: React.ReactNode;
  animation?: AnimationStyle;
}

export const SceneWrapper: React.FC<SceneWrapperProps> = ({
  theme,
  children,
  animation,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  let opacity = 1;
  let transform = "none";

  if (animation === "fade_in") {
    opacity = Math.min(1, t * 2);
  } else if (animation === "scale_in") {
    const progress = Math.min(1, t * 1.5);
    opacity = progress;
    transform = `scale(${0.8 + 0.2 * progress})`;
  } else if (animation === "slide_up") {
    const progress = Math.min(1, t * 2);
    opacity = progress;
    transform = `translateY(${(1 - progress) * 50}px)`;
  } else if (animation === "zoom_in") {
    const progress = Math.min(1, t * 1.5);
    opacity = progress;
    transform = `scale(${1.3 - 0.3 * progress})`;
  } else if (animation === "fade_out") {
    const duration = 30 / fps;
    opacity = t < 0.5 ? 1 : Math.max(0, 1 - (t - 0.5) / duration);
  }

  const background =
    theme.backgroundGradient
      ? `linear-gradient(135deg, ${theme.backgroundGradient[0]}, ${theme.backgroundGradient[1]})`
      : theme.background;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.background,
        background,
        justifyContent: "center",
        alignItems: "center",
        opacity,
        transform,
        transition: "opacity 0.3s, transform 0.3s",
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
