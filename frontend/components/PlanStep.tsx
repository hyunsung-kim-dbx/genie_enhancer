/**
 * Step 3: Plan and apply enhancements
 */

'use client';

import { useState } from 'react';

interface PlanStepProps {
  state: any;
  onUpdate: (updates: any) => void;
  onNext: () => void;
  onBack: () => void;
  sessionId: string | null;
}

export function PlanStep({ state, onUpdate, onNext, onBack, sessionId }: PlanStepProps) {
  const [planJobId, setPlanJobId] = useState<string | null>(null);
  const [applyJobId, setApplyJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<any>(null);
  const [applied, setApplied] = useState(false);

  const startPlanning = async () => {
    setLoading(true);
    try {
      const failedResults = state.scoreResult?.results?.filter((r: any) => !r.passed) || [];

      const response = await fetch('/api/jobs/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          workspace_config: {
            host: state.host,
            token: state.token,
            warehouse_id: state.warehouse_id,
            space_id: state.space_id,
            llm_endpoint: state.llm_endpoint,
          },
          failed_benchmarks: failedResults,
        }),
      });

      const data = await response.json();
      setPlanJobId(data.job_id);
      pollPlanJob(data.job_id);
    } catch (error) {
      console.error('Failed to start planning:', error);
      setLoading(false);
    }
  };

  const pollPlanJob = async (id: string) => {
    const interval = setInterval(async () => {
      const response = await fetch(`/api/jobs/${id}`);
      const job = await response.json();

      if (job.status === 'completed') {
        clearInterval(interval);
        setPlan(job.result);
        setLoading(false);
      } else if (job.status === 'failed') {
        clearInterval(interval);
        setLoading(false);
        alert('Planning failed: ' + job.error);
      }
    }, 2000);
  };

  const applyFixes = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/jobs/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          workspace_config: {
            host: state.host,
            token: state.token,
            warehouse_id: state.warehouse_id,
            space_id: state.space_id,
            llm_endpoint: state.llm_endpoint,
          },
          grouped_fixes: plan.grouped_fixes,
          dry_run: false,
        }),
      });

      const data = await response.json();
      setApplyJobId(data.job_id);
      pollApplyJob(data.job_id);
    } catch (error) {
      console.error('Failed to apply fixes:', error);
      setLoading(false);
    }
  };

  const pollApplyJob = async (id: string) => {
    const interval = setInterval(async () => {
      const response = await fetch(`/api/jobs/${id}`);
      const job = await response.json();

      if (job.status === 'completed') {
        clearInterval(interval);
        setApplied(true);
        setLoading(false);
        onUpdate({ appliedFixes: true });
      } else if (job.status === 'failed') {
        clearInterval(interval);
        setLoading(false);
        alert('Apply failed: ' + job.error);
      }
    }, 2000);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">🔧 Plan & Apply Enhancements</h2>

      {!plan && !loading && (
        <div>
          <p className="mb-4">Generate enhancement plan from failed benchmarks.</p>
          <button
            onClick={startPlanning}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
          >
            Generate Plan
          </button>
        </div>
      )}

      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>{applied ? 'Applying fixes...' : 'Generating plan...'}</p>
        </div>
      )}

      {plan && !applied && (
        <div>
          <div className="bg-blue-100 p-6 rounded mb-4">
            <h3 className="text-xl font-bold mb-2">Plan Ready</h3>
            <p>Total fixes: {plan.total_fixes}</p>
          </div>

          <button
            onClick={applyFixes}
            className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700"
          >
            Apply Fixes
          </button>
        </div>
      )}

      {applied && (
        <div>
          <div className="bg-green-100 p-6 rounded mb-4">
            <h3 className="text-xl font-bold mb-2">✓ Fixes Applied</h3>
          </div>

          <div className="flex justify-between">
            <button
              onClick={onBack}
              className="bg-gray-300 text-gray-700 px-6 py-2 rounded hover:bg-gray-400"
            >
              ← Back
            </button>
            <button
              onClick={onNext}
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
