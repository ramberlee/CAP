/** Scene types supported by the video renderer */
export type SceneType =
  | "title"
  | "text_sequence"
  | "highlight"
  | "image_text"
  | "bullet_points"
  | "ending";

/** Animation styles for different scene types */
export type AnimationStyle =
  | "fade_in"
  | "scale_in"
  | "slide_up"
  | "typewriter"
  | "pulse"
  | "zoom_in"
  | "fade_out";

/** Theme identifiers - can be extended by LLM */
export type ThemeId =
  | "dark_tech"
  | "light_clean"
  | "vibrant"
  | "minimal"
  | "news";

/** Theme color palette */
export interface ThemePalette {
  background: string;
  backgroundGradient?: [string, string];
  text: string;
  textSecondary: string;
  accent: string;
  accentSecondary: string;
  surface: string;
  surfaceBorder: string;
}

/** A single scene in the video composition plan */
export interface Scene {
  type: SceneType;
  text?: string;
  lines?: string[];
  items?: string[];
  imagePath?: string;
  duration: number;
  animation?: AnimationStyle;
}

/** Complete video composition plan produced by the LLM */
export interface CompositionPlan {
  title?: string;
  theme: ThemeId | string;
  scenes: Scene[];
  audioPath?: string;
  subtitles?: string;
  tags?: string[];
}

/** Input props passed to Remotion composition */
export interface RemotionInputProps {
  plan: CompositionPlan;
}
