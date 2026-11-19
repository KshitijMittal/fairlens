// FastAPI sends `detail` in three shapes: a string, a list of validation
// errors, or (for our own problem responses) an object with its own `detail`.
// Rendering the object directly gave the user "[object Object]" in a red block,
// so every caller goes through here.
export function apiError(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (item as { msg?: string })?.msg)
      .filter((msg): msg is string => Boolean(msg));
    if (messages.length) return messages.join(". ");
  }
  if (detail && typeof detail === "object") {
    const inner = (detail as { detail?: unknown }).detail;
    if (typeof inner === "string") return inner;
  }
  return `The server could not complete this request (${status}). Try again in a moment.`;
}
