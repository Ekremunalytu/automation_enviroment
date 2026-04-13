import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./layout/AppShell";
import { EmptyState } from "../components/ui/EmptyState";

const ReportsPage = lazy(async () => ({
  default: (await import("../features/reports/ReportsPage")).ReportsPage,
}));
const SimulationPage = lazy(async () => ({
  default: (await import("../features/simulation/SimulationPage")).SimulationPage,
}));
const MarketplacePage = lazy(async () => ({
  default: (await import("../features/marketplace/MarketplacePage")).MarketplacePage,
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
        </Routes>
      </Suspense>
    </AppShell>
  );
}
