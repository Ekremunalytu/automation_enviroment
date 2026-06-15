import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  Badge,
  Eyebrow,
  GhostButton,
  PageTitle,
  SectionTitle,
  V3,
} from "../../components/v3";
import { apiClient } from "../../lib/api/client";
import { apiHealthTone, type Tone } from "./systemHealth";

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
  const [selected, setSelected] = useState<string>("api");

  const health = useQuery({
    queryKey: ["system-health"],
    queryFn: ({ signal }) => apiClient.getHealth(signal),
    refetchInterval: 5_000,
    retry: 1,
  });

  // The one real card: it polls /api/health (the local API container), NOT
  // the executor sandbox — so it is labelled "API", not "executor". Tone is
  // computed case-insensitively (the backend emits "OK"); see systemHealth.ts.
  const apiService: ServiceCard = {
    id: "api",
    name: "API",
    status: health.isError ? "down" : health.data?.status ?? (health.isLoading ? "checking" : "unknown"),
    tone: apiHealthTone({ isError: health.isError, status: health.data?.status }),
    detail: health.data?.service
      ? `Live · ${health.data.service} · /api/health`
      : "Local API health probe · /api/health",
    metrics: [
      ["status", health.data?.status ?? "—"],
      ["service", health.data?.service ?? "—"],
      ["sample rate", "5s"],
      ["source", "/api/health"],
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
    apiService,
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
          Appliance
          <br />
          status.
        </PageTitle>
        <p style={{ fontSize: 15, color: V3.ink3, marginTop: 18, maxWidth: 600, lineHeight: 1.6 }}>
          Only the API card reflects a real measurement — the local{" "}
          <code style={{ fontFamily: "'JetBrains Mono', monospace", color: V3.coral }}>/api/health</code>{" "}
          probe. Catalog, sandbox, and telemetry render mock values, and the
          executor sandbox&apos;s own health is not yet measured, until [BACKLOG ui-v3-6]
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
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: service.isStub ? "space-between" : "flex-end",
                  gap: 8,
                }}
              >
                {service.isStub ? (
                  <span
                    data-testid={`service-mock-${service.id}`}
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 9,
                      fontWeight: 700,
                      letterSpacing: "0.16em",
                      color: sel ? "rgba(0, 0, 0, 0.7)" : V3.warn,
                      border: `1px solid ${sel ? "rgba(0, 0, 0, 0.4)" : V3.warn}`,
                      padding: "2px 5px",
                    }}
                  >
                    MOCK
                  </span>
                ) : null}
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

          {svc.isStub ? (
            <div
              role="note"
              style={{
                border: `1px solid ${V3.warn}`,
                background: V3.warnBg,
                color: V3.warn,
                padding: "10px 14px",
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
                lineHeight: 1.5,
              }}
            >
              Mock data — not measured. The metrics and live log below are
              placeholders until [BACKLOG ui-v3-6] delivers a real {svc.name} probe.
            </div>
          ) : null}

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
              background: V3.paper,
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
                    background: svc.isStub ? V3.ink3 : V3.coral,
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
                  {svc.isStub ? "mock" : "streaming"}
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
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 12,
            }}
          >
            <Eyebrow>Inventory</Eyebrow>
            <Badge tone="warn">Mock</Badge>
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
