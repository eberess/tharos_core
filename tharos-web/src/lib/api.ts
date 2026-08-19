const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
