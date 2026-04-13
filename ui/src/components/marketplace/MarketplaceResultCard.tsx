import type { MarketplaceExtensionDto } from "../../lib/types/contracts";
import { Badge } from "../ui/Badge";

export function MarketplaceResultCard({
  extension,
  readyToAnalyze,
  onDownload,
  onAnalyze,
  busy,
}: {
  extension: MarketplaceExtensionDto;
  readyToAnalyze: boolean;
  onDownload: () => void;
  onAnalyze: () => void;
  busy?: boolean;
}) {
  return (
    <article className="grid gap-5 py-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-start">
      <div className="min-w-0 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <div className="font-display text-xl font-semibold tracking-tight text-ink">{extension.displayName}</div>
            <div className="mt-1 font-mono text-xs text-mute">
              {extension.publisher}.{extension.name}
            </div>
          </div>
          <Badge tone={readyToAnalyze ? "success" : "default"}>
            {readyToAnalyze ? "Ready to analyze" : "Marketplace"}
          </Badge>
        </div>
        <p className="max-w-3xl text-sm leading-6 text-mute sm:text-[15px]">{extension.description}</p>
        <div className="flex flex-wrap gap-2">
          <Badge tone="accent">v{extension.version}</Badge>
          <Badge tone="default">{extension.installs.toLocaleString()} installs</Badge>
          <Badge tone="default">{extension.rating.toFixed(1)} rating</Badge>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2 lg:self-center">
        {!readyToAnalyze ? (
          <button
            className="solid-button disabled:cursor-not-allowed disabled:opacity-50"
            disabled={busy}
            onClick={onDownload}
            type="button"
          >
            {busy ? "Downloading…" : "Download"}
          </button>
        ) : (
          <button
            className="subtle-button disabled:cursor-not-allowed disabled:opacity-50"
            disabled={busy}
            onClick={onAnalyze}
            type="button"
          >
            {busy ? "Starting…" : "Analyze"}
          </button>
        )}
      </div>
    </article>
  );
}
