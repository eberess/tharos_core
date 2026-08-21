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

export interface ParseFileResponse {
  filename: string;
  total_lines: number;
  global_variables: Array<{
    name: string;
    type: string;
    is_global: boolean;
    line: number;
  }>;
  procedures: Array<{
    name: string;
    parameters: Array<{
      name: string;
      type: string;
    }>;
    local_variables: Array<{
      name: string;
      type: string;
      line: number;
    }>;
    start_line: number;
    end_line: number;
    has_return: boolean;
  }>;
  hfsql_queries: Array<{
    type: string;
    target_table: string;
    sql: string;
    line: number;
  }>;
  dependencies: string[];
}
