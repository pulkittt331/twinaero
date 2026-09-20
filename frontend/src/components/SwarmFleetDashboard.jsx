import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function SwarmFleetDashboard({ onSelectUAV, onSwarmFault, onSwarmUpdated }) {
  const [swarmData, setSwarmData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedFaults, setSelectedFaults] = useState({});
  const [errorMsg, setErrorMsg] = useState(null);

  const fetchSwarmStatus = async () => {
    try {
      const res = await axios.get('/api/swarm/status');
      setSwarmData(res.data);
      if (onSwarmUpdated) onSwarmUpdated(res.data);
    } catch (err) {
      console.error('Failed to fetch swarm status:', err);
    }
  };

  useEffect(() => {
    fetchSwarmStatus();
    const interval = setInterval(fetchSwarmStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSelect = async (uavId) => {
    setLoading(true);
    try {
      let data;
      if (onSelectUAV) {
        data = await onSelectUAV(uavId);
      } else {
        const res = await axios.post('/api/swarm/select', { uav_id: uavId });
        data = res.data;
      }
      setSwarmData(data);
      if (onSwarmUpdated) onSwarmUpdated(data);
    } catch (err) {
      console.error('Error selecting UAV:', err);
      setErrorMsg('Failed to select active UAV twin.');
    } finally {
      setLoading(false);
    }
  };

  const handleInjectFault = async (uavId) => {
    const faultType = selectedFaults[uavId] || 'overheating';
    setLoading(true);
    try {
      let data;
      if (onSwarmFault) {
        data = await onSwarmFault(uavId, faultType);
      } else {
        const res = await axios.post('/api/swarm/inject-fault', { uav_id: uavId, fault_type: faultType });
        data = res.data;
      }
      setSwarmData(data);
      if (onSwarmUpdated) onSwarmUpdated(data);
    } catch (err) {
      console.error('Error injecting swarm fault:', err);
      setErrorMsg('Failed to inject fault into ' + uavId);
    } finally {
      setLoading(false);
    }
  };

  if (!swarmData || !swarmData.uavs) {
    return (
      <div style={{ padding: '12px', color: '#888', fontSize: '0.8rem' }}>
        ⚡ Synchronizing Tactical Swarm Telemetry...
      </div>
    );
  }

  const uavList = Object.values(swarmData.uavs);

  return (
    <div style={{ marginBottom: '20px', padding: '16px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid rgba(0,210,255,0.25)' }}>
      {/* Header & Fleet Summary Metrics */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <p className="section-header" style={{ margin: 0 }}>
            🛸 Multi-UAV Swarm & Tactical Fleet Telemetry
          </p>
          <span style={{ fontSize: '0.7rem', color: '#aaa' }}>
            Realtime multi-drone digital twin isolation & autonomous mission handover
          </span>
        </div>

        <div style={{ display: 'flex', gap: '16px', fontSize: '0.75rem' }}>
          <div style={{ padding: '4px 10px', backgroundColor: 'rgba(0,210,255,0.1)', borderRadius: '4px', border: '1px solid rgba(0,210,255,0.3)' }}>
            Squad Avg Health: <b style={{ color: swarmData.swarm_health_avg > 80 ? '#00e676' : '#ff9100' }}>{swarmData.swarm_health_avg}%</b>
          </div>
          <div style={{ padding: '4px 10px', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.1)' }}>
            Active UAVs: <b>{swarmData.total_uavs} Squad Units</b>
          </div>
          <div style={{ padding: '4px 10px', backgroundColor: swarmData.active_faults_count > 0 ? 'rgba(255,23,68,0.15)' : 'rgba(0,230,118,0.1)', borderRadius: '4px', border: `1px solid ${swarmData.active_faults_count > 0 ? '#ff1744' : '#00e676'}` }}>
            Active Faults: <b>{swarmData.active_faults_count}</b>
          </div>
        </div>
      </div>

      {/* Autonomous Re-allocation Banner */}
      {swarmData.reallocation_notices && swarmData.reallocation_notices.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          {swarmData.reallocation_notices.map((notice, idx) => (
            <div key={idx} style={{ padding: '10px 14px', backgroundColor: 'rgba(255,145,0,0.12)', border: '1px solid #ff9100', borderRadius: '6px', color: '#ffab40', fontSize: '0.75rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>⚠️</span>
              <span>{notice.notice}</span>
            </div>
          ))}
        </div>
      )}

      {/* UAV Fleet Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
        {uavList.map((uav) => {
          const isSelected = uav.id === swarmData.active_uav_id;
          const isFaulty = uav.fault !== 'NORMAL';
          const hiColor = uav.health_index > 80 ? '#00e676' : uav.health_index > 50 ? '#ff9100' : '#ff1744';

          return (
            <div
              key={uav.id}
              style={{
                backgroundColor: isSelected ? 'rgba(0,210,255,0.08)' : 'rgba(0,0,0,0.3)',
                padding: '12px',
                borderRadius: '6px',
                border: isSelected ? '2px solid #00d2ff' : isFaulty ? '1px solid #ff1744' : '1px solid rgba(255,255,255,0.08)',
                boxShadow: isSelected ? '0 0 10px rgba(0,210,255,0.2)' : 'none',
                position: 'relative'
              }}
            >
              {/* Header Badge */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <b style={{ fontSize: '0.9rem', color: isSelected ? '#00d2ff' : '#fff' }}>
                  {uav.name}
                </b>
                {isSelected && (
                  <span style={{ fontSize: '0.6rem', padding: '1px 6px', borderRadius: '3px', backgroundColor: '#00d2ff', color: '#000', fontWeight: 'bold' }}>
                    ACTIVE TWIN
                  </span>
                )}
              </div>

              <span style={{ fontSize: '0.65rem', color: '#888', display: 'block', marginBottom: '8px' }}>
                {uav.role} ({uav.engine})
              </span>

              {/* Health Index Bar */}
              <div style={{ marginBottom: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', marginBottom: '2px' }}>
                  <span style={{ color: '#aaa' }}>Health Index</span>
                  <b style={{ color: hiColor }}>{uav.health_index}%</b>
                </div>
                <div style={{ width: '100%', height: '5px', backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${uav.health_index}%`, height: '100%', backgroundColor: hiColor, transition: 'width 0.3s ease' }} />
                </div>
              </div>

              {/* Status & RUL */}
              <div style={{ fontSize: '0.7rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginBottom: '10px' }}>
                <div>
                  <span style={{ color: '#666' }}>Fault Mode:</span>
                  <b style={{ color: isFaulty ? '#ff1744' : '#00e676', display: 'block' }}>
                    {uav.fault.toUpperCase()}
                  </b>
                </div>
                <div>
                  <span style={{ color: '#666' }}>RUL:</span>
                  <b style={{ color: '#ffd600', display: 'block' }}>
                    {uav.rul_estimate ? `${uav.rul_estimate}s` : 'Nominal'}
                  </b>
                </div>
              </div>

              <div style={{ fontSize: '0.65rem', color: '#aaa', backgroundColor: 'rgba(0,0,0,0.3)', padding: '4px 6px', borderRadius: '3px', marginBottom: '10px' }}>
                🎯 Sector: <b style={{ color: '#00d2ff' }}>{uav.assigned_objective}</b>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <button
                  onClick={() => handleSelect(uav.id)}
                  disabled={loading}
                  style={{
                    padding: '5px 10px',
                    borderRadius: '4px',
                    border: 'none',
                    backgroundColor: isSelected ? 'rgba(0,210,255,0.3)' : 'rgba(255,255,255,0.1)',
                    color: isSelected ? '#00d2ff' : '#ccc',
                    fontSize: '0.7rem',
                    fontWeight: 'bold',
                    cursor: 'pointer'
                  }}
                >
                  {isSelected ? '🎯 Currently Inspecting' : '🔍 Inspect Twin'}
                </button>

                <div style={{ display: 'flex', gap: '4px' }}>
                  <select
                    value={selectedFaults[uav.id] || 'overheating'}
                    onChange={(e) => setSelectedFaults({ ...selectedFaults, [uav.id]: e.target.value })}
                    style={{ flex: 1, backgroundColor: '#1a1a2e', color: '#fff', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '3px', fontSize: '0.65rem', padding: '2px 4px' }}
                  >
                    <option value="overheating">Overheating</option>
                    <option value="lubrication">Lubrication</option>
                    <option value="injector">Injector</option>
                    <option value="vibration">Vibration</option>
                  </select>
                  <button
                    onClick={() => handleInjectFault(uav.id)}
                    style={{ padding: '2px 8px', backgroundColor: 'rgba(255,23,68,0.2)', border: '1px solid #ff1744', borderRadius: '3px', color: '#ff4d4d', fontSize: '0.65rem', cursor: 'pointer' }}
                  >
                    ⚡ Fault
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
