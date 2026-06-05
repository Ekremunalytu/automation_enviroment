import type { CSSProperties } from "react";
import { useNavigate } from "react-router-dom";

import { Dialog, GhostButton, SolidButton, V3 } from "../../components/v3";
import type { VsixExtractionMetricsDto, VsixThresholdBreachDetail } from "../../lib/types/contracts";
import { formatBytes, formatBreachLabel, formatBreachValue } from "./format";

type VsixIntegrityBannerProps = {
  artifact: string;
  metrics: VsixExtractionMetricsDto;
  onDismiss: () => void;
};

export function VsixIntegrityBanner({
  artifact,
  metrics,
  onDismiss,
}: VsixIntegrityBannerProps) {
  // The banner is the post-download mirror of the threshold-breach popup
  // — both surfaces flag VSIX-side risk, so we keep the accent rail in
  // the coral/danger family rather than the green/ok family.
  return (
    <div
      role="status"
      style={{
        border: `1px solid ${V3.rule}`,
        borderLeft: `3px solid ${V3.coral}`,
        background: V3.paper2,
        padding: "12px 16px",
        marginBottom: 16,
        display: "flex",
        gap: 16,
        alignItems: "center",
        flexWrap: "wrap",
      }}
    >
      <div style={{ flex: "1 1 auto", minWidth: 240 }}>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10,
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            color: V3.coral,
          }}
        >
          ● VSIX integrity
        </div>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            color: V3.ink2,
            marginTop: 4,
          }}
        >
          {artifact}: {metrics.file_count.toLocaleString()} entries ·{" "}
          {formatBytes(metrics.uncompressed_size)} uncompressed ·{" "}
          {metrics.compression_ratio.toFixed(2)}:1 ratio
          {metrics.rejected_entry_count > 0
            ? ` · ${metrics.rejected_entry_count} entries skipped`
            : ""}
        </div>
      </div>
      <GhostButton onClick={onDismiss}>Dismiss</GhostButton>
    </div>
  );
}

type ThresholdBreachDialogProps = {
  breachDetail: VsixThresholdBreachDetail | null;
  onClose: () => void;
};

export function ThresholdBreachDialog({
  breachDetail,
  onClose,
}: ThresholdBreachDialogProps) {
  const navigate = useNavigate();
  return (
    <Dialog
      open={breachDetail !== null}
      onClose={onClose}
      eyebrow="Threshold breach"
      title={
        breachDetail
          ? `${breachDetail.publisher}.${breachDetail.name}@${breachDetail.version} exceeds ${formatBreachLabel(breachDetail.breach_kind).toLowerCase()}`
          : ""
      }
      tone="danger"
      actions={
        <>
          <GhostButton onClick={onClose}>Dismiss</GhostButton>
          <SolidButton
            onClick={() => {
              onClose();
              navigate("/settings?section=security");
            }}
          >
            Open Security settings
          </SolidButton>
        </>
      }
    >
      {breachDetail ? (
        <>
          <p style={{ margin: 0 }}>
            The package was rejected before extraction completed. The VSIX
            archive trips the configured{" "}
            <strong style={{ color: V3.ink }}>
              {formatBreachLabel(breachDetail.breach_kind).toLowerCase()}
            </strong>{" "}
            guard, which protects against zip-bomb / DoS extraction patterns.
            Raise the threshold from{" "}
            <strong style={{ color: V3.ink }}>Settings → Security</strong> if
            you trust this publisher and want to proceed.
          </p>
          <dl
            style={{
              margin: "18px 0 0",
              display: "grid",
              gridTemplateColumns: "auto 1fr",
              rowGap: 8,
              columnGap: 18,
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 12,
            }}
          >
            <dt style={{ color: V3.ink3 }}>Threshold</dt>
            <dd style={{ margin: 0, color: V3.ink }}>
              {formatBreachLabel(breachDetail.breach_kind)} ({breachDetail.threshold_name})
            </dd>
            <dt style={{ color: V3.ink3 }}>Configured limit</dt>
            <dd style={{ margin: 0, color: V3.ink }}>
              {formatBreachValue(breachDetail.breach_kind, breachDetail.threshold_value)}
            </dd>
            <dt style={{ color: V3.ink3 }}>Observed</dt>
            <dd style={{ margin: 0, color: V3.coral }}>
              {formatBreachValue(breachDetail.breach_kind, breachDetail.observed_value)}
            </dd>
          </dl>
        </>
      ) : null}
    </Dialog>
  );
}

const META_STYLE: CSSProperties = {
  display: "inline-flex",
  flexDirection: "column",
  gap: 2,
  padding: "0 14px 0 0",
};

export function Meta({ k, v }: { k: string; v: string }) {
  return (
    <span style={META_STYLE}>
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
          fontSize: 12.5,
          color: V3.ink,
          fontWeight: 500,
        }}
      >
        {v}
      </span>
    </span>
  );
}

export function Divider() {
  return (
    <span
      aria-hidden
      style={{
        width: 1,
        height: 24,
        background: V3.rule,
        margin: "0 14px 0 0",
      }}
    />
  );
}
