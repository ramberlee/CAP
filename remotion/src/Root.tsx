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
        durationInFrames={1401}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultPlan}
      />
    </>
  );
};

registerRoot(RemotionRoot);
