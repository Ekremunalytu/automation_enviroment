import { Eyebrow, PageTitle } from "../../components/v3";

export function SettingsPage() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <Eyebrow>Console</Eyebrow>
        <PageTitle>Settings</PageTitle>
      </div>
      <div style={{ color: "#8a8780", fontSize: 13, maxWidth: 540 }}>
        Console preferences and console-side controls land here. Page is under
        construction in the v3 redesign.
      </div>
    </div>
  );
}
