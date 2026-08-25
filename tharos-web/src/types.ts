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

// New types for v0.3
export interface DependencyGraphResponse {
  dependencies: Record<string, any>;
  transpilation_order: string[];
  has_cycles: boolean;
  cycles: string[][];
}

export interface TranslationResult {
  original_query: string;
  translated_code: string;
  is_raw_sql: boolean;
  warnings?: string[];
}

export interface DbTranslationResponse {
  original_filename: string;
  translations: Record<string, TranslationResult>;
}

// ── v0.4 : Génération IHM (WinDev → React/shadcn) ───────────────────────────

export type UIControlType =
  | "input"
  | "button"
  | "table"
  | "label"
  | "checkbox"
  | "select";

export interface UIControl {
  name: string;
  control_type: UIControlType;
  label: string | null;
  wtype: string | null;
  default_value: string | null;
  columns: string[];
  line: number;
}

export interface UIEvent {
  event_name: string;
  control_name: string;
  procedure_name: string;
  body_lines: string[];
}

export interface UIWindowStructure {
  filename: string;
  title: string | null;
  controls: UIControl[];
  events: UIEvent[];
  total_lines: number;
}

export interface GenerateUIResponse {
  success: boolean;
  component_name: string;
  tsx_code: string;
  ui_structure: UIWindowStructure;
  warnings: string[];
  error: string | null;
}