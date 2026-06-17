/** Scene types supported by the video renderer */
export type SceneType =
  | "title"
  | "text_sequence"
  | "highlight"
  | "image_text"
  | "bullet_points"
  | "ending"
  | "data_card"
  | "comparison"
  | "keyword_burst"
  | "progress_bar";

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
  /** English search query for image_text scenes (10-30 chars) */
  image_query?: string;
  /** Optional emoji/icon to display as a visual anchor (e.g. "🤖", "⚡", "🧠") */
  icon?: string;
  duration: number;
  animation?: AnimationStyle;
  /** Free-form visual style description (e.g. "cyberpunk neon, bold", "minimal zen, calm") */
  visual_style?: string;
  /** Emotional mood of this scene: "urgent", "calm", "inspiring", "mysterious", "playful", "serious", "hopeful", "dramatic" */
  mood?: string;
  /** Layout preference: "split left-right", "spotlight center", "left aligned", "stacked cards", "timeline left", "corner pinned", "wide spread" */
  layout_hint?: string;

  // ── Data visualization fields (data_card / comparison / keyword_burst) ──
  /** Label shown above a data_card number */
  visual_label?: string;
  /** Numeric value for data_card (counts up from 0) */
  visual_value?: number;
  /** Unit text for data_card (e.g. "倍", "%", "万") */
  visual_unit?: string;
  /** Trend direction for data_card arrow animation */
  visual_trend?: "up" | "down" | "flat";
  /** Left-side text for comparison scene */
  visual_left?: string;
  /** Right-side text for comparison scene */
  visual_right?: string;
  /** Keywords to burst onto screen (keyword_burst) */
  visual_keywords?: string[];
  /** Progress value 0-100 for progress_bar */
  visual_progress?: number;
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
