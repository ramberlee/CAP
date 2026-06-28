import React from 'react';
import { Composition, registerRoot } from 'remotion';
import VideoComposition from './VideoComposition';
import { CompositionPlan } from './types';

const FPS = 24;
const WIDTH = 1920;
const HEIGHT = 1080;
const MAX_DURATION_FRAMES = 180 * FPS; // upper bound

const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CAPVideo"
      component={VideoComposition}
      durationInFrames={MAX_DURATION_FRAMES}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      calculateMetadata={({ props }) => {
        const plan = (props as any)?.plan as CompositionPlan | undefined;
        if (plan?.scenes?.length) {
          const totalSec = plan.scenes.reduce((s, sc) => s + (sc.duration || 3), 0);
          return { durationInFrames: Math.ceil(totalSec * FPS) };
        }
        return { durationInFrames: MAX_DURATION_FRAMES };
      }}
      defaultProps={{
        plan: {
          theme: 'dark_glass',
          scenes: [],
        },
      }}
    />
  );
};

registerRoot(RemotionRoot);
