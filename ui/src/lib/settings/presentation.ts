import { useSyncExternalStore } from "react";

// Presentation settings that are legitimately the browser's concern (no
// backend effect), so they are real, persisted client-side, and applied live.
// Theme lives in `lib/theme/theme.ts`; this module owns density + time zone.
export type DensityId = "compact" | "comfortable" | "spacious";

export const DENSITIES: ReadonlyArray<{ id: DensityId; label: string }> = [
  { id: "compact", label: "Compact" },
  { id: "comfortable", label: "Comfortable" },
  { id: "spacious", label: "Spacious" },
];

// Curated IANA zones + "local" (the browser default). `resolveTimeZone`
// maps "local" → undefined so `toLocale*` uses the browser zone.
export const TIME_ZONES: ReadonlyArray<{ id: string; label: string }> = [
  { id: "local", label: "Browser local" },
  { id: "UTC", label: "UTC" },
  { id: "Europe/Istanbul", label: "Istanbul" },
  { id: "Europe/London", label: "London" },
  { id: "Europe/Berlin", label: "Berlin" },
  { id: "America/New_York", label: "New York" },
  { id: "America/Los_Angeles", label: "Los Angeles" },
  { id: "Asia/Tokyo", label: "Tokyo" },
];

export const DEFAULT_DENSITY: DensityId = "comfortable";
export const DEFAULT_TIME_ZONE = "local";

export interface PresentationSettings {
  density: DensityId;
  timeZone: string;
}

const STORAGE_KEY = "extrace-v3-presentation";
const VALID_ZONES = new Set(TIME_ZONES.map((zone) => zone.id));

function isDensity(value: unknown): value is DensityId {
  return value === "compact" || value === "comfortable" || value === "spacious";
}

function defaults(): PresentationSettings {
  return { density: DEFAULT_DENSITY, timeZone: DEFAULT_TIME_ZONE };
}

export function loadPresentation(): PresentationSettings {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaults();
    const parsed = JSON.parse(raw) as Partial<PresentationSettings>;
    return {
      density: isDensity(parsed.density) ? parsed.density : DEFAULT_DENSITY,
      timeZone:
        typeof parsed.timeZone === "string" && VALID_ZONES.has(parsed.timeZone)
          ? parsed.timeZone
          : DEFAULT_TIME_ZONE,
    };
  } catch {
    return defaults();
  }
}

let current: PresentationSettings = defaults();
const listeners = new Set<() => void>();

function persist(): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
  } catch {
    /* localStorage unavailable — session-only */
  }
}

function notify(): void {
  listeners.forEach((listener) => listener());
}

/** Paint density onto <html data-density="…"> so `--v3-row-pad-y` re-resolves. */
export function applyDensity(density: DensityId): void {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.density = density;
}

export function getDensity(): DensityId {
  return current.density;
}

export function getTimeZone(): string {
  return current.timeZone;
}

/** Resolve the stored zone to a `toLocale*` `timeZone` option — "local" (or an
 * unknown value) → undefined, i.e. the browser's own zone. */
export function resolveTimeZone(zone: string = current.timeZone): string | undefined {
  return zone && zone !== "local" ? zone : undefined;
}

export function setDensity(density: DensityId): void {
  current = { ...current, density };
  persist();
  applyDensity(density);
  notify();
}

export function setTimeZone(timeZone: string): void {
  current = { ...current, timeZone };
  persist();
  notify();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Load persisted presentation settings and paint density. Call once at start. */
export function initPresentation(): PresentationSettings {
  current = loadPresentation();
  applyDensity(current.density);
  return current;
}

export function useDensity(): [DensityId, (density: DensityId) => void] {
  const density = useSyncExternalStore(subscribe, getDensity, () => DEFAULT_DENSITY);
  return [density, setDensity];
}

export function useTimeZone(): [string, (timeZone: string) => void] {
  const timeZone = useSyncExternalStore(subscribe, getTimeZone, () => DEFAULT_TIME_ZONE);
  return [timeZone, setTimeZone];
}
