import React from 'react';

export default function EmergencyAdvisoryCard({ statusData }) {
  if (!statusData || statusData.uninitialized || !statusData.advisory) {
    return null;
  }

  const advisory = statusData.advisory;
  const glide = advisory.glide_footprint || {};
  const airfields = advisory.airfields || [];
  const throttleCap = advisory.recommended_throttle_cap || 100;
  const mavlinkText = advisory.mavlink_statustext || '';

  const diag = statusData.diagnostic_status || {};
  const isFault = diag.anomaly === 'YES';

  return (
    <div style={{ marginTop: '20px' }}>
      <p className="section-header">🚨 Autonomous Pilot Advisory & Emergency Diversion</p>
      
      <div className="residual-metrics-grid" style={{ marginBottom: '16px' }}>
        <div className="metric-card" style={{ borderColor: isFault ? '#ff1744' : '#2563eb' }}>
          <div className="metric-label">Recommended Throttle Cap</div>
          <div className="metric-value" style={{ color: isFault ? '#ff1744' : '#2563eb' }}>
            {throttleCap}%
          </div>
          <div className="metric-delta">
            {isFault ? 'CAP THROTTLE IMMEDIATELY' : 'Full Power Envelope Available'}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Safe Glide Radius (Engine-Out)</div>
          <div className="metric-value">{glide.powered_glide_nm || 0.0} NM</div>
          <div className="metric-delta">
            {glide.glide_km || 0.0} km ({glide.pure_glide_nm || 0.0} NM Pure Glide)
          </div>
        </div>
      </div>

      {airfields.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <p className="section-header" style={{ fontSize: '0.75rem', marginBottom: '8px' }}>
            Regional Diversion Recovery Airfields
          </p>
          <table className="evidence-table" style={{ width: '100%', textAlign: 'left' }}>
            <thead>
              <tr style={{ color: '#888', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <th style={{ padding: '6px' }}>Airfield / Recovery Base</th>
                <th style={{ padding: '6px' }}>Dist (NM)</th>
                <th style={{ padding: '6px' }}>Bearing</th>
                <th style={{ padding: '6px' }}>Runway</th>
                <th style={{ padding: '6px' }}>ETE</th>
                <th style={{ padding: '6px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {airfields.map((af) => (
                <tr key={af.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '6px', fontWeight: 'bold' }}>{af.name}</td>
                  <td style={{ padding: '6px' }}>{af.dist_nm} NM</td>
                  <td style={{ padding: '6px' }}>{af.bearing_deg}°</td>
                  <td style={{ padding: '6px' }}>{af.runway_ft} ft</td>
                  <td style={{ padding: '6px' }}>{af.ete_min} min</td>
                  <td style={{ padding: '6px' }}>
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.7rem',
                        fontWeight: 'bold',
                        backgroundColor: `${af.status_color}22`,
                        color: af.status_color,
                        border: `1px solid ${af.status_color}`
                      }}
                    >
                      {af.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {mavlinkText && (
        <div>
          <p className="section-header" style={{ fontSize: '0.75rem', marginBottom: '6px' }}>
            📡 Ground Control Station (MAVLink STATUSTEXT Stream)
          </p>
          <div
            style={{
              backgroundColor: '#0a0a14',
              border: '1px solid rgba(0, 210, 255, 0.3)',
              borderRadius: '6px',
              padding: '10px 14px',
              fontFamily: 'monospace',
              fontSize: '0.75rem',
              color: mavlinkText.includes('ALERT') ? '#ff4d4d' : mavlinkText.includes('WARNING') ? '#ffaa00' : '#00d2ff',
              lineHeight: '1.4'
            }}
          >
            {mavlinkText}
          </div>
        </div>
      )}
    </div>
  );
}
