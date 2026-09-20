import React from 'react';

export default function DiagnosticPipeline({ statusData }) {
  if (!statusData || statusData.uninitialized) {
    return null;
  }

  const friendlyNames = {
    cht: 'Cylinder Head Temp (Avg)',
    oil_temp: 'Oil Temp',
    vibration: 'Vibration',
    rpm: 'RPM',
    fuel_flow: 'Fuel Flow',
    egt: 'Exhaust Gas Temp (Avg)',
    oil_pressure: 'Oil Pressure',
    map: 'Manifold Abs. Pressure (MAP)',
    knock_index: 'Detonation / Knock Index',
    cht1: 'Cylinder 1 CHT',
    cht2: 'Cylinder 2 CHT',
    cht3: 'Cylinder 3 CHT',
    cht4: 'Cylinder 4 CHT',
    egt1: 'Cylinder 1 EGT',
    egt2: 'Cylinder 2 EGT',
    egt3: 'Cylinder 3 EGT',
    egt4: 'Cylinder 4 EGT'
  };

  const { diagnostic_status, z_scores, degradation_proxy, rul_estimate } = statusData;
  const isAnomaly = diagnostic_status.anomaly === 'YES';
  const isConfirmed = diagnostic_status.confirmed;
  const faultType = diagnostic_status.fault;
  const fTypeLower = faultType !== 'NORMAL' ? faultType.toLowerCase() : 'normal';

  const rulStr = rul_estimate !== null && rul_estimate !== undefined ? `${Math.round(rul_estimate)}s` : '—';
  const confidence = diagnostic_status.model_probability ? (diagnostic_status.model_probability * 100).toFixed(0) : '0';

  const ev = diagnostic_status.evidence || {};
  const hasEvidence = Object.keys(ev).length > 0;
  const evKey = ev.key;
  const evSensorName = friendlyNames[evKey] || evKey;
  const evZScore = evKey && z_scores ? z_scores[evKey] : 0.0;

  return (
    <div>
      <p className="section-header">AI Diagnostic Pipeline</p>

      {isAnomaly && isConfirmed ? (
        <>
          <span className="status-pill pill-red">⚠ CONFIRMED FAULT</span>

          <table className="evidence-table">
            <tbody>
              <tr>
                <td>Fault Type</td>
                <td><b>{faultType}</b></td>
              </tr>
              <tr>
                <td>AI Confidence</td>
                <td>{confidence}%</td>
              </tr>
              <tr>
                <td>3-Sample Confirmed</td>
                <td>✅ Yes</td>
              </tr>
            </tbody>
          </table>

          {hasEvidence && (
            <>
              <p className="section-header" style={{ fontSize: '0.7rem', marginTop: '16px' }}>
                Primary Evidence
              </p>
              <table className="evidence-table">
                <tbody>
                  <tr>
                    <td>Key Sensor</td>
                    <td><code>{evSensorName}</code></td>
                  </tr>
                  <tr>
                    <td>Actual</td>
                    <td>{ev.observed !== undefined ? ev.observed.toFixed(1) : '—'}</td>
                  </tr>
                  <tr>
                    <td>Expected</td>
                    <td>{ev.expected !== undefined ? ev.expected.toFixed(1) : '—'}</td>
                  </tr>
                  <tr>
                    <td>Residual</td>
                    <td>{ev.residual !== undefined ? ev.residual.toFixed(1) : '—'}</td>
                  </tr>
                  <tr>
                    <td>Z-Score</td>
                    <td><b>{evZScore !== undefined ? evZScore.toFixed(1) : '—'}</b></td>
                  </tr>
                </tbody>
              </table>
            </>
          )}

          <p className="section-header" style={{ fontSize: '0.7rem', marginTop: '16px' }}>
            Degradation & RUL Forecast
          </p>

          {fTypeLower !== 'normal' && fTypeLower !== 'injector' ? (
            <>
              <table className="evidence-table">
                <tbody>
                  <tr>
                    <td>Degradation Proxy</td>
                    <td><b>{degradation_proxy !== undefined ? degradation_proxy.toFixed(3) : '0.000'}</b></td>
                  </tr>
                  <tr>
                    <td>Prototype RUL Mean</td>
                    <td><b>{rulStr}</b></td>
                  </tr>
                  {statusData.rul_ci_95 && (
                    <tr>
                      <td>95% Confidence Interval</td>
                      <td><b>{statusData.rul_ci_95.lower_95}s – {statusData.rul_ci_95.upper_95}s</b> (±{statusData.rul_ci_95.std_dev}s)</td>
                    </tr>
                  )}
                </tbody>
              </table>
              <p className="desc-text" style={{ fontSize: '0.75rem', marginTop: '8px' }}>
                Bayesian ensemble forecast with 95% CI uncertainty bounds.
              </p>
            </>
          ) : fTypeLower === 'injector' ? (
            <table className="evidence-table">
              <tbody>
                <tr>
                  <td>Degradation Proxy</td>
                  <td>0.00</td>
                </tr>
                <tr>
                  <td>Prototype RUL</td>
                  <td><i>Unavailable for this fault</i></td>
                </tr>
              </tbody>
            </table>
          ) : null}

          {diagnostic_status.xai_attribution && Object.keys(diagnostic_status.xai_attribution).length > 0 && (
            <>
              <p className="section-header" style={{ fontSize: '0.7rem', marginTop: '16px' }}>
                🔍 XAI Feature Attribution (SHAP)
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '8px' }}>
                {Object.entries(diagnostic_status.xai_attribution).slice(0, 5).map(([key, val]) => (
                  <div key={key} style={{ fontSize: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                      <span style={{ color: '#a0a0a0' }}>{friendlyNames[key] || key}</span>
                      <b style={{ color: val > 25 ? '#ff4d4d' : '#00d2ff' }}>{val}%</b>
                    </div>
                    <div style={{ width: '100%', height: '5px', backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, val)}%`, height: '100%', backgroundColor: val > 25 ? '#ff4d4d' : '#00d2ff', borderRadius: '3px' }} />
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      ) : isAnomaly ? (
        <>
          <span className="status-pill pill-amber">⏳ ANOMALY DETECTED</span>
          <p className="desc-text" style={{ marginTop: '12px' }}>
            Awaiting 3-sample temporal confirmation to suppress transient false alarms.
          </p>
        </>
      ) : (
        <>
          <span className="status-pill pill-green">✓ ALL SYSTEMS NOMINAL</span>
          <p className="desc-text" style={{ marginTop: '12px' }}>
            Telemetry aligns with Digital Twin expectations. No anomaly detected.
          </p>
          {diagnostic_status.xai_attribution && Object.keys(diagnostic_status.xai_attribution).length > 0 && (
            <div style={{ marginTop: '14px' }}>
              <p className="section-header" style={{ fontSize: '0.7rem' }}>
                🔍 Live Sensor Attribution
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '6px' }}>
                {Object.entries(diagnostic_status.xai_attribution).slice(0, 3).map(([key, val]) => (
                  <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#888' }}>
                    <span>{friendlyNames[key] || key}</span>
                    <span>{val}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
