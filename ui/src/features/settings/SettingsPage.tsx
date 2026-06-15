import { useEffect, useState, type CSSProperties, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";

import {
  Badge,
  Eyebrow,
  Field,
  GhostButton,
  PageTitle,
  SectionTitle,
  SolidButton,
  V3,
} from "../../components/v3";
import { ApiError } from "../../lib/api/http";
import { apiClient } from "../../lib/api/client";
import type { VsixThresholdsUpdateRequestDto } from "../../lib/types/contracts";
import { THEMES, useTheme, type ThemeId } from "../../lib/theme/theme";

const VSIX_THRESHOLDS_QUERY_KEY = ["security-thresholds"] as const;
const VSIX_KEYS = {
  size: "vsix_max_uncompressed_size",
  ratio: "vsix_max_compression_ratio",
  count: "vsix_max_file_count",
} as const;

// Preview values for the console controls that are NOT yet enforced. They
// render disabled behind a "Not yet enforced" affordance — previews of the
// intended setting, not live state — so the console never implies a backend
// effect it does not have. Backend enforcement (auto-analyze, strict net,
// retention, …) is deferred to a later stream; server-side persistence of
// the operator settings is Stream 9 (`operator-settings-ops`).
type DensityId = "compact" | "comfortable" | "spacious";
type RetentionId = "7" | "30" | "90" | "inf";

const PREVIEW = {
  operatorName: "",
  timeZone: "UTC+03:00 · Istanbul",
  density: "comfortable" as DensityId,
  jobTimeout: "600s",
  retention: "30" as RetentionId,
  buffer: "2048 events",
};

const DISABLED_INPUT: CSSProperties = { opacity: 0.5, cursor: "not-allowed" };

type SectionId = "general" | "executor" | "security" | "telemetry" | "danger";

const SECTIONS: { id: SectionId; label: string; hint: string }[] = [
  { id: "general", label: "General", hint: "Console & appearance" },
  { id: "executor", label: "Executor", hint: "Sandbox runtime" },
  { id: "security", label: "Security", hint: "VSIX hardening" },
  { id: "telemetry", label: "Telemetry", hint: "Stream & retention" },
  { id: "danger", label: "Danger", hint: "Reset & purge" },
];

function isSectionId(value: unknown): value is SectionId {
  return (
    value === "general" ||
    value === "executor" ||
    value === "security" ||
    value === "telemetry" ||
    value === "danger"
  );
}

export function SettingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const sectionFromUrl = searchParams.get("section");
  const [section, setSectionState] = useState<SectionId>(
    isSectionId(sectionFromUrl) ? sectionFromUrl : "general",
  );
  const [theme, setTheme] = useTheme();

  const setSection = (next: SectionId) => {
    setSectionState(next);
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("section", next);
    setSearchParams(nextParams, { replace: true });
  };

  // React to deep-link navigation (e.g. the Marketplace download popup
  // sending the operator straight to ?section=security).
  useEffect(() => {
    if (isSectionId(sectionFromUrl) && sectionFromUrl !== section) {
      setSectionState(sectionFromUrl);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sectionFromUrl]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 48 }}>
      <header style={{ paddingBottom: 32, borderBottom: `1px solid ${V3.rule}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Eyebrow>Settings</Eyebrow>
        </div>
        <PageTitle style={{ marginTop: 18 }}>
          Configure
          <br />
          the appliance.
        </PageTitle>
        <p style={{ fontSize: 15, color: V3.ink3, marginTop: 18, maxWidth: 580, lineHeight: 1.6 }}>
          Single-operator preferences. Only the VSIX security thresholds are
          enforced today — persisted by the local API. The console, executor,
          and telemetry controls below are not yet wired to a backend and are
          shown disabled until that enforcement lands.
        </p>
      </header>

      <section
        className="settings-layout"
        style={{
          display: "grid",
          gap: 32,
          alignItems: "start",
        }}
      >
        <nav
          aria-label="Settings sections"
          style={{
            border: `1px solid ${V3.rule}`,
            background: V3.paper2,
            display: "flex",
            flexDirection: "column",
          }}
        >
          {SECTIONS.map((entry, index) => {
            const active = section === entry.id;
            return (
              <button
                key={entry.id}
                type="button"
                onClick={() => setSection(entry.id)}
                aria-current={active ? "page" : undefined}
                style={{
                  background: active ? V3.coral : "transparent",
                  color: active ? V3.paper : V3.ink,
                  border: "none",
                  borderBottom: index < SECTIONS.length - 1 ? `1px solid ${V3.rule}` : "none",
                  padding: "18px 18px",
                  textAlign: "left",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  fontFamily: "inherit",
                  transition: "background 140ms",
                }}
              >
                <span style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                  <span
                    style={{
                      fontFamily: "'Manrope', sans-serif",
                      fontSize: 18,
                      fontWeight: 700,
                      letterSpacing: 0,
                      textTransform: "uppercase",
                      lineHeight: 1,
                    }}
                  >
                    {entry.label}
                  </span>
                  <span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 10,
                      letterSpacing: "0.06em",
                      color: active ? "rgba(0, 0, 0, 0.6)" : V3.ink4,
                    }}
                  >
                    {entry.hint}
                  </span>
                </span>
              </button>
            );
          })}
        </nav>

        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {section === "general" ? (
            <>
              <SectionTitle>General</SectionTitle>
              <Group label="Profile">
                <FormRow
                  k="Operator name"
                  desc="Stamped on exported reports (export not yet available)."
                  note={<NotEnforced />}
                  control={
                    <Field
                      placeholder="analyst-01"
                      value={PREVIEW.operatorName}
                      inputProps={{ disabled: true }}
                      inputStyle={{ maxWidth: 340, ...DISABLED_INPUT }}
                    />
                  }
                />
                <FormRow
                  k="Time zone"
                  desc="All timestamps render in this zone."
                  note={<NotEnforced />}
                  control={
                    <Field
                      mono
                      value={PREVIEW.timeZone}
                      inputProps={{ disabled: true }}
                      inputStyle={{ minWidth: 280, ...DISABLED_INPUT }}
                    />
                  }
                />
              </Group>
              <Group label="Appearance">
                <FormRow
                  k="Theme"
                  desc="Visual treatment of the console. Applies immediately."
                  control={
                    <Segmented<ThemeId>
                      value={theme}
                      onChange={setTheme}
                      options={THEMES.map((t) => [t.id, t.label] as [ThemeId, string])}
                    />
                  }
                />
                <FormRow
                  k="Density"
                  desc="Row height across tables and ledgers."
                  note={<NotEnforced />}
                  control={
                    <Segmented<DensityId>
                      value={PREVIEW.density}
                      disabled
                      options={[
                        ["compact", "Compact"],
                        ["comfortable", "Comfortable"],
                        ["spacious", "Spacious"],
                      ]}
                    />
                  }
                />
              </Group>
            </>
          ) : null}

          {section === "executor" ? (
            <>
              <SectionTitle>Executor runtime</SectionTitle>
              <Group label="Sandbox">
                <ToggleRow
                  k="Auto-analyze on download"
                  desc="Pipe new catalog entries straight into a sandbox run."
                  checked={false}
                  disabled
                  note={<NotEnforced />}
                />
                <ToggleRow
                  k="Strict network mode"
                  desc="Block all outbound requests except to whitelisted hosts."
                  checked={false}
                  disabled
                  note={<NotEnforced />}
                />
                <ReadonlyRow
                  k="Concurrency"
                  desc="The appliance runs a single-active serial queue — one sandbox at a time (B3). Parallel sandbox pools are a non-goal."
                  value="Single active · serial"
                />
                <FormRow
                  k="Job timeout"
                  desc="Auto-abort after this duration."
                  note={<NotEnforced />}
                  control={
                    <Field
                      mono
                      value={PREVIEW.jobTimeout}
                      inputProps={{ disabled: true }}
                      inputStyle={{ maxWidth: 200, ...DISABLED_INPUT }}
                    />
                  }
                />
              </Group>
            </>
          ) : null}

          {section === "security" ? <SecuritySection /> : null}

          {section === "telemetry" ? (
            <>
              <SectionTitle>Telemetry stream</SectionTitle>
              <Group label="Collection">
                <ToggleRow
                  k="Verbose logs"
                  desc="Keep raw process traces (ptrace, syscall) on disk."
                  checked={false}
                  disabled
                  note={<NotEnforced />}
                />
                <ToggleRow
                  k="Retain artifacts"
                  desc="Persist downloaded extension binaries after analysis."
                  checked={false}
                  disabled
                  note={<NotEnforced />}
                />
                <FormRow
                  k="Retention"
                  desc="Auto-purge events older than this."
                  note={<NotEnforced />}
                  control={
                    <Segmented<RetentionId>
                      value={PREVIEW.retention}
                      disabled
                      options={[
                        ["7", "7d"],
                        ["30", "30d"],
                        ["90", "90d"],
                        ["inf", "∞"],
                      ]}
                    />
                  }
                />
                <FormRow
                  k="Buffer"
                  desc="Memory window before flush."
                  note={<NotEnforced />}
                  control={
                    <Field
                      mono
                      value={PREVIEW.buffer}
                      inputProps={{ disabled: true }}
                      inputStyle={{ maxWidth: 240, ...DISABLED_INPUT }}
                    />
                  }
                />
              </Group>
            </>
          ) : null}

          {section === "danger" ? (
            <>
              <SectionTitle>Danger zone</SectionTitle>
              <div
                style={{
                  border: `1px solid ${V3.coral}`,
                  background: "rgba(255, 92, 66, 0.05)",
                  padding: "24px 26px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 18,
                }}
              >
                <Eyebrow style={{ color: V3.coral }}>Irreversible</Eyebrow>
                <DangerRow
                  k="Clear catalog"
                  desc="Drop all catalog entries and downloaded artifacts. Reports are kept."
                  cta="Clear"
                />
                <DangerRow
                  k="Wipe reports"
                  desc="Delete all activation reports. Catalog entries remain available for re-analysis."
                  cta="Wipe"
                />
                <DangerRow
                  k="Factory reset"
                  desc="Return appliance to first-boot state. Catalog, reports, settings — all gone."
                  cta="Reset"
                />
              </div>
            </>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function bytesToMib(bytes: number): number {
  return Math.round((bytes / (1024 * 1024)) * 100) / 100;
}

function mibToBytes(mib: number): number {
  return Math.round(mib * 1024 * 1024);
}

function SecuritySection() {
  const queryClient = useQueryClient();
  const thresholdsQuery = useQuery({
    queryKey: VSIX_THRESHOLDS_QUERY_KEY,
    queryFn: ({ signal }) => apiClient.getSecurityThresholds(signal),
    staleTime: 30_000,
  });

  const persisted = thresholdsQuery.data;
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [draftSource, setDraftSource] = useState<typeof persisted>(undefined);
  const [feedback, setFeedback] = useState<{ kind: "ok" | "error"; text: string } | null>(
    null,
  );

  // Re-seed the editable draft from the server snapshot whenever it changes
  // (initial load, post-save echo, or a refetch). Render-time adjustment —
  // React's documented pattern for deriving state from a changing prop/query —
  // instead of a setState-in-effect (which the react-hooks lint rejects as a
  // cascading-render risk).
  if (persisted && persisted !== draftSource) {
    setDraftSource(persisted);
    setDraft({
      [VSIX_KEYS.size]: String(bytesToMib(persisted.values[VSIX_KEYS.size] ?? 0)),
      [VSIX_KEYS.ratio]: String(persisted.values[VSIX_KEYS.ratio] ?? 0),
      [VSIX_KEYS.count]: String(persisted.values[VSIX_KEYS.count] ?? 0),
    });
  }

  const updateMutation = useMutation({
    mutationFn: (payload: VsixThresholdsUpdateRequestDto) =>
      apiClient.updateSecurityThresholds(payload),
    onSuccess: (next) => {
      queryClient.setQueryData(VSIX_THRESHOLDS_QUERY_KEY, next);
      setFeedback({ kind: "ok", text: "Saved." });
    },
    onError: (error) => {
      setFeedback({
        kind: "error",
        text: error instanceof ApiError ? error.message : "Update failed.",
      });
    },
  });

  // Order matters: error must come BEFORE the loading fallback. React Query
  // surfaces a failed first fetch as `isLoading=false, isError=true,
  // data=undefined`, so the previous order (`isLoading || !persisted` first)
  // collapsed every error into "Loading…" forever — the operator landing
  // here from a VSIX threshold-breach popup never saw the real cause when
  // the API was unreachable.
  if (thresholdsQuery.isError) {
    return (
      <>
        <SectionTitle>Security</SectionTitle>
        <p style={{ color: V3.coral, fontSize: 13 }}>
          Could not load thresholds: {String(thresholdsQuery.error)}
        </p>
      </>
    );
  }

  if (thresholdsQuery.isLoading || !persisted) {
    return (
      <>
        <SectionTitle>Security</SectionTitle>
        <p style={{ color: V3.ink3, fontSize: 13 }}>
          Loading operator-tunable VSIX hardening thresholds…
        </p>
      </>
    );
  }

  const draftValues: Record<string, number> = {
    [VSIX_KEYS.size]: mibToBytes(parseFloat(draft[VSIX_KEYS.size] || "0") || 0),
    [VSIX_KEYS.ratio]: Math.round(parseFloat(draft[VSIX_KEYS.ratio] || "0") || 0),
    [VSIX_KEYS.count]: Math.round(parseFloat(draft[VSIX_KEYS.count] || "0") || 0),
  };

  const dirty = Object.entries(draftValues).some(
    ([key, value]) => value !== persisted.values[key],
  );

  const onSave = () => {
    setFeedback(null);
    const changed: Record<string, number> = {};
    for (const [key, value] of Object.entries(draftValues)) {
      if (value !== persisted.values[key]) changed[key] = value;
    }
    if (Object.keys(changed).length === 0) return;
    updateMutation.mutate({ values: changed });
  };

  const onDiscard = () => {
    if (!persisted) return;
    setDraft({
      [VSIX_KEYS.size]: String(bytesToMib(persisted.values[VSIX_KEYS.size] ?? 0)),
      [VSIX_KEYS.ratio]: String(persisted.values[VSIX_KEYS.ratio] ?? 0),
      [VSIX_KEYS.count]: String(persisted.values[VSIX_KEYS.count] ?? 0),
    });
    setFeedback(null);
  };

  const fields = [
    {
      key: VSIX_KEYS.size,
      label: "Max uncompressed size",
      desc: "Cumulative inflated bytes ceiling. Primary zip-bomb defense.",
      unit: "MiB",
      bounds: persisted.bounds[VSIX_KEYS.size],
      defaultValue: persisted.defaults[VSIX_KEYS.size],
      effective: persisted.values[VSIX_KEYS.size],
      transform: bytesToMib,
    },
    {
      key: VSIX_KEYS.ratio,
      label: "Max compression ratio",
      desc: "Catches pathological compression (zip-bomb signature).",
      unit: ":1",
      bounds: persisted.bounds[VSIX_KEYS.ratio],
      defaultValue: persisted.defaults[VSIX_KEYS.ratio],
      effective: persisted.values[VSIX_KEYS.ratio],
      transform: (n: number) => n,
    },
    {
      key: VSIX_KEYS.count,
      label: "Max file count",
      desc: "Caps the extract-loop iteration count (DoS guard).",
      unit: "entries",
      bounds: persisted.bounds[VSIX_KEYS.count],
      defaultValue: persisted.defaults[VSIX_KEYS.count],
      effective: persisted.values[VSIX_KEYS.count],
      transform: (n: number) => n,
    },
  ] as const;

  return (
    <>
      <SectionTitle>VSIX hardening</SectionTitle>
      <p style={{ fontSize: 13.5, color: V3.ink3, lineHeight: 1.55, maxWidth: 640 }}>
        Operator-tunable thresholds that gate marketplace downloads. The size +
        ratio guards form the primary zip-bomb defense; the entry-count guard
        caps extract-loop iteration. Raising a value lets larger or more
        complex VSIX archives through — only do so for trusted publishers.
      </p>

      <div
        style={{
          border: `1px solid ${V3.rule}`,
          background: V3.paper2,
        }}
      >
        <div
          style={{
            padding: "14px 20px",
            borderBottom: `1px solid ${V3.rule}`,
            background: V3.paper3,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 16,
          }}
        >
          <Eyebrow>Thresholds</Eyebrow>
          <Badge tone="accent">Backend-persisted</Badge>
        </div>
        <div style={{ display: "flex", flexDirection: "column" }}>
          {fields.map((field, index) => {
            const overridden = field.effective !== field.defaultValue;
            const min = field.transform(field.bounds.min_value);
            const max = field.transform(field.bounds.max_value);
            return (
              <div
                key={field.key}
                style={{
                  ...ROW_STYLE,
                  borderBottom: index < fields.length - 1 ? `1px solid ${V3.rule}` : "none",
                }}
              >
                <RowLabel k={field.label} desc={field.desc} />
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <Field
                      mono
                      value={draft[field.key] ?? ""}
                      onChange={(value) =>
                        setDraft((current) => ({ ...current, [field.key]: value }))
                      }
                      inputStyle={{ maxWidth: 180 }}
                    />
                    <span
                      style={{
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: 11,
                        color: V3.ink3,
                      }}
                    >
                      {field.unit}
                    </span>
                    {overridden ? <Badge tone="warn">Overridden</Badge> : null}
                  </div>
                  <span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 10.5,
                      color: V3.ink4,
                    }}
                  >
                    range {min.toLocaleString()}…{max.toLocaleString()} ·
                    default {field.transform(field.defaultValue).toLocaleString()}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {feedback ? (
        <div
          role={feedback.kind === "error" ? "alert" : "status"}
          style={{
            border: `1px solid ${feedback.kind === "ok" ? V3.ok : V3.coral}`,
            background: feedback.kind === "ok" ? V3.okBg : V3.dangerBg,
            color: feedback.kind === "ok" ? V3.ok : V3.coral,
            padding: "10px 14px",
            fontSize: 12.5,
            fontFamily: "'JetBrains Mono', monospace",
          }}
        >
          {feedback.text}
        </div>
      ) : null}

      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          gap: 10,
          paddingTop: 14,
          borderTop: `1px solid ${V3.rule}`,
        }}
      >
        <GhostButton onClick={onDiscard} disabled={!dirty || updateMutation.isPending}>
          Discard
        </GhostButton>
        <SolidButton
          onClick={onSave}
          disabled={!dirty || updateMutation.isPending}
        >
          {updateMutation.isPending ? "Saving…" : "Save thresholds"}
        </SolidButton>
      </div>
    </>
  );
}

function NotEnforced() {
  return <Badge tone="neutral">Not yet enforced</Badge>;
}

function Group({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div style={{ border: `1px solid ${V3.rule}`, background: V3.paper2 }}>
      <div
        style={{
          padding: "14px 20px",
          borderBottom: `1px solid ${V3.rule}`,
          background: V3.paper3,
        }}
      >
        <Eyebrow>{label}</Eyebrow>
      </div>
      <div style={{ display: "flex", flexDirection: "column" }}>
        {childrenWithDividers(children)}
      </div>
    </div>
  );
}

function childrenWithDividers(children: ReactNode): ReactNode {
  const arr = Array.isArray(children) ? children : [children];
  return arr.filter(Boolean).map((child, index, all) => (
    <div
      key={index}
      style={{
        borderBottom: index < all.length - 1 ? `1px solid ${V3.rule}` : "none",
      }}
    >
      {child}
    </div>
  ));
}

const ROW_STYLE: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 240px), 1fr))",
  gap: 24,
  padding: "18px 20px",
  alignItems: "center",
};

function FormRow({
  k,
  desc,
  control,
  note,
}: {
  k: string;
  desc: string;
  control: ReactNode;
  note?: ReactNode;
}) {
  return (
    <div style={ROW_STYLE}>
      <RowLabel k={k} desc={desc} note={note} />
      <div>{control}</div>
    </div>
  );
}

function ReadonlyRow({ k, desc, value }: { k: string; desc: string; value: string }) {
  return (
    <div style={ROW_STYLE}>
      <RowLabel k={k} desc={desc} note={<Badge tone="neutral">Read-only</Badge>} />
      <span
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 13,
          color: V3.ink2,
          letterSpacing: "0.02em",
        }}
      >
        {value}
      </span>
    </div>
  );
}

function RowLabel({ k, desc, note }: { k: string; desc: string; note?: ReactNode }) {
  return (
    <div>
      <div
        style={{
          fontFamily: "'Manrope', sans-serif",
          fontSize: 15,
          fontWeight: 700,
          color: V3.ink,
          letterSpacing: 0,
        }}
      >
        {k}
      </div>
      <div style={{ fontSize: 12.5, color: V3.ink3, marginTop: 4, maxWidth: 480, lineHeight: 1.5 }}>
        {desc}
      </div>
      {note ? <div style={{ marginTop: 8 }}>{note}</div> : null}
    </div>
  );
}

function ToggleRow({
  k,
  desc,
  checked,
  onChange,
  disabled,
  note,
}: {
  k: string;
  desc: string;
  checked: boolean;
  onChange?: (value: boolean) => void;
  disabled?: boolean;
  note?: ReactNode;
}) {
  return (
    <div style={ROW_STYLE}>
      <RowLabel k={k} desc={desc} note={note} />
      <button
        type="button"
        onClick={() => {
          if (!disabled) onChange?.(!checked);
        }}
        disabled={disabled}
        aria-pressed={checked}
        aria-label={k}
        style={{
          width: 52,
          height: 28,
          padding: 0,
          border: `1px solid ${checked ? V3.coral : V3.rule2}`,
          background: checked ? V3.coral : V3.paper3,
          position: "relative",
          cursor: disabled ? "not-allowed" : "pointer",
          borderRadius: 0,
          transition: "all 140ms",
          opacity: disabled ? 0.45 : 1,
        }}
      >
        <span
          aria-hidden
          style={{
            position: "absolute",
            top: 2,
            left: checked ? 26 : 2,
            width: 22,
            height: 22,
            background: checked ? V3.paper : V3.ink2,
            transition: "left 160ms",
          }}
        />
      </button>
    </div>
  );
}

function Segmented<V extends string>({
  value,
  onChange,
  options,
  disabled,
}: {
  value: V;
  onChange?: (value: V) => void;
  options: ReadonlyArray<readonly [V, string]>;
  disabled?: boolean;
}) {
  return (
    <div style={{ display: "inline-flex", border: `1px solid ${V3.rule2}`, opacity: disabled ? 0.5 : 1 }}>
      {options.map(([v, label], index) => {
        const active = v === value;
        return (
          <button
            key={v}
            type="button"
            onClick={() => {
              if (!disabled) onChange?.(v);
            }}
            disabled={disabled}
            aria-pressed={active}
            style={{
              background: active ? V3.coral : "transparent",
              color: active ? V3.paper : V3.ink,
              border: "none",
              borderLeft: index > 0 ? `1px solid ${V3.rule2}` : "none",
              padding: "9px 14px",
              cursor: disabled ? "not-allowed" : "pointer",
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              transition: "background 140ms",
            }}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}

function DangerRow({ k, desc, cta }: { k: string; desc: string; cta: string }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 240px), 1fr))",
        gap: 18,
        paddingTop: 14,
        alignItems: "center",
        borderTop: `1px dashed rgba(255, 92, 66, 0.3)`,
      }}
    >
      <RowLabel k={k} desc={desc} note={<Badge tone="neutral">Not yet available</Badge>} />
      <button
        type="button"
        disabled
        title="Persistence API unavailable"
        style={{
          background: "transparent",
          border: `1px solid ${V3.coral}`,
          color: V3.coral,
          padding: "10px 18px",
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          cursor: "not-allowed",
          borderRadius: 0,
          fontFamily: "inherit",
          transition: "all 140ms",
          opacity: 0.6,
        }}
      >
        {cta}
      </button>
    </div>
  );
}
