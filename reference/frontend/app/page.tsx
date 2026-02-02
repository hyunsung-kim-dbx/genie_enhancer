/**
 * Main application page with 6-step workflow and session sidebar.
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { Stepper } from '@/components/Stepper';
import { ParseStep } from '@/components/ParseStep';
import { GenerateStep } from '@/components/GenerateStep';
import { ValidateStep } from '@/components/ValidateStep';
import { BenchmarkStep } from '@/components/BenchmarkStep';
import { DeployStep } from '@/components/DeployStep';
import SessionSidebar from '@/components/SessionSidebar';
import { useSessionManager } from '@/lib/hooks/useSessionManager';

export default function Home() {
  const [currentStep, setCurrentStep] = useState(1);
  const [workflowState, setWorkflowState] = useState<any>({});
  const [restoringSession, setRestoringSession] = useState(false);
  const isInitialMount = useRef(true);
  const [creatingSession, setCreatingSession] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Session management
  const {
    sessions,
    currentSessionId,
    loading: sessionsLoading,
    hasMore,
    loadMoreSessions,
    createSession,
    switchSession,
    renameSession,
    deleteSession,
  } = useSessionManager();

  const steps = ['Upload & Extract', 'Generate', 'Validate', 'Benchmark', 'Deploy', 'Complete'];

  // Restore state when currentSessionId changes (including initial load)
  useEffect(() => {
    const restoreSessionState = async () => {
      if (!currentSessionId) return;

      // Skip initial mount restoration since useSessionManager already calls switchSession
      if (isInitialMount.current) {
        isInitialMount.current = false;

        // Still need to fetch and restore state on initial load
        try {
          setRestoringSession(true);
          const { state, currentStep: restoredStep } = await switchSession(currentSessionId);
          setWorkflowState(state);
          setCurrentStep(restoredStep);
        } catch (error) {
          console.error('Failed to restore initial session state:', error);
          setCurrentStep(1);
          setWorkflowState({});
        } finally {
          setRestoringSession(false);
        }
      }
    };

    restoreSessionState();
  }, [currentSessionId, switchSession]);

  // Handle session switching with state restoration
  const handleSessionSwitch = async (sessionId: string) => {
    setRestoringSession(true);
    try {
      const { state, currentStep: restoredStep } = await switchSession(sessionId);
      setWorkflowState(state);
      setCurrentStep(restoredStep);
    } catch (error) {
      console.error('Failed to restore session:', error);
      // Fallback: start at step 1 with empty state
      setCurrentStep(1);
      setWorkflowState({});
    } finally {
      setRestoringSession(false);
    }
  };

  // Handle session creation
  const handleSessionCreate = async () => {
    setCreatingSession(true);
    setCreateError(null);
    try {
      await createSession();
      // New sessions start at step 1 with empty state
      setCurrentStep(1);
      setWorkflowState({});
    } catch (error) {
      console.error('Failed to create session:', error);
      setCreateError(error instanceof Error ? error.message : 'Failed to create session');
    } finally {
      setCreatingSession(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Session Sidebar */}
      <SessionSidebar
        currentSessionId={currentSessionId}
        sessions={sessions}
        hasMore={hasMore}
        loading={sessionsLoading}
        onSessionSwitch={handleSessionSwitch}
        onSessionCreate={handleSessionCreate}
        onSessionRename={renameSession}
        onSessionDelete={deleteSession}
        onLoadMore={loadMoreSessions}
      />

      {/* Main Content */}
      <div className="flex-1 overflow-auto bg-gradient-to-br from-gray-50 to-gray-100">
        {/* Loading Overlay */}
        {restoringSession && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg shadow-xl">
              <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-gray-700">Restoring session...</p>
            </div>
          </div>
        )}

        <div className="container mx-auto p-8 max-w-6xl">
          <header className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Genie Lamp Agent
            </h1>
            <p className="text-gray-600">
              Generate Databricks Genie Spaces from natural language requirements
            </p>
            {currentSessionId && (
              <p className="text-sm text-gray-500 mt-1" suppressHydrationWarning>
                Session: {currentSessionId}
              </p>
            )}
          </header>

          <Stepper currentStep={currentStep} steps={steps} />

          <div className="bg-white rounded-lg shadow-lg p-8 mt-8">
            {/* Empty State - Show when no session exists */}
            {!currentSessionId && (
              <div className="text-center py-12">
                <div className="bg-blue-50 p-8 rounded-lg border border-blue-200 inline-block">
                  <h2 className="text-3xl font-bold text-blue-900 mb-4">
                    ✨ Welcome to Genie Lamp Agent
                  </h2>
                  <p className="text-gray-700 mb-6 max-w-md">
                    Get started by creating your first session. Each session tracks a complete workflow from requirements to deployment.
                  </p>

                  {createError && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                      <p className="text-red-800 text-sm">
                        <span className="font-semibold">Error:</span> {createError}
                      </p>
                    </div>
                  )}

                  <button
                    onClick={handleSessionCreate}
                    disabled={creatingSession}
                    className="px-8 py-4 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-lg font-medium"
                  >
                    {creatingSession ? (
                      <span className="flex items-center justify-center gap-2">
                        <div className="animate-spin h-5 w-5 border-3 border-white border-t-transparent rounded-full" />
                        Creating session...
                      </span>
                    ) : (
                      'Create New Session'
                    )}
                  </button>

                  <p className="text-sm text-gray-500 mt-4">
                    Your session will be saved automatically as you progress through the workflow.
                  </p>
                </div>
              </div>
            )}

            {currentStep === 1 && currentSessionId && (
              <ParseStep
                sessionId={currentSessionId}
              onComplete={(result) => {
                setWorkflowState((s: any) => ({ ...s, parseResult: result }));
                setCurrentStep(2);
              }}
                existingResult={workflowState.parseResult}
              />
            )}

            {currentStep === 2 && currentSessionId && (
              <GenerateStep
                sessionId={currentSessionId}
              requirementsPath={workflowState.parseResult?.output_path}
              onComplete={(result) => {
                setWorkflowState((s: any) => ({ ...s, generateResult: result }));
                setCurrentStep(3);
              }}
                onPrevious={() => setCurrentStep(1)}
                existingResult={workflowState.generateResult}
              />
            )}

            {currentStep === 3 && currentSessionId && (
              <ValidateStep
                sessionId={currentSessionId}
              configPath={workflowState.generateResult?.output_path}
              onComplete={(result) => {
                setWorkflowState((s: any) => ({ ...s, validateResult: result }));
                setCurrentStep(4);
              }}
                onPrevious={() => setCurrentStep(2)}
                existingResult={workflowState.validateResult}
              />
            )}

            {currentStep === 4 && currentSessionId && (
              <BenchmarkStep
                sessionId={currentSessionId}
              onComplete={(benchmarks) => {
                setWorkflowState((s: any) => ({ ...s, benchmarks }));
                setCurrentStep(5);
              }}
                onPrevious={() => setCurrentStep(3)}
                existingResult={workflowState.benchmarks}
              />
            )}

            {currentStep === 5 && currentSessionId && (
              <DeployStep
                sessionId={currentSessionId}
              configPath={workflowState.generateResult?.output_path}
              onComplete={(result) => {
                setWorkflowState((s: any) => ({ ...s, deployResult: result }));
                setCurrentStep(6);
              }}
                onPrevious={() => setCurrentStep(4)}
                existingResult={workflowState.deployResult}
              />
            )}

            {currentStep === 6 && (
              <div className="text-center">
                <div className="bg-green-50 p-8 rounded-lg border border-green-200">
                  <h2 className="text-3xl font-bold text-green-800 mb-4">
                    ✅ Complete!
                  </h2>
                  <div className="space-y-3">
                    <p className="text-gray-700">
                      <span className="font-semibold">Space ID:</span>{' '}
                      <code className="bg-gray-100 px-2 py-1 rounded">
                        {workflowState.deployResult?.space_id}
                      </code>
                    </p>
                    <a
                      href={workflowState.deployResult?.space_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                    >
                      Open Genie Space →
                    </a>
                  </div>
                </div>

                <div className="mt-6 flex gap-3 justify-center">
                  <button
                    onClick={() => setCurrentStep(5)}
                    className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                  >
                    ← Back to Deploy
                  </button>
                  <button
                    onClick={async () => {
                      await handleSessionCreate();
                    }}
                    className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    Start New Workflow
                  </button>
                </div>
              </div>
            )}
          </div>

          <footer className="mt-8 text-center text-sm text-gray-500">
            <p>Powered by Databricks Foundation Models</p>
          </footer>
        </div>
      </div>
    </div>
  );
}
