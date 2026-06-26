import { Scene } from '../types';
import { ThemePalette } from '../themes';

/** Props passed to each scene component by VideoComposition */
export interface SceneComponentProps {
  scene: Scene;
  theme: ThemePalette;
  frame: number;
  fps: number;
  startFrame: number;
}
