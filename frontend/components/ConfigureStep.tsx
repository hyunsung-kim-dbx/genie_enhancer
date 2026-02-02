/**
 * Step 1: Configure workspace and space settings
 */

'use client';

import { useState, useEffect } from 'react';

interface ConfigureStepProps {
  state: any;
  onUpdate: (updates: any) => void;
  onNext: () => void;
  sessionId: string | null;
}

interface Warehouse {
  id: string;
  name: string;
  state: string;
}

interface GenieSpace {
  id: string;
  name: string;
  description?: string;
}

export function ConfigureStep({ state, onUpdate, onNext, sessionId }: ConfigureStepProps) {
  const [config, setConfig] = useState({
    host: state.host || '',
    token: state.token || '',
    warehouse_id: state.warehouse_id || '',
    space_id: state.space_id || '',
    llm_endpoint: state.llm_endpoint || 'databricks-gpt-5-2',
  });

  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [spaces, setSpaces] = useState<GenieSpace[]>([]);
  const [loadingWarehouses, setLoadingWarehouses] = useState(false);
  const [loadingSpaces, setLoadingSpaces] = useState(false);
  const [error, setError] = useState('');

  // Fetch default workspace config on mount
  useEffect(() => {
    const fetchDefaultConfig = async () => {
      try {
        const response = await fetch('/api/workspace/config');
        const data = await response.json();
        if (data.host || data.token) {
          setConfig(prev => ({
            ...prev,
            host: data.host || prev.host,
            token: data.token || prev.token,
          }));
        }
      } catch (err) {
        console.error('Failed to fetch default config:', err);
      }
    };
    fetchDefaultConfig();
  }, []);

  // Fetch warehouses and spaces when host and token are provided
  useEffect(() => {
    if (!config.host || !config.token) {
      setWarehouses([]);
      setSpaces([]);
      return;
    }

    const fetchResources = async () => {
      setError('');

      // Fetch warehouses
      setLoadingWarehouses(true);
      try {
        const whResponse = await fetch('/api/workspace/warehouses', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ host: config.host, token: config.token }),
        });
        const whData = await whResponse.json();
        if (whData.error) {
          setError(`Warehouses: ${whData.error}`);
          setWarehouses([]);
        } else {
          setWarehouses(whData.warehouses || []);
        }
      } catch (err) {
        setError(`Failed to fetch warehouses: ${err}`);
        setWarehouses([]);
      } finally {
        setLoadingWarehouses(false);
      }

      // Fetch Genie spaces
      setLoadingSpaces(true);
      try {
        const spaceResponse = await fetch('/api/workspace/spaces', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ host: config.host, token: config.token }),
        });
        const spaceData = await spaceResponse.json();
        if (spaceData.error) {
          setError(prev => prev ? `${prev} | Spaces: ${spaceData.error}` : `Spaces: ${spaceData.error}`);
          setSpaces([]);
        } else {
          setSpaces(spaceData.spaces || []);
        }
      } catch (err) {
        setError(prev => prev ? `${prev} | Failed to fetch spaces: ${err}` : `Failed to fetch spaces: ${err}`);
        setSpaces([]);
      } finally {
        setLoadingSpaces(false);
      }
    };

    // Debounce the fetch to avoid too many requests
    const timeoutId = setTimeout(fetchResources, 500);
    return () => clearTimeout(timeoutId);
  }, [config.host, config.token]);

  const handleNext = () => {
    onUpdate(config);
    onNext();
  };

  const isValid = config.host && config.token && config.warehouse_id && config.space_id;

  return (
    <div className="space-y-6 text-gray-900">
      <h2 className="text-2xl font-bold text-gray-900">⚙️ Configure Workspace</h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700">Databricks Host</label>
          <input
            type="text"
            value={config.host}
            onChange={(e) => setConfig({ ...config, host: e.target.value })}
            placeholder="https://your-workspace.cloud.databricks.com"
            className="w-full px-4 py-2 border rounded text-gray-900 bg-white"
          />
          {config.host && !config.host.startsWith('https://') && (
            <p className="text-sm text-amber-600 mt-1">⚠️ Host should start with https://</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700">Access Token</label>
          <input
            type="password"
            value={config.token}
            onChange={(e) => setConfig({ ...config, token: e.target.value })}
            placeholder="dapi..."
            className="w-full px-4 py-2 border rounded text-gray-900 bg-white"
          />
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700">SQL Warehouse</label>
          {loadingWarehouses ? (
            <div className="text-sm text-gray-500 py-2">Loading warehouses...</div>
          ) : warehouses.length > 0 ? (
            <select
              value={config.warehouse_id}
              onChange={(e) => setConfig({ ...config, warehouse_id: e.target.value })}
              className="w-full px-4 py-2 border rounded text-gray-900 bg-white"
            >
              <option value="">Select a warehouse...</option>
              {warehouses.map((wh) => (
                <option key={wh.id} value={wh.id}>
                  {wh.name} ({wh.state})
                </option>
              ))}
            </select>
          ) : config.host && config.token ? (
            <input
              type="text"
              value={config.warehouse_id}
              onChange={(e) => setConfig({ ...config, warehouse_id: e.target.value })}
              placeholder="Enter warehouse ID manually..."
              className="w-full px-4 py-2 border rounded text-gray-900 bg-white"
            />
          ) : (
            <input
              type="text"
              value={config.warehouse_id}
              onChange={(e) => setConfig({ ...config, warehouse_id: e.target.value })}
              placeholder="Enter host and token first..."
              className="w-full px-4 py-2 border rounded bg-gray-50 text-gray-500"
              disabled
            />
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700">Genie Space</label>
          {loadingSpaces ? (
            <div className="text-sm text-gray-500 py-2">Loading spaces...</div>
          ) : spaces.length > 0 ? (
            <select
              value={config.space_id}
              onChange={(e) => setConfig({ ...config, space_id: e.target.value })}
              className="w-full px-4 py-2 border rounded text-gray-900 bg-white"
            >
              <option value="">Select a space...</option>
              {spaces.map((space) => (
                <option key={space.id} value={space.id}>
                  {space.name} ({space.id})
                </option>
              ))}
            </select>
          ) : config.host && config.token ? (
            <input
              type="text"
              value={config.space_id}
              onChange={(e) => setConfig({ ...config, space_id: e.target.value })}
              placeholder="Enter space ID manually..."
              className="w-full px-4 py-2 border rounded text-gray-900 bg-white"
            />
          ) : (
            <input
              type="text"
              value={config.space_id}
              onChange={(e) => setConfig({ ...config, space_id: e.target.value })}
              placeholder="Enter host and token first..."
              className="w-full px-4 py-2 border rounded bg-gray-50 text-gray-500"
              disabled
            />
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700">LLM Endpoint</label>
          <select
            value={config.llm_endpoint}
            onChange={(e) => setConfig({ ...config, llm_endpoint: e.target.value })}
            className="w-full px-4 py-2 border rounded text-gray-900 bg-white"
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
