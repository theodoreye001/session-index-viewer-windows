import type { SessionUsage } from "../types";
import { usageLine } from "../utils/usage";

interface UsageRowProps {
  usage: SessionUsage;
  source: string;
  onOpen: () => void;
}

// Compact one-line usage chip. Primary signal is ctx (+ out when real);
// full breakdown opens in UsageModal on click.
export function UsageRow({ usage, source, onOpen }: UsageRowProps) {
  const line = usageLine(usage, source);
  return (
    <div className="meta-row">
      <div className="meta-label">usage</div>
      <button
        type="button"
        className="usage-chip"
        onClick={(e) => {
          e.stopPropagation();
          onOpen();
        }}
        title="View usage details"
        aria-label={`Usage: ${line}. Open details.`}
      >
        <span className="usage-chip-text">{line}</span>
        <span className="usage-chip-affordance" aria-hidden="true">
          ↗
        </span>
      </button>
    </div>
  );
}
