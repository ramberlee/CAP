import React from "react";
import { Composition, registerRoot } from "remotion";
import VideoComposition from "./VideoComposition";

/**
 * Calculate total duration (in frames) from props.
 * Reads durationInFrames directly (set by Python), or falls back to
 * summing scene durations from the plan.
 */
function calcDurationFrames(props: Record<string, unknown> | undefined): number {
  // If Python pre-calculated durationInFrames, use it directly
  if (props?.durationInFrames && typeof props.durationInFrames === "number") {
    return props.durationInFrames as number;
  }

  // Fallback: calculate from plan scenes
  const plan = props?.plan as Record<string, unknown> | undefined;
  const scenes = plan?.scenes as Array<Record<string, unknown>> | undefined;
  if (!scenes || scenes.length === 0) return 90; // 3s default

  let totalSec = 0;
  for (const s of scenes) {
    totalSec += (s.duration as number) || 3;
  }
  totalSec = Math.max(3, totalSec + 1);
  return Math.round(totalSec * 30);
}

const defaultPlan: Record<string, unknown> = {
  plan: {
    title: "示例视频",
    theme: "dark_tech",
    scenes: [
      { type: "title", text: "示例视频", duration: 3, animation: "scale_in" },
      {
        type: "text_sequence",
        lines: ["这是 Remotion 生成的", "动态视频"],
        duration: 4,
        animation: "fade_in",
      },
      {
        type: "ending",
        text: "感谢观看",
        duration: 3,
        animation: "fade_out",
      },
    ],
  },
};

const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="CAPVideo"
        component={VideoComposition}
        durationInFrames={calcDurationFrames(defaultPlan)}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultPlan}
        calculateMetadata={async ({ props }) => {
          const p = props as Record<string, unknown>;
          return {
            durationInFrames: calcDurationFrames(p),
            fps: 30,
            width: 1080,
            height: 1920,
          };
        }}
      />
    </>
  );
};

registerRoot(RemotionRoot);
