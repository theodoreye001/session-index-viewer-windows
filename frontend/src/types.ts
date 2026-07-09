// Session shapes returned by GET /api/sessions. The `usage` field is
// present when an adapter can derive token/tool metrics (Claude, Codex,
// Devin, Grok). Field semantics differ by source — see usage utils.

export interface SessionUsage {
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
  cache_creation_tokens: number;
  tool_calls: number;
  user_turns: number;
  messages: number;
  peak_context_tokens: number;
  duration_s: number;
  model: string;
}

export interface Session {
  source: "claude" | "codex" | "devin" | "grok" | string;
  host: string;
  timestamp: string;
  cwd: string;
  session_id: string;
  title: string;
  first_user: string;
  last_user: string;
  last_assistant: string;
  resume_command: string;
  usage: SessionUsage | null;
}

export type SourceFilter = "all" | "claude" | "codex" | "devin" | "grok";
