import { Eyebrow, PageTitle } from "../../components/v3";

export function SystemPage() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <Eyebrow>Service</Eyebrow>
        <PageTitle>System</PageTitle>
      </div>
      <div style={{ color: "#8a8780", fontSize: 13, maxWidth: 540 }}>
        Executor and telemetry surfaces land here. Page is under construction
        in the v3 redesign.
      </div>
    </div>
  );
}
