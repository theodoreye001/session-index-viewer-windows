import { useEffect, useMemo, useRef, useState } from "react";
import type { Session } from "../types";
import { formatRelative, sourceAccent } from "../utils/format";

interface CommandPaletteProps {
  sessions: Session[];
  onJump: (session: Session) => void;
  onClose: () => void;
}

// Cmd+K palette: quick search across all sessions, jump to a card.
// Independent from the toolbar filters so it works as a jump shortcut.
export function CommandPalette({
  sessions,
  onJump,
  onClose,
}: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [activeIdx, setActiveIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    return sessions
      .filter((item) => {
        if (!q) return true;
        const haystack = [
          item.title,
          item.session_id,
          item.cwd,
          item.first_user,
          item.host,
          item.source,
        ]
          .join("\n")
          .toLowerCase();
        return haystack.includes(q);
      })
      .slice(0, 50);
  }, [sessions, query]);

  useEffect(() => {
    setActiveIdx(0);
  }, [query]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const item = results[activeIdx];
      if (item) onJump(item);
    } else if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    }
  };

  return (
    <div
      className="palette-overlay"
      ref={overlayRef}
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
    >
      <div className="palette" role="dialog" aria-label="Jump to session">
        <input
          ref={inputRef}
          className="palette-input"
          type="text"
          placeholder="Jump to session by title, id, or cwd…"
          autoComplete="off"
          spellCheck={false}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <div className="palette-results">
          {results.length === 0 ? (
            <div className="palette-empty">No matching sessions.</div>
          ) : (
            results.map((item, idx) => {
              const title =
                item.title ||
                (item.first_user
                  ? item.first_user.slice(0, 60)
                  : item.session_id);
              return (
                <div
                  key={`${item.source}|${item.session_id}`}
                  className={`palette-item ${idx === activeIdx ? "is-active" : ""}`}
                  data-idx={idx}
                  onClick={() => onJump(item)}
                >
                  <span
                    className="palette-item-source"
                    style={{ color: sourceAccent(item.source) }}
                  >
                    {item.source}
                  </span>
                  <span className="palette-item-title">{title}</span>
                  <span className="palette-item-meta">
                    {formatRelative(item.timestamp)}
                  </span>
                </div>
              );
            })
          )}
        </div>
        <div className="palette-hint">
          <span>
            <kbd>↑</kbd>
            <kbd>↓</kbd> navigate
          </span>
          <span>
            <kbd>Enter</kbd> jump
          </span>
          <span>
            <kbd>Esc</kbd> close
          </span>
        </div>
      </div>
    </div>
  );
}
