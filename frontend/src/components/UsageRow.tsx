import type { SessionUsage } from "../types";
import { usageSummary, usageTooltip } from "../utils/usage";
import { MetaRow } from "./MetaRow";

// Usage row only renders for Devin sessions (usage !== null). Shows a
// one-line summary and a multi-line hover tooltip with the full
// token / cache / duration breakdown.
export function UsageRow({ usage }: { usage: SessionUsage }) {
  return (
    <MetaRow label="usage" tooltip={usageTooltip(usage)} multiline>
      <div className="meta-value">{usageSummary(usage)}</div>
    </MetaRow>
  );
}
