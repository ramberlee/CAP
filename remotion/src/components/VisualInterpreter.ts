/**
 * Dynamic Visual Style Interpreter
 * 
 * Maps LLM-generated visual descriptions (free-form text) into concrete
 * CSS styles and rendering parameters. This allows every scene to have
 * a unique visual identity instead of following rigid templates.
 */

import { ThemePalette } from "../types";

/** The full set of computed visual styles for a scene */
export interface ComputedStyle {
  // Text
  fontSize: number;
  fontWeight: number;
  textShadow: string;
  letterSpacing: number;
  lineHeight: number;

  // Colors (overrides theme palette)
  accentOverride: string | null;
  textColorOverride: string | null;
  bgOverride: string | null;

  // Layout
  textAlign: "center" | "left" | "right";
  flexAlign: "center" | "flex-start" | "flex-end";
  maxWidth: string;

  // Decorations
  decorationDensity: "subtle" | "moderate" | "rich";
  decorationStyle: "orb" | "line" | "grid" | "particle" | "geometric";
  glowIntensity: number; // 0-1

  // Motion
  animationSpeed: "slow" | "normal" | "fast";
  motionStyle: "gentle" | "bold" | "none";
  entrancePattern: "stagger" | "wave" | "burst" | "cascade";

  // Mood-based
  colorTemperature: "warm" | "cool" | "neutral";
  contrastLevel: "low" | "medium" | "high";
}

/** Default style when no visual description is provided */
const DEFAULT_STYLE: ComputedStyle = {
  fontSize: 48,
  fontWeight: 600,
  textShadow: "none",
  letterSpacing: 0,
  lineHeight: 1.4,
  accentOverride: null,
  textColorOverride: null,
  bgOverride: null,
  textAlign: "center",
  flexAlign: "center",
  maxWidth: "90%",
  decorationDensity: "moderate",
  decorationStyle: "orb",
  glowIntensity: 0.3,
  animationSpeed: "normal",
  motionStyle: "gentle",
  entrancePattern: "stagger",
  colorTemperature: "neutral",
  contrastLevel: "medium",
};

// ── keyword → style mapping tables ──────────────────────────────

/** Map visual style keywords to overrides */
const STYLE_KEYWORDS: Record<string, Partial<ComputedStyle>> = {
  // ── tech / futuristic ──
  cyberpunk: {
    glowIntensity: 0.9, contrastLevel: "high", colorTemperature: "cool",
    decorationStyle: "geometric", motionStyle: "bold", textShadow: "0 0 30px currentColor",
  },
  neon: {
    glowIntensity: 0.95, contrastLevel: "high", colorTemperature: "cool",
    textShadow: "0 0 40px currentColor, 0 0 80px currentColor", decorationStyle: "line",
  },
  holographic: {
    glowIntensity: 0.7, letterSpacing: 3, colorTemperature: "cool",
    decorationStyle: "grid", motionStyle: "gentle",
  },
  scifi: {
    glowIntensity: 0.6, contrastLevel: "high", decorationStyle: "geometric",
    letterSpacing: 2, motionStyle: "bold",
  },
  digital: {
    glowIntensity: 0.4, decorationStyle: "grid", letterSpacing: 1,
    colorTemperature: "cool",
  },
  matrix: {
    glowIntensity: 0.8, colorTemperature: "cool", contrastLevel: "high",
    decorationStyle: "line", textShadow: "0 0 20px currentColor",
  },

  // ── elegant / premium ──
  luxurious: {
    glowIntensity: 0.4, letterSpacing: 3, fontWeight: 700,
    decorationStyle: "geometric", motionStyle: "gentle", colorTemperature: "warm",
  },
  cinematic: {
    glowIntensity: 0.3, contrastLevel: "high", colorTemperature: "warm",
    decorationStyle: "line", motionStyle: "gentle", letterSpacing: 2,
  },
  elegant: {
    glowIntensity: 0.2, letterSpacing: 2, fontWeight: 300,
    decorationStyle: "line", motionStyle: "gentle", colorTemperature: "neutral",
  },
  premium: {
    glowIntensity: 0.3, fontWeight: 700, letterSpacing: 2,
    decorationStyle: "geometric", motionStyle: "gentle",
  },

  // ── bold / energetic ──
  explosive: {
    glowIntensity: 1.0, motionStyle: "bold", animationSpeed: "fast",
    entrancePattern: "burst", contrastLevel: "high", decorationDensity: "rich",
  },
  energetic: {
    motionStyle: "bold", animationSpeed: "fast", decorationDensity: "rich",
    entrancePattern: "wave", contrastLevel: "high",
  },
  dynamic: {
    motionStyle: "bold", animationSpeed: "normal", entrancePattern: "wave",
    decorationDensity: "moderate",
  },
  bold: {
    fontWeight: 800, fontSize: 64, contrastLevel: "high",
    motionStyle: "bold", decorationDensity: "moderate",
  },
  impactful: {
    fontWeight: 800, fontSize: 60, contrastLevel: "high",
    motionStyle: "bold", entrancePattern: "burst",
  },

  // ── calm / minimal ──
  minimal: {
    glowIntensity: 0.05, decorationDensity: "subtle", contrastLevel: "low",
    decorationStyle: "line", motionStyle: "none", letterSpacing: 1,
  },
  zen: {
    glowIntensity: 0, decorationDensity: "subtle", motionStyle: "none",
    decorationStyle: "line", colorTemperature: "neutral", contrastLevel: "low",
  },
  calm: {
    animationSpeed: "slow", motionStyle: "gentle", decorationDensity: "subtle",
    entrancePattern: "stagger", contrastLevel: "low",
  },
  clean: {
    glowIntensity: 0.1, decorationDensity: "subtle", letterSpacing: 1,
    contrastLevel: "medium", decorationStyle: "line",
  },
  soft: {
    glowIntensity: 0.15, animationSpeed: "slow", motionStyle: "gentle",
    contrastLevel: "low", colorTemperature: "warm",
  },

  // ── playful / creative ──
  playful: {
    decorationDensity: "rich", decorationStyle: "particle",
    entrancePattern: "burst", motionStyle: "bold", colorTemperature: "warm",
  },
  creative: {
    decorationStyle: "geometric", motionStyle: "bold",
    entrancePattern: "wave", letterSpacing: 1,
  },
  vibrant: {
    contrastLevel: "high", colorTemperature: "warm", decorationDensity: "rich",
    decorationStyle: "particle", glowIntensity: 0.5,
  },
  pop: {
    contrastLevel: "high", decorationStyle: "geometric", motionStyle: "bold",
    animationSpeed: "fast", letterSpacing: -0.5,
  },

  // ── mood overrides ──
  urgent: {
    animationSpeed: "fast", motionStyle: "bold", contrastLevel: "high",
    colorTemperature: "warm", entrancePattern: "burst",
  },
  mysterious: {
    glowIntensity: 0.5, contrastLevel: "high", colorTemperature: "cool",
    decorationStyle: "orb", motionStyle: "gentle", letterSpacing: 2,
  },
  inspiring: {
    glowIntensity: 0.5, colorTemperature: "warm", motionStyle: "bold",
    entrancePattern: "wave", fontWeight: 700,
  },
  serious: {
    decorationDensity: "subtle", motionStyle: "none", contrastLevel: "high",
    fontWeight: 700, letterSpacing: 1,
  },
  hopeful: {
    colorTemperature: "warm", motionStyle: "gentle", glowIntensity: 0.4,
    entrancePattern: "stagger",
  },
  dramatic: {
    glowIntensity: 0.8, contrastLevel: "high", motionStyle: "bold",
    entrancePattern: "burst", animationSpeed: "fast",
  },
};

/** Layout hints → flex/align overrides */
const LAYOUT_HINTS: Record<string, Partial<ComputedStyle>> = {
  "split left-right": { textAlign: "left", flexAlign: "flex-start", maxWidth: "55%" },
  "left aligned": { textAlign: "left", flexAlign: "flex-start" },
  "right aligned": { textAlign: "right", flexAlign: "flex-end" },
  "spotlight center": { textAlign: "center", flexAlign: "center", maxWidth: "70%" },
  "stacked cards": { textAlign: "left", flexAlign: "center", maxWidth: "80%" },
  "wide spread": { textAlign: "center", maxWidth: "100%" },
  "timeline left": { textAlign: "left", flexAlign: "flex-start", maxWidth: "75%" },
  "corner pinned": { textAlign: "left", flexAlign: "flex-end", maxWidth: "60%" },
};

// ── the interpreter ─────────────────────────────────────────────

/**
 * Compute visual styles from LLM-provided descriptions.
 * 
 * @param visualStyle  Free-form style description (e.g. "cyberpunk neon, bold")
 * @param mood         Emotional tone (e.g. "urgent", "calm", "inspiring")
 * @param layoutHint   Layout preference (e.g. "split left-right", "spotlight center")
 * @param theme        Current theme palette for context
 * @returns            ComputedStyle with all rendering parameters
 */
export function computeStyle(
  visualStyle: string | undefined,
  mood: string | undefined,
  layoutHint: string | undefined,
  theme: ThemePalette
): ComputedStyle {
  // Start with defaults
  const style: ComputedStyle = { ...DEFAULT_STYLE };

  // Collect all keywords from visual style description
  const allKeywords = (visualStyle || "").toLowerCase()
    .split(/[\s,，、|/]+/)
    .filter(Boolean);

  // Also check mood as a keyword
  if (mood) {
    allKeywords.push(mood.toLowerCase());
  }

  // Apply keyword-based overrides (later keywords override earlier ones)
  for (const kw of allKeywords) {
    const overrides = STYLE_KEYWORDS[kw];
    if (overrides) {
      Object.assign(style, overrides);
    }
  }

  // Apply layout hints
  if (layoutHint) {
    const hint = LAYOUT_HINTS[layoutHint.toLowerCase()];
    if (hint) {
      Object.assign(style, hint);
    }
  }

  // ── derive accent color from mood if not explicitly set ──
  if (!style.accentOverride) {
    if (style.colorTemperature === "warm") {
      // Shift toward warm: use accentSecondary or warm accent
      style.accentOverride = theme.accentSecondary || theme.accent;
    } else if (style.colorTemperature === "cool") {
      style.accentOverride = theme.accent;
    }
  }

  // ── cap/extend values based on theme contrast ──
  if (style.contrastLevel === "high") {
    style.fontWeight = Math.max(style.fontWeight, 700);
  } else if (style.contrastLevel === "low") {
    style.fontWeight = Math.min(style.fontWeight, 400);
  }

  // ── glow intensity → text shadow ──
  if (style.glowIntensity > 0.5 && !visualStyle?.includes("shadow")) {
    const accent = style.accentOverride || theme.accent;
    const alpha = Math.round(style.glowIntensity * 60);
    style.textShadow = [
      `0 0 ${20 * style.glowIntensity}px ${accent}${alpha.toString(16).padStart(2, "0")}`,
      `0 0 ${50 * style.glowIntensity}px ${accent}${Math.round(alpha * 0.5).toString(16).padStart(2, "0")}`,
    ].join(", ");
  }

  return style;
}

/**
 * Get CSS animation duration based on speed preference.
 */
export function getAnimationDuration(speed: ComputedStyle["animationSpeed"]): number {
  switch (speed) {
    case "fast": return 0.3;
    case "slow": return 0.8;
    default: return 0.5;
  }
}

/**
 * Ease-out cubic: fast start, smooth deceleration.
 */
export function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

/**
 * Ease-in-out cubic: smooth acceleration and deceleration.
 */
export function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

/**
 * Get entrance stagger delay for items based on pattern.
 */
export function getStaggerDelay(
  index: number,
  total: number,
  pattern: ComputedStyle["entrancePattern"],
  baseDelay: number = 0.2
): number {
  switch (pattern) {
    case "burst":
      // All items come in almost simultaneously
      return index * 0.05;
    case "wave":
      // Sine wave pattern — middle items appear first
      const mid = (total - 1) / 2;
      return Math.abs(index - mid) * baseDelay * 0.5;
    case "cascade":
      // Fast sequential
      return index * baseDelay * 0.7;
    case "stagger":
    default:
      return index * baseDelay;
  }
}
