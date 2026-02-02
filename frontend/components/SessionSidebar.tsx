/**
 * Session management sidebar
 */

'use client';

import { useState, useEffect } from 'react';

interface SessionSidebarProps {
  currentSessionId: string | null;
  onSessionChange: (sessionId: string) => void;
}

export default function SessionSidebar({ currentSessionId, onSessionChange }: SessionSidebarProps) {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/sessions');
      const data = await response.json();
      setSessions(data.sessions || []);

      // Auto-select first session if none selected
      if (!currentSessionId && data.sessions.length > 0) {
        onSessionChange(data.sessions[0].session_id);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const createSession = async () => {
    try {
      const response = await fetch('/api/sessions/create', { method: 'POST' });
      const session = await response.json();
      setSessions([session, ...sessions]);
      onSessionChange(session.session_id);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  return (
    <div className="w-64 bg-white border-r border-gray-200 p-4 overflow-y-auto">
      <div className="mb-4">
        <button
          onClick={createSession}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
        >
          + New Session
        </button>
      </div>

      <div className="space-y-2">
        {loading ? (
          <p className="text-gray-500 text-sm">Loading...</p>
        ) : (
          sessions.map((session) => (
            <div
              key={session.session_id}
              onClick={() => onSessionChange(session.session_id)}
              className={`
                p-3 rounded cursor-pointer
                ${currentSessionId === session.session_id
                  ? 'bg-blue-100 border-blue-500'
                  : 'bg-gray-50 hover:bg-gray-100'
                }
              `}
            >
              <p className="font-medium text-sm">{session.name}</p>
              <p className="text-xs text-gray-500">{session.updated_at}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
