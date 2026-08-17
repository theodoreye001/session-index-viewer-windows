import { memo } from "react";

// Placeholder card shown while /api/sessions is in flight. Mirrors the
// real card's two-column layout so the first paint doesn't reflow when
// data arrives.
function SkeletonCardImpl() {
  return (
    <div className="card card-skeleton" aria-hidden="true">
      <div className="card-side">
        <div className="card-head">
          <span className="sk-line sk-pill" />
          <span className="sk-line sk-star" />
        </div>
        <div className="sk-line sk-meta" />
        <div className="sk-line sk-meta" />
        <div className="sk-line sk-meta short" />
        <div className="sk-line sk-button" />
      </div>
      <div className="card-main">
        <div className="sk-line sk-title" />
        <div className="sk-line sk-body" />
        <div className="sk-line sk-body" />
        <div className="sk-line sk-body short" />
      </div>
    </div>
  );
}

export const SkeletonCard = memo(SkeletonCardImpl);
