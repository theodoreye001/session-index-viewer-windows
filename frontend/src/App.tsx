import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Session, SourceFilter } from "./types";
import { useSessions } from "./hooks/useSessions";
import { usePinned } from "./hooks/usePinned";
import { sessionKey } from "./utils/format";
import { postResume } from "./api";
import { Toolbar } from "./components/Toolbar";
import { SessionCard } from "./components/SessionCard";
import { CommandPalette } from "./components/CommandPalette";

interface FilterState {
  query: string;
  source: SourceFilter;
  host: string;
}

const INITIAL_FILTER: FilterState = {
  query: "",
  source: "all",
  host: "all",
};

export default function App() {
  const { sessions, error, loading, reload } = useSessions();
  const { pinnedIds, toggle: togglePin, has: isPinned } = usePinned();

  const [filter, setFilter] = useState<FilterState>(INITIAL_FILTER);
  const [activeIdx, setActiveIdx] = useState(0);
  const [paletteOpen, setPaletteOpen] = useState(false);
  // Bumped to ask the active SessionCard to open its usage modal.
  const [usageOpenRequest, setUsageOpenRequest] = useState(0);
  const { query, source, host } = filter;

  const boardRef = useRef<HTMLDivElement>(null);

  const hosts = useMemo(
    () => Array.from(new Set(sessions.map((s) => s.host))).toSorted(),
    [sessions],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return sessions
      .filter((item) => {
        if (source !== "all" && item.source !== source) return false;
        if (host !== "all" && item.host !== host) return false;
        if (!q) return true;
        const haystack = [
          item.cwd,
          item.session_id,
          item.title,
          item.first_user,
          item.last_user,
          item.last_assistant,
        ]
          .join("\n")
          .toLowerCase();
        return haystack.includes(q);
      })
      .sort((a, b) => {
        // Pinned sessions float above the rest; within each group,
        // newest first.
        const ap = pinnedIds.has(sessionKey(a)) ? 1 : 0;
        const bp = pinnedIds.has(sessionKey(b)) ? 1 : 0;
        if (ap !== bp) return bp - ap;
        const left = new Date(a.timestamp).getTime() || 0;
        const right = new Date(b.timestamp).getTime() || 0;
        return right - left;
      });
  }, [sessions, query, source, host, pinnedIds]);

  // Clamp activeIdx inline so we never render a stale out-of-bounds
  // selection (deriving during render avoids an extra effect commit).
  const safeActiveIdx =
    filtered.length === 0 ? 0 : Math.min(activeIdx, filtered.length - 1);

  const scrollActiveIntoView = useCallback(() => {
    const card = boardRef.current?.querySelector(".card.is-active");
    card?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, []);

  // Keyboard navigation: j/k move, Enter opens, c copies resume cmd,
  // p pins, u opens usage, Cmd+K toggles palette. Ignored while typing
  // in inputs or when the palette is open. Single-letter shortcuts must
  // not fire with modifiers — otherwise Cmd/Ctrl+C steals the browser
  // copy of selected text.
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
        return;
      }

      if (paletteOpen) return;
      // Leave Cmd/Ctrl/Alt combos to the browser (copy, paste, print…).
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      if (e.key === "j" || e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIdx((i) => {
          const next = Math.min(i + 1, filtered.length - 1);
          if (next !== i) setTimeout(scrollActiveIntoView, 0);
          return next;
        });
      } else if (e.key === "k" || e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIdx((i) => {
          const next = Math.max(i - 1, 0);
          if (next !== i) setTimeout(scrollActiveIntoView, 0);
          return next;
        });
      } else if (e.key === "Enter") {
        e.preventDefault();
        const item = filtered[safeActiveIdx];
        if (item) void postResume(item);
      } else if (e.key === "c") {
        e.preventDefault();
        const item = filtered[safeActiveIdx];
        if (item) void navigator.clipboard.writeText(item.resume_command);
      } else if (e.key === "p") {
        e.preventDefault();
        const item = filtered[safeActiveIdx];
        if (item) togglePin(item);
      } else if (e.key === "u") {
        e.preventDefault();
        const item = filtered[safeActiveIdx];
        if (item?.usage) setUsageOpenRequest((n) => n + 1);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [filtered, safeActiveIdx, paletteOpen, togglePin, scrollActiveIntoView]);

  const jumpToSession = useCallback(
    (item: Session) => {
      setPaletteOpen(false);
      setFilter(INITIAL_FILTER);
      // Defer the index lookup until after the filter clears.
      requestAnimationFrame(() => {
        const idx = filtered.findIndex(
          (s) =>
            s.source === item.source && s.session_id === item.session_id,
        );
        if (idx >= 0) {
          setActiveIdx(idx);
          setTimeout(scrollActiveIntoView, 0);
        }
      });
    },
    [filtered, scrollActiveIntoView],
  );

  const queryText = query.trim();

  return (
    <main className="shell">
      <section className="hero">
        <div className="eyebrow">Session Index Viewer</div>
        <h1>
          Pick up
          <br />
          Where you left off.
        </h1>
        <Toolbar
          query={query}
          onQueryChange={(v) => setFilter((f) => ({ ...f, query: v }))}
          source={source}
          onSourceChange={(v) =>
            setFilter((f) => ({ ...f, source: v }))
          }
          host={host}
          onHostChange={(v) => setFilter((f) => ({ ...f, host: v }))}
          hosts={hosts}
          onRefresh={reload}
        />
      </section>

      <section ref={boardRef} className="board" aria-live="polite">
        {loading && <div className="empty">Loading sessions…</div>}
        {error && (
          <div className="empty">
            Failed to load /api/sessions. Is server.py running?
          </div>
        )}
        {!loading && !error && filtered.length === 0 && (
          <div className="empty">
            No matching sessions. Try a different query.
          </div>
        )}
        {!loading &&
          !error &&
          filtered.map((item, idx) => (
            <SessionCard
              key={sessionKey(item)}
              session={item}
              index={idx}
              active={idx === safeActiveIdx}
              pinned={isPinned(item)}
              queryText={queryText}
              onPin={() => togglePin(item)}
              onActivate={() => setActiveIdx(idx)}
              usageOpenRequest={
                idx === safeActiveIdx ? usageOpenRequest : 0
              }
            />
          ))}
      </section>

      {paletteOpen && (
        <CommandPalette
          sessions={sessions}
          onJump={jumpToSession}
          onClose={() => setPaletteOpen(false)}
        />
      )}
    </main>
  );
}
