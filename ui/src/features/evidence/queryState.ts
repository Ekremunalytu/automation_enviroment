import type { EvidenceFilterState } from "../../components/evidence/FilterRail";
import type { EvidenceEventView } from "../../lib/types/view-models";

export type InspectorTab = "provenance" | "relations" | "rules";

export function normalizeInspectorTab(raw: string | null): InspectorTab {
  if (raw === "relations" || raw === "rules") return raw;
  if (raw === "rule") return "rules";
  return "provenance";
}

export function parseEvidenceFilters(searchParams: URLSearchParams): EvidenceFilterState {
  return {
    kinds: searchParams.get("kind") ? [searchParams.get("kind")!] : [],
    actors: searchParams.get("actor") ? [searchParams.get("actor")!] : [],
    collectors: searchParams.get("collector") ? [searchParams.get("collector")!] : [],
    scenarios: searchParams.get("scenario") ? [searchParams.get("scenario")!] : [],
    sensitiveOnly: searchParams.get("sensitive") === "true",
    search: searchParams.get("search") || "",
  };
}

export function applyEvidenceFilters(searchParams: URLSearchParams, filters: EvidenceFilterState) {
  const params = new URLSearchParams(searchParams);
  const assign = (key: string, value?: string) => {
    if (value) params.set(key, value);
    else params.delete(key);
  };

  assign("kind", filters.kinds[0]);
  assign("actor", filters.actors[0]);
  assign("collector", filters.collectors[0]);
  assign("scenario", filters.scenarios[0]);
  assign("search", filters.search || undefined);

  if (filters.sensitiveOnly) params.set("sensitive", "true");
  else params.delete("sensitive");

  return params;
}

export function countEvidenceFilters(filters: EvidenceFilterState) {
  return [
    filters.kinds.length,
    filters.actors.length,
    filters.collectors.length,
    filters.scenarios.length,
    filters.sensitiveOnly ? 1 : 0,
    filters.search ? 1 : 0,
  ].reduce((sum, count) => sum + count, 0);
}

export function filterEvidenceEvents(
  events: EvidenceEventView[],
  filters: EvidenceFilterState,
  deferredSearch: string,
) {
  return events.filter((event) => {
    if (filters.kinds.length && !filters.kinds.includes(event.kindLabel)) return false;
    if (filters.actors.length && !filters.actors.includes(event.actorLabel)) return false;
    if (filters.collectors.length && !filters.collectors.includes(event.collectorLabel)) return false;
    if (filters.scenarios.length && !filters.scenarios.includes(event.scenarioName)) return false;
    if (filters.sensitiveOnly && !event.sensitive) return false;

    if (deferredSearch) {
      const haystack = [
        event.artifact,
        event.summaryDisplay,
        event.extensionId,
        event.host,
        event.path,
        event.scenarioName,
      ]
        .join(" ")
        .toLowerCase();
      if (!haystack.includes(deferredSearch.toLowerCase())) return false;
    }

    return true;
  });
}

export function buildEvidenceFilterOptions(events: EvidenceEventView[]) {
  return {
    kinds: [...new Set(events.map((event) => event.kindLabel))],
    actors: [...new Set(events.map((event) => event.actorLabel))],
    collectors: [...new Set(events.map((event) => event.collectorLabel))],
    scenarios: [...new Set(events.map((event) => event.scenarioName).filter(Boolean))],
  };
}
