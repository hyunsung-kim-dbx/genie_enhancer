/**
 * Step 4: Validate results
 */

'use client';

import { useState } from 'react';

interface ApplyStepProps {
  state: any;
  onUpdate: (updates: any) => void;
  onBack: () => void;
  sessionId: string | null;
}

export function ApplyStep({ state, onUpdate, onBack, sessionId }: ApplyStepProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const startValidation = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/jobs/validate', {
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
          benchmarks: state.benchmarks || [],
          initial_score: state.scoreResult?.score || 0,
          target_score: 0.90,
        }),
      });

      const data = await response.json();
      setJobId(data.job_id);
      pollJob(data.job_id);
    } catch (error) {
      console.error('Failed to start validation:', error);
      setLoading(false);
    }
  };

  const pollJob = async (id: string) => {
    const interval = setInterval(async () => {
      const response = await fetch(`/api/jobs/${id}`);
      const job = await response.json();

      if (job.status === 'completed') {
        clearInterval(interval);
        setResult(job.result);
        setLoading(false);
      } else if (job.status === 'failed') {
        clearInterval(interval);
        setLoading(false);
        alert('Validation failed: ' + job.error);
      }
    }, 2000);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">✅ Validate Results</h2>

      {!result && !loading && (
        <div>
          <p className="mb-4">Re-score benchmarks to validate improvements.</p>
          <button
            onClick={startValidation}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
          >
            Start Validation
          </button>
        </div>
      )}

      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Validating enhancements...</p>
        </div>
      )}

      {result && (
        <div>
          <div className={`p-6 rounded mb-4 ${result.target_reached ? 'bg-green-100' : 'bg-yellow-100'}`}>
            <h3 className="text-2xl font-bold mb-4">
              {result.target_reached ? '🎉 Target Reached!' : '📊 Results'}
            </h3>
            <div className="space-y-2">
              <p><strong>Initial Score:</strong> {(result.initial_score * 100).toFixed(1)}%</p>
              <p><strong>New Score:</strong> {(result.new_score * 100).toFixed(1)}%</p>
              <p><strong>Improvement:</strong> {(result.improvement * 100).toFixed(1)}%</p>
              <p><strong>Target:</strong> {(result.target_score * 100).toFixed(1)}%</p>
            </div>
          </div>

          <div className="flex justify-between">
            <button
              onClick={onBack}
              className="bg-gray-300 text-gray-700 px-6 py-2 rounded hover:bg-gray-400"
            >
              ← Back
            </button>
            <button
              onClick={() => window.location.reload()}
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
            >
              Start New Enhancement
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
