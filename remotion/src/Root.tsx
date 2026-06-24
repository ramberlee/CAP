import React from "react";
import { Composition, registerRoot } from "remotion";
import VideoComposition from "./VideoComposition";
import { SceneOpening } from "./scenes/SceneOpening";

const defaultPlan: Record<string, unknown> = {} as Record<string, unknown>;

const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="SceneOpening"
        component={SceneOpening}
        durationInFrames={150}
        fps={30}
        width={960}
        height={540}
      />
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
