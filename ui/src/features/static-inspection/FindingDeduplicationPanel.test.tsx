import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { StaticFindingDeduplicationRecordDto } from "../../lib/types/contracts";
import { FindingDeduplicationPanel } from "./FindingDeduplicationPanel";

const records: StaticFindingDeduplicationRecordDto[] = Array.from(
  { length: 26 },
  (_, index) => ({
    rule_id: `extrace.s5.rule_${index + 1}`,
    rule_version: "1.2.0",
    reason: index === 25 ? "source_map_echo" : "vendor_echo",
    canonical_path: `src/canonical-${index + 1}.js`,
    canonical_line_number: index + 1,
    duplicate_path: `vendor/duplicate-${index + 1}.js`,
    duplicate_line_number: index + 1,
    evidence_fingerprint: (index + 1).toString(16).padStart(64, "0"),
  }),
);

describe("FindingDeduplicationPanel", () => {
  it("searches reasons and paths and paginates bounded evidence", async () => {
    render(<FindingDeduplicationPanel records={records} retainedFindings={4} />);

    const table = screen.getByRole("table", {
      name: "Finding deduplication evidence",
    });
    expect(within(table).getByText("src/canonical-1.js:1")).toBeInTheDocument();
    expect(within(table).queryByText("src/canonical-26.js:26")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Next deduplication page" }));
    expect(
      await within(table).findByText("src/canonical-26.js:26"),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search deduplication evidence"), {
      target: { value: "source_map_echo" },
    });
    expect(await within(table).findByText("Source Map Echo")).toBeInTheDocument();
    expect(within(table).queryByText("Vendor Echo")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search deduplication evidence"), {
      target: { value: "does-not-exist" },
    });
    expect(
      await screen.findByText("No deduplication evidence matches the current search."),
    ).toBeInTheDocument();
  });

  it("shows a legacy-compatible empty state", () => {
    render(<FindingDeduplicationPanel records={[]} retainedFindings={0} />);

    expect(
      screen.getByText("No exact vendor or source-map finding echo was suppressed."),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Search deduplication evidence"),
    ).not.toBeInTheDocument();
  });
});
