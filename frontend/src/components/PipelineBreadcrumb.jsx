import React from 'react';

export default function PipelineBreadcrumb({ statusData, missionResults }) {
  const steps = [
    "Telemetry",
    "Digital Twin",
    "Residuals",
    "Anomaly",
    "Confirmation",
    "Diagnosis",
    "Degradation",
    "RUL",
    "Mission Risk"
  ];

  let activeStep = 0;
  if (!statusData || statusData.uninitialized || statusData.current_time === 0) {
    activeStep = 0;
  } else if (
    statusData.diagnostic_status &&
    statusData.diagnostic_status.anomaly === "YES" &&
    statusData.diagnostic_status.confirmed
  ) {
    if (missionResults && !missionResults.error) {
      activeStep = 8;
    } else {
      activeStep = 5;
    }
  } else if (
    statusData.diagnostic_status &&
    statusData.diagnostic_status.anomaly === "YES"
  ) {
    activeStep = 3;
  } else {
    activeStep = 1;
  }

  return (
    <div className="pipeline-bar">
      {steps.map((step, idx) => {
        const isActive = idx <= activeStep;
        return (
          <React.Fragment key={step}>
            <span className={`pipeline-step ${isActive ? 'active' : ''}`}>
              {step}
            </span>
            {idx < steps.length - 1 && (
              <span className="pipeline-arrow">→</span>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
