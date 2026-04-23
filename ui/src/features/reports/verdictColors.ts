export const verdictColors = {
  malicious: {
    banner: "border-danger/30 bg-danger/10 text-danger",
    badge: "bg-danger/15 text-danger",
  },
  suspicious: {
    banner: "border-warning/30 bg-warning/10 text-warning",
    badge: "bg-warning/15 text-warning",
  },
  clean_with_notes: {
    banner: "border-sky-500/30 bg-sky-500/10 text-sky-200",
    badge: "bg-sky-500/15 text-sky-200",
  },
  clean: {
    banner: "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
    badge: "bg-emerald-500/15 text-emerald-200",
  },
  inconclusive: {
    banner: "border-lineStrong bg-panelAlt text-inkSoft",
    badge: "bg-panelAlt text-inkSoft",
  },
} as const;
