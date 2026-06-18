import React from "react";
import { AbsoluteFill, useVideoConfig, useCurrentFrame, Img, staticFile } from "remotion";
import { ThemePalette, AnimationStyle } from "../types";
import BackgroundDecorations from "../components/BackgroundDecorations";
import { ComputedStyle, computeStyle, easeOutCubic } from "../components/VisualInterpreter";

interface SceneWrapperProps {
  theme: ThemePalette;
  children: React.ReactNode;
  animation?: AnimationStyle;
  /** LLM-provided visual description */
  visualStyle?: string;
  /** Emotional mood */
  mood?: string;
  /** Layout preference */
  layoutHint?: string;
  /** Icon/emoji to render as a large background watermark */
  icon?: string;
  /** Pre-computed style (override auto-computed) */
  computedStyle?: ComputedStyle;
  /** Background image path (file:// URL or relative path) */
  imagePath?: string;
}

export const SceneWrapper: React.FC<SceneWrapperProps> = ({
  theme,
  children,
  animation,
  visualStyle,
  mood,
  layoutHint,
  icon,
  computedStyle,
  imagePath,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;
  const duration = durationInFrames / fps;

  // Compute dynamic visual style from LLM descriptions
  const cs = computedStyle || computeStyle(visualStyle, mood, layoutHint, theme);

  // ── animation (same as before but using computed speed) ──
  let opacity = 1;
  let transform = "none";

  const speedMultiplier = cs.animationSpeed === "fast" ? 1.7 : cs.animationSpeed === "slow" ? 0.6 : 1.0;

  if (animation === "fade_in") {
    opacity = easeOutCubic(Math.min(1, t * 2 * speedMultiplier));
  } else if (animation === "scale_in") {
    const progress = easeOutCubic(Math.min(1, t * 1.5 * speedMultiplier));
    opacity = progress;
    transform = `scale(${0.8 + 0.2 * progress})`;
  } else if (animation === "slide_up") {
    const progress = easeOutCubic(Math.min(1, t * 2 * speedMultiplier));
    opacity = progress;
    transform = `translateY(${(1 - progress) * 50}px)`;
  } else if (animation === "zoom_in") {
    const progress = easeOutCubic(Math.min(1, t * 1.5 * speedMultiplier));
    opacity = progress;
    transform = `scale(${1.3 - 0.3 * progress})`;
  } else if (animation === "fade_out") {
    // Fade out only in the last ~1/3 of the scene
    const fadeDuration = Math.min(1.0, duration / 3);
    const fadeStart = Math.max(0, duration - fadeDuration);
    opacity = t < fadeStart ? 1 : Math.max(0, 1 - (t - fadeStart) / fadeDuration);
  }

  // ── motion style: subtle per-frame transforms ──
  let motionTransform = "";
  if (cs.motionStyle === "bold") {
    const shake = Math.sin(t * 8) * 1.5;
    motionTransform = `translateX(${shake}px)`;
  } else if (cs.motionStyle === "gentle") {
    const breathe = Math.sin(t * 1.5) * 3;
    motionTransform = `translateY(${breathe}px)`;
  }

  // ── animated gradient ──
  const gradientAngle = 135 + Math.sin(t * 0.3) * 10;
  const bgColor = cs.bgOverride || theme.background;

  const background = theme.backgroundGradient
    ? `linear-gradient(${gradientAngle}deg, ${theme.backgroundGradient[0]}, ${theme.backgroundGradient[1]})`
    : bgColor;

  // ── glow overlay for high glow scenes ──
  const accentColor = cs.accentOverride || theme.accent;
  const showGlow = cs.glowIntensity > 0.4;
  const glowPulse = 1 + 0.05 * Math.sin(t * 2);

  // ── build content flex alignment ──
  const justifyContent = cs.flexAlign === "flex-start"
    ? "flex-start"
    : cs.flexAlign === "flex-end"
      ? "flex-end"
      : "center";
  const alignItems = cs.textAlign === "left"
    ? "flex-start"
    : cs.textAlign === "right"
      ? "flex-end"
      : "center";

  return (
    <AbsoluteFill
      style={{
        backgroundColor: bgColor,
        background,
        justifyContent: "center",
        alignItems: "center",
        opacity,
        transform: [transform, motionTransform].filter(Boolean).join(" "),
        overflow: "hidden",
      }}
    >
      {/* Background image layer — LLM-assigned per scene */}
      {imagePath && (
        <Img
          src={imagePath.startsWith("http") || imagePath.startsWith("file") ? imagePath : staticFile(imagePath)}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            zIndex: -1,
          }}
        />
      )}
      {/* Dark overlay on top of background image for text readability */}
      {imagePath && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `linear-gradient(180deg, ${bgColor}44 0%, ${bgColor}22 40%, ${bgColor}66 100%)`,
            zIndex: 0,
          }}
        />
      )}

      {/* Background decorations with dynamic style */}
      <BackgroundDecorations
        theme={theme}
        density={cs.decorationDensity}
      />

      {/* Ambient glow behind content */}
      {showGlow && (
        <div
          style={{
            position: "absolute",
            width: "80%",
            height: "40%",
            borderRadius: "50%",
            background: `radial-gradient(ellipse, ${accentColor}${Math.round(cs.glowIntensity * 25).toString(16).padStart(2, "0")} 0%, transparent 70%)`,
            transform: `scale(${glowPulse})`,
            pointerEvents: "none",
            zIndex: 0,
            filter: "blur(40px)",
          }}
        />
      )}

      {/* Large background watermark icon */}
      {icon && (
        <div
          style={{
            position: "absolute",
            fontSize: cs.glowIntensity > 0.6 ? 350 : 280,
            opacity: 0.03 + cs.glowIntensity * 0.03,
            pointerEvents: "none",
            transform: `translateY(${Math.sin(t * 0.4) * 8}px)`,
            filter: cs.glowIntensity > 0.5 ? `drop-shadow(0 0 ${cs.glowIntensity * 30}px ${accentColor})` : "none",
          }}
        >
          {icon}
        </div>
      )}

      {/* Content layer */}
      <div
        style={{
          position: "relative",
          zIndex: 1,
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent,
          alignItems,
          padding: cs.textAlign === "left" ? "0 80px" : cs.textAlign === "right" ? "0 80px" : 40,
        }}
      >
        {children}
      </div>
    </AbsoluteFill>
  );
};
