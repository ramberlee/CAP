import React from "react";
import { Composition, registerRoot } from "remotion";
import VideoComposition from "./VideoComposition";

const defaultPlan: Record<string, unknown> = {} as Record<string, unknown>;

const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="CAPVideo"
        component={VideoComposition}
        durationInFrames={3141}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={defaultPlan}
      />
    </>
  );
};

registerRoot(RemotionRoot);
