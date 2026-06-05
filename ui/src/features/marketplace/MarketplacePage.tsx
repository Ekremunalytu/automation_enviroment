import { useSearchParams } from "react-router-dom";

import { Eyebrow, PageTitle, Tabs, V3 } from "../../components/v3";
import type { TabSpec } from "../../components/v3";
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

  const isOffline = tab === "offline";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 40 }}>
      <header style={{ paddingBottom: 24, borderBottom: `1px solid ${V3.rule2}` }}>
        <Eyebrow>Extension intake</Eyebrow>
        <PageTitle style={{ marginTop: 14 }}>Find, download, analyze.</PageTitle>
        <p
          style={{
            fontSize: 15,
            color: V3.ink3,
            marginTop: 14,
            maxWidth: 580,
            lineHeight: 1.6,
          }}
        >
          {isOffline
            ? "Stage extensions from a local .vsix drop folder for air-gapped runs, then hand each one to the sandbox. No marketplace egress required."
            : "Search the VS Code marketplace, shortlist a candidate, then hand it to the sandbox. Each download adds one entry to the local catalog."}
        </p>
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

      {isOffline ? <OfflineIntakePanel /> : <OnlineIntakePanel />}
    </div>
  );
}
