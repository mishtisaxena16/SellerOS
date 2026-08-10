import React from 'react';
import ConfidenceIndicator from './ConfidenceIndicator';
import SourceTags from './SourceTags';
import {
  AgentExecutionResult,
  ExecutionStatus,
  AgentFinding,
  AgentRecommendation,
  ExecutionSource,
} from '../types/execution';

// =========================================================
// Phase 6.3D — Import/type updates only.
// Local execution-related interfaces have been removed in
// favor of the shared types imported from
// `types/execution.ts`. No visual or logic changes.
// =========================================================

interface AgentExecutionCardProps
  extends Pick<
    AgentExecutionResult,
    | 'agentName'
    | 'status'
    | 'confidence'
    | 'executionTime'
    | 'summary'
    | 'findings'
    | 'recommendations'
    | 'sources'
  > {
  expanded: boolean;
  onToggleExpand: () => void;
}

const STATUS_LABELS: Record<ExecutionStatus, string> = {
  idle: 'Idle',
  queued: 'Queued',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
  waiting_for_approval: 'Waiting for Approval',
};

const AgentExecutionCard: React.FC<AgentExecutionCardProps> = ({
  agentName,
  status,
  confidence,
  executionTime,
  summary,
  findings,
  recommendations,
  sources,
  expanded,
  onToggleExpand,
}) => {
  return (
    <div className={`agent-execution-card ${expanded ? 'agent-execution-card--expanded' : ''}`}>
      <button
        type="button"
        className="agent-execution-card__header"
        onClick={onToggleExpand}
        aria-expanded={expanded}
      >
        <span className="agent-execution-card__name">{agentName}</span>
        <span className={`agent-execution-card__status agent-execution-card__status--${status}`}>
          {STATUS_LABELS[status]}
        </span>
        <ConfidenceIndicator confidence={confidence} />
        <span className="agent-execution-card__toggle-icon">
          {expanded ? '−' : '+'}
        </span>
      </button>

      {expanded && (
        <div className="agent-execution-card__body">
          <p className="agent-execution-card__execution-time">
            Execution time: {executionTime}ms
          </p>

          <p className="agent-execution-card__summary">{summary}</p>

          {findings.length > 0 && (
            <div className="agent-execution-card__section">
              <h4 className="agent-execution-card__section-title">Key Findings</h4>
              <ul className="agent-execution-card__list">
                {findings.map((finding: AgentFinding, index: number) => (
                  <li
                    key={`${finding.title}-${index}`}
                    className={`agent-execution-card__finding agent-execution-card__finding--${finding.severity ?? 'info'}`}
                  >
                    <span className="agent-execution-card__finding-title">
                      {finding.title}
                    </span>
                    <span className="agent-execution-card__finding-description">
                      {finding.description}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {recommendations.length > 0 && (
            <div className="agent-execution-card__section">
              <h4 className="agent-execution-card__section-title">Recommendations</h4>
              <ul className="agent-execution-card__list">
                {recommendations.map((rec: AgentRecommendation, index: number) => (
                  <li
                    key={`${rec.title}-${index}`}
                    className={`agent-execution-card__recommendation agent-execution-card__recommendation--${rec.priority ?? 'medium'}`}
                  >
                    <span className="agent-execution-card__recommendation-title">
                      {rec.title}
                    </span>
                    <span className="agent-execution-card__recommendation-description">
                      {rec.description}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {sources.length > 0 && (
            <div className="agent-execution-card__section">
              <h4 className="agent-execution-card__section-title">Supporting Sources</h4>
              <SourceTags sources={sources as ExecutionSource[]} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AgentExecutionCard;
