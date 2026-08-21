function resolveApiBase(): string {
  // Build-time override (or explicit NEXT_PUBLIC_API_URL) takes precedence.
  const fromEnv = process.env.NEXT_PUBLIC_API_URL;
  if (fromEnv) return fromEnv;

  // At runtime, target the same host the dashboard is served from, but on the
  // API port. This keeps things working whether the user reaches the UI via
  // localhost, a Tailscale IP, or a MagicDNS name — no rebuild required.
  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }
  return "http://localhost:8000";
}

const API_BASE = resolveApiBase();

export async function detectLanguage(
  filename: string,
  content: string
): Promise<import("@/types").DetectResponse> {
  const res = await fetch(`${API_BASE}/api/v1/detect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename, content }),
  });
  if (!res.ok) throw new Error(`Detect failed: ${res.status}`);
  return res.json();
}

export async function transpileCode(
  filename: string,
  content: string,
  procedure: string,
  maxAttempts: number = 3
): Promise<import("@/types").TranspileResponse> {
  const res = await fetch(`${API_BASE}/api/v1/transpile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      filename,
      content,
      procedure,
      max_attempts: maxAttempts,
    }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Transpile failed: ${res.status}`);
  }
  return res.json();
}

export async function parseFile(
  filename: string,
  content: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/parse-file`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename, content }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Parse failed: ${res.status}`);
  }
  return res.json();
}
