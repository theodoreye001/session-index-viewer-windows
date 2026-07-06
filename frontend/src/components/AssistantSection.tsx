import { useLayoutEffect, useRef, useState } from "react";
import { renderMarkdown } from "../utils/markdown";

const COLLAPSED_MAX_HEIGHT = 260;

interface AssistantSectionProps {
  sessionKey: string;
  lastAssistant: string;
}

// Last reply rendered as markdown, with expand/collapse when the
// content overflows the collapsed max height. The toggle button only
// appears when the content is tall enough to need it.
export function AssistantSection({
  sessionKey,
  lastAssistant,
}: AssistantSectionProps) {
  const [expanded, setExpanded] = useState(false);
  const [needsToggle, setNeedsToggle] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);

  // Measure overflow via ResizeObserver so the toggle appears whenever
  // the rendered height changes (content update, font load, etc.).
  // useLayoutEffect runs synchronously before paint, so the initial
  // measurement is set without a visible empty-state flash. Empty deps:
  // the observer reacts to size, not to prop changes.
  useLayoutEffect(() => {
    const el = bodyRef.current;
    if (!el) return;
    const update = () =>
      setNeedsToggle(el.scrollHeight > COLLAPSED_MAX_HEIGHT + 8);
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <section className="section">
      <div className="section-title">
        <svg
          viewBox="0 0 12 12"
          width="10"
          height="10"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M9.5 3.5v2a2 2 0 0 1-2 2H3" />
          <path d="M5 5.5L3 7.5l2 2" />
        </svg>
        Last reply
      </div>
      <div
        ref={bodyRef}
        className={`section-body markdown assistant-body ${
          expanded ? "is-expanded" : "is-collapsed"
        }`}
        data-assistant-key={sessionKey}
        dangerouslySetInnerHTML={{
          __html: renderMarkdown(lastAssistant || " "),
        }}
      />
      {needsToggle && (
        <div className="section-actions" data-session-key={sessionKey}>
          <button
            className="toggle-button"
            type="button"
            onClick={() => setExpanded((v) => !v)}
          >
            {expanded ? "Collapse" : "Expand"}
          </button>
        </div>
      )}
    </section>
  );
}
