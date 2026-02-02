/**
 * Stepper component for workflow progress visualization.
 */

interface StepperProps {
  currentStep: number;
  steps: string[];
}

export function Stepper({ currentStep, steps }: StepperProps) {
  return (
    <div className="flex items-center justify-between mb-8">
      {steps.map((step, idx) => {
        const stepNumber = idx + 1;
        const isActive = stepNumber === currentStep;
        const isCompleted = stepNumber < currentStep;

        return (
          <div key={idx} className="flex items-center">
            <div
              className={`
                w-10 h-10 rounded-full flex items-center justify-center font-semibold
                transition-colors duration-200
                ${
                  isActive
                    ? 'bg-blue-500 text-white'
                    : isCompleted
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-600'
                }
              `}
            >
              {isCompleted ? '✓' : stepNumber}
            </div>
            <span
              className={`ml-2 ${
                isActive ? 'font-semibold' : 'text-gray-600'
              }`}
            >
              {step}
            </span>
            {idx < steps.length - 1 && (
              <div
                className={`w-16 h-1 mx-4 ${
                  isCompleted ? 'bg-green-500' : 'bg-gray-200'
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
