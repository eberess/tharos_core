export interface DetectResponse {
  filename: string;
  detected_language: "windev" | "unknown";
  confidence: number;
  matched_patterns: string[];
}

export interface AttemptInfo {
  attempt: number;
  passed: boolean;
  exit_code: number;
  logs: string;
}

export interface TranspileResponse {
  success: boolean;
  procedure: string;
  generated_code: string;
  test_code: string;
  attempts: number;
  history: AttemptInfo[];
  error: string | null;
}
