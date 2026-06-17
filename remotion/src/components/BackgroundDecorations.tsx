import React, { useMemo } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { ThemePalette } from "../types";

interface BackgroundDecorationsProps {
  theme: ThemePalette;
  /** Density of decorations: "subtle" | "moderate" | "rich" */
  density?: "subtle" | "moderate" | "rich";
}

/**
 * Animated background decorations: floating orbs, rotating shapes,
 * and subtle geometric patterns that add visual depth to any scene.
 */
const BackgroundDecorations: React.FC<BackgroundDecorationsProps> = ({
  theme,
  density = "moderate",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // Pre-generate stable decorative elements positions
  const decorations = useMemo(() => {
    const orbs: Array<{
      id: number;
      x: number;
      y: number;
      size: number;
      speed: number;
      phaseX: number;
      phaseY: number;
      opacity: number;
      color: string;
    }> = [];

    const orbColors = [theme.accent, theme.accentSecondary, theme.textSecondary];
    const counts: Record<string, number> = { subtle: 3, moderate: 5, rich: 8 };
    const count = counts[density] || 5;

    for (let i = 0; i < count; i++) {
      orbs.push({
        id: i,
        x: 10 + Math.random() * 80, // % from left
        y: 10 + Math.random() * 80, // % from top
        size: 40 + Math.random() * 120,
        speed: 0.3 + Math.random() * 0.7,
        phaseX: Math.random() * Math.PI * 2,
        phaseY: Math.random() * Math.PI * 2,
        opacity: 0.03 + Math.random() * 0.06,
        color: orbColors[i % orbColors.length],
      });
    }

    return { orbs };
  }, [theme, density]);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        pointerEvents: "none",
        zIndex: 0,
      }}
    >
      {/* Floating orbs */}
      {decorations.orbs.map((orb) => {
        const floatX = Math.sin(t * orb.speed + orb.phaseX) * 8;
        const floatY = Math.cos(t * orb.speed * 0.7 + orb.phaseY) * 6;
        const pulse = 1 + 0.05 * Math.sin(t * orb.speed * 1.5);

        return (
          <div
            key={`orb-${orb.id}`}
            style={{
              position: "absolute",
              left: `calc(${orb.x}% + ${floatX}px)`,
              top: `calc(${orb.y}% + ${floatY}px)`,
              width: orb.size,
              height: orb.size,
              borderRadius: "50%",
              background: `radial-gradient(circle, ${orb.color} 0%, transparent 70%)`,
              opacity: orb.opacity,
              transform: `scale(${pulse})`,
              filter: "blur(20px)",
            }}
          />
        );
      })}

      {/* Subtle dot grid — only for moderate and rich */}
      {density !== "subtle" && (
        <DotGrid
          theme={theme}
          opacity={density === "rich" ? 0.06 : 0.03}
          t={t}
        />
      )}

      {/* Corner decorations — only for rich */}
      {density === "rich" && <CornerDecorations theme={theme} t={t} />}
    </div>
  );
};

/** Subtle animated dot grid */
const DotGrid: React.FC<{
  theme: ThemePalette;
  opacity: number;
  t: number;
}> = ({ theme, opacity, t }) => {
  const dots = useMemo(() => {
    const result: Array<{ x: number; y: number }> = [];
    const spacing = 120;
    for (let x = 0; x < 1080; x += spacing) {
      for (let y = 0; y < 1920; y += spacing) {
        result.push({ x, y });
      }
    }
    return result;
  }, []);

  return (
    <div style={{ position: "absolute", inset: 0, opacity }}>
      {dots.map((dot, i) => {
        const flicker = 0.5 + 0.5 * Math.sin(t * 0.8 + i * 0.7);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: dot.x,
              top: dot.y,
              width: 2,
              height: 2,
              borderRadius: "50%",
              background: theme.text,
              opacity: 0.3 + flicker * 0.7,
            }}
          />
        );
      })}
    </div>
  );
};

/** Decorative lines/arcs in corners */
const CornerDecorations: React.FC<{
  theme: ThemePalette;
  t: number;
}> = ({ theme, t }) => {
  const rotate = t * 15; // degrees per second

  return (
    <>
      {/* Top-right arc */}
      <div
        style={{
          position: "absolute",
          top: -100,
          right: -100,
          width: 300,
          height: 300,
          borderRadius: "50%",
          border: `1px solid ${theme.accent}15`,
          borderRightColor: "transparent",
          borderBottomColor: "transparent",
          transform: `rotate(${rotate}deg)`,
        }}
      />
      {/* Bottom-left arc */}
      <div
        style={{
          position: "absolute",
          bottom: -150,
          left: -150,
          width: 400,
          height: 400,
          borderRadius: "50%",
          border: `1px solid ${theme.accentSecondary}10`,
          borderLeftColor: "transparent",
          borderTopColor: "transparent",
          transform: `rotate(${-rotate * 0.7}deg)`,
        }}
      />
    </>
  );
};

export default BackgroundDecorations;
