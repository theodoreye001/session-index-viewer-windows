# Changelog

## 2026-08-11

### Performance
- **Virtual list.** The session board now uses
  [`@tanstack/react-virtual`](https://tanstack.com/virtual) window
  virtualization — only visible cards are mounted in the DOM, and
  variable card heights are measured per-item via `measureElement`.
  `SessionCard` is wrapped in `React.memo` with stable `useCallback`
  props so unchanged cards skip re-render. This keeps the UI smooth
  with the new 1000-session limit.
- **Window-scrolled layout.** Switched from a container-scrolled
  virtualizer to `useWindowVirtualizer` so the hero section scrolls
  away naturally with the page instead of being frozen at the top.
  A back-to-top button (↑) appears in the bottom-right after
  scrolling past the hero.

### Usage modal
- **Context pressure bar.** The usage modal now shows a colour-coded
  progress bar comparing peak context tokens against the model's
  context window limit. Green (< 60 %), yellow (60–85 %), red
  (≥ 85 %). Model → limit mapping is prefix-based and covers Claude,
  GPT/Codex, GLM, Gemini, Grok, DeepSeek, Kimi, and SWE variants,
  including 1 M-context variants.
- **Global single-instance modal.** `UsageModal` state was lifted
  from per-card to the App level so multiple modals can no longer
  stack on top of each other.

### Session limit
- **100 → 1000 sessions.** The default and maximum scan limits were
  raised from 100 / 500 to 1000 / 1000 across the backend
  (`siv/config.py`), frontend API client, and legacy shell indexer.
  This makes older sessions searchable without sacrificing
  responsiveness (virtual list + mtime/size cache).

### Terminal launch
- **Clean Ghostty windows.** Ghostty is now launched with
  `--window-save-state=never` so new terminal instances don't
  inherit the layout of previously closed windows.
