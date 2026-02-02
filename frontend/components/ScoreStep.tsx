/**
 * Step 2: Score benchmarks
 */

'use client';

import { useState } from 'react';

interface ScoreStepProps {
  state: any;
  onUpdate: (updates: any) => void;
  onNext: () => void;
  onBack: () => void;
  sessionId: string | null;
}

export function ScoreStep({ state, onUpdate, onNext, onBack, sessionId }: ScoreStepProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const startScoring = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/jobs/score', {
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
        }),
      });

      const data = await response.json();
      setJobId(data.job_id);

      // Poll for results
      pollJob(data.job_id);
    } catch (error) {
      console.error('Failed to start scoring:', error);
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
        onUpdate({ scoreResult: job.result });
      } else if (job.status === 'failed') {
        clearInterval(interval);
        setLoading(false);
        alert('Scoring failed: ' + job.error);
      }
    }, 2000);
  };

  const handleNext = () => {
    onNext();
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">📊 Score Benchmarks</h2>

      {!result && !loading && (
        <div>
          <p className="mb-4">Ready to score benchmarks against your Genie Space.</p>
          <button
            onClick={startScoring}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
          >
            Start Scoring
          </button>
        </div>
      )}

      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Scoring in progress...</p>
        </div>
      )}

      {result && (
        <div>
          <div className="bg-green-100 p-6 rounded mb-4">
            <h3 className="text-xl font-bold mb-2">Score: {(result.score * 100).toFixed(1)}%</h3>
            <p>Passed: {result.passed} / {result.total}</p>
            <p>Failed: {result.failed}</p>
          </div>

          <div className="flex justify-between">
            <button
              onClick={onBack}
              className="bg-gray-300 text-gray-700 px-6 py-2 rounded hover:bg-gray-400"
            >
              ← Back
            </button>
            <button
              onClick={handleNext}
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
