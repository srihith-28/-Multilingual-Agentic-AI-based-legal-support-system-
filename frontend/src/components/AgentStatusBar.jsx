import React from 'react';
import {
  Search,
  Brain,
  ShieldCheck,
  FileText,
  Radar,
  Lightbulb,
  CheckCircle2,
  MessageSquare,
} from 'lucide-react';

const PIPELINE_STAGES = [
  { id: 'input',        label: 'Language Detection',   icon: Radar },
  { id: 'safety',       label: 'Safety Check',          icon: ShieldCheck },
  { id: 'intent',       label: 'Intent Classifier',     icon: Lightbulb },
  { id: 'context',      label: 'Context Extraction',    icon: FileText },
  { id: 'retrieval',    label: 'Hybrid RAG Search',     icon: Search },
  { id: 'reasoning',    label: 'Legal Reasoning',       icon: Brain },
  { id: 'verification', label: 'Citation Verification', icon: CheckCircle2 },
  { id: 'response',     label: 'Response Synthesis',    icon: MessageSquare },
];

/**
 * AgentStatusBar
 * Shows the multi-agent pipeline as a horizontal step indicator.
 * When `isLoading` is true it animates through stages automatically.
 * When `isLoading` is false and `completed` is true, all steps show as done.
 */
export default function AgentStatusBar({ isLoading, completed }) {
  const [activeStage, setActiveStage] = React.useState(-1);

  React.useEffect(() => {
    if (!isLoading) {
      if (completed) setActiveStage(PIPELINE_STAGES.length - 1);
      else setActiveStage(-1);
      return;
    }

    // Auto-advance through stages while loading
    setActiveStage(0);
    let current = 0;
    const STAGE_DURATION = 2200; // ms per stage

    const interval = setInterval(() => {
      current = Math.min(current + 1, PIPELINE_STAGES.length - 1);
      setActiveStage(current);
    }, STAGE_DURATION);

    return () => clearInterval(interval);
  }, [isLoading, completed]);

  if (activeStage < 0) return null;

  return (
    <div className="agent-status-bar" role="status" aria-label="AI pipeline progress">
      <div className="pipeline-track">
        {PIPELINE_STAGES.map((stage, idx) => {
          const Icon = stage.icon;
          const isDone    = completed || (isLoading && idx < activeStage);
          const isActive  = isLoading && idx === activeStage;
          const isPending = !isDone && !isActive;

          return (
            <React.Fragment key={stage.id}>
              <div
                className={`pipeline-step ${isDone ? 'done' : isActive ? 'active' : 'pending'}`}
                title={stage.label}
              >
                <div className="step-icon-wrap">
                  <Icon size={12} />
                  {isActive && <span className="step-pulse" />}
                </div>
                <span className="step-label">{stage.label}</span>
              </div>
              {idx < PIPELINE_STAGES.length - 1 && (
                <div className={`pipeline-connector ${isDone ? 'done' : ''}`} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
