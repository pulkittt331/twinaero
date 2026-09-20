import React from 'react';

export default function MissionRiskCard({ missionResults }) {
  if (!missionResults) {
    return (
      <div>
        <p className="section-header">Mission Risk Assessment</p>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <p style={{ fontSize: '2rem', marginBottom: '4px' }}>🚀</p>
          <p className="desc-text" style={{ textAlign: 'center' }}>
            Select a mission profile and click<br />
            <b>"Simulate Future Risk"</b> in the sidebar.
          </p>
        </div>
      </div>
    );
  }

  if (missionResults.error) {
    return (
      <div>
        <p className="section-header">Mission Risk Assessment</p>
        <div className="advisory-box error">
          Simulation failed: {missionResults.error}
        </div>
      </div>
    );
  }

  const { risk, margin, adv, profile } = missionResults;

  let cLabel = "GREEN";
  let fLabel = "GREEN";

  if (risk && risk.includes("|")) {
    const parts = risk.split("|");
    cLabel = parts[0].replace("Current Risk:", "").trim();
    fLabel = parts[1].replace("Future Mission Risk:", "").trim();
  } else if (risk) {
    cLabel = risk;
  }

  const getRiskClass = (label) => {
    if (label === 'RED') return 'risk-card-red';
    if (label === 'AMBER') return 'risk-card-amber';
    return 'risk-card-green';
  };

  const getRiskIcon = (label) => {
    if (label === 'RED') return '🔴';
    if (label === 'AMBER') return '🟡';
    return '🟢';
  };

  const isRed = adv && (adv.includes('RED') || cLabel === 'RED');

  return (
    <div>
      <p className="section-header">Mission Risk Assessment</p>

      <div className={`risk-card ${getRiskClass(cLabel)}`}>
        <h4>Current Engine Condition</h4>
        <p className="risk-value">
          {getRiskIcon(cLabel)} {cLabel}
        </p>
      </div>

      <div className={`risk-card ${getRiskClass(fLabel)}`}>
        <h4>Future Mission — {profile || 'Nominal'}</h4>
        <p className="risk-value">
          {getRiskIcon(fLabel)} {fLabel}
        </p>
      </div>

      <table className="evidence-table">
        <tbody>
          <tr>
            <td>Mission Profile</td>
            <td>{profile || '—'}</td>
          </tr>
          <tr>
            <td>Future Min. Margin</td>
            <td>{margin !== undefined ? margin.toFixed(2) : '—'}</td>
          </tr>
        </tbody>
      </table>

      <div className={`advisory-box ${isRed ? 'error' : 'success'}`}>
        <b>{adv}</b>
      </div>
    </div>
  );
}
