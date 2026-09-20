import React from 'react';

export default function TopMetrics({ statusData, missionResults }) {
  if (!statusData || statusData.uninitialized) {
    return null;
  }

  const { diagnostic_status, health_index, rul_estimate } = statusData;

  let statusText = "NOMINAL";
  if (diagnostic_status.fault !== "NORMAL") {
    if (diagnostic_status.confirmed) {
      statusText = "FAULT DETECTED";
    } else {
      statusText = "ANALYZING...";
    }
  }

  const faultDisplay = diagnostic_status.fault !== "NORMAL" ? diagnostic_status.fault : "—";
  const rulStr = rul_estimate !== null && rul_estimate !== undefined ? `${Math.round(rul_estimate)}s` : "—";

  let cRisk = "—";
  if (missionResults && !missionResults.error && missionResults.risk) {
    const riskStr = missionResults.risk;
    if (riskStr.includes("|")) {
      const part = riskStr.split("|")[0];
      if (part.includes(":")) {
        cRisk = part.split(":")[1].trim();
      }
    }
  }

  return (
    <div className="top-metrics-grid">
      <div className="metric-card">
        <div className="metric-label">Engine Status</div>
        <div className="metric-value">{statusText}</div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Health Index</div>
        <div className="metric-value">{health_index !== undefined ? health_index.toFixed(1) : "—"}</div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Fault</div>
        <div className="metric-value">{faultDisplay}</div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Prototype RUL</div>
        <div className="metric-value">{rulStr}</div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Current Risk</div>
        <div className="metric-value">{cRisk}</div>
      </div>
    </div>
  );
}
