import React, { useMemo, useState } from 'react';
import ExecutionTimeline from './ExecutionTimeline';
import AgentExecutionCard from './AgentExecutionCard';
import SellerCoachSummary, {
  type SellerCoachSummaryData,
  type SellerCoachStrength,
  type SellerCoachIssue,
} from './SellerCoachSummary';
import { AgentExecutionResult, ExecutionStatus } from '../types/execution';
import type { ExecutionPlanStep, ExecutionStepStatus } from '../api/chat';

// =========================================================
// Phase 6.5C — Shared Rendering Cleanup
//
// AgentConsole.tsx (Phase 6.5A) and FloatingAI.tsx (Phase 6.5B) had
// independently assembled the exact same three-stage execution UI —
// Execution Timeline -> Agent Cards -> Seller Coach Summary — from the
// same `AgentExecutionResult[]` model, including identical helper
// functions and an identical mock-data fallback. This component is
// that UI, extracted once so both callers render it (and stay in
// sync) instead of maintaining two copies.
//
// What stays out of this component on purpose:
// - The "Final AI Response" chat thread and its input. AgentConsole
//   and FloatingAI don't share an implementation there today (see
//   CHANGELOG_PHASE6_5B.md) and this phase is rendering cleanup only —
//   no new features, no API integration — so that divergence is left
//   as-is rather than papered over.
// - Any data fetching. Like the components it replaces, this only
//   ever reshapes an `AgentExecutionResult[]` that's handed to it; it
//   never talks to the backend, RAG, the connector layer, or any
//   marketplace API itself.
// =========================================================

interface ExecutionResultsPanelProps {
  /** Real execution results for the current turn/session. When
   * omitted or empty, falls back to representative mock data so the
   * panel still has something to show — the same fallback both
   * AgentConsole and FloatingAI already relied on individually. */
  executionResults?: AgentExecutionResult[];
  className?: string;
}

// =========================================================
// Mock fallback (previously duplicated verbatim in both
// AgentConsole.tsx and FloatingAI.tsx). Field shapes match the shared
// AgentExecutionResult type from Phase 6.3D. Remove once backend
// orchestration always provides real execution results.
// =========================================================

const MOCK_EXECUTION_RESULTS: AgentExecutionResult[] = [
  {
    id: 'analytics-agent-001',
    agentName: 'Analytics Agent',
    status: 'completed',
    confidence: 87,
    executionTime: 1240,
    summary: 'Sales velocity increased 18% week-over-week across top SKUs.',
    findings: [
      {
        title: 'Mobile checkout conversion improved',
        description: 'Conversion rate improved on mobile checkout flow',
        severity: 'info',
      },
      {
        title: 'Revenue concentration',
        description: 'Top 3 SKUs account for 42% of total revenue',
        severity: 'info',
      },
    ],
    recommendations: [
      {
        title: 'Increase ad spend',
        description: 'Increase ad spend on top-performing SKUs',
        priority: 'high',
      },
      {
        title: 'Investigate desktop drop-off',
        description: 'Investigate desktop checkout drop-off',
        priority: 'medium',
      },
    ],
    sources: [
      { id: 'src-sales-dashboard', name: 'Sales Dashboard', type: 'dashboard' },
      { id: 'src-marketplace-api', name: 'Marketplace Analytics API', type: 'api' },
    ],
  },
  {
    id: 'inventory-agent-001',
    agentName: 'Inventory Agent',
    status: 'completed',
    confidence: 74,
    executionTime: 980,
    summary: 'Two SKUs are projected to stock out within 7 days.',
    findings: [
      {
        title: 'SKU-1042 low cover',
        description: 'SKU-1042 has 6 days of cover remaining',
        severity: 'warning',
      },
      {
        title: 'SKU-2078 low cover',
        description: 'SKU-2078 has 4 days of cover remaining',
        severity: 'critical',
      },
    ],
    recommendations: [
      {
        title: 'Trigger reorder',
        description: 'Trigger reorder for SKU-1042 and SKU-2078',
        priority: 'high',
      },
      {
        title: 'Review supplier lead times',
        description: 'Review supplier lead times for restock planning',
        priority: 'medium',
      },
    ],
    sources: [
      { id: 'src-inventory-sync', name: 'Inventory Sync', type: 'integration' },
      { id: 'src-warehouse-feed', name: 'Warehouse Feed', type: 'integration' },
    ],
  },
  {
    id: 'pricing-agent-001',
    agentName: 'Pricing Agent',
    status: 'completed',
    confidence: 68,
    executionTime: 1510,
    summary: 'Competitor pricing has shifted on 5 tracked listings.',
    findings: [
      {
        title: 'Market price decline',
        description: 'Average competitor price dropped 6% this week',
        severity: 'warning',
      },
      {
        title: 'Above-market pricing',
        description: 'Your pricing remains above market on 2 listings',
        severity: 'warning',
      },
    ],
    recommendations: [
      {
        title: 'Adjust pricing',
        description: 'Consider a 3-5% price adjustment on affected listings',
        priority: 'medium',
      },
      {
        title: 'Monitor competitors',
        description: 'Monitor competitor response before further changes',
        priority: 'low',
      },
    ],
    sources: [
      { id: 'src-competitor-tracker', name: 'Competitor Price Tracker', type: 'tool' },
    ],
  },
  {
    id: 'seller-coach-001',
    agentName: 'Seller Coach',
    status: 'completed',
    confidence: 91,
    executionTime: 760,
    summary: 'Account health is strong with one actionable improvement.',
    findings: [
      {
        title: 'Order defect rate healthy',
        description: 'Order defect rate is within safe threshold',
        severity: 'info',
      },
      {
        title: 'Response time increasing',
        description: 'Response time to buyer messages has increased slightly',
        severity: 'warning',
      },
    ],
    recommendations: [
      {
        title: 'Respond faster to buyers',
        description: 'Respond to buyer messages within 12 hours to maintain rating',
        priority: 'medium',
      },
    ],
    sources: [
      { id: 'src-seller-performance', name: 'Seller Performance Dashboard', type: 'dashboard' },
    ],
  },
];

// =========================================================
// Data shaping helpers (previously duplicated verbatim in both
// AgentConsole.tsx and FloatingAI.tsx).
// =========================================================

function toExecutionStepStatus(status: ExecutionStatus): ExecutionStepStatus {
  switch (status) {
    case 'completed':
      return 'completed';
    case 'failed':
      return 'failed';
    case 'running':
      return 'running';
    case 'idle':
    case 'queued':
    case 'waiting_for_approval':
    default:
      return 'pending';
  }
}

function toAgentId(agentName: string): string {
  return agentName.trim().toLowerCase().replace(/\s+agent$/, '').replace(/\s+/g, '_');
}

function toExecutionPlan(results: AgentExecutionResult[]): ExecutionPlanStep[] {
  return results.map((result, index) => ({
    agent_id: toAgentId(result.agentName),
    display_name: result.agentName,
    reason: result.summary,
    execution_order: index + 1,
    status: toExecutionStepStatus(result.status),
  }));
}

const TERMINAL_STATUSES: ExecutionStatus[] = ['completed', 'failed'];

function deriveCoachSummary(results: AgentExecutionResult[]): SellerCoachSummaryData {
  const completedResults = results.filter((r) => r.status === 'completed');
  const failedCount = results.filter((r) => r.status === 'failed').length;

  const avgConfidence = completedResults.length
    ? Math.round(
        completedResults.reduce((sum, r) => sum + r.confidence, 0) / completedResults.length
      )
    : 0;

  const label =
    avgConfidence >= 85 ? 'Excellent' :
    avgConfidence >= 70 ? 'Good' :
    avgConfidence >= 50 ? 'Fair' :
    'Needs attention';

  const aiSummary = failedCount > 0
    ? `${completedResults.length} of ${results.length} agents completed successfully (${failedCount} failed), with an average confidence of ${avgConfidence}%.`
    : `All ${results.length} agent${results.length === 1 ? '' : 's'} completed, with an average confidence of ${avgConfidence}%.`;

  const strengths: SellerCoachStrength[] = [];
  const issues: SellerCoachIssue[] = [];

  for (const result of completedResults) {
    for (const finding of result.findings) {
      if (finding.severity === 'critical' || finding.severity === 'warning') {
        issues.push({
          id: `${result.id}-${finding.title}`,
          title: finding.title,
          detail: finding.description,
          severity: finding.severity === 'critical' ? 'critical' : 'warning',
        });
      } else {
        strengths.push({
          id: `${result.id}-${finding.title}`,
          title: finding.title,
          detail: finding.description,
        });
      }
    }
  }

  return {
    health: { score: avgConfidence, label },
    aiSummary,
    strengths: strengths.slice(0, 3),
    issues: issues.slice(0, 3),
  };
}

// =========================================================
// ExecutionResultsPanel
//
// Renders, in order: Execution Timeline -> Agent Cards -> Seller
// Coach Summary. Owns its own per-card expand/collapse state, since
// nothing outside this panel ever needed to read or control it in
// either of the two places it was previously duplicated.
// =========================================================

const ExecutionResultsPanel: React.FC<ExecutionResultsPanelProps> = ({
  executionResults,
  className = '',
}) => {
  // Only fall back to mock data when no real results exist.
  const resultsToRender = useMemo<AgentExecutionResult[]>(() => {
    if (executionResults && executionResults.length > 0) return executionResults;
    return MOCK_EXECUTION_RESULTS;
  }, [executionResults]);

  const hasResults = resultsToRender.length > 0;

  // Cards should appear as each agent finishes — only terminal
  // (completed/failed) results are shown; still-running/queued agents
  // stay represented in the timeline above until they finish.
  const finishedResults = useMemo(
    () => resultsToRender.filter((r) => TERMINAL_STATUSES.includes(r.status)),
    [resultsToRender]
  );

  // Seller Coach summary appears only once every agent has reached a
  // terminal state — not while any are still idle/queued/running/
  // waiting for approval.
  const allAgentsFinished =
    hasResults && resultsToRender.every((r) => TERMINAL_STATUSES.includes(r.status));

  const executionPlan = useMemo(() => toExecutionPlan(resultsToRender), [resultsToRender]);

  const coachSummary = useMemo(
    () => (allAgentsFinished ? deriveCoachSummary(resultsToRender) : null),
    [allAgentsFinished, resultsToRender]
  );

  // Independent expand/collapse state per card.
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});
  const toggleCard = (id: string) => {
    setExpandedCards((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className={`execution-results-panel space-y-3 ${className}`}>
      {/* Execution Timeline — stays visible for the whole run; statuses
          update in place as agents move from pending -> running -> done. */}
      <div className="execution-results-panel__execution-timeline">
        <ExecutionTimeline executionPlan={executionPlan} />
      </div>

      {/* Agent Execution Cards — appear one by one as each agent finishes. */}
      {finishedResults.length > 0 && (
        <div
          className="execution-results-panel__agent-cards space-y-2"
          data-testid="execution-results-agent-cards"
        >
          {finishedResults.map((result) => (
            <AgentExecutionCard
              key={result.id}
              agentName={result.agentName}
              status={result.status}
              confidence={result.confidence}
              executionTime={result.executionTime}
              summary={result.summary}
              findings={result.findings}
              recommendations={result.recommendations}
              sources={result.sources}
              expanded={!!expandedCards[result.id]}
              onToggleExpand={() => toggleCard(result.id)}
            />
          ))}
        </div>
      )}

      {/* Seller Coach Summary — appears once all agents have completed. */}
      {coachSummary && (
        <div className="execution-results-panel__coach-summary">
          <SellerCoachSummary data={coachSummary} />
        </div>
      )}
    </div>
  );
};

export default ExecutionResultsPanel;
