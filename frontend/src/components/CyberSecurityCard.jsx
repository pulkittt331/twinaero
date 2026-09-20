import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function CyberSecurityCard({ onFetchSecurity, onSimulateAttack }) {
  const [secStatus, setSecStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState(null);

  const fetchSecurity = async () => {
    try {
      let data;
      if (onFetchSecurity) {
        data = await onFetchSecurity();
      } else {
        const res = await axios.get('/api/security/status');
        data = res.data;
      }
      setSecStatus(data);
    } catch (err) {
      console.error('Failed to fetch security status:', err);
    }
  };

  useEffect(() => {
    fetchSecurity();
    const interval = setInterval(fetchSecurity, 2500);
    return () => clearInterval(interval);
  }, []);

  const handleTriggerAttack = async (attackType) => {
    setLoading(true);
    setActionMsg(null);
    try {
      let data;
      if (onSimulateAttack) {
        data = await onSimulateAttack(attackType);
      } else {
        const res = await axios.post('/api/security/simulate-attack', { attack_type: attackType });
        data = res.data;
      }
      setActionMsg(data.message);
      await fetchSecurity();
    } catch (err) {
      console.error('Failed to trigger attack scenario:', err);
      setActionMsg('Failed to trigger attack scenario.');
    } finally {
      setLoading(false);
    }
  };

  if (!secStatus) {
    return (
      <div style={{ padding: '12px', color: '#888', fontSize: '0.8rem' }}>
        🛡️ Initializing Cyber-Security Integrity Monitor...
      </div>
    );
  }

  const isTampered = secStatus.is_tampered;
  const statusColor = isTampered ? '#ff1744' : '#00e676';

  return (
    <div style={{ marginTop: '20px', padding: '16px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: `1px solid ${isTampered ? '#ff1744' : 'rgba(0,230,118,0.25)'}` }}>
      {/* Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <p className="section-header" style={{ margin: 0 }}>
            🛡️ Cyber-Security & Telemetry Anti-Spoofing Engine
          </p>
          <span style={{ fontSize: '0.7rem', color: '#aaa' }}>
            1st Law PINN thermodynamic cross-validation & MAVLink sensor tampering defense
          </span>
        </div>

        <div style={{ padding: '6px 14px', borderRadius: '4px', backgroundColor: isTampered ? 'rgba(255,23,68,0.18)' : 'rgba(0,230,118,0.15)', border: `1px solid ${statusColor}`, color: statusColor, fontWeight: 'bold', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>{isTampered ? '🚨 MALICIOUS TELEMETRY SPOOFING DETECTED' : '🛡️ SECURE / TAMPER-FREE'}</span>
        </div>
      </div>

      {actionMsg && (
        <div style={{ padding: '8px 12px', backgroundColor: 'rgba(0,210,255,0.1)', border: '1px solid #00d2ff', borderRadius: '4px', color: '#00d2ff', fontSize: '0.75rem', marginBottom: '14px' }}>
          ⚡ {actionMsg}
        </div>
      )}

      {/* Security Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
        <div style={{ backgroundColor: 'rgba(0,0,0,0.25)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <span style={{ fontSize: '0.7rem', color: '#888', display: 'block' }}>Thermo Energy Residual</span>
          <b style={{ fontSize: '1.1rem', color: secStatus.thermo_energy_divergence_sigma > 3.0 ? '#ff1744' : '#00e676' }}>
            {secStatus.thermo_energy_divergence_sigma} σ
          </b>
          <span style={{ fontSize: '0.65rem', color: '#666', display: 'block' }}>Threshold: 3.0σ</span>
        </div>

        <div style={{ backgroundColor: 'rgba(0,0,0,0.25)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <span style={{ fontSize: '0.7rem', color: '#888', display: 'block' }}>Threat Confidence</span>
          <b style={{ fontSize: '1.1rem', color: isTampered ? '#ff9100' : '#888' }}>
            {secStatus.max_confidence_pct > 0 ? `${secStatus.max_confidence_pct}%` : '0% (Clean)'}
          </b>
          <span style={{ fontSize: '0.65rem', color: '#666', display: 'block' }}>Bayesian Security Auditor</span>
        </div>

        <div style={{ backgroundColor: 'rgba(0,0,0,0.25)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <span style={{ fontSize: '0.7rem', color: '#888', display: 'block' }}>Compromised Channels</span>
          <b style={{ fontSize: '0.85rem', color: isTampered ? '#ff1744' : '#00e676' }}>
            {secStatus.compromised_channels && secStatus.compromised_channels.length > 0 ? secStatus.compromised_channels.join(', ').toUpperCase() : 'NONE'}
          </b>
          <span style={{ fontSize: '0.65rem', color: '#666', display: 'block' }}>Sensory Isolation</span>
        </div>

        <div style={{ backgroundColor: 'rgba(0,0,0,0.25)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <span style={{ fontSize: '0.7rem', color: '#888', display: 'block' }}>Fallback Sanitizer</span>
          <b style={{ fontSize: '0.85rem', color: secStatus.sanitized_fallback_active ? '#00d2ff' : '#aaa' }}>
            {secStatus.sanitized_fallback_active ? 'ACTIVE (PINN Override)' : 'STANDBY (Passthrough)'}
          </b>
          <span style={{ fontSize: '0.65rem', color: '#00e676', display: 'block' }}>Autopilot Shield</span>
        </div>
      </div>

      {/* Threat Log List */}
      {secStatus.threats && secStatus.threats.length > 0 && (
        <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: 'rgba(255,23,68,0.08)', borderRadius: '6px', border: '1px solid rgba(255,23,68,0.3)' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#ff4d4d', display: 'block', marginBottom: '8px' }}>
            🚨 Active Cyber Threat Analysis Log:
          </span>
          {secStatus.threats.map((t, idx) => (
            <div key={idx} style={{ fontSize: '0.7rem', color: '#ff8080', marginBottom: '4px' }}>
              • <b>[{t.type}]</b> ({t.severity} - {t.confidence}% Confidence): {t.details}
            </div>
          ))}
        </div>
      )}

      {/* Simulate Cyber Attack Controls */}
      <div>
        <span style={{ fontSize: '0.75rem', color: '#aaa', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
          ⚔️ Cyber Attack Simulation Suite:
        </span>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            onClick={() => handleTriggerAttack('EGT_TAMPERING')}
            disabled={loading}
            style={{ padding: '6px 14px', borderRadius: '4px', border: '1px solid #ff1744', backgroundColor: 'rgba(255,23,68,0.15)', color: '#ff4d4d', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 'bold' }}
          >
            🔥 Inject EGT Sensor Tampering
          </button>
          <button
            onClick={() => handleTriggerAttack('GPS_SPOOFING')}
            disabled={loading}
            style={{ padding: '6px 14px', borderRadius: '4px', border: '1px solid #ff9100', backgroundColor: 'rgba(255,145,0,0.15)', color: '#ffab40', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 'bold' }}
          >
            🛰️ Inject GPS Altitude Spoofing
          </button>
          <button
            onClick={() => handleTriggerAttack('REPLAY_ATTACK')}
            disabled={loading}
            style={{ padding: '6px 14px', borderRadius: '4px', border: '1px solid #e040fb', backgroundColor: 'rgba(224,64,251,0.15)', color: '#ea80fc', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 'bold' }}
          >
            🔄 Inject Telemetry Replay Attack
          </button>
          <button
            onClick={() => handleTriggerAttack('CLEAR')}
            disabled={loading}
            style={{ padding: '6px 14px', borderRadius: '4px', border: '1px solid #00e676', backgroundColor: 'rgba(0,230,118,0.15)', color: '#00e676', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 'bold' }}
          >
            ✅ Clear Attack (Sanitize Telemetry)
          </button>
        </div>
      </div>
    </div>
  );
}
