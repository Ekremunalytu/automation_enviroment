import { useMemo, useState, type CSSProperties, type ReactNode } from "react";

import {
  Eyebrow,
  Field,
  GhostButton,
  PageTitle,
  SectionTitle,
  SolidButton,
  V3,
} from "../../components/v3";

const STORAGE_KEY = "extrace-v3-settings";

type ThemeId = "shift5" | "parchment" | "terminal";
type DensityId = "compact" | "comfortable" | "spacious";
type PoolSizeId = "2" | "4" | "8" | "16";
type RetentionId = "7" | "30" | "90" | "inf";

type SettingsState = {
  operatorName: string;
  timeZone: string;
  theme: ThemeId;
  density: DensityId;
  autoAnalyze: boolean;
  strictNet: boolean;
  poolSize: PoolSizeId;
  jobTimeout: string;
  verboseLogs: boolean;
  retainArtifacts: boolean;
  retention: RetentionId;
  buffer: string;
};

const DEFAULT_SETTINGS: SettingsState = {
  operatorName: "",
  timeZone: "UTC+03:00 · Istanbul",
  theme: "shift5",
  density: "comfortable",
  autoAnalyze: true,
  strictNet: true,
  poolSize: "4",
  jobTimeout: "600s",
  verboseLogs: false,
  retainArtifacts: true,
  retention: "30",
  buffer: "2048 events",
};

type SectionId = "general" | "executor" | "telemetry" | "danger";

const SECTIONS: { id: SectionId; label: string; hint: string }[] = [
  { id: "general", label: "General", hint: "Console & appearance" },
  { id: "executor", label: "Executor", hint: "Sandbox runtime" },
  { id: "telemetry", label: "Telemetry", hint: "Stream & retention" },
  { id: "danger", label: "Danger", hint: "Reset & purge" },
];

function loadSettings(): SettingsState {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    const parsed = JSON.parse(raw) as Partial<SettingsState>;
    return { ...DEFAULT_SETTINGS, ...parsed };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function SettingsPage() {
  const [section, setSection] = useState<SectionId>("general");
  const initial = useMemo(() => loadSettings(), []);
  const [settings, setSettings] = useState<SettingsState>(initial);
  const [persisted, setPersisted] = useState<SettingsState>(initial);
  const dirty = JSON.stringify(settings) !== JSON.stringify(persisted);

  const update = <K extends keyof SettingsState>(key: K, value: SettingsState[K]) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const save = () => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
      setPersisted(settings);
    } catch {
      /* localStorage unavailable */
    }
  };

  const discard = () => {
    setSettings(persisted);
  };

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
        <p style={{ fontSize: 15, color: V3.ink3, marginTop: 18, maxWidth: 560, lineHeight: 1.6 }}>
          Single-operator preferences. Changes are persisted to this browser&apos;s localStorage
          until the [BACKLOG ui-v3-5] settings persistence API lands.
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
                  desc="Stamped on exported reports."
                  control={
                    <Field
                      placeholder="analyst-01"
                      value={settings.operatorName}
                      onChange={(value) => update("operatorName", value)}
                      inputStyle={{ maxWidth: 340 }}
                    />
                  }
                />
                <FormRow
                  k="Time zone"
                  desc="All timestamps render in this zone."
                  control={
                    <Field
                      mono
                      value={settings.timeZone}
                      onChange={(value) => update("timeZone", value)}
                      inputStyle={{ minWidth: 280 }}
                    />
                  }
                />
              </Group>
              <Group label="Appearance">
                <FormRow
                  k="Theme"
                  desc="Visual treatment of the console."
                  control={
                    <Segmented<ThemeId>
                      value={settings.theme}
                      onChange={(value) => update("theme", value)}
                      options={[
                        ["shift5", "Shift5"],
                        ["parchment", "Parchment"],
                        ["terminal", "Terminal"],
                      ]}
                    />
                  }
                />
                <FormRow
                  k="Density"
                  desc="Row height across tables and ledgers."
                  control={
                    <Segmented<DensityId>
                      value={settings.density}
                      onChange={(value) => update("density", value)}
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
                  checked={settings.autoAnalyze}
                  onChange={(value) => update("autoAnalyze", value)}
                />
                <ToggleRow
                  k="Strict network mode"
                  desc="Block all outbound requests except to whitelisted hosts."
                  checked={settings.strictNet}
                  onChange={(value) => update("strictNet", value)}
                />
                <FormRow
                  k="Pool size"
                  desc="Concurrent sandbox containers."
                  control={
                    <Segmented<PoolSizeId>
                      value={settings.poolSize}
                      onChange={(value) => update("poolSize", value)}
                      options={[
                        ["2", "2"],
                        ["4", "4"],
                        ["8", "8"],
                        ["16", "16"],
                      ]}
                    />
                  }
                />
                <FormRow
                  k="Job timeout"
                  desc="Auto-abort after this duration."
                  control={
                    <Field
                      mono
                      placeholder="600s"
                      value={settings.jobTimeout}
                      onChange={(value) => update("jobTimeout", value)}
                      inputStyle={{ maxWidth: 200 }}
                    />
                  }
                />
              </Group>
            </>
          ) : null}

          {section === "telemetry" ? (
            <>
              <SectionTitle>Telemetry stream</SectionTitle>
              <Group label="Collection">
                <ToggleRow
                  k="Verbose logs"
                  desc="Keep raw process traces (ptrace, syscall) on disk."
                  checked={settings.verboseLogs}
                  onChange={(value) => update("verboseLogs", value)}
                />
                <ToggleRow
                  k="Retain artifacts"
                  desc="Persist downloaded extension binaries after analysis."
                  checked={settings.retainArtifacts}
                  onChange={(value) => update("retainArtifacts", value)}
                />
                <FormRow
                  k="Retention"
                  desc="Auto-purge events older than this."
                  control={
                    <Segmented<RetentionId>
                      value={settings.retention}
                      onChange={(value) => update("retention", value)}
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
                  control={
                    <Field
                      mono
                      placeholder="2048 events"
                      value={settings.buffer}
                      onChange={(value) => update("buffer", value)}
                      inputStyle={{ maxWidth: 240 }}
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

          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              gap: 10,
              paddingTop: 14,
              borderTop: `1px solid ${V3.rule}`,
            }}
          >
            <GhostButton onClick={discard} disabled={!dirty}>
              Discard
            </GhostButton>
            <SolidButton onClick={save} disabled={!dirty}>
              Save changes
            </SolidButton>
          </div>
        </div>
      </section>
    </div>
  );
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

function FormRow({ k, desc, control }: { k: string; desc: string; control: ReactNode }) {
  return (
    <div style={ROW_STYLE}>
      <RowLabel k={k} desc={desc} />
      <div>{control}</div>
    </div>
  );
}

function RowLabel({ k, desc }: { k: string; desc: string }) {
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
    </div>
  );
}

function ToggleRow({
  k,
  desc,
  checked,
  onChange,
}: {
  k: string;
  desc: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <div style={ROW_STYLE}>
      <RowLabel k={k} desc={desc} />
      <button
        type="button"
        onClick={() => onChange(!checked)}
        aria-pressed={checked}
        aria-label={k}
        style={{
          width: 52,
          height: 28,
          padding: 0,
          border: `1px solid ${checked ? V3.coral : V3.rule2}`,
          background: checked ? V3.coral : V3.paper3,
          position: "relative",
          cursor: "pointer",
          borderRadius: 0,
          transition: "all 140ms",
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
}: {
  value: V;
  onChange: (value: V) => void;
  options: ReadonlyArray<readonly [V, string]>;
}) {
  return (
    <div style={{ display: "inline-flex", border: `1px solid ${V3.rule2}` }}>
      {options.map(([v, label], index) => {
        const active = v === value;
        return (
          <button
            key={v}
            type="button"
            onClick={() => onChange(v)}
            aria-pressed={active}
            style={{
              background: active ? V3.coral : "transparent",
              color: active ? V3.paper : V3.ink,
              border: "none",
              borderLeft: index > 0 ? `1px solid ${V3.rule2}` : "none",
              padding: "9px 14px",
              cursor: "pointer",
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
      <RowLabel k={k} desc={desc} />
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
