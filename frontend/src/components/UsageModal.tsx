import { useEffect, useId, useRef, useState } from "react";
import type { Session } from "../types";
import {
  formatDuration,
  formatRelative,
  formatTokens,
  sourceAccent,
} from "../utils/format";
import {
  cacheHitRate,
  contextPressure,
  contextSize,
  isContextOnlyUsage,
  lifetimeTotal,
  modelContextLimit,
  pressureColor,
  tokenMixParts,
  usageCopyText,
  usageSemanticsNote,
} from "../utils/usage";

interface UsageModalProps {
  session: Session;
  onClose: () => void;
  /** Keyboard open: skip enter animation (high-frequency path). */
  instant?: boolean;
  /** Element to restore focus to on close (usage chip). */
  returnFocusTo?: HTMLElement | null;
}

function TableGroup({
  title,
  rows,
}: {
  title: string;
  rows: { label: string; value: string }[];
}) {
  if (rows.length === 0) return null;
  return (
    <section className="usage-group">
      <div className="usage-section-label">{title}</div>
      <dl className="usage-table">
        {rows.map((row) => (
          <div key={row.label} className="usage-table-row">
            <dt>{row.label}</dt>
            <dd>{row.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export function UsageModal({
  session,
  onClose,
  instant = false,
  returnFocusTo = null,
}: UsageModalProps) {
  const usage = session.usage;
  const titleId = useId();
  const dialogRef = useRef<HTMLDivElement>(null);
  const [entered, setEntered] = useState(instant);
  const accent = sourceAccent(session.source);

  useEffect(() => {
    // Focus the dialog shell so Esc works; restore chip on unmount.
    dialogRef.current?.focus();
    let raf = 0;
    if (!instant) {
      raf = requestAnimationFrame(() => setEntered(true));
    }
    return () => {
      if (raf) cancelAnimationFrame(raf);
      returnFocusTo?.focus?.();
    };
  }, [instant, returnFocusTo]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        onClose();
      }
    };
    document.addEventListener("keydown", onKey, true);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey, true);
      document.body.style.overflow = prev;
    };
  }, [onClose]);

  if (!usage) return null;

  const contextOnly = isContextOnlyUsage(session.source, usage);
  const mix = tokenMixParts(usage, contextOnly);
  const hit = cacheHitRate(usage);
  const total = lifetimeTotal(usage);
  const ctx = contextSize(usage);
  const ctxLimit = modelContextLimit(usage.model, session.source);
  const pressure = contextPressure(usage, usage.model, session.source);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(usageCopyText(session));
    } catch (err) {
      console.error(err);
    }
  };

  // Overview: no Output cell when size-only; Messages replaces duplicate Activity.
  const kpis = contextOnly
    ? [
        { label: "Context", value: formatTokens(ctx) },
        { label: "Tools", value: String(usage.tool_calls || 0) },
        { label: "Turns", value: String(usage.user_turns || 0) },
        {
          label: "Duration",
          value: formatDuration(usage.duration_s || 0),
        },
        { label: "Messages", value: String(usage.messages || 0) },
      ]
    : [
        { label: "Context", value: formatTokens(ctx) },
        {
          label: "Output",
          value: formatTokens(usage.output_tokens || 0),
        },
        { label: "Tools", value: String(usage.tool_calls || 0) },
        { label: "Turns", value: String(usage.user_turns || 0) },
        {
          label: "Duration",
          value: formatDuration(usage.duration_s || 0),
        },
      ];

  const tokenRows: { label: string; value: string }[] = contextOnly
    ? []
    : [
        { label: "Input", value: formatTokens(usage.input_tokens || 0) },
        { label: "Output", value: formatTokens(usage.output_tokens || 0) },
        {
          label: "Cache read",
          value: formatTokens(usage.cache_read_tokens || 0),
        },
        {
          label: "Cache write",
          value: formatTokens(usage.cache_creation_tokens || 0),
        },
        { label: "Lifetime total", value: formatTokens(total) },
        {
          label: "Cache hit rate",
          value: hit === null ? "—" : `${hit}%`,
        },
        {
          label: "Peak context",
          value: formatTokens(usage.peak_context_tokens || 0),
        },
      ];

  // Activity only for extras not already in Overview (messages when full set).
  const activityRows: { label: string; value: string }[] = contextOnly
    ? []
    : [{ label: "Messages", value: String(usage.messages || 0) }];

  const backdropClass = [
    "usage-modal-backdrop",
    entered ? "is-entered" : "",
    instant ? "is-instant" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const panelClass = [
    "usage-modal",
    entered ? "is-entered" : "",
    instant ? "is-instant" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={backdropClass}
      role="presentation"
      onClick={onClose}
    >
      <div
        ref={dialogRef}
        className={panelClass}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        style={{ "--accent": accent } as React.CSSProperties}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="usage-modal-head">
          <div className="usage-modal-head-text">
            <div className="usage-modal-eyebrow">Session usage</div>
            <h2 id={titleId} className="usage-modal-title">
              <span className="usage-modal-title-text">
                {session.title || session.session_id}
              </span>
              <span className="usage-modal-time">
                {formatRelative(session.timestamp)}
              </span>
            </h2>
            <div className="usage-modal-meta">
              <span className="source-pill" style={{ color: accent }}>
                {session.source}
              </span>
              {usage.model && (
                <span className="usage-model-pill" title="Model">
                  {usage.model}
                </span>
              )}
            </div>
          </div>
          <button
            type="button"
            className="usage-modal-close"
            onClick={onClose}
            aria-label="Close usage details"
          >
            ✕
          </button>
        </header>

        <section className="usage-group">
          <div className="usage-section-label">Overview</div>
          <div
            className={`usage-kpi-grid ${contextOnly ? "usage-kpi-grid--4" : ""}`}
          >
            {kpis.map((k) => (
              <div key={k.label} className="usage-kpi">
                <div className="usage-kpi-value">{k.value}</div>
                <div className="usage-kpi-label">{k.label}</div>
              </div>
            ))}
          </div>
          {pressure !== null && (
            <div className="usage-pressure">
              <div className="usage-pressure-head">
                <span className="usage-pressure-label">
                  Context pressure
                </span>
                <span
                  className="usage-pressure-value"
                  style={{ color: pressureColor(pressure) }}
                >
                  {pressure}% of {formatTokens(ctxLimit)}
                </span>
              </div>
              <div className="usage-pressure-track">
                <div
                  className="usage-pressure-fill"
                  style={{
                    width: `${pressure}%`,
                    background: pressureColor(pressure),
                  }}
                />
              </div>
            </div>
          )}
        </section>

        {contextOnly ? (
          <section className="usage-group">
            <div className="usage-callout" role="note">
              <strong>Context size only</strong>
              This agent does not store lifetime input/output totals — only how
              full the context window was ({formatTokens(ctx)} tokens).
            </div>
          </section>
        ) : (
          <section className="usage-group">
            <div className="usage-section-label">Tokens</div>
            {mix.length > 0 && (
              <div className="usage-mix-bars">
                {mix.map((part) => (
                  <div key={part.key} className="usage-mix-row">
                    <span className="usage-mix-label">{part.label}</span>
                    <div className="usage-mix-track">
                      <div
                        className="usage-mix-fill"
                        style={{
                          // Share of lifetime total; scaleX keeps GPU-friendly path
                          transform: `scaleX(${Math.max(part.pct / 100, 0.02)})`,
                          background: part.color,
                        }}
                      />
                    </div>
                    <span className="usage-mix-value">
                      {formatTokens(part.value)}
                      <span className="usage-mix-pct">
                        {Math.round(part.pct)}%
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            )}
            <dl className="usage-table">
              {tokenRows.map((row) => (
                <div key={row.label} className="usage-table-row">
                  <dt>{row.label}</dt>
                  <dd>{row.value}</dd>
                </div>
              ))}
            </dl>
          </section>
        )}

        <TableGroup title="Activity" rows={activityRows} />

        <p className="usage-semantics">
          {usageSemanticsNote(session.source, contextOnly)}
        </p>

        <footer className="usage-modal-foot">
          <button
            type="button"
            className="toggle-button usage-modal-primary"
            onClick={handleCopy}
          >
            Copy summary
          </button>
          <button
            type="button"
            className="toggle-button usage-modal-secondary"
            onClick={onClose}
          >
            Close
          </button>
        </footer>
      </div>
    </div>
  );
}
