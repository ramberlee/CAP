import { ThemePalette, ThemeId } from "./types";

export const themes: Record<string, ThemePalette> = {
  dark_tech: {
    background: "#0D1117",
    backgroundGradient: ["#0D1117", "#161B22"],
    text: "#FFFFFF",
    textSecondary: "#8B949E",
    accent: "#58A6FF",
    accentSecondary: "#FFD700",
    surface: "#161B22",
    surfaceBorder: "#30363D",
  },
  light_clean: {
    background: "#FFFFFF",
    backgroundGradient: ["#FFFFFF", "#F6F8FA"],
    text: "#1F2328",
    textSecondary: "#656D76",
    accent: "#0969DA",
    accentSecondary: "#BF3989",
    surface: "#F6F8FA",
    surfaceBorder: "#D0D7DE",
  },
  vibrant: {
    background: "#1A0A2E",
    backgroundGradient: ["#1A0A2E", "#16213E"],
    text: "#FFFFFF",
    textSecondary: "#E0AAFF",
    accent: "#FF6B35",
    accentSecondary: "#F7C948",
    surface: "#1A1A3E",
    surfaceBorder: "#4A1A6E",
  },
  minimal: {
    background: "#000000",
    text: "#FFFFFF",
    textSecondary: "#AAAAAA",
    accent: "#FFFFFF",
    accentSecondary: "#888888",
    surface: "#111111",
    surfaceBorder: "#333333",
  },
  news: {
    background: "#F0F2F5",
    backgroundGradient: ["#F0F2F5", "#E8ECF0"],
    text: "#1A1A2E",
    textSecondary: "#4A4A6A",
    accent: "#E63946",
    accentSecondary: "#1D3557",
    surface: "#FFFFFF",
    surfaceBorder: "#D0D7DE",
  },
};

export function getTheme(themeId: string): ThemePalette {
  return themes[themeId] || themes.dark_tech;
}
