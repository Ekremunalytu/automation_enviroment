import { useEffect, useState, type CSSProperties, type PropsWithChildren } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { LogoMark, V3 } from "../../components/v3";

type NavId = "reports" | "simulation" | "marketplace" | "settings" | "system";

type NavSpec = {
  id: NavId;
  label: string;
  hint: string;
  to: string;
};

const NAV: NavSpec[] = [
  { id: "reports", label: "Reports", hint: "Activation reports & artifacts", to: "/reports?report=latest&tab=overview" },
  { id: "simulation", label: "Simulation", hint: "Sandbox scenarios, live", to: "/simulation" },
  { id: "marketplace", label: "Marketplace", hint: "Extension intake", to: "/marketplace" },
  { id: "settings", label: "Settings", hint: "Console preferences", to: "/settings" },
  { id: "system", label: "System", hint: "Executor & telemetry", to: "/system" },
];

const RAIL_STORAGE_KEY = "extrace-v3-rail";

function readStoredCollapsed(): boolean {
  try {
    return window.localStorage.getItem(RAIL_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

function readIsNarrow(): boolean {
  if (typeof window === "undefined") return false;
  return window.innerWidth < 820;
}

function activeIdFromPath(pathname: string): NavId {
  if (pathname.startsWith("/simulation")) return "simulation";
  if (pathname.startsWith("/marketplace")) return "marketplace";
  if (pathname.startsWith("/settings")) return "settings";
  if (pathname.startsWith("/system")) return "system";
  return "reports";
}

export function AppShell({ children }: PropsWithChildren) {
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState<boolean>(() => readStoredCollapsed());
  const [isNarrow, setIsNarrow] = useState<boolean>(() => readIsNarrow());
  const activeId = activeIdFromPath(location.pathname);

  useEffect(() => {
    document.body.dataset.theme = "v3";
    return () => {
      delete document.body.dataset.theme;
    };
  }, []);

  useEffect(() => {
    const onResize = () => setIsNarrow(readIsNarrow());
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const toggle = () => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        window.localStorage.setItem(RAIL_STORAGE_KEY, next ? "1" : "0");
      } catch {
        /* localStorage may be unavailable; ignore */
      }
      return next;
    });
  };

  const effectiveCollapsed = isNarrow || collapsed;
  const railWidth = effectiveCollapsed ? 72 : 280;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: `${railWidth}px 1fr`,
        minHeight: "100vh",
        fontFamily: "'Manrope', sans-serif",
        color: V3.ink,
        background: V3.paper,
        transition: "grid-template-columns 200ms ease",
      }}
    >
      <aside
        style={{
          position: "sticky",
          top: 0,
          height: "100vh",
          borderRight: `1px solid ${V3.rule}`,
          background: "#000",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <button
          type="button"
          onClick={toggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!collapsed}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          style={{
            padding: effectiveCollapsed ? "24px 0 22px" : "26px 22px 22px",
            borderBottom: `1px solid ${V3.rule}`,
            display: "flex",
            alignItems: "center",
            justifyContent: effectiveCollapsed ? "center" : "flex-start",
            cursor: "pointer",
            userSelect: "none",
            background: "transparent",
            border: 0,
            borderBottomStyle: "solid",
            borderBottomColor: V3.rule,
            borderBottomWidth: 1,
            color: "inherit",
            font: "inherit",
            width: "100%",
            textAlign: "left",
          }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <LogoMark size={28} />
            {!effectiveCollapsed ? (
              <span
                style={{
                  display: "flex",
                  flexDirection: "column",
                  lineHeight: 1.05,
                }}
              >
                <span
                  style={{
                    fontSize: 22,
                    fontWeight: 800,
                    letterSpacing: 0,
                    color: V3.ink,
                    textTransform: "uppercase",
                  }}
                >
                  ExTrace
                </span>
              </span>
            ) : null}
          </span>
        </button>

        {!effectiveCollapsed ? (
          <div
            style={{
              padding: "18px 22px 8px",
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <span style={{ width: 14, height: 1, background: V3.coral }} />
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 10,
                fontWeight: 500,
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                color: V3.ink4,
              }}
            >
              Index
            </span>
          </div>
        ) : null}

        <nav
          aria-label="Primary"
          style={{
            padding: effectiveCollapsed ? "14px 10px" : "4px 14px",
            display: "flex",
            flexDirection: "column",
            gap: 0,
          }}
        >
          {NAV.map((item) => (
            <NavItem
              key={item.id}
              collapsed={effectiveCollapsed}
              active={activeId === item.id}
              item={item}
              onClick={() => navigate(item.to)}
            />
          ))}
        </nav>

        <div style={{ flex: 1 }} />
      </aside>

      <main
        style={{
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
          background: V3.paper,
          position: "relative",
        }}
      >
        <div
          key={location.pathname}
          className="v3-page-reveal v3-scrollbar"
          style={{ padding: isNarrow ? "28px 16px 72px" : "48px 56px 96px", width: "100%" }}
        >
          {children}
        </div>
      </main>
    </div>
  );
}

type NavItemProps = {
  item: NavSpec;
  active: boolean;
  collapsed: boolean;
  onClick: () => void;
};

function NavItem({ item, active, collapsed, onClick }: NavItemProps) {
  const [hover, setHover] = useState(false);

  if (collapsed) {
    const dotBg = active ? V3.paper : hover ? V3.coral : V3.ink3;
    const buttonBg = active ? V3.coral : hover ? V3.paper3 : "transparent";
    return (
      <button
        type="button"
        onClick={onClick}
        title={item.label}
        aria-label={item.label}
        aria-current={active ? "page" : undefined}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        style={collapsedNavStyle(buttonBg)}
      >
        <span
          aria-hidden
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: dotBg,
            transition: "background 140ms",
          }}
        />
      </button>
    );
  }

  const buttonBg = active ? V3.coral : hover ? V3.paper3 : "transparent";
  const labelColor = active ? V3.paper : V3.ink;
  const hintColor = active ? "rgba(0, 0, 0, 0.6)" : V3.ink4;
  const chevronColor = active ? V3.paper : hover ? V3.coral : V3.ink4;

  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={expandedNavStyle(buttonBg)}
    >
      <span
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 2,
          minWidth: 0,
        }}
      >
        <span
                  style={{
                    fontSize: 18,
                    fontWeight: 700,
                    color: labelColor,
                    letterSpacing: 0,
                    textTransform: "uppercase",
                  }}
        >
          {item.label}
        </span>
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10,
            color: hintColor,
            letterSpacing: "0.04em",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {item.hint}
        </span>
      </span>
      <span
        aria-hidden
        style={{
          fontSize: 14,
          color: chevronColor,
          fontWeight: 700,
          transition: "color 140ms",
        }}
      >
        ›
      </span>
    </button>
  );
}

function collapsedNavStyle(background: string): CSSProperties {
  return {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background,
    border: "none",
    padding: "14px 0",
    cursor: "pointer",
    borderRadius: 0,
    transition: "all 140ms",
    width: "100%",
    fontFamily: "inherit",
    color: "inherit",
  };
}

function expandedNavStyle(background: string): CSSProperties {
  return {
    display: "grid",
    gridTemplateColumns: "1fr 12px",
    gap: 10,
    alignItems: "center",
    background,
    border: "none",
    padding: "14px 14px",
    cursor: "pointer",
    borderRadius: 0,
    textAlign: "left",
    transition: "all 140ms",
    width: "100%",
    fontFamily: "inherit",
    color: "inherit",
    position: "relative",
  };
}
