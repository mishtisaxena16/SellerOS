import { apiRequest } from './client';
import {
  AgentExecutionResult,
  ExecutionStatus,
  ExecutionSource,
} from '../types/execution';

// =========================================================
// Phase 6.3D — Type definitions updated to reuse the shared
// execution types from `types/execution.ts`. Duplicate local
// interfaces for execution status, sources, and results have
// been removed. API endpoints, request logic, and fetch
// functions are unchanged.
// =========================================================

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  createdAt: string;
}

export interface ChatSession {
  id: string;
  messages: ChatMessage[];
  executionResults?: AgentExecutionResult[];
}

export interface SendChatMessageRequest {
  sessionId: string;
  content: string;
}

export interface SendChatMessageResponse {
  response: string;
  intent: string[];
  marketplace: string | null;
  awaiting_approval: boolean;
  thread_id: string | null;
  guardrail_findings: string[];
  unimplemented_intents: string[];
}

export interface GetExecutionResultsResponse {
  sessionId: string;
  status: ExecutionStatus;
  results: AgentExecutionResult[];
  sources: ExecutionSource[];
}

// =========================================================
// Phase 6.5A — Restored for Agent Console integration.
//
// ExecutionPlanStep/ExecutionStepStatus originally lived here (Phase
// 6.2) and are still what ExecutionTimeline.tsx and
// ExecutionStatusBadge.tsx import from this module. Phase 6.3D's
// rewrite of this file (consolidating chat/session types onto the
// shared `types/execution.ts` models) dropped them, which left those
// two components with a broken import. Restoring them here — purely
// additive, nothing above this is changed — is what lets
// ExecutionTimeline actually render in AgentConsole again.
// =========================================================

/**
 * Lifecycle status of a single step in an execution plan, as rendered
 * by ExecutionStatusBadge inside ExecutionTimeline.
 */
export type ExecutionStepStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';

/**
 * A single planned step in a `ChatResponse.execution_plan` — which
 * agent will run, why, in what order, and its current status.
 */
export interface ExecutionPlanStep {
  agent_id: string;
  display_name: string;
  reason: string;
  execution_order: number;
  status: ExecutionStepStatus;
}

const API_BASE_URL = '/chat';

/**
 * Sends a chat message to the SellerOS assistant and returns
 * the assistant's reply along with any agent execution
 * results produced for that turn.
 */
export async function sendChatMessage(
  request: SendChatMessageRequest
): Promise<SendChatMessageResponse> {
  return apiRequest<SendChatMessageResponse>(API_BASE_URL, {
    method: 'POST',
    body: {
        message: request.content,
        session_id: request.sessionId,
    },
  });
}

/**
 * Fetches the current chat session, including message
 * history and any available execution results.
 */
export async function getChatSession(sessionId: string): Promise<ChatSession> {
  return apiRequest<ChatSession>(`${API_BASE_URL}/sessions/${sessionId}`);
}

/**
 * Fetches agent execution results for a given chat session.
 */
export async function getExecutionResults(
  sessionId: string
): Promise<GetExecutionResultsResponse> {
  return apiRequest<GetExecutionResultsResponse>(
    `${API_BASE_URL}/sessions/${sessionId}/executions`
  );
}