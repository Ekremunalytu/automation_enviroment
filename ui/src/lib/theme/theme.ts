import { useSyncExternalStore } from "react";

// Console color theme. The palette hex values live in `src/index.css`
// (`:root` = shift5 dark default; `:root[data-palette="parchment"|"terminal"]`
// overrides). This module persists the operator's choice and paints it onto
// <html data-palette="…"> so every `var(--…)`-backed surface re-themes.
export type ThemeId = "shift5" | "parchment" | "terminal";

export const THEMES: ReadonlyArray<{ id: ThemeId; label: string }> = [
  { id: "shift5", label: "Shift5" },
  { id: "parchment", label: "Parchment" },
  { id: "terminal", label: "Terminal" },
];

export const DEFAULT_THEME: ThemeId = "shift5";

const STORAGE_KEY = "extrace-v3-theme";

export function isThemeId(value: unknown): value is ThemeId {
  return value === "shift5" || value === "parchment" || value === "terminal";
}

export function loadTheme(): ThemeId {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return isThemeId(raw) ? raw : DEFAULT_THEME;
  } catch {
    return DEFAULT_THEME;
  }
}

/** Paint the theme onto <html data-palette="…">. The default (shift5) palette
 * is the bare `:root`, so any value still leaves the dark defaults intact. */
export function applyTheme(theme: ThemeId): void {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.palette = theme;
}

let current: ThemeId = DEFAULT_THEME;
const listeners = new Set<() => void>();

export function getTheme(): ThemeId {
  return current;
}

export function setTheme(theme: ThemeId): void {
  current = theme;
  try {
    window.localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    /* localStorage unavailable — apply for this session only */
  }
  applyTheme(theme);
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Initialise the store from localStorage and paint <html> before first
 * render, so the opening paint is already themed. Call once at app start. */
export function initTheme(): ThemeId {
  current = loadTheme();
  applyTheme(current);
  return current;
}

/** Subscribe a component to the active theme. Returns `[theme, setTheme]`. */
export function useTheme(): [ThemeId, (theme: ThemeId) => void] {
  const theme = useSyncExternalStore(subscribe, getTheme, () => DEFAULT_THEME);
  return [theme, setTheme];
}
