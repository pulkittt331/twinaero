import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function FlightDataRecorderCard({ onFetchReplay, onFetchReport, onDownloadCSV }) {
  const [replayData, setReplayData] = useState(null);
  const [currentFrameIdx, setCurrentFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [reportData, setReportData] = useState(null);
  const [showReportModal, setShowReportModal] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);
  const [downloadingCSV, setDownloadingCSV] = useState(false);

  const fetchReplay = async () => {
    try {
      let data;
      if (onFetchReplay) {
        data = await onFetchReplay();
      } else {
        const res = await axios.get('/api/fdr/replay');
        data = res.data;
      }
      setReplayData(data);
      if (data && data.frames && data.frames.length > 0 && currentFrameIdx === 0) {
        setCurrentFrameIdx(data.frames.length - 1);
      }
    } catch (err) {
      console.error('Failed to fetch FDR replay slice:', err);
    }
  };

  useEffect(() => {
    fetchReplay();
    const interval = setInterval(fetchReplay, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let timer;
    if (isPlaying && replayData && replayData.frames && replayData.frames.length > 0) {
      timer = setInterval(() => {
        setCurrentFrameIdx((prev) => {
          if (prev >= replayData.frames.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1000 / playbackSpeed);
    }
    return () => clearInterval(timer);
  }, [isPlaying, replayData, playbackSpeed]);

  const handleGenerateReport = async () => {
    setLoadingReport(true);
    try {
      let data;
      if (onFetchReport) {
        data = await onFetchReport();
      } else {
        const res = await axios.get('/api/fdr/report');
        data = res.data;
      }
      setReportData(data);
      setShowReportModal(true);
    } catch (err) {
      console.error('Failed to generate diagnostic report:', err);
    } finally {
      setLoadingReport(false);
    }
  };

  const handleDownloadCSV = async () => {
    setDownloadingCSV(true);
    try {
      let csvText;
      if (onDownloadCSV) {
        csvText = await onDownloadCSV();
      } else {
        const endpoints = ['', 'http://127.0.0.1:8000', 'http://localhost:8000'];
        let lastErr = null;
        for (const base of endpoints) {
          try {
            const res = await axios.get(`${base}/api/fdr/download-csv`, { responseType: 'text' });
            csvText = res.data;
            break;
          } catch (e) {
            lastErr = e;
          }
        }
        if (!csvText && lastErr) throw lastErr;
      }

      if (typeof csvText === 'object') {
        csvText = JSON.stringify(csvText);
      }
      
      const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'twinaero_fdr_telemetry.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download FDR CSV:', err);
    } finally {
      setDownloadingCSV(false);
    }
  };

  if (!replayData || !replayData.frames || replayData.frames.length === 0) {
    return (
      <div style={{ marginTop: '20px', padding: '16px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
        <p className="section-header" style={{ margin: 0, marginBottom: '8px' }}>
          📹 Blackbox Flight Data Recorder (FDR)
        </p>
        <p className="desc-text" style={{ fontSize: '0.75rem', color: '#888' }}>
          Initializing FDR time-series telemetry buffer... Run healthy engine or simulate mission to record blackbox frames.
        </p>
      </div>
    );
  }

  const frames = replayData.frames;
  const safeIdx = Math.min(Math.max(0, currentFrameIdx), frames.length - 1);
  const activeFrame = frames[safeIdx] || {};

  return (
    <div style={{ marginTop: '20px', padding: '16px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid rgba(0,210,255,0.2)' }}>
      {/* Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <p className="section-header" style={{ margin: 0 }}>
            📹 Blackbox Flight Data Recorder (FDR) & Replay Scrubber
          </p>
          <span style={{ fontSize: '0.7rem', color: '#aaa' }}>
            Time-series telemetry logging, incident timeline replay, and diagnostic maintenance report export
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={handleGenerateReport}
            disabled={loadingReport}
            style={{ padding: '6px 14px', borderRadius: '4px', backgroundColor: 'rgba(0,210,255,0.15)', border: '1px solid #00d2ff', color: '#00d2ff', fontWeight: 'bold', fontSize: '0.75rem', cursor: 'pointer' }}
          >
            {loadingReport ? '📄 Generating Report...' : '📄 Post-Flight Report'}
          </button>
          <button
            onClick={handleDownloadCSV}
            style={{ padding: '6px 14px', borderRadius: '4px', backgroundColor: 'rgba(0,230,118,0.15)', border: '1px solid #00e676', color: '#00e676', fontWeight: 'bold', fontSize: '0.75rem', cursor: 'pointer' }}
          >
            📥 Download FDR (.csv)
          </button>
        </div>
      </div>

      {/* Replay Controls & Timeline Scrubber */}
      <div style={{ backgroundColor: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.08)', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            style={{ padding: '6px 16px', borderRadius: '4px', backgroundColor: isPlaying ? '#ff9100' : '#00e676', border: 'none', color: '#000', fontWeight: 'bold', fontSize: '0.75rem', cursor: 'pointer' }}
          >
            {isPlaying ? '⏸ Pause' : '▶ Play Replay'}
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: '#aaa' }}>
            <span>Speed:</span>
            {[1, 2, 5, 10].map((s) => (
              <button
                key={s}
                onClick={() => setPlaybackSpeed(s)}
                style={{
                  padding: '2px 8px',
                  borderRadius: '3px',
                  border: playbackSpeed === s ? '1px solid #00d2ff' : '1px solid rgba(255,255,255,0.15)',
                  backgroundColor: playbackSpeed === s ? 'rgba(0,210,255,0.2)' : 'transparent',
                  color: playbackSpeed === s ? '#00d2ff' : '#aaa',
                  cursor: 'pointer',
                  fontSize: '0.65rem'
                }}
              >
                {s}x
              </button>
            ))}
          </div>

          <div style={{ marginLeft: 'auto', fontSize: '0.75rem', color: '#00d2ff', fontWeight: 'bold' }}>
            Frame #{activeFrame.step_id || 0} / {frames.length} ({activeFrame.flight_time_s || 0}s)
          </div>
        </div>

        {/* Range Slider */}
        <input
          type="range"
          min="0"
          max={frames.length - 1}
          value={safeIdx}
          onChange={(e) => {
            setIsPlaying(false);
            setCurrentFrameIdx(parseInt(e.target.value, 10));
          }}
          style={{ width: '100%', cursor: 'pointer', accentColor: '#00d2ff' }}
        />
      </div>

      {/* Frame Active Metrics Inspection */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px', fontSize: '0.75rem' }}>
        <div style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '8px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <span style={{ color: '#888', display: 'block', fontSize: '0.65rem' }}>Replay Altitude</span>
          <b style={{ color: '#fff' }}>{activeFrame.altitude_ft} ft MSL</b>
        </div>
        <div style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '8px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <span style={{ color: '#888', display: 'block', fontSize: '0.65rem' }}>Engine Speed</span>
          <b style={{ color: '#00d2ff' }}>{activeFrame.engine_rpm} RPM</b>
        </div>
        <div style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '8px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <span style={{ color: '#888', display: 'block', fontSize: '0.65rem' }}>Exhaust Temp (EGT)</span>
          <b style={{ color: '#ffd600' }}>{activeFrame.egt_c}°C</b>
        </div>
        <div style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '8px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <span style={{ color: '#888', display: 'block', fontSize: '0.65rem' }}>Health Index</span>
          <b style={{ color: activeFrame.health_index > 80 ? '#00e676' : '#ff1744' }}>{activeFrame.health_index}%</b>
        </div>
        <div style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '8px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <span style={{ color: '#888', display: 'block', fontSize: '0.65rem' }}>Fault Status</span>
          <b style={{ color: activeFrame.fault_status !== 'NORMAL' ? '#ff1744' : '#00e676' }}>{activeFrame.fault_status}</b>
        </div>
      </div>

      {/* Post-Flight Diagnostic Report Modal */}
      {showReportModal && reportData && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.85)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 9999, padding: '20px' }}>
          <div style={{ backgroundColor: '#161922', width: '600px', maxWidth: '100%', borderRadius: '8px', border: '1px solid #00d2ff', padding: '24px', color: '#fff', boxShadow: '0 0 20px rgba(0,210,255,0.3)', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px', marginBottom: '16px' }}>
              <h3 style={{ margin: 0, color: '#00d2ff' }}>📄 Post-Flight Diagnostic Maintenance Report</h3>
              <button onClick={() => setShowReportModal(false)} style={{ background: 'none', border: 'none', color: '#aaa', fontSize: '1.2rem', cursor: 'pointer' }}>✖</button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.8rem', marginBottom: '16px' }}>
              <div><span style={{ color: '#888' }}>Report ID:</span> <b>{reportData.report_id}</b></div>
              <div><span style={{ color: '#888' }}>Target UAV:</span> <b>{reportData.uav_id}</b></div>
              <div><span style={{ color: '#888' }}>Flight Duration:</span> <b>{reportData.flight_duration_sec} seconds</b></div>
              <div><span style={{ color: '#888' }}>Total FDR Frames:</span> <b>{reportData.total_fdr_frames} frames</b></div>
              <div><span style={{ color: '#888' }}>Min Health Index:</span> <b style={{ color: reportData.minimum_health_index > 50 ? '#00e676' : '#ff1744' }}>{reportData.minimum_health_index}%</b></div>
              <div><span style={{ color: '#888' }}>Avg Health Index:</span> <b>{reportData.average_health_index}%</b></div>
            </div>

            <div style={{ marginBottom: '16px', padding: '10px', backgroundColor: 'rgba(0,0,0,0.3)', borderRadius: '4px' }}>
              <span style={{ color: '#aaa', fontSize: '0.75rem', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>Diagnosed Fault Modes:</span>
              <b style={{ color: reportData.diagnosed_faults.includes('NONE (HEALTHY)') ? '#00e676' : '#ff1744', fontSize: '0.85rem' }}>
                {reportData.diagnosed_faults.join(', ')}
              </b>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <span style={{ color: '#00d2ff', fontSize: '0.8rem', fontWeight: 'bold', display: 'block', marginBottom: '6px' }}>🔧 Recommended Maintenance Action Items:</span>
              <ul style={{ fontSize: '0.75rem', color: '#ddd', paddingLeft: '20px' }}>
                {reportData.maintenance_action_items.map((item, idx) => (
                  <li key={idx} style={{ marginBottom: '4px' }}>{item}</li>
                ))}
              </ul>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.7rem', color: '#aaa', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '12px' }}>
              <div>Edge ONNX Model: <b style={{ color: '#00e676' }}>{reportData.edge_onnx_verification}</b></div>
              <div>Cyber Anti-Spoofing: <b style={{ color: '#00e676' }}>{reportData.cyber_security_audit}</b></div>
            </div>

            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                onClick={() => window.print()}
                style={{ padding: '6px 16px', borderRadius: '4px', backgroundColor: '#00d2ff', border: 'none', color: '#000', fontWeight: 'bold', fontSize: '0.75rem', cursor: 'pointer' }}
              >
                🖨️ Print / Save PDF
              </button>
              <button
                onClick={() => setShowReportModal(false)}
                style={{ padding: '6px 16px', borderRadius: '4px', backgroundColor: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', color: '#fff', fontSize: '0.75rem', cursor: 'pointer' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
