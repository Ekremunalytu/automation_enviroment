import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  EmptyState,
  Eyebrow,
  PageTitle,
  V3,
} from "../../components/v3";
import { apiClient } from "../../lib/api/client";
import type {
  SystemServiceHealthDto,
} from "../../lib/types/contracts";
import { resolveTimeZone } from "../../lib/settings/presentation";
import type { Tone } from "./systemHealth";

function healthTone(health: SystemServiceHealthDto["health"]): Tone {
  if (health === "ok") return "ok";
  if (health === "degraded") return "warn";
  if (health === "down") return "danger";
  return "neutral";
}

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

function observedLabel(value: string): string {
  return new Date(value).toLocaleTimeString([], {
    timeZone: resolveTimeZone(),
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function SystemPage() {
  const [selected, setSelected] = useState<string>("api");
  const health = useQuery({
    queryKey: ["system-health"],
    queryFn: ({ signal }) => apiClient.getSystemHealth(signal),
    refetchInterval: 5_000,
    retry: 1,
  });

  const services = health.data?.services ?? [];
  const service = services.find((entry) => entry.id === selected) ?? services[0];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 40 }}>
      <header style={{ paddingBottom: 24, borderBottom: `1px solid ${V3.rule}` }}>
        <PageTitle>Runtime pulse.</PageTitle>
        {health.data ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              marginTop: 14,
            }}
          >
            <span
              aria-hidden
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                background: V3.ok,
                boxShadow: `0 0 10px ${V3.ok}`,
              }}
            />
            <Eyebrow>
              Measured {observedLabel(health.data.observed_at)}
            </Eyebrow>
          </div>
        ) : null}
      </header>

      {health.isLoading ? (
        <EmptyState
          eyebrow="Measuring"
          title="Reading appliance state"
          body="Collecting database and container health."
        />
      ) : health.isError ? (
        <EmptyState
          eyebrow="Unavailable"
          title="System health could not be read"
          body={String(health.error)}
        />
      ) : health.data && service ? (
        <>
          <section
            aria-label="Measured services"
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(min(100%, 180px), 1fr))",
              border: `1px solid ${V3.rule}`,
              background: V3.paper2,
            }}
          >
            {services.map((entry, index) => {
              const isSelected = entry.id === service.id;
              const tone = healthTone(entry.health);
              const dot = toneDot(tone);
              return (
                <button
                  key={entry.id}
                  type="button"
                  onClick={() => setSelected(entry.id)}
                  aria-pressed={isSelected}
                  data-testid={`service-tile-${entry.id}`}
                  style={{
                    background: isSelected ? V3.coral : "transparent",
                    color: isSelected ? V3.paper : V3.ink,
                    border: "none",
                    borderRight:
                      index < services.length - 1
                        ? `1px solid ${V3.rule}`
                        : "none",
                    padding: "22px 20px",
                    textAlign: "left",
                    cursor: "pointer",
                    display: "flex",
                    flexDirection: "column",
                    gap: 13,
                    fontFamily: "inherit",
                    transition: "background 140ms",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "flex-end",
                    }}
                  >
                    <span
                      aria-hidden
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        background: isSelected ? V3.paper : dot,
                        boxShadow: isSelected ? "none" : `0 0 8px ${dot}`,
                      }}
                    />
                  </div>
                  <div
                    style={{
                      fontFamily: "'Manrope', sans-serif",
                      fontSize: 28,
                      fontWeight: 800,
                      lineHeight: 0.95,
                      textTransform: "uppercase",
                      color: isSelected ? V3.paper : V3.ink,
                    }}
                  >
                    {entry.name}
                  </div>
                  <div
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 10,
                      fontWeight: 600,
                      letterSpacing: "0.12em",
                      textTransform: "uppercase",
                      color: isSelected ? "rgba(0, 0, 0, 0.7)" : dot,
                    }}
                  >
                    · {entry.status}
                  </div>
                </button>
              );
            })}
          </section>

          <section
            className="system-detail-layout"
            style={{ display: "grid", gap: 28 }}
          >
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit, minmax(min(100%, 140px), 1fr))",
                  border: `1px solid ${V3.rule}`,
                  background: V3.paper2,
                }}
              >
                {service.metrics.map((metric, index) => (
                  <div
                    key={metric.label}
                    style={{
                      padding: "20px 18px",
                      borderRight:
                        index < service.metrics.length - 1
                          ? `1px solid ${V3.rule}`
                          : "none",
                      minWidth: 0,
                    }}
                  >
                    <Eyebrow>{metric.label}</Eyebrow>
                    <div
                      style={{
                        fontFamily: "'Manrope', sans-serif",
                        fontSize: metric.value.length > 18 ? 16 : 22,
                        fontWeight: 800,
                        color: V3.ink,
                        marginTop: 10,
                        lineHeight: 1.1,
                        overflowWrap: "anywhere",
                      }}
                    >
                      {metric.value}
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
                <Eyebrow>Observed facts</Eyebrow>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    marginTop: 14,
                  }}
                >
                  {service.observations.map((line) => (
                    <div
                      key={line}
                      style={{
                        display: "grid",
                        gridTemplateColumns: "12px minmax(0, 1fr)",
                        gap: 10,
                        padding: "8px 0",
                        borderBottom: `1px dashed ${V3.rule}`,
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: 12,
                        lineHeight: 1.5,
                        color: V3.ink2,
                      }}
                    >
                      <span style={{ color: V3.coral }}>›</span>
                      <span>{line}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <aside
              style={{
                border: `1px solid ${V3.rule}`,
                background: V3.paper2,
                alignSelf: "start",
              }}
            >
              <div
                style={{
                  padding: "18px 20px",
                  borderBottom: `1px solid ${V3.rule}`,
                  background: V3.paper3,
                }}
              >
                <Eyebrow>API runtime inventory</Eyebrow>
              </div>
              {health.data.inventory.map((item) => (
                <div
                  key={item.label}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "minmax(90px, 0.7fr) minmax(0, 1.3fr)",
                    gap: 12,
                    padding: "12px 20px",
                    borderBottom: `1px dashed ${V3.rule}`,
                    alignItems: "baseline",
                  }}
                >
                  <Eyebrow>{item.label}</Eyebrow>
                  <span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 12,
                      color: V3.ink,
                      textAlign: "right",
                      overflowWrap: "anywhere",
                    }}
                  >
                    {item.value}
                  </span>
                </div>
              ))}
            </aside>
          </section>
        </>
      ) : null}
    </div>
  );
}
