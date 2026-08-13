import type { Session } from "./types";

export async function fetchSessions(limit = 1000): Promise<Session[]> {
  const res = await fetch(`/api/sessions?limit=${limit}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function postResume(
  session: Pick<Session, "source" | "session_id" | "cwd">,
): Promise<{ ok: boolean; error?: string }> {
  const res = await fetch("/api/resume", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      source: session.source,
      session_id: session.session_id,
      cwd: session.cwd,
    }),
  });
  return res.json();
}
