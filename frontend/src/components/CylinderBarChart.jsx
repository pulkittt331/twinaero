import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

export default function CylinderBarChart({ lastObs }) {
  const data = [
    {
      Cylinder: 'Cyl 1',
      'CHT (°C)': lastObs.cht1 || 0,
      'EGT (°C)': lastObs.egt1 || 0
    },
    {
      Cylinder: 'Cyl 2',
      'CHT (°C)': lastObs.cht2 || 0,
      'EGT (°C)': lastObs.egt2 || 0
    },
    {
      Cylinder: 'Cyl 3',
      'CHT (°C)': lastObs.cht3 || 0,
      'EGT (°C)': lastObs.egt3 || 0
    },
    {
      Cylinder: 'Cyl 4',
      'CHT (°C)': lastObs.cht4 || 0,
      'EGT (°C)': lastObs.egt4 || 0
    }
  ];

  return (
    <div className="chart-container" style={{ height: 260 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="Cylinder" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="CHT (°C)" fill="#f97316" radius={[4, 4, 0, 0]} />
          <Bar dataKey="EGT (°C)" fill="#ef4444" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
