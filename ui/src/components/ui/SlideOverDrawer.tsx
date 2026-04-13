import type { PropsWithChildren } from "react";
import { useEffect } from "react";

export function SlideOverDrawer({
  open,
  title,
  description,
  onClose,
  children,
}: PropsWithChildren<{
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
}>) {
  useEffect(() => {
    if (!open) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex">
      <button
        aria-label="Close filters"
        className="flex-1 cursor-default bg-canvasDeep/72 backdrop-blur-sm"
        onClick={onClose}
        type="button"
      />
      <aside
        aria-modal="true"
        className="h-full w-full max-w-[440px] border-l border-line bg-panel shadow-soft"
        role="dialog"
      >
        <div className="flex h-full flex-col">
          <div className="border-b border-line px-5 py-5">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-2">
                <div className="eyebrow">Filters</div>
                <h2 className="font-display text-xl font-semibold tracking-tight text-ink">{title}</h2>
                {description ? <p className="text-sm leading-6 text-mute sm:text-[15px]">{description}</p> : null}
              </div>
              <button className="ghost-button px-2.5 py-2" onClick={onClose} type="button">
                Close
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto px-5 py-5 scroll-thin">{children}</div>
        </div>
      </aside>
    </div>
  );
}
