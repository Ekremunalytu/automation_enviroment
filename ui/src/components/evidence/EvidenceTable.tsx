import type { EvidenceEventView } from "../../lib/types/view-models";
import { EvidenceLedger } from "./EvidenceLedger";

export function EvidenceTable({
  events,
  selectedEventId,
  onSelect,
}: {
  events: EvidenceEventView[];
  selectedEventId?: string;
  onSelect: (eventId: string) => void;
}) {
  return <EvidenceLedger events={events} selectedEventId={selectedEventId} onSelect={onSelect} expandSelected={false} />;
}
