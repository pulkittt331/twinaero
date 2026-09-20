import React, { useState, useEffect } from 'react';
import axios from 'axios';

const HARDWARE_OPTIONS = [
  'NVIDIA Jetson Orin Nano',
  'Raspberry Pi 5',
  'PX4 Companion Computer'
];

export default function EdgeOptimizationCard({ onFetchBenchmark, onExportONNX }) {
  const [selectedDevice, setSelectedDevice] = useState('NVIDIA Jetson Orin Nano');
  const [benchmark, setBenchmark] = useState(null);
  const [loadingBenchmark, setLoadingBenchmark] = useState(false);
  const [exportData, setExportData] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const fetchBenchmark = async (device) => {
    setLoadingBenchmark(true);
    setErrorMsg(null);
    try {
      let data;
      if (onFetchBenchmark) {
        data = await onFetchBenchmark(device);
      } else {
        const res = await axios.get(`/api/edge-benchmark?target_device=${encodeURIComponent(device)}`);
        data = res.data;
      }
      setBenchmark(data);
    } catch (err) {
      console.error('Failed to fetch edge benchmark:', err);
      setErrorMsg('Failed to fetch edge benchmark metrics.');
    } finally {
      setLoadingBenchmark(false);
    }
  };

  useEffect(() => {
    fetchBenchmark(selectedDevice);
  }, [selectedDevice]);

  const handleExport = async () => {
    setExporting(true);
    setErrorMsg(null);
    try {
      let data;
      if (onExportONNX) {
        data = await onExportONNX();
      } else {
        const res = await axios.post('/api/edge-export-onnx');
        data = res.data;
      }
      setExportData(data);
    } catch (err) {
      console.error('Failed to export ONNX model:', err);
      setErrorMsg('ONNX export failed.');
    } finally {
      setExporting(false);
    }
  };

  const handleDownload = () => {
    if (!exportData || !exportData.payload_base64) return;
    const blob = new Blob([atob(exportData.payload_base64)], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = exportData.filename || 'twinaero_pinn_diagnostic_int8.onnx';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ marginTop: '20px', padding: '16px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid rgba(0,210,255,0.2)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <p className="section-header" style={{ margin: 0 }}>
          ⚡ Defense-Grade Edge Optimization & INT8 Quantization Benchmark
        </p>
        <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: '4px', backgroundColor: 'rgba(0,230,118,0.15)', color: '#00e676', border: '1px solid #00e676' }}>
          ARM64 / CUDA Ready
        </span>
      </div>

      <p className="desc-text" style={{ marginBottom: '14px' }}>
        Benchmark real-time inference latency, INT8 memory footprint, and export ONNX / TensorRT runtime models for embedded UAV microcontrollers.
      </p>

      {/* Device Selector */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {HARDWARE_OPTIONS.map((dev) => (
          <button
            key={dev}
            onClick={() => setSelectedDevice(dev)}
            style={{
              padding: '6px 14px',
              borderRadius: '4px',
              border: selectedDevice === dev ? '1px solid #00d2ff' : '1px solid rgba(255,255,255,0.15)',
              backgroundColor: selectedDevice === dev ? 'rgba(0,210,255,0.15)' : 'rgba(0,0,0,0.2)',
              color: selectedDevice === dev ? '#00d2ff' : '#aaa',
              cursor: 'pointer',
              fontSize: '0.75rem',
              fontWeight: selectedDevice === dev ? 'bold' : 'normal',
              transition: 'all 0.2s ease'
            }}
          >
            💻 {dev}
          </button>
        ))}
      </div>

      {errorMsg && (
        <div style={{ padding: '8px 12px', backgroundColor: 'rgba(255,23,68,0.1)', border: '1px solid #ff1744', borderRadius: '4px', color: '#ff4d4d', fontSize: '0.75rem', marginBottom: '12px' }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {/* Benchmark Grid */}
      {benchmark && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
          <div style={{ backgroundColor: 'rgba(0,0,0,0.25)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span style={{ fontSize: '0.7rem', color: '#888', display: 'block' }}>Inference Latency</span>
            <b style={{ fontSize: '1.1rem', color: benchmark.latency_ms <= 2.5 ? '#00e676' : '#ff9100' }}>
              {benchmark.latency_ms} ms
            </b>
            <span style={{ fontSize: '0.65rem', color: '#666', display: 'block' }}>Jitter: ±{benchmark.latency_jitter_ms}ms</span>
          </div>

          <div style={{ backgroundColor: 'rgba(0,0,0,0.25)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span style={{ fontSize: '0.7rem', color: '#888', display: 'block' }}>RAM Footprint</span>
            <b style={{ fontSize: '1.1rem', color: '#00d2ff' }}>
              {benchmark.ram_footprint_mb} MB
            </b>
            <span style={{ fontSize: '0.65rem', color: '#666', display: 'block' }}>INT8 Compressed ({benchmark.quantization_compression})</span>
          </div>

          <div style={{ backgroundColor: 'rgba(0,0,0,0.25)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span style={{ fontSize: '0.7rem', color: '#888', display: 'block' }}>Throughput</span>
            <b style={{ fontSize: '1.1rem', color: '#ffd600' }}>
              {benchmark.throughput_fps} steps/s
            </b>
            <span style={{ fontSize: '0.65rem', color: '#666', display: 'block' }}>Zero Frame-Drop</span>
          </div>

          <div style={{ backgroundColor: 'rgba(0,0,0,0.25)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span style={{ fontSize: '0.7rem', color: '#888', display: 'block' }}>Precision</span>
            <b style={{ fontSize: '0.85rem', color: '#e0e0e0' }}>
              {benchmark.precision}
            </b>
            <span style={{ fontSize: '0.65rem', color: '#00e676', display: 'block' }}>Status: {benchmark.status}</span>
          </div>
        </div>
      )}

      {/* Target Specs Summary */}
      {benchmark && (
        <div style={{ padding: '10px 14px', backgroundColor: 'rgba(0,210,255,0.04)', borderRadius: '6px', border: '1px solid rgba(0,210,255,0.15)', fontSize: '0.75rem', marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#aaa', marginBottom: '4px' }}>
            <span>Target Architecture: <b style={{ color: '#fff' }}>{benchmark.architecture}</b></span>
            <span>Runtime Engine: <b style={{ color: '#00d2ff' }}>{benchmark.framework}</b></span>
          </div>
        </div>
      )}

      {/* Export Action & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="sidebar-btn"
          style={{ width: 'auto', padding: '8px 20px', backgroundColor: '#00e676', color: '#000', fontWeight: 'bold', cursor: 'pointer' }}
        >
          {exporting ? '⚡ Compiling ONNX Model...' : '⚡ Export ONNX / TensorRT Model'}
        </button>

        {exportData && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', color: '#00e676' }}>
            <span>✅ Exported <b>{exportData.filename}</b> ({exportData.byte_size_kb} KB)</span>
            <button
              onClick={handleDownload}
              style={{ padding: '4px 10px', backgroundColor: 'rgba(0,230,118,0.2)', border: '1px solid #00e676', borderRadius: '4px', color: '#00e676', cursor: 'pointer', fontSize: '0.7rem' }}
            >
              📥 Download .onnx
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
