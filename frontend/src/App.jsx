import React, { useState, useEffect } from 'react';
import axios from 'axios';

import Sidebar from './components/Sidebar';
import HeaderBanner from './components/HeaderBanner';
import PipelineBreadcrumb from './components/PipelineBreadcrumb';
import SwarmFleetDashboard from './components/SwarmFleetDashboard';
import TopMetrics from './components/TopMetrics';
import DigitalTwinChart from './components/DigitalTwinChart';
import DiagnosticPipeline from './components/DiagnosticPipeline';
import MissionRiskCard from './components/MissionRiskCard';
import EmergencyAdvisoryCard from './components/EmergencyAdvisoryCard';
import WhatIfSimulator from './components/WhatIfSimulator';
import EdgeOptimizationCard from './components/EdgeOptimizationCard';
import CyberSecurityCard from './components/CyberSecurityCard';
import FlightDataRecorderCard from './components/FlightDataRecorderCard';
import DebugSection from './components/DebugSection';

import './app.css';

const API_ENDPOINTS = [
  '', // Relative URL (uses Vite Proxy)
  'http://127.0.0.1:8000',
  'http://localhost:8000'
];

async function apiRequest(method, endpoint, data = null) {
  let lastError = null;
  for (const base of API_ENDPOINTS) {
    try {
      const url = `${base}${endpoint}`;
      const config = { method, url, data };
      const res = await axios(config);
      return res.data;
    } catch (err) {
      lastError = err;
    }
  }
  throw lastError;
}

export default function App() {
  const [statusData, setStatusData] = useState(null);
  const [missionResults, setMissionResults] = useState(null);
  const [debugMode, setDebugMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const fetchStatus = async () => {
    try {
      const data = await apiRequest('get', '/api/status');
      setStatusData(data);
      setErrorMessage(null);
    } catch (err) {
      console.error('Failed to fetch status', err);
      setErrorMessage('Failed to connect to backend server. Make sure FastAPI server on port 8000 is running.');
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleStartHealthy = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await apiRequest('post', '/api/start-healthy');
      setStatusData(data);
      setMissionResults(null);
    } catch (err) {
      console.error('Error starting healthy engine', err);
      setErrorMessage('Failed to start healthy engine: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleInjectFault = async (faultType) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await apiRequest('post', '/api/inject-fault', { fault_type: faultType });
      setStatusData(data);
      setMissionResults(null);
    } catch (err) {
      console.error('Error injecting fault', err);
      setErrorMessage('Failed to inject fault: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateMission = async (profile) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await apiRequest('post', '/api/simulate-mission', { profile });
      setMissionResults(data);
    } catch (err) {
      console.error('Error simulating mission', err);
      setMissionResults({ error: err.response?.data?.detail || err.message });
      setErrorMessage('Mission simulation failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleIngestMAVLink = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const samplePacket = {
        mavpackettype: "HIGH_LATENCY2",
        altitude: 12000,
        throttle: 85,
        engine_rpm: 4800,
        fuel_flow: 22.4,
        egt: 720.0,
        cht: 165.0,
        temperature: 95.0,
        press: 68.0,
        vibration: 1.8,
        battery_voltage: 26.2,
        manifold_pressure: 34.5,
        knock_index: 3.5,
        afr: 14.2,
        lambda_val: 0.96,
        cht1: 166.0, cht2: 164.0, cht3: 167.0, cht4: 163.0,
        egt1: 725.0, egt2: 718.0, egt3: 728.0, egt4: 715.0
      };
      const data = await apiRequest('post', '/api/ingest-mavlink', { mav_packet: samplePacket });
      setStatusData(data);
      setMissionResults(null);
    } catch (err) {
      console.error('Error ingesting MAVLink packet', err);
      setErrorMessage('Failed to ingest MAVLink packet: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateWhatIf = async (data) => {
    return await apiRequest('post', '/api/what-if-simulate', data);
  };

  const handleFetchBenchmark = async (device) => {
    return await apiRequest('get', `/api/edge-benchmark?target_device=${encodeURIComponent(device)}`);
  };

  const handleExportONNX = async () => {
    return await apiRequest('post', '/api/edge-export-onnx');
  };

  const handleSelectUAV = async (uavId) => {
    const res = await apiRequest('post', '/api/swarm/select', { uav_id: uavId });
    await fetchStatus();
    return res;
  };

  const handleSwarmFault = async (uavId, faultType) => {
    const res = await apiRequest('post', '/api/swarm/inject-fault', { uav_id: uavId, fault_type: faultType });
    await fetchStatus();
    return res;
  };

  const handleFetchSecurity = async () => {
    return await apiRequest('get', '/api/security/status');
  };

  const handleSimulateAttack = async (attackType) => {
    return await apiRequest('post', '/api/security/simulate-attack', { attack_type: attackType });
  };

  const handleFetchReplay = async () => {
    return await apiRequest('get', '/api/fdr/replay');
  };

  const handleFetchReport = async () => {
    return await apiRequest('get', `/api/fdr/report?uav_id=${statusData?.active_uav_id || 'UAV-ALPHA'}`);
  };

  const handleDownloadCSV = async () => {
    return await apiRequest('get', '/api/fdr/download-csv');
  };

  const handleReset = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await apiRequest('post', '/api/reset');
      setStatusData(data);
      setMissionResults(null);
    } catch (err) {
      console.error('Error resetting demo', err);
      setErrorMessage('Failed to reset demo: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const isUninitialized = !statusData || statusData.uninitialized || statusData.current_time === 0;

  return (
    <div className="app-container">
      <Sidebar
        onStartHealthy={handleStartHealthy}
        onInjectFault={handleInjectFault}
        onSimulateMission={handleSimulateMission}
        onIngestMAVLink={handleIngestMAVLink}
        onReset={handleReset}
        activeUAVId={statusData?.active_uav_id || 'UAV-ALPHA'}
        onSelectUAV={handleSelectUAV}
        debugMode={debugMode}
        setDebugMode={setDebugMode}
        loading={loading}
      />

      <main className="main-content">
        <HeaderBanner />
        <PipelineBreadcrumb statusData={statusData} missionResults={missionResults} />

        {errorMessage && (
          <div className="advisory-box error" style={{ marginBottom: '16px' }}>
            ⚠️ {errorMessage}
          </div>
        )}

        {isUninitialized ? (
          <div className="empty-state">
            <div className="empty-state-icon">✈️</div>
            <h3>Ready to Monitor</h3>
            <p>
              Click <b>▶ Start Healthy Engine</b> in the sidebar to begin ingesting telemetry.
            </p>
          </div>
        ) : (
          <>
            <SwarmFleetDashboard onSelectUAV={handleSelectUAV} onSwarmFault={handleSwarmFault} />
            <TopMetrics statusData={statusData} missionResults={missionResults} />

            <div className="dashboard-grid">
              <div style={{ flex: 2.2 }}>
                <DigitalTwinChart statusData={statusData} />
              </div>

              <div style={{ flex: 1.4 }}>
                <DiagnosticPipeline statusData={statusData} />
              </div>

              <div style={{ flex: 1.4 }}>
                <MissionRiskCard missionResults={missionResults} />
              </div>
            </div>

            <EmergencyAdvisoryCard statusData={statusData} />
            <WhatIfSimulator onSimulateWhatIf={handleSimulateWhatIf} />
            <EdgeOptimizationCard onFetchBenchmark={handleFetchBenchmark} onExportONNX={handleExportONNX} />
            <CyberSecurityCard onFetchSecurity={handleFetchSecurity} onSimulateAttack={handleSimulateAttack} />
            <FlightDataRecorderCard onFetchReplay={handleFetchReplay} onFetchReport={handleFetchReport} onDownloadCSV={handleDownloadCSV} />

            {debugMode && <DebugSection statusData={statusData} />}
          </>
        )}
      </main>
    </div>
  );
}
