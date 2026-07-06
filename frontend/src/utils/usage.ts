import type { SessionUsage } from "../types";
import { formatTokens, formatDuration, escapeHtml } from "./format";

// One-line summary shown in the meta-value cell.
export function usageSummary(u: SessionUsage): string {
  const total =
    (u.input_tokens || 0) +
    (u.output_tokens || 0) +
    (u.cache_read_tokens || 0) +
    (u.cache_creation_tokens || 0);
  const peak = u.peak_context_tokens
    ? ` · peak ${formatTokens(u.peak_context_tokens)}`
    : "";
  return `${formatTokens(total)} tokens${peak} · ${u.tool_calls || 0} tools · ${u.user_turns || 0} turns`;
}

// Multi-line breakdown shown in the hover tooltip. Real newlines are
// preserved inside a quoted HTML attribute and rendered by the
// pre-line white-space rule; only the model name is user-adjacent so
// it gets escaped.
export function usageTooltip(u: SessionUsage): string {
  const cacheRead = u.cache_read_tokens || 0;
  const input = u.input_tokens || 0;
  // cache hit rate: of all input-bound tokens, how many came from
  // cache reads instead of fresh processing. Higher = better reuse.
  const hitRate =
    cacheRead + input > 0
      ? Math.round((cacheRead / (cacheRead + input)) * 100)
      : null;
  const lines = [
    `model: ${escapeHtml(u.model || "—")}`,
    `input tokens: ${formatTokens(input)}`,
    `output tokens: ${formatTokens(u.output_tokens || 0)}`,
    `cache read: ${formatTokens(cacheRead)}`,
    `cache creation: ${formatTokens(u.cache_creation_tokens || 0)}`,
    `cache hit rate: ${hitRate === null ? "—" : hitRate + "%"}`,
    `peak context: ${formatTokens(u.peak_context_tokens || 0)}`,
    `tool calls: ${u.tool_calls || 0}`,
    `user turns: ${u.user_turns || 0}`,
    `messages: ${u.messages || 0}`,
    `duration: ${formatDuration(u.duration_s || 0)}`,
  ];
  return lines.join("\n");
}
