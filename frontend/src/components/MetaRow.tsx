// A labelled meta row with an optional hover tooltip. The tooltip is
// CSS-driven (data-tooltip + ::after) to avoid per-row React state.
interface MetaRowProps {
  label: string;
  tooltip?: string;
  multiline?: boolean;
  children: React.ReactNode;
}

export function MetaRow({ label, tooltip, multiline, children }: MetaRowProps) {
  return (
    <div
      className="meta-row"
      data-tooltip={tooltip}
      data-tooltip-multiline={multiline ? "" : undefined}
    >
      <div className="meta-label">{label}</div>
      {children}
    </div>
  );
}
