/**
 * Session sidebar component with list, rename, switch, and delete capabilities.
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { Session } from '@/lib/api-client';

interface SessionSidebarProps {
  currentSessionId: string | null;
  sessions: Session[];
  hasMore: boolean;
  loading: boolean;
  onSessionSwitch: (sessionId: string) => Promise<void>;
  onSessionCreate: () => Promise<void>;
  onSessionRename: (sessionId: string, newName: string) => Promise<void>;
  onSessionDelete: (sessionId: string) => Promise<void>;
  onLoadMore: () => Promise<void>;
}

export default function SessionSidebar({
  currentSessionId,
  sessions,
  hasMore,
  loading,
  onSessionSwitch,
  onSessionCreate,
  onSessionRename,
  onSessionDelete,
  onLoadMore,
}: SessionSidebarProps) {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');
  const [switchingSessionId, setSwitchingSessionId] = useState<string | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when editing starts
  useEffect(() => {
    if (editingSessionId && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingSessionId]);

  // Handle scroll for infinite loading
  const handleScroll = () => {
    const container = scrollContainerRef.current;
    if (!container || loading || !hasMore) return;

    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;

    // Trigger load more when scrolled near bottom (100px threshold)
    if (scrollTop + clientHeight >= scrollHeight - 100) {
      onLoadMore();
    }
  };

  // Debounced scroll handler
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    let timeoutId: NodeJS.Timeout;
    const debouncedHandleScroll = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(handleScroll, 200);
    };

    container.addEventListener('scroll', debouncedHandleScroll);
    return () => {
      container.removeEventListener('scroll', debouncedHandleScroll);
      clearTimeout(timeoutId);
    };
  }, [loading, hasMore, onLoadMore]);

  const handleEditStart = (session: Session) => {
    setEditingSessionId(session.session_id);
    setEditingName(session.name);
  };

  const handleEditSave = async (sessionId: string) => {
    if (editingName.trim()) {
      await onSessionRename(sessionId, editingName.trim());
    }
    setEditingSessionId(null);
  };

  const handleEditCancel = () => {
    setEditingSessionId(null);
    setEditingName('');
  };

  const handleKeyDown = (e: React.KeyboardEvent, sessionId: string) => {
    if (e.key === 'Enter') {
      handleEditSave(sessionId);
    } else if (e.key === 'Escape') {
      handleEditCancel();
    }
  };

  const handleSessionSwitch = async (sessionId: string) => {
    if (sessionId === currentSessionId) return;

    setSwitchingSessionId(sessionId);
    try {
      await onSessionSwitch(sessionId);
    } finally {
      setSwitchingSessionId(null);
    }
  };

  const formatLocalTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return 'Unknown';
    }
  };

  const getStepName = (step: number) => {
    const stepNames = [
      'Upload & Extract',
      'Generate',
      'Validate',
      'Benchmark',
      'Deploy',
      'Complete'
    ];
    return stepNames[step - 1] || 'Unknown';
  };

  return (
    <div className="w-[300px] h-screen bg-gray-50 border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="px-4 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Sessions</h2>
        <button
          onClick={onSessionCreate}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          + New Session
        </button>
      </div>

      {/* Session List */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto"
      >
        {sessions.length === 0 && !loading ? (
          <div className="px-4 py-8 text-center text-gray-500 text-sm">
            No sessions yet. Create your first one!
          </div>
        ) : (
          <>
            {sessions.map((session) => {
              const isActive = session.session_id === currentSessionId;
              const isEditing = editingSessionId === session.session_id;
              const isSwitching = switchingSessionId === session.session_id;

              return (
                <div
                  key={session.session_id}
                  className={`
                    px-4 py-3 cursor-pointer transition-colors relative group
                    ${isActive ? 'bg-blue-50 border-l-4 border-blue-500' : 'hover:bg-gray-100'}
                  `}
                  onClick={() => !isEditing && handleSessionSwitch(session.session_id)}
                  onDoubleClick={() => !isActive && handleEditStart(session)}
                >
                  {/* Session Name */}
                  {isEditing ? (
                    <input
                      ref={inputRef}
                      type="text"
                      value={editingName}
                      onChange={(e) => setEditingName(e.target.value)}
                      onBlur={() => handleEditSave(session.session_id)}
                      onKeyDown={(e) => handleKeyDown(e, session.session_id)}
                      className="w-full px-2 py-1 text-sm font-medium border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 truncate pr-2">
                          {isSwitching ? (
                            <span className="flex items-center gap-2">
                              <div className="animate-spin h-3 w-3 border-2 border-blue-500 border-t-transparent rounded-full" />
                              {session.name}
                            </span>
                          ) : (
                            session.name
                          )}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          Step {session.current_step}: {getStepName(session.current_step)}
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5">
                          {formatLocalTime(session.updated_at)}
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {/* Edit Button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEditStart(session);
                          }}
                          className="p-1 hover:bg-gray-200 rounded"
                          title="Rename"
                        >
                          <svg
                            className="w-4 h-4 text-gray-600"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                            />
                          </svg>
                        </button>

                        {/* Delete Button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSessionDelete(session.session_id);
                          }}
                          className="p-1 hover:bg-red-100 rounded"
                          title="Delete"
                        >
                          <svg
                            className="w-4 h-4 text-red-600"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* Loading Spinner at Bottom */}
            {loading && (
              <div className="py-4 flex justify-center">
                <div className="animate-spin h-6 w-6 border-3 border-blue-500 border-t-transparent rounded-full" />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
