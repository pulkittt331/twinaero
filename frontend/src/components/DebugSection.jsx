import React from 'react';

export default function DebugSection({ statusData }) {
  if (!statusData || statusData.uninitialized) return null;

  const obsHistory = statusData.obs_history || [];
  const lastObs = obsHistory.length > 0 ? obsHistory[obsHistory.length - 1] : {};

  return (
    <div className="debug-section">
      <div style={{ color: '#d97706', fontWeight: 600, fontSize: '0.9rem', marginBottom: '12px' }}>
        ⚠️ Developer Debug Mode — Not for presentation
      </div>

      <div className="debug-json-container">
        <div>
          <p className="section-header" style={{ fontSize: '0.7rem' }}>Last Telemetry Observation</p>
          <pre className="debug-json-box">
            {JSON.stringify(lastObs, null, 2)}
          </pre>
        </div>
        <div>
          <p className="section-header" style={{ fontSize: '0.7rem' }}>Diagnostic State Overview</p>
          <pre className="debug-json-box">
            {JSON.stringify(statusData.diagnostic_status || {}, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}
