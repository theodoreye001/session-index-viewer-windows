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
  // prevQuery is only consulted to detect changes, never rendered, so a
  // ref avoids the pointless re-render a useState would trigger.
  const prevQueryRef = useRef(query);
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);

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

  // Reset the selection when the query changes, adjusted inline during
  // render (prev-value comparison) so there is no stale-frame effect.
  if (query !== prevQueryRef.current) {
    prevQueryRef.current = query;
    setActiveIdx(0);
  }

  // Open the native dialog on mount; native <dialog> gives us focus
  // trapping, Escape-to-close, and the backdrop for free. The backdrop
  // click-to-close is wired via addEventListener so the dialog element
  // itself stays free of JSX interaction attributes.
  useEffect(() => {
    const dlg = dialogRef.current;
    if (!dlg) return;
    if (!dlg.open) dlg.showModal();
    inputRef.current?.focus();
    const onBackdropClick = (e: MouseEvent) => {
      if (e.target === dlg) onClose();
    };
    dlg.addEventListener("click", onBackdropClick);
    return () => {
      dlg.removeEventListener("click", onBackdropClick);
      if (dlg.open) dlg.close();
    };
  }, [onClose]);

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
    <dialog
      ref={dialogRef}
      className="palette"
      aria-label="Jump to session"
    >
      <input
        ref={inputRef}
        className="palette-input"
        type="text"
        placeholder="Jump to session by title, id, or cwd…"
        aria-label="Search sessions to jump to"
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
              <button
                type="button"
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
              </button>
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
    </dialog>
  );
}
