/**
 * Main application page with 4-step enhancement workflow.
 */

'use client';

import { useState, useEffect } from 'react';
import { Stepper } from '@/components/Stepper';
import { ConfigureStep } from '@/components/ConfigureStep';
import { ScoreStep } from '@/components/ScoreStep';
import { PlanStep } from '@/components/PlanStep';
import { ApplyStep } from '@/components/ApplyStep';
import SessionSidebar from '@/components/SessionSidebar';

export default function Home() {
  const [currentStep, setCurrentStep] = useState(1);
  const [workflowState, setWorkflowState] = useState<any>({});
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const steps = ['Configure', 'Score', 'Plan & Apply', 'Validate'];

  // Update workflow state
  const updateState = (updates: any) => {
    setWorkflowState((prev: any) => ({ ...prev, ...updates }));
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Session Sidebar */}
      <SessionSidebar
        currentSessionId={currentSessionId}
        onSessionChange={(sessionId) => {
          setCurrentSessionId(sessionId);
          // Reset workflow on session change
          setCurrentStep(1);
          setWorkflowState({});
        }}
      />

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto p-8">
          <header className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              🧞 Genie Space Enhancement
            </h1>
            <p className="text-lg text-gray-600">
              Automated improvement system with benchmark-driven evaluation
            </p>
          </header>

          {/* Stepper */}
          <div className="mb-8">
            <Stepper currentStep={currentStep} steps={steps} />
          </div>

          {/* Step Content */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            {currentStep === 1 && (
              <ConfigureStep
                state={workflowState}
                onUpdate={updateState}
                onNext={() => setCurrentStep(2)}
                sessionId={currentSessionId}
              />
            )}

            {currentStep === 2 && (
              <ScoreStep
                state={workflowState}
                onUpdate={updateState}
                onNext={() => setCurrentStep(3)}
                onBack={() => setCurrentStep(1)}
                sessionId={currentSessionId}
              />
            )}

            {currentStep === 3 && (
              <PlanStep
                state={workflowState}
                onUpdate={updateState}
                onNext={() => setCurrentStep(4)}
                onBack={() => setCurrentStep(2)}
                sessionId={currentSessionId}
              />
            )}

            {currentStep === 4 && (
              <ApplyStep
                state={workflowState}
                onUpdate={updateState}
                onBack={() => setCurrentStep(3)}
                sessionId={currentSessionId}
              />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
