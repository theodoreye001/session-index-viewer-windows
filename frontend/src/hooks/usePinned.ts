import { useCallback, useState } from "react";
import { sessionKey } from "../utils/format";
import type { Session } from "../types";

const STORAGE_KEY = "pinnedSessions";

// Persist the pin set to localStorage. Module-scope so the function
// identity stays stable and memoized children don't re-render.
function savePinned(next: Set<string>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...next]));
}

// Pinned session ids persist in localStorage so starred sessions
// survive reloads. The pin set is stored as a JSON array.
export function usePinned() {
  const [pinnedIds, setPinnedIds] = useState<Set<string>>(
    () => new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]")),
  );

  const toggle = useCallback((session: Session) => {
    const key = sessionKey(session);
    setPinnedIds((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      savePinned(next);
      return next;
    });
  }, []);

  const has = useCallback(
    (session: Session) => pinnedIds.has(sessionKey(session)),
    [pinnedIds],
  );

  return { pinnedIds, toggle, has };
}
