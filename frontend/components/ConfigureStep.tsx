/**
 * Step 1: Configure workspace and space settings
 */

'use client';

import { useState } from 'react';

interface ConfigureStepProps {
  state: any;
  onUpdate: (updates: any) => void;
  onNext: () => void;
  sessionId: string | null;
}

export function ConfigureStep({ state, onUpdate, onNext, sessionId }: ConfigureStepProps) {
  const [config, setConfig] = useState({
    host: state.host || '',
    token: state.token || '',
    warehouse_id: state.warehouse_id || '',
    space_id: state.space_id || '',
    llm_endpoint: state.llm_endpoint || 'databricks-gpt-5-2',
  });

  const handleNext = () => {
    onUpdate(config);
    onNext();
  };

  const isValid = config.host && config.token && config.warehouse_id && config.space_id;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">⚙️ Configure Workspace</h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Databricks Host</label>
          <input
            type="text"
            value={config.host}
            onChange={(e) => setConfig({ ...config, host: e.target.value })}
            placeholder="https://your-workspace.cloud.databricks.com"
            className="w-full px-4 py-2 border rounded"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Access Token</label>
          <input
            type="password"
            value={config.token}
            onChange={(e) => setConfig({ ...config, token: e.target.value })}
            placeholder="dapi..."
            className="w-full px-4 py-2 border rounded"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">SQL Warehouse ID</label>
          <input
            type="text"
            value={config.warehouse_id}
            onChange={(e) => setConfig({ ...config, warehouse_id: e.target.value })}
            placeholder="abc123..."
            className="w-full px-4 py-2 border rounded"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Genie Space ID</label>
          <input
            type="text"
            value={config.space_id}
            onChange={(e) => setConfig({ ...config, space_id: e.target.value })}
            placeholder="01234..."
            className="w-full px-4 py-2 border rounded"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">LLM Endpoint</label>
          <select
            value={config.llm_endpoint}
            onChange={(e) => setConfig({ ...config, llm_endpoint: e.target.value })}
            className="w-full px-4 py-2 border rounded"
          >
            <option value="databricks-gpt-5-2">databricks-gpt-5-2</option>
            <option value="databricks-gpt-4-turbo">databricks-gpt-4-turbo</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleNext}
          disabled={!isValid}
          className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
        >
          Next →
        </button>
      </div>
    </div>
  );
}
