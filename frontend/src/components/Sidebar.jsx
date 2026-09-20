import React, { useState } from 'react';

export default function Sidebar({
  onStartHealthy,
  onInjectFault,
  onSimulateMission,
  onIngestMAVLink,
  onReset,
  activeUAVId = 'UAV-ALPHA',
  onSelectUAV,
  debugMode,
  setDebugMode,
  loading
}) {
  const [missionProfile, setMissionProfile] = useState('Nominal');

  return (
    <aside className="sidebar">
      <div>
        <h3>✈️ TwinAero-X</h3>
        <p className="sidebar-caption">SIH Problem Statement 26054</p>
      </div>
      <div className="sidebar-divider" />

      <div>
        <p className="section-header">🛸 Tactical Swarm Squad</p>
        <label style={{ fontSize: '0.75rem', color: '#888', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
          Active UAV Twin Focus
        </label>
        <select
          className="sidebar-select"
          value={activeUAVId}
          onChange={(e) => onSelectUAV && onSelectUAV(e.target.value)}
          disabled={loading}
          style={{ marginBottom: '8px' }}
        >
          <option value="UAV-ALPHA">UAV-ALPHA (Alpha Recon)</option>
          <option value="UAV-BRAVO">UAV-BRAVO (Bravo Scout)</option>
          <option value="UAV-CHARLIE">UAV-CHARLIE (Charlie Cargo)</option>
          <option value="UAV-DELTA">UAV-DELTA (Delta Escort)</option>
        </select>
      </div>

      <div className="sidebar-divider" />

      <div>
        <p className="section-header">Demo Controls</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button
            className="sidebar-btn"
            onClick={onStartHealthy}
            disabled={loading}
          >
            ▶ Start Healthy Engine
          </button>
          <button
            className="sidebar-btn"
            onClick={onIngestMAVLink}
            disabled={loading}
          >
            📡 Ingest MAVLink Packet
          </button>
        </div>
      </div>

      <div>
        <p className="section-header">Inject Fault</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button
            className="sidebar-btn"
            onClick={() => onInjectFault('overheating')}
            disabled={loading}
          >
            🔥 Overheating
          </button>
          <button
            className="sidebar-btn"
            onClick={() => onInjectFault('lubrication')}
            disabled={loading}
          >
            🛢️ Lubrication Degradation
          </button>
          <button
            className="sidebar-btn"
            onClick={() => onInjectFault('vibration')}
            disabled={loading}
          >
            📳 Vibration Fault
          </button>
          <button
            className="sidebar-btn"
            onClick={() => onInjectFault('injector')}
            disabled={loading}
          >
            ⚙️ Injector Fault
          </button>
        </div>
      </div>

      <div>
        <p className="section-header">Mission Simulation</p>
        <label style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
          Mission Profile
        </label>
        <select
          className="sidebar-select"
          value={missionProfile}
          onChange={(e) => setMissionProfile(e.target.value)}
        >
          <option value="Conservative">Conservative</option>
          <option value="Nominal">Nominal</option>
          <option value="Aggressive">Aggressive</option>
        </select>

        <button
          className="sidebar-btn"
          onClick={() => onSimulateMission(missionProfile)}
          disabled={loading}
        >
          🚀 Simulate Future Risk
        </button>
      </div>

      <div className="sidebar-divider" />

      <div>
        <button
          className="sidebar-btn"
          onClick={onReset}
          disabled={loading}
        >
          🔄 Reset Demo
        </button>
      </div>

      <div style={{ marginTop: 'auto' }}>
        <label className="sidebar-checkbox-label">
          <input
            type="checkbox"
            checked={debugMode}
            onChange={(e) => setDebugMode(e.target.checked)}
          />
          Developer Debug Mode
        </label>
      </div>
    </aside>
  );
}
