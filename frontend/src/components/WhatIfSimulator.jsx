import React, { useState } from 'react';
import axios from 'axios';

export default function WhatIfSimulator({ onSimulateWhatIf }) {
  const [throttleCap, setThrottleCap] = useState(55);
  const [targetAltitude, setTargetAltitude] = useState(10000);
  const [durationSec, setDurationSec] = useState(60);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleSimulate = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      let data;
      if (onSimulateWhatIf) {
        data = await onSimulateWhatIf({
          throttle_cap: parseFloat(throttleCap),
          altitude: parseFloat(targetAltitude),
          duration: parseInt(durationSec, 10)
        });
      } else {
        const endpoints = ['', 'http://127.0.0.1:8000', 'http://localhost:8000'];
        let lastErr = null;
        for (const base of endpoints) {
          try {
            const res = await axios.post(`${base}/api/what-if-simulate`, {
              throttle_cap: parseFloat(throttleCap),
              altitude: parseFloat(targetAltitude),
              duration: parseInt(durationSec, 10)
            });
            data = res.data;
            break;
          } catch (e) {
            lastErr = e;
          }
        }
        if (!data && lastErr) throw lastErr;
      }
      setResult(data);
    } catch (err) {
      console.error('What-If simulation failed:', err);
      setErrorMsg('Simulation request failed. Ensure backend server on port 8000 is active.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: '20px', padding: '16px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
      <p className="section-header">🎮 Interactive "What-If" Trajectory Simulator</p>
      <p className="desc-text" style={{ marginBottom: '14px' }}>
        Test custom operator throttle caps and flight altitudes to evaluate engine safety margins prior to commanding GCS trajectory changes.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '14px' }}>
        <div>
          <label style={{ fontSize: '0.75rem', color: '#aaa', display: 'block', marginBottom: '4px' }}>
            Throttle Cap: <b>{throttleCap}%</b>
          </label>
          <input
            type="range"
            min="30"
            max="100"
            step="5"
            value={throttleCap}
            onChange={(e) => setThrottleCap(e.target.value)}
            style={{ width: '100%', cursor: 'pointer' }}
          />
        </div>

        <div>
          <label style={{ fontSize: '0.75rem', color: '#aaa', display: 'block', marginBottom: '4px' }}>
            Flight Altitude (ft MSL)
          </label>
          <input
            type="number"
            min="0"
            max="30000"
            step="1000"
            value={targetAltitude}
            onChange={(e) => setTargetAltitude(e.target.value)}
            style={{
              width: '100%',
              backgroundColor: '#1a1a2e',
              border: '1px solid rgba(255,255,255,0.2)',
              color: '#fff',
              padding: '6px 10px',
              borderRadius: '4px'
            }}
          />
        </div>

        <div>
          <label style={{ fontSize: '0.75rem', color: '#aaa', display: 'block', marginBottom: '4px' }}>
            Duration (Seconds)
          </label>
          <input
            type="number"
            min="10"
            max="300"
            step="10"
            value={durationSec}
            onChange={(e) => setDurationSec(e.target.value)}
            style={{
              width: '100%',
              backgroundColor: '#1a1a2e',
              border: '1px solid rgba(255,255,255,0.2)',
              color: '#fff',
              padding: '6px 10px',
              borderRadius: '4px'
            }}
          />
        </div>
      </div>

      <button
        onClick={handleSimulate}
        disabled={loading}
        className="sidebar-btn"
        style={{ width: 'auto', padding: '10px 24px', backgroundColor: '#00d2ff', color: '#000', fontWeight: 'bold', cursor: 'pointer' }}
      >
        {loading ? '⚡ Simulating Trajectory...' : '▶ Run What-If Trajectory Simulation'}
      </button>

      {errorMsg && (
        <div style={{ marginTop: '12px', padding: '10px', backgroundColor: 'rgba(255,23,68,0.1)', border: '1px solid #ff1744', borderRadius: '4px', color: '#ff4d4d', fontSize: '0.75rem' }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {result && (
        <div style={{ marginTop: '16px', padding: '14px', backgroundColor: 'rgba(0,210,255,0.05)', borderRadius: '6px', border: '1px solid rgba(0,210,255,0.3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: '#aaa' }}>Trajectory Assessment</span>
            <b style={{ color: result.safety_margin > 0.2 ? '#00e676' : result.safety_margin > 0.0 ? '#ff9100' : '#ff1744' }}>
              {result.risk_assessment}
            </b>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.75rem' }}>
            <div>
              <span style={{ color: '#888' }}>Forecast Safety Margin:</span> <b>{(result.safety_margin * 100).toFixed(1)}%</b>
            </div>
            <div>
              <span style={{ color: '#888' }}>Failure Time:</span> <b>{result.failure_time ? `${result.failure_time}s` : 'None (Safe)'}</b>
            </div>
            {result.forecast_rul_ci && (
              <div style={{ gridColumn: '1 / -1', marginTop: '4px' }}>
                <span style={{ color: '#888' }}>Forecast RUL (95% CI):</span>{' '}
                <b>{result.forecast_rul_ci.mean}s [{result.forecast_rul_ci.lower_95}s – {result.forecast_rul_ci.upper_95}s]</b>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
