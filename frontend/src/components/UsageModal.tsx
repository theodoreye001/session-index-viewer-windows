import { useEffect, useId, useRef } from "react";
import type { Session } from "../types";
import {
  formatDuration,
  formatRelative,
  formatTokens,
  sourceAccent,
} from "../utils/format";
import {
  cacheHitRate,
  isContextOnlyUsage,
  lifetimeTotal,
  tokenMixParts,
  usageCopyText,
  usageSemanticsNote,
} from "../utils/usage";

interface UsageModalProps {
  session: Session;
  onClose: () => void;
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

export function UsageModal({ session, onClose }: UsageModalProps) {
  const usage = session.usage;
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const accent = sourceAccent(session.source);

  useEffect(() => {
    closeRef.current?.focus();
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
  const maxMix = Math.max(...mix.map((p) => p.value), 1);
  const hit = cacheHitRate(usage);
  const total = lifetimeTotal(usage);
  const ctx = usage.peak_context_tokens || usage.input_tokens || 0;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(usageCopyText(session));
    } catch (err) {
      console.error(err);
    }
  };

  // 1) Overview first — scannable vitals, no duplicates below.
  const kpis = [
    {
      label: "Context",
      value: formatTokens(ctx),
      hint: contextOnly ? "window size" : "peak size",
    },
    {
      label: "Output",
      value: contextOnly ? "n/a" : formatTokens(usage.output_tokens || 0),
      hint: contextOnly ? "not recorded" : "lifetime",
    },
    {
      label: "Tools",
      value: String(usage.tool_calls || 0),
      hint: "calls",
    },
    {
      label: "Turns",
      value: String(usage.user_turns || 0),
      hint: "user",
    },
    {
      label: "Duration",
      value: formatDuration(usage.duration_s || 0),
      hint: "wall clock",
    },
  ];

  // 2) Tokens group — only token accounting fields (model lives in header).
  const tokenRows: { label: string; value: string }[] = contextOnly
    ? [
        {
          label: "Context size",
          value: formatTokens(ctx),
        },
      ]
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
        {
          label: "Lifetime total",
          value: formatTokens(total),
        },
        {
          label: "Cache hit rate",
          value: hit === null ? "—" : `${hit}%`,
        },
        {
          label: "Peak context",
          value: formatTokens(usage.peak_context_tokens || 0),
        },
      ];

  // 3) Activity — counts not repeated as primary KPIs only if useful extras.
  const activityRows: { label: string; value: string }[] = [
    { label: "Tool calls", value: String(usage.tool_calls || 0) },
    { label: "User turns", value: String(usage.user_turns || 0) },
    { label: "Messages", value: String(usage.messages || 0) },
    {
      label: "Duration",
      value: formatDuration(usage.duration_s || 0),
    },
  ];

  return (
    <div
      className="usage-modal-backdrop"
      role="presentation"
      onClick={onClose}
    >
      <div
        className="usage-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        style={{ "--accent": accent } as React.CSSProperties}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="usage-modal-head">
          <div className="usage-modal-head-text">
            <div className="usage-modal-eyebrow">Session usage</div>
            {/* Title + relative time; host/username omitted (same machine is the default). */}
            <h2 id={titleId} className="usage-modal-title">
              <span className="usage-modal-title-text">
                {session.title || session.session_id}
              </span>
              <span className="usage-modal-time">
                {formatRelative(session.timestamp)}
              </span>
            </h2>
            {/* Source then model, adjacent — one identity strip. */}
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
            ref={closeRef}
            type="button"
            className="usage-modal-close"
            onClick={onClose}
            aria-label="Close usage details"
          >
            ✕
          </button>
        </header>

        {/* Overview */}
        <section className="usage-group">
          <div className="usage-section-label">Overview</div>
          <div className="usage-kpi-grid">
            {kpis.map((k) => (
              <div key={k.label} className="usage-kpi">
                <div className="usage-kpi-value">{k.value}</div>
                <div className="usage-kpi-label">{k.label}</div>
                <div className="usage-kpi-hint">{k.hint}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Tokens */}
        <section className="usage-group">
          <div className="usage-section-label">Tokens</div>
          {contextOnly && (
            <div className="usage-callout" role="note">
              <strong>Context size only.</strong> This agent does not store
              lifetime input/output token totals on disk — only how large the
              context window was. Numbers below are window size, not cumulative
              usage.
            </div>
          )}
          {mix.length > 0 && !contextOnly && (
            <div className="usage-mix-bars">
              {mix.map((part) => (
                <div key={part.key} className="usage-mix-row">
                  <span className="usage-mix-label">{part.label}</span>
                  <div className="usage-mix-track">
                    <div
                      className="usage-mix-fill"
                      style={{
                        width: `${Math.max((part.value / maxMix) * 100, 2)}%`,
                        background: part.color,
                      }}
                    />
                  </div>
                  <span className="usage-mix-value">
                    {formatTokens(part.value)}
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

        <TableGroup title="Activity" rows={activityRows} />

        <p className="usage-semantics">
          {usageSemanticsNote(session.source, contextOnly)}
        </p>

        <footer className="usage-modal-foot">
          <button type="button" className="toggle-button" onClick={handleCopy}>
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
