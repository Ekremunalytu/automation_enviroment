import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  Eyebrow,
  GhostButton,
  PageTitle,
  SectionTitle,
  V3,
} from "../../components/v3";
import { apiClient } from "../../lib/api/client";

type Tone = "ok" | "neutral" | "accent" | "warn" | "danger";

type ServiceCard = {
  id: string;
  name: string;
  status: string;
  tone: Tone;
  detail: string;
  metrics: ReadonlyArray<readonly [string, string]>;
  log: string[];
  isStub: boolean;
};

const STUB_SERVICES: Omit<ServiceCard, "isStub">[] = [
  {
    id: "catalog",
    name: "catalog",
    status: "synced",
    tone: "ok",
    detail: "Local extension index · 412 entries",
    metrics: [
      ["entries", "412"],
      ["last sync", "2m ago"],
      ["size", "1.84 GB"],
      ["drift", "0"],
    ],
    log: ["catalog.sync · 412/412", "manifest hash verified", "no schema drift", "idle"],
  },
  {
    id: "sandbox",
    name: "sandbox",
    status: "idle",
    tone: "neutral",
    detail: "Isolated container pool · 4 slots free",
    metrics: [
      ["slots", "4 / 4"],
      ["last run", "6m ago"],
      ["cpu", "2.1%"],
      ["ram", "184 MB"],
    ],
    log: [
      "pool.scaled · 4 ready",
      "last job · job-8f3a2c1",
      "disposed in 412ms",
      "awaiting intake",
    ],
  },
  {
    id: "telemetry",
    name: "telemetry",
    status: "live",
    tone: "accent",
    detail: "Stream collector · 1,248 ev/min",
    metrics: [
      ["rate", "1,248 ev/min"],
      ["lag", "< 50ms"],
      ["buffer", "14%"],
      ["retention", "30d"],
    ],
    log: ["stream.connect · ok", "buffer drained", "rate stable", "flushing every 2s"],
  },
];

const INVENTORY: ReadonlyArray<readonly [string, string]> = [
  ["hostname", "extrace.local"],
  ["platform", "linux/x86_64"],
  ["kernel", "6.6.12-amd64"],
  ["docker", "25.0.3"],
  ["python", "3.11.7"],
  ["node", "20.11.1"],
  ["disk", "64% / 256 GB"],
  ["session", "single-user"],
];

function toneDot(tone: Tone): string {
  switch (tone) {
    case "ok":
      return V3.ok;
    case "warn":
      return V3.warn;
    case "danger":
      return V3.coral;
    case "accent":
      return V3.coral;
    default:
      return V3.ink3;
  }
}

export function SystemPage() {
  const [selected, setSelected] = useState<string>("executor");

  const health = useQuery({
    queryKey: ["system-health"],
    queryFn: ({ signal }) => apiClient.getHealth(signal),
    refetchInterval: 5_000,
    retry: 1,
  });

  const executorService: ServiceCard = {
    id: "executor",
    name: "executor",
    status: health.isError ? "down" : health.data?.status ?? (health.isLoading ? "checking" : "unknown"),
    tone: health.isError ? "danger" : health.data?.status === "ok" ? "ok" : "warn",
    detail: health.data?.service
      ? `Live · ${health.data.service}`
      : "Dockerized VS Code · Playwright · Xvfb",
    metrics: [
      ["status", health.data?.status ?? "—"],
      ["service", health.data?.service ?? "—"],
      ["sample rate", "5s"],
      ["source", "/health"],
    ],
    log: health.isError
      ? ["health.fetch · failed", String(health.error)]
      : health.data
        ? [
            `health.fetch · ${health.data.status}`,
            `service · ${health.data.service}`,
            `sampled at ${new Date().toLocaleTimeString()}`,
            "polling every 5s",
          ]
        : ["awaiting first response"],
    isStub: false,
  };

  const services: ServiceCard[] = [
    executorService,
    ...STUB_SERVICES.map((service) => ({ ...service, isStub: true })),
  ];

  const svc = services.find((entry) => entry.id === selected) ?? services[0];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 48 }}>
      <header style={{ paddingBottom: 32, borderBottom: `1px solid ${V3.rule}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Eyebrow>System status</Eyebrow>
        </div>
        <PageTitle style={{ marginTop: 18 }}>
          All systems
          <br />
          operational.
        </PageTitle>
        <p style={{ fontSize: 15, color: V3.ink3, marginTop: 18, maxWidth: 580, lineHeight: 1.6 }}>
          Live state of the appliance. Only the executor service polls the real{" "}
          <code style={{ fontFamily: "'JetBrains Mono', monospace", color: V3.coral }}>/health</code>{" "}
          endpoint; catalog, sandbox, and telemetry render mock values until [BACKLOG ui-v3-6]
          delivers per-service health and telemetry endpoints.
        </p>
      </header>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 180px), 1fr))",
          border: `1px solid ${V3.rule}`,
          background: V3.paper2,
        }}
      >
        {services.map((service, index) => {
          const sel = service.id === selected;
          const dot = toneDot(service.tone);
          return (
            <button
              key={service.id}
              type="button"
              onClick={() => setSelected(service.id)}
              aria-pressed={sel}
              data-testid={`service-tile-${service.id}`}
              style={{
                background: sel ? V3.coral : "transparent",
                color: sel ? V3.paper : V3.ink,
                border: "none",
                borderRight: index < services.length - 1 ? `1px solid ${V3.rule}` : "none",
                padding: "24px 22px",
                textAlign: "left",
                cursor: "pointer",
                display: "flex",
                flexDirection: "column",
                gap: 14,
                fontFamily: "inherit",
                transition: "background 140ms",
                position: "relative",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 8 }}>
                <span
                  aria-hidden
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: sel ? V3.paper : dot,
                    boxShadow: sel ? "none" : `0 0 8px ${dot}`,
                  }}
                />
              </div>
              <div
                style={{
                  fontFamily: "'Manrope', sans-serif",
                  fontSize: 32,
                  fontWeight: 800,
                  letterSpacing: 0,
                  lineHeight: 0.95,
                  textTransform: "uppercase",
                  color: sel ? V3.paper : V3.ink,
                }}
              >
                {service.name}
              </div>
              <div
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 11,
                  fontWeight: 600,
                  letterSpacing: "0.12em",
                  textTransform: "uppercase",
                  color: sel ? "rgba(0, 0, 0, 0.7)" : dot,
                }}
              >
                · {service.status}
              </div>
            </button>
          );
        })}
      </section>

      <section className="system-detail-layout" style={{ display: "grid", gap: 28 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
            <Eyebrow>Service</Eyebrow>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: V3.ink3 }}>›</span>
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
                color: V3.coral,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
              }}
            >
              {svc.name}
            </span>
          </div>
          <SectionTitle>{svc.detail}</SectionTitle>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 140px), 1fr))",
              border: `1px solid ${V3.rule}`,
              background: V3.paper2,
            }}
          >
            {svc.metrics.map(([label, value], index) => (
              <div
                key={label}
                style={{
                  padding: "22px 20px",
                  borderRight: index < svc.metrics.length - 1 ? `1px solid ${V3.rule}` : "none",
                }}
              >
                <Eyebrow>{label}</Eyebrow>
                <div
                  style={{
                    fontFamily: "'Manrope', sans-serif",
                    fontSize: 30,
                    fontWeight: 800,
                    color: V3.ink,
                    letterSpacing: 0,
                    marginTop: 10,
                    lineHeight: 1,
                  }}
                >
                  {value}
                </div>
              </div>
            ))}
          </div>

          <div
            style={{
              border: `1px solid ${V3.rule}`,
              background: "#000",
              padding: "18px 20px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
              <Eyebrow>Live log</Eyebrow>
              <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span
                  aria-hidden
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: V3.coral,
                  }}
                />
                <span
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 10,
                    color: V3.ink3,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                  }}
                >
                  streaming
                </span>
              </span>
            </div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
                lineHeight: 1.9,
                color: V3.ink2,
                letterSpacing: "0.02em",
              }}
            >
              {svc.log.map((line, index) => (
                <div
                  key={`${line}-${index}`}
                  style={{ display: "grid", gridTemplateColumns: "70px 12px 1fr", gap: 10 }}
                >
                  <span style={{ color: V3.ink4 }}>
                    {String(14).padStart(2, "0")}:{String(11 + index).padStart(2, "0")}:
                    {String(2 + index * 7).padStart(2, "0")}
                  </span>
                  <span style={{ color: V3.coral }}>›</span>
                  <span>{line}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <aside
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 0,
            border: `1px solid ${V3.rule}`,
            background: V3.paper2,
          }}
        >
          <div
            style={{
              padding: "18px 20px",
              borderBottom: `1px solid ${V3.rule}`,
              background: V3.paper3,
            }}
          >
            <Eyebrow>Inventory</Eyebrow>
          </div>
          {INVENTORY.map(([k, v]) => (
            <div
              key={k}
              style={{
                display: "grid",
                gridTemplateColumns: "1fr auto",
                gap: 10,
                padding: "12px 20px",
                borderBottom: `1px dashed ${V3.rule}`,
                alignItems: "baseline",
              }}
            >
              <span
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 10,
                  fontWeight: 500,
                  letterSpacing: "0.18em",
                  textTransform: "uppercase",
                  color: V3.ink3,
                }}
              >
                {k}
              </span>
              <span
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 12,
                  color: V3.ink,
                  letterSpacing: "0.02em",
                }}
              >
                {v}
              </span>
            </div>
          ))}
          <div style={{ padding: "18px 20px", display: "flex", flexDirection: "column", gap: 10 }}>
            <GhostButton
              disabled
              ariaLabel="Restart executor (backend pending)"
              style={{ width: "100%", justifyContent: "center" }}
            >
              Restart executor
            </GhostButton>
            <GhostButton
              disabled
              ariaLabel="Re-sync catalog (backend pending)"
              style={{ width: "100%", justifyContent: "center" }}
            >
              Re-sync catalog
            </GhostButton>
          </div>
        </aside>
      </section>
    </div>
  );
}
