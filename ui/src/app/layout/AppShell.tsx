import { useState, type PropsWithChildren } from "react";
import { NavLink, useLocation } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/reports?report=latest&tab=overview", label: "Reports", path: "/reports" },
  { to: "/simulation", label: "Simulation", path: "/simulation" },
  { to: "/marketplace", label: "Marketplace", path: "/marketplace" },
];

function PrimaryNav({ onNavigate }: { onNavigate?: () => void }) {
  const location = useLocation();

  return (
    <nav aria-label="Primary" className="flex flex-col gap-2 lg:flex-row lg:items-center">
      {NAV_ITEMS.map((item) => {
        const active = location.pathname.startsWith(item.path);
        return (
          <NavLink
            className={`nav-button ${active ? "nav-button-active" : ""}`}
            key={item.path}
            onClick={onNavigate}
            to={item.to}
          >
            {item.label}
          </NavLink>
        );
      })}
    </nav>
  );
}

export function AppShell({ children }: PropsWithChildren) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="sticky top-0 z-40 border-b border-line bg-canvas/92 backdrop-blur-xl">
        <div className="shell-frame">
          <div className="flex min-h-[78px] items-center justify-between gap-4">
            <div className="flex min-w-0 items-center gap-4">
              <button
                aria-expanded={mobileNavOpen}
                aria-label="Open navigation"
                className="ghost-button px-3 py-2 lg:hidden"
                onClick={() => setMobileNavOpen(true)}
                type="button"
              >
                Menu
              </button>

              <NavLink className="flex min-w-0 items-center gap-3" to="/reports?report=latest&tab=overview">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-accent/20 bg-accent/10 font-display text-lg font-semibold text-accentSoft">
                  Ex
                </div>
                <div className="min-w-0">
                  <div className="font-display text-[28px] font-semibold tracking-[-0.04em] text-ink">ExTrace</div>
                  <div className="text-sm text-mute">Extension analysis workspace</div>
                </div>
              </NavLink>
            </div>

            <div className="hidden lg:block">
              <PrimaryNav />
            </div>

            <div className="hidden items-center gap-2 lg:flex">
              <NavLink className="ghost-button" to="/reports?report=latest&tab=overview">
                Latest Report
              </NavLink>
              <NavLink className="solid-button" to="/marketplace">
                New Analysis
              </NavLink>
            </div>
          </div>
        </div>
      </header>

      <main className="page-reveal shell-frame py-8">{children}</main>

      {mobileNavOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            aria-label="Close navigation"
            className="absolute inset-0 bg-canvasDeep/70 backdrop-blur-sm"
            onClick={() => setMobileNavOpen(false)}
            type="button"
          />
          <div className="absolute inset-x-4 top-4 rounded-[24px] border border-line bg-panel p-4 shadow-soft">
            <div className="flex items-center justify-between gap-3">
              <div className="font-display text-xl font-semibold tracking-tight text-ink">ExTrace</div>
              <button className="ghost-button px-3 py-2" onClick={() => setMobileNavOpen(false)} type="button">
                Close
              </button>
            </div>
            <div className="mt-4">
              <PrimaryNav onNavigate={() => setMobileNavOpen(false)} />
            </div>
            <div className="mt-4 flex gap-2">
              <NavLink className="ghost-button flex-1" onClick={() => setMobileNavOpen(false)} to="/reports?report=latest&tab=overview">
                Latest Report
              </NavLink>
              <NavLink className="solid-button flex-1" onClick={() => setMobileNavOpen(false)} to="/marketplace">
                New Analysis
              </NavLink>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
