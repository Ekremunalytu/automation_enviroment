import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";

import { PageTitle, Tabs, V3 } from "../../components/v3";
import type { TabSpec } from "../../components/v3";
import { apiClient } from "../../lib/api/client";
import { OnlineIntakePanel } from "./OnlineIntakePanel";
import { OfflineIntakePanel } from "./OfflineIntakePanel";

type MarketTab = "marketplace" | "offline";

const MARKET_TABS: TabSpec<MarketTab>[] = [
  { value: "marketplace", label: "Marketplace" },
  { value: "offline", label: "Offline" },
];

function tabFromParam(raw: string | null): MarketTab {
  return raw === "offline" ? "offline" : "marketplace";
}

export function MarketplacePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = tabFromParam(searchParams.get("tab"));
  const executorPreferencesQuery = useQuery({
    queryKey: ["executor-preferences"],
    queryFn: ({ signal }) => apiClient.getExecutorPreferences(signal),
    staleTime: 30_000,
  });

  const isOffline = tab === "offline";
  const dynamicAnalysisEnabled =
    executorPreferencesQuery.data?.dynamic_analysis_enabled ?? false;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 40 }}>
      <header style={{ paddingBottom: 24, borderBottom: `1px solid ${V3.rule2}` }}>
        <PageTitle>Find, download, analyze.</PageTitle>
      </header>

      <Tabs<MarketTab>
        ariaLabel="Extension intake source"
        tabs={MARKET_TABS}
        value={tab}
        onChange={(nextTab) => {
          const params = new URLSearchParams(searchParams);
          params.set("tab", nextTab);
          setSearchParams(params, { replace: true });
        }}
      />

      {executorPreferencesQuery.isLoading ? (
        <p role="status" style={{ color: V3.ink3, fontSize: 13 }}>
          Loading dynamic scan preference before intake actions…
        </p>
      ) : isOffline ? (
        <OfflineIntakePanel dynamicAnalysisEnabled={dynamicAnalysisEnabled} />
      ) : (
        <OnlineIntakePanel dynamicAnalysisEnabled={dynamicAnalysisEnabled} />
      )}
    </div>
  );
}
