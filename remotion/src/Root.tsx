import React from "react";
import { Composition, registerRoot } from "remotion";
import VideoComposition from "./VideoComposition";

// Maximum video duration in seconds (30 seconds should cover any video)
const MAX_DURATION_SECONDS = 30;
const MAX_DURATION_FRAMES = MAX_DURATION_SECONDS * 30;

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
        durationInFrames={MAX_DURATION_FRAMES}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultPlan}
      />
    </>
  );
};

registerRoot(RemotionRoot);
