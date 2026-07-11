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
  if (peak > 0 && input > 0 && Math.abs(peak - input) / peak < 0.05) {
    return true;
  }
  return false;
}

export function contextSize(u: SessionUsage): number {
  return u.peak_context_tokens || u.input_tokens || 0;
}

export interface TokenMixPart {
  key: string;
  label: string;
  value: number;
  /** 0–100 share of lifetime total (or of context when size-only). */
  pct: number;
  color: string;
}

/** Parts for modal bars — percentages of lifetime total (not max item). */
export function tokenMixParts(
  u: SessionUsage,
  contextOnly: boolean,
): TokenMixPart[] {
  if (contextOnly) {
    const v = contextSize(u);
    return v > 0
      ? [
          {
            key: "ctx",
            label: "context",
            value: v,
            pct: 100,
            color: "var(--usage-ctx)",
          },
        ]
      : [];
  }
  const total = lifetimeTotal(u) || 1;
  const raw = [
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
  return raw
    .filter((p) => p.value > 0)
    .map((p) => ({
      ...p,
      pct: Math.max((p.value / total) * 100, 0),
    }));
}

export interface UsageChipModel {
  primary: string;
  secondary: string;
  sizeOnly: boolean;
  /** Flat string for aria-label / legacy */
  line: string;
}

/** Structured chip copy: bold primary ctx, muted secondary meta. */
export function usageChipModel(
  usage: SessionUsage,
  source: string,
): UsageChipModel {
  const contextOnly = isContextOnlyUsage(source, usage);
  const ctx = contextSize(usage);
  const out = usage.output_tokens || 0;
  const tools = usage.tool_calls || 0;
  const turns = usage.user_turns || 0;

  const primary = ctx > 0 ? `${formatTokens(ctx)} ctx` : "—";

  const sec: string[] = [];
  if (!contextOnly && out > 0) sec.push(`${formatTokens(out)} out`);
  if (tools > 0) sec.push(`${tools} tools`);
  if (turns > 0) sec.push(`${turns} turns`);

  const secondary = sec.join(" · ");
  const line = [primary, contextOnly ? "size only" : "", secondary]
    .filter(Boolean)
    .join(" · ");

  return {
    primary,
    secondary,
    sizeOnly: contextOnly,
    line: line || "—",
  };
}

/** @deprecated prefer usageChipModel */
export function usageLine(usage: SessionUsage, source: string): string {
  return usageChipModel(usage, source).line;
}

export function usageSemanticsNote(source: string, contextOnly: boolean): string {
  if (contextOnly || source === "grok") {
    return "Grok records context-window size (how full the prompt was), not a running bill of input/output tokens.";
  }
  if (source === "claude") {
    return "Claude sums each assistant turn’s usage. Cache read/write often dominate the lifetime total; Context is peak size for one turn.";
  }
  if (source === "codex") {
    return "Codex uses the last cumulative token_count. Context is the largest per-turn total seen in the session.";
  }
  if (source === "devin") {
    return "Devin aggregates metrics from its session database (lifetime sums). Context is peak assistant input tokens.";
  }
  return "Token fields are best-effort from on-disk metadata; adapters differ.";
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
    `context: ${formatTokens(contextSize(u))}`,
    `output: ${contextOnly ? "n/a" : formatTokens(u.output_tokens || 0)}`,
    `input: ${formatTokens(u.input_tokens || 0)}`,
    `cache read: ${formatTokens(u.cache_read_tokens || 0)}`,
    `cache write: ${formatTokens(u.cache_creation_tokens || 0)}`,
    `lifetime total: ${contextOnly ? "n/a (context size only)" : formatTokens(lifetimeTotal(u))}`,
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

export function usageSummary(u: SessionUsage): string {
  return usageLine(u, "");
}

export function usageTooltip(u: SessionUsage): string {
  return usageLine(u, "");
}
