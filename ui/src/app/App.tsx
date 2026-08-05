import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./layout/AppShell";
import { EmptyState } from "../components/v3";

const ReportsPage = lazy(async () => ({
  default: (await import("../features/reports")).ReportsPage,
}));
const SimulationPage = lazy(async () => ({
  default: (await import("../features/simulation")).SimulationPage,
}));
const MarketplacePage = lazy(async () => ({
  default: (await import("../features/marketplace")).MarketplacePage,
}));
const RulesPage = lazy(async () => ({
  default: (await import("../features/rules")).RulesPage,
}));
const SettingsPage = lazy(async () => ({
  default: (await import("../features/settings")).SettingsPage,
}));
const SystemPage = lazy(async () => ({
  default: (await import("../features/system")).SystemPage,
}));
export function App() {
  return (
    <AppShell>
      <Suspense
        fallback={
          <EmptyState
            eyebrow="Loading"
            body="Preparing the selected investigation surface."
            title="Opening analyst workspace"
          />
        }
      >
        <Routes>
          <Route element={<Navigate replace to="/reports?report=latest&tab=overview" />} path="/" />
          <Route element={<ReportsPage />} path="/reports" />
          <Route element={<SimulationPage />} path="/simulation" />
          <Route element={<MarketplacePage />} path="/marketplace" />
          <Route element={<RulesPage />} path="/rules" />
          <Route element={<SettingsPage />} path="/settings" />
          <Route element={<SystemPage />} path="/system" />
        </Routes>
      </Suspense>
    </AppShell>
  );
}
