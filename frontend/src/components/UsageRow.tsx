import { forwardRef } from "react";
import type { SessionUsage } from "../types";
import { usageChipModel } from "../utils/usage";

interface UsageRowProps {
  usage: SessionUsage;
  source: string;
  onOpen: () => void;
}

// Compact usage chip: bold primary ctx, muted secondary meta.
// Full breakdown opens in UsageModal on click.
export const UsageRow = forwardRef<HTMLButtonElement, UsageRowProps>(
  function UsageRow({ usage, source, onOpen }, ref) {
    const chip = usageChipModel(usage, source);
    return (
      <div className="meta-row">
        <div className="meta-label">usage</div>
        <button
          ref={ref}
          type="button"
          className="usage-chip"
          onClick={(e) => {
            e.stopPropagation();
            onOpen();
          }}
          title="View usage details"
          aria-label={`Usage: ${chip.line}. Open details.`}
        >
          <span className="usage-chip-primary">{chip.primary}</span>
          {chip.sizeOnly && (
            <span className="usage-chip-tag">size only</span>
          )}
          {chip.secondary && (
            <span className="usage-chip-secondary">{chip.secondary}</span>
          )}
          <span className="usage-chip-affordance" aria-hidden="true">
            ›
          </span>
        </button>
      </div>
    );
  },
);
