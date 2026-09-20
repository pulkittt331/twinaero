import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import CylinderBarChart from './CylinderBarChart';

export default function DigitalTwinChart({ statusData }) {
  const [selectedSensor, setSelectedSensor] = useState('cht');

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
    afr: 'Air-Fuel Ratio (AFR)',
    lambda_val: 'Lambda Index (λ)',
    cht1: 'Cylinder 1 CHT',
    cht2: 'Cylinder 2 CHT',
    cht3: 'Cylinder 3 CHT',
    cht4: 'Cylinder 4 CHT',
    egt1: 'Cylinder 1 EGT',
    egt2: 'Cylinder 2 EGT',
    egt3: 'Cylinder 3 EGT',
    egt4: 'Cylinder 4 EGT'
  };

  const obsHistory = statusData?.obs_history || [];
  const resHistory = statusData?.res_history || [];
  const zScores = statusData?.z_scores || {};

  const chartData = obsHistory.map((obs, idx) => {
    const res = resHistory[idx] || {};
    const actual = obs[selectedSensor] !== undefined ? obs[selectedSensor] : 0.0;
    const resKey = `res_${selectedSensor}`;
    const residualVal = res[resKey] !== undefined ? res[resKey] : 0.0;
    const expected = actual - residualVal;
    return {
      timeStep: idx,
      Actual: parseFloat(actual.toFixed(2)),
      'Twin Expected': parseFloat(expected.toFixed(2))
    };
  });

  const lastObs = obsHistory.length > 0 ? obsHistory[obsHistory.length - 1] : {};
  const lastRes = resHistory.length > 0 ? resHistory[resHistory.length - 1] : {};

  const actualVal = lastObs[selectedSensor] !== undefined ? lastObs[selectedSensor] : 0.0;
  const resVal = lastRes[`res_${selectedSensor}`] !== undefined ? lastRes[`res_${selectedSensor}`] : 0.0;
  const expVal = actualVal - resVal;
  const zVal = zScores[selectedSensor] !== undefined ? zScores[selectedSensor] : 0.0;

  // Domain fidelity stats
  const c1_v = lastObs.cht1 || 0.0;
  const c2_v = lastObs.cht2 || 0.0;
  const c3_v = lastObs.cht3 || 0.0;
  const c4_v = lastObs.cht4 || 0.0;
  const spread = Math.max(c1_v, c2_v, c3_v, c4_v) - Math.min(c1_v, c2_v, c3_v, c4_v);
  const mapVal = lastObs.map !== undefined ? lastObs.map : 29.92;
  const knockVal = lastObs.knock_index !== undefined ? lastObs.knock_index : 0.0;
  const afrVal = lastObs.afr !== undefined ? lastObs.afr : 14.7;
  const lambdaVal = lastObs.lambda_val !== undefined ? lastObs.lambda_val : 1.0;

  const energyErr = lastObs.energy_balance_error !== undefined ? lastObs.energy_balance_error : 0.0;
  const thermalEff = lastObs.thermal_efficiency !== undefined ? lastObs.thermal_efficiency : 0.0;

  return (
    <div>
      <p className="section-header">Digital Twin vs Actual Telemetry</p>
      <p className="desc-text">
        The Digital Twin calculates what each sensor <b>should</b> read. The gap between expected and actual is the <b>residual</b> — the signal our AI analyzes.
      </p>

      <select
        className="sensor-select"
        value={selectedSensor}
        onChange={(e) => setSelectedSensor(e.target.value)}
      >
        {Object.entries(friendlyNames).map(([key, name]) => (
          <option key={key} value={key}>
            {name}
          </option>
        ))}
      </select>

      <div className="chart-container" style={{ height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="timeStep" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="Actual"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="Twin Expected"
              stroke="#dc2626"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="residual-metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Actual</div>
          <div className="metric-value">{actualVal.toFixed(1)}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Expected</div>
          <div className="metric-value">{expVal.toFixed(1)}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Residual</div>
          <div className="metric-value">{resVal.toFixed(2)}</div>
          <div className="metric-delta">Z = {zVal.toFixed(1)}</div>
        </div>
      </div>

      <p className="section-header" style={{ marginTop: '24px' }}>
        Aero Engine Domain & PINN Thermodynamics
      </p>

      <div className="residual-metrics-grid" style={{ marginBottom: '16px' }}>
        <div className="metric-card">
          <div className="metric-label">4-Cyl CHT Spread</div>
          <div className="metric-value">{spread.toFixed(1)}°C</div>
          <div className="metric-delta" style={{ color: spread > 35 ? '#dc2626' : '#6b7280' }}>
            {spread > 35 ? 'Misfire Warning' : 'Nominal'}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Air-Fuel Ratio (AFR)</div>
          <div className="metric-value">{afrVal.toFixed(1)}</div>
          <div className="metric-delta" style={{ color: lambdaVal > 1.08 ? '#d97706' : '#065f46' }}>
            {lambdaVal > 1.08 ? 'LEAN BURN (λ=' + lambdaVal.toFixed(2) + ')' : 'Stoichiometric (λ=' + lambdaVal.toFixed(2) + ')'}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">PINN Energy Residual</div>
          <div className="metric-value">{energyErr.toFixed(1)}%</div>
          <div className="metric-delta" style={{ color: energyErr > 10 ? '#dc2626' : '#065f46' }}>
            {energyErr > 10 ? 'Energy Imbalance' : `Thermal Eff: ${thermalEff.toFixed(1)}%`}
          </div>
        </div>
      </div>

      <CylinderBarChart lastObs={lastObs} />
    </div>
  );
}
