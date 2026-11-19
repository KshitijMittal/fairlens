// A tick or a cross that draws itself once (UI_UX 8). The stroke is revealed by
// animating dash-offset, so the mark reads as written rather than popped in.
export default function StatusMark({ state, size = 40 }: { state: "ok" | "error"; size?: number }) {
  return (
    <svg
      className={`mark mark--${state}`}
      width={size}
      height={size}
      viewBox="0 0 40 40"
      role="img"
      aria-label={state === "ok" ? "Success" : "Failed"}
    >
      <circle cx="20" cy="20" r="18" fill="none" stroke="currentColor" strokeWidth="2" />
      {state === "ok" ? (
        <path d="M12 20.5l5.5 5.5L28 15" fill="none" stroke="currentColor" strokeWidth="2.5"
          strokeLinecap="round" strokeLinejoin="round" className="mark__stroke" />
      ) : (
        <path d="M14 14l12 12M26 14L14 26" fill="none" stroke="currentColor" strokeWidth="2.5"
          strokeLinecap="round" className="mark__stroke" />
      )}
    </svg>
  );
}
