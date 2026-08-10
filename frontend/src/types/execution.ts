// =========================================================
// Phase 6.3D — Shared Execution Types
//
// Centralized TypeScript interfaces for agent execution.
// All AI chat components (AgentConsole, FloatingAI,
// AgentExecutionCard, chat.ts) should import their
// execution-related types from this module instead of
// declaring local/duplicate interfaces.
// =========================================================

/**
 * Lifecycle status of a single agent execution.
 */
export type ExecutionStatus =
  | 'idle'
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'
  | 'waiting_for_approval';

/**
 * Confidence score for an agent execution result.
 * Represented as a whole number percentage, 0–100.
 */
export type ConfidenceLevel = number;

/**
 * A single supporting source referenced by an agent's
 * execution result (e.g. a dashboard, API, or document).
 */
export interface ExecutionSource {
  id: string;
  name: string;
  type: string;
  url?: string;
  description?: string;
}

/**
 * A single actionable recommendation produced by an agent.
 */
export interface AgentRecommendation {
  title: string;
  description: string;
  priority?: 'low' | 'medium' | 'high';
}

/**
 * A single finding/insight produced by an agent during
 * execution.
 */
export interface AgentFinding {
  title: string;
  description: string;
  severity?: 'info' | 'warning' | 'critical';
}

/**
 * The full result of a single agent's execution, as
 * rendered by AgentExecutionCard inside AgentConsole and
 * FloatingAI.
 */
export interface AgentExecutionResult {
  id: string;
  agentName: string;
  agentIcon?: string;
  status: ExecutionStatus;
  confidence: ConfidenceLevel;
  executionTime: number;
  summary: string;
  findings: AgentFinding[];
  recommendations: AgentRecommendation[];
  sources: ExecutionSource[];
  startedAt?: string;
  completedAt?: string;
  metadata?: Record<string, unknown>;
}
