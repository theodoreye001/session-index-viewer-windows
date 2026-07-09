import type { Session, SessionUsage } from "../types";
import { formatDuration, formatTokens } from "./format";

/** Lifetime sum when adapters report cumulative in/out/cache. */
export function lifetimeTotal(u: SessionUsage): number {
  return (
    (u.input_tokens || 0) +
    (u.output_tokens || 0) +
    (u.cache_read_tokens || 0) +
    (u.cache_creation_tokens || 0)
  );
}

/** Cache hit rate among input-bound tokens; null if not meaningful. */
export function cacheHitRate(u: SessionUsage): number | null {
  const cacheRead = u.cache_read_tokens || 0;
  const input = u.input_tokens || 0;
  if (cacheRead + input <= 0) return null;
  // Grok maps context into input with no real cache split.
  if (cacheRead === 0) return null;
  return Math.round((cacheRead / (cacheRead + input)) * 100);
}

/**
 * True when usage is context occupancy only (no real lifetime split).
 * Grok is the main case; also treat empty out+cache with input≈peak.
 */
export function isContextOnlyUsage(source: string, u: SessionUsage): boolean {
  if (source === "grok") return true;
  const out = u.output_tokens || 0;
  const cr = u.cache_read_tokens || 0;
  const cc = u.cache_creation_tokens || 0;
  const peak = u.peak_context_tokens || 0;
  const input = u.input_tokens || 0;
  if (out > 0 || cr > 0 || cc > 0) return false;
  if (peak > 0 && input > 0 && Math.abs(peak - input) / peak < 0.05) return true;
  return false;
}

export interface TokenMixPart {
  key: string;
  label: string;
  value: number;
  color: string;
}

/** Parts for the modal stacked/relative bars. Zeroes omitted. */
export function tokenMixParts(u: SessionUsage, contextOnly: boolean): TokenMixPart[] {
  if (contextOnly) {
    const v = u.peak_context_tokens || u.input_tokens || 0;
    return v > 0
      ? [{ key: "ctx", label: "context", value: v, color: "var(--usage-ctx)" }]
      : [];
  }
  const parts: TokenMixPart[] = [
    {
      key: "input",
      label: "input",
      value: u.input_tokens || 0,
      color: "var(--usage-input)",
    },
    {
      key: "output",
      label: "output",
      value: u.output_tokens || 0,
      color: "var(--usage-output)",
    },
    {
      key: "cache_read",
      label: "cache read",
      value: u.cache_read_tokens || 0,
      color: "var(--usage-cache-read)",
    },
    {
      key: "cache_write",
      label: "cache write",
      value: u.cache_creation_tokens || 0,
      color: "var(--usage-cache-write)",
    },
  ];
  return parts.filter((p) => p.value > 0);
}

/**
 * Compact card-line summary with priority truncation:
 *   wide:  257k ctx · 336k out · 81 tools · 50 turns · 1h
 *   mid:   257k ctx · 81 tools · 50 turns
 *   narrow:257k ctx · 50 turns
 *   grok:  186k ctx · context only · 123 tools · 10 turns
 */
export function usageLine(usage: SessionUsage, source: string): string {
  const contextOnly = isContextOnlyUsage(source, usage);
  const ctx = usage.peak_context_tokens || 0;
  const out = usage.output_tokens || 0;
  const tools = usage.tool_calls || 0;
  const turns = usage.user_turns || 0;
  const dur = usage.duration_s || 0;

  const parts: string[] = [];
  if (ctx > 0) parts.push(`${formatTokens(ctx)} ctx`);
  else if (contextOnly && (usage.input_tokens || 0) > 0) {
    parts.push(`${formatTokens(usage.input_tokens)} ctx`);
  }

  // Card chip: short flag that full lifetime totals are unavailable.
  // Modal expands this as "Context size only" with a plain-language note.
  if (contextOnly) {
    parts.push("size only");
  } else if (out > 0) {
    parts.push(`${formatTokens(out)} out`);
  }

  if (tools > 0) parts.push(`${tools} tools`);
  if (turns > 0) parts.push(`${turns} turns`);
  if (dur > 0) parts.push(formatDuration(dur));

  if (parts.length === 0) return "—";
  return parts.join(" · ");
}

export function usageSemanticsNote(source: string, contextOnly: boolean): string {
  if (contextOnly || source === "grok") {
    return "Source note: Grok saves context-window size (how full the prompt was), not a running bill of input/output tokens.";
  }
  if (source === "claude") {
    return "Source note: Claude sums each assistant turn’s usage. Cache read/write often dominate the lifetime total; Context is peak size for one turn.";
  }
  if (source === "codex") {
    return "Source note: Codex uses the last cumulative token_count. Context is the largest per-turn total seen in the session.";
  }
  if (source === "devin") {
    return "Source note: Devin aggregates metrics from its session database (lifetime sums). Context is peak assistant input tokens.";
  }
  return "Source note: token fields are best-effort from on-disk metadata; adapters differ.";
}

/** Plain-text block for clipboard / Slack. */
export function usageCopyText(session: Session): string {
  const u = session.usage;
  if (!u) return "";
  const contextOnly = isContextOnlyUsage(session.source, u);
  const hit = cacheHitRate(u);
  const lines = [
    `source: ${session.source}`,
    `title: ${session.title || "(none)"}`,
    `model: ${u.model || "—"}`,
    `ctx/peak: ${formatTokens(u.peak_context_tokens || 0)}`,
    `output: ${formatTokens(u.output_tokens || 0)}`,
    `input: ${formatTokens(u.input_tokens || 0)}`,
    `cache read: ${formatTokens(u.cache_read_tokens || 0)}`,
    `cache write: ${formatTokens(u.cache_creation_tokens || 0)}`,
    `lifetime total: ${contextOnly ? "n/a (context only)" : formatTokens(lifetimeTotal(u))}`,
    `cache hit: ${hit === null ? "—" : hit + "%"}`,
    `tools: ${u.tool_calls || 0}`,
    `turns: ${u.user_turns || 0}`,
    `messages: ${u.messages || 0}`,
    `duration: ${formatDuration(u.duration_s || 0)}`,
    `session: ${session.session_id}`,
    `cwd: ${session.cwd}`,
  ];
  return lines.join("\n");
}

// Kept for any legacy call sites; prefer usageLine for the card.
export function usageSummary(u: SessionUsage): string {
  return usageLine(u, "");
}

export function usageTooltip(u: SessionUsage): string {
  return usageLine(u, "");
}
